from datetime import datetime
import json
import time
from config import *
from netbox_client import NetboxClient
from nessus_scanner import NessusScanner
from elastic_client import ElasticClient
from vulnerability_parser import VulnerabilityParser
from report_generator import ReportGenerator
import os
from loguru import logger

class AppController:
    def __init__(self):
        self.netbox = NetboxClient(NETBOX_URL, NETBOX_TOKEN)
        self.scanner = NessusScanner(NESSUS_URL, NESSUS_ACCESSKEY, NESSUS_SECRETKEY)
        self.elastic = ElasticClient(ELASTIC_URL, ELASTIC_INDEX, ELASTIC_APIKEY)
        logger.info("Initializing AppController")

    def _wait_for_scan_completion(self, scan_id):
        """
        Wait for a Nessus scan to complete, checking status every 30 seconds.
        
        Args:
            scan_id: The ID of the Nessus scan to monitor
        """
        # Wait for scan to complete, checking status every 30 seconds
        while self.scanner.get_scan_status(scan_id) != 'completed':
            time.sleep(30)
            logger.debug(f"Scan {scan_id} status: {self.scanner.get_scan_status(scan_id)}")
        logger.info(f"Scan {scan_id} completed")

    def _parse_data_and_generate_reports(self, csv_data, netbox_targets=None, org_name=None):
        """
        Parse CSV data, generate reports, and store vulnerability data in Elasticsearch.
        
        Args:
            csv_data: Raw CSV data from Nessus
            netbox_targets: Optional list of detailed target information from Netbox for enrichment
            org_name: Optional organization name to include in the report name
        """
        # First parse vulnerabilities from CSV data
        logger.info("Parsing vulnerabilities from CSV data")
        parser = VulnerabilityParser(csv_data, netbox_targets)
        parsed_data, documents = parser.parse()
        
        # No documents were generated
        if not documents:
            logger.error("No vulnerability documents were generated from the CSV data")
            return

        report_scan_name = parsed_data['scan']['name']  
        if not report_scan_name:
            report_scan_name = f"Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate reports using the parsed data
        report = ReportGenerator(parsed_data)
        
        # Save CSV export (raw data from Nessus)
        csv_path = os.path.join(RAW_DATA_DIR, f"{report_scan_name}.csv")
        with open(csv_path, 'wb') as f:
            f.write(csv_data)
        logger.info(f"Nessus CSV export saved to: {csv_path}")
        
        # Generate and save PDF report
        pdf_path = report.generate_pdf(REPORTS_DIR, report_scan_name)
        if pdf_path:
            logger.info(f"PDF report saved to: {pdf_path}")
        else:
            logger.error("Failed to generate PDF report")

        # Store parsed vulnerabilities in Elasticsearch
        if ELASTIC_URL and ELASTIC_INDEX and ELASTIC_APIKEY:
            try:
                logger.info("Storing vulnerabilities in Elasticsearch")
                # Store documents in a JSON file
                json_path = os.path.join(RAW_DATA_DIR, f"{report_scan_name}.json")
                with open(json_path, 'w') as f:
                    json.dump(documents, f, indent=2)
                logger.info(f"Vulnerability data saved to: {json_path}")
                
                # Store documents in Elasticsearch
                doc_ids = self.elastic.store_vulnerabilities_bulk(documents)
                logger.info(f"Successfully stored {len(doc_ids)} vulnerabilities in Elasticsearch")
            except Exception as e:
                logger.error(f"Failed to store vulnerabilities: {e}")
        else:
            logger.warning("Elasticsearch integration not configured - skipping data upload")

        # TODO: Generate and save Netbox services CSV
        # netbox_csv_path = os.path.join(SCAN_REPORTS_DIR, f"{scan_name}_netbox.csv")
        # report.generate_netbox_csv(netbox_csv_path, vulnerabilities)
    def run_scan_for_selected_orgs(self, org_ids):
        """
        Execute vulnerability assessments for the specified organizations.
        
        Args:
            org_ids: List of organization IDs to run scans for
            
        Returns:
            dict: Status for each scanned organization
        """
        logger.info(f"Starting vulnerability assessments for organizations: {org_ids}")
        
        results = {}
        total_orgs = len(org_ids)
        
        # Run scan for each organization
        for index, org_id in enumerate(org_ids, 1):
            org_info = self.netbox.get_organization_by_id(org_id)
            org_name = org_info.get('name', f'Organization {org_id}') if org_info else f'Organization {org_id}'
            
            logger.info(f"Processing organization {index}/{total_orgs}: {org_name} (ID: {org_id})")
            results[org_id] = self.run_organization_scan(org_id)
            
            # Log the result of this organization scan
            status = results[org_id].get('status', 'unknown')
            if status == 'completed':
                logger.info(f"Completed scan for organization {org_name}")
            else:
                logger.warning(f"Scan for organization {org_name} ended with status: {status}")
        
        logger.info(f"Completed all {total_orgs} organization scans")
        return results

    def run_organization_scan(self, org_id):
        """
        Run a complete vulnerability scan for a single organization.
        
        Args:
            org_id: The ID of the organization to run a scan for
            
        Returns:
            dict: Status of the scan for this organization
        """
        org_info = self.netbox.get_organization_by_id(org_id)
        if not org_info:
            logger.error(f"Could not get organization info for ID {org_id}. Aborting scan.")
            return {'status': 'error', 'message': 'Could not get organization info'}
        
        org_name = org_info.get('name', '').replace(' ', '_')
        logger.info(f"Running scan for organization: {org_name}")
        
        # Get IP addresses and target information for this organization
        ip_list, target_info = self.netbox.get_scan_targets_for_organization(org_id)
        
        if not ip_list:
            logger.error(f"No scan targets found for organization {org_name}. Aborting scan.")
            return {'status': 'error', 'message': 'No scan targets found'}
        
        # Create scan with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        scan_name = f"{org_name}_EGIS_Assessment_{timestamp}"
        
        try:
            # Create scan in Nessus
            scan_id = self.scanner.create_scan(scan_name, ip_list)
            logger.info(f"Created scan {scan_id} for organization {org_name}")
            
            # Launch the scan
            if not self.scanner.launch_scan(scan_id):
                logger.error(f"Failed to launch scan {scan_id} for organization {org_name}")
                return {'status': 'failed', 'message': 'Failed to launch scan'}
                
            logger.info(f"Launched scan {scan_id} for organization {org_name}")
            
            # Wait for scan completion
            self._wait_for_scan_completion(scan_id)
            
            # Get results from Nessus
            csv_data = self.scanner.export_scan_results(scan_id)
            
            # Process results
            self._parse_data_and_generate_reports(csv_data, target_info, org_name)
            
            return {
                'status': 'completed',
                'scan_id': scan_id,
                'scan_name': scan_name
            }
            
        except Exception as e:
            logger.error(f"Error running scan for organization {org_name}: {e}")
            return {'status': 'error', 'message': str(e)}

    def process_completed_nessus_scan(self, scan_id, org_id=None):
        """
        Process a completed Nessus scan by ID with optional organization-specific enrichment.
        
        Args:
            scan_id: The ID of the Nessus scan to process
            org_id: Optional organization ID to use for target enrichment
        """
        logger.info(f"Processing Nessus scan with ID: {scan_id}")
        
        # Get CSV data from Nessus
        csv_data = self.scanner.export_scan_results(scan_id)
        
        # Get target information for enrichment if org_id is provided
        netbox_targets = None
        org_name = None
        
        if org_id:
            # Get organization info for scan name
            org_info = self.netbox.get_organization_by_id(org_id)
            if org_info:
                org_name = org_info.get('name', '').replace(' ', '_')
                
            # Get targets for this organization
            _, netbox_targets = self.netbox.get_scan_targets_for_organization(org_id)
        
        # Process data and generate reports
        self._parse_data_and_generate_reports(csv_data, netbox_targets, org_name)

    def process_local_csv(self, csv_file_path, org_id=None):
        """
        Process a locally saved CSV file and generate reports with optional organization enrichment.
        
        Args:
            csv_file_path: Path to the local CSV file
            org_id: Optional organization ID to use for target enrichment
        """
        logger.info(f"Processing local CSV file: {csv_file_path}")
            
        with open(csv_file_path, 'rb') as f:
            csv_data = f.read()
        
        # Get target information for enrichment if org_id is provided
        netbox_targets = None
        org_name = None
        
        if org_id:
            # Get organization info for scan name
            org_info = self.netbox.get_organization_by_id(org_id)
            if org_info:
                org_name = org_info.get('name', '').replace(' ', '_')
                
            # Get targets for this organization
            _, netbox_targets = self.netbox.get_scan_targets_for_organization(org_id)
        
        # Process data and generate reports
        self._parse_data_and_generate_reports(csv_data, netbox_targets, org_name)

    def get_organizations(self):
        """
        Get all organizations (tenants) from Netbox.
        
        Returns:
            list: A list of tenant objects containing tenant information
        """
        return self.netbox.get_all_organizations()

