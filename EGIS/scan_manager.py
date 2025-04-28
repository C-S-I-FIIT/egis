from datetime import datetime
import time
from config import *
from netbox_client import NetboxClient
from nessus_scanner import NessusScanner
from elastic_client import ElasticClient
from vulnerability_parser import VulnerabilityParser
from report_generator import ReportGenerator
import os
from loguru import logger

class ScanManager:
    def __init__(self):
        self.netbox = NetboxClient(NETBOX_URL, NETBOX_TOKEN)
        self.scanner = NessusScanner(NESSUS_URL, NESSUS_ACCESSKEY, NESSUS_SECRETKEY)
        self.elastic = ElasticClient(ELASTIC_URL, ELASTIC_INDEX, ELASTIC_APIKEY)
        logger.info("Initializing ScanManager")

    def _get_scan_targets(self):
        # Get targets from Netbox and return their IPs
        targets = self.netbox.get_devices_for_scanning()
        if not targets:
            logger.error("No targets found in Netbox")
            return None
        return [t['ip'] for t in targets]

    def _wait_for_scan_completion(self, scan_id):
        # Wait for scan to complete, checking status every 30 seconds
        while self.scanner.get_scan_status(scan_id) != 'completed':
            time.sleep(30)
            logger.debug(f"Scan {scan_id} status: {self.scanner.get_scan_status(scan_id)}")
        logger.info(f"Scan {scan_id} completed")

    def _generate_reports(self, scan_name, scan_details, csv_data):
        # Generate and save all report types
        # First parse vulnerabilities from CSV data
        logger.info("Parsing vulnerabilities from CSV data")
        parser = VulnerabilityParser(csv_data, scan_name, scan_details)
        vulnerability_data = parser.parse()
        
        # Generate reports using the parsed vulnerability data
        report = ReportGenerator(vulnerability_data)
        
        # Save CSV export (raw data from Nessus)
        csv_path = os.path.join(RAW_DATA_DIR, f"{scan_name}.csv")
        with open(csv_path, 'wb') as f:
            f.write(csv_data)
        logger.info(f"Nessus CSV export saved to: {csv_path}")
        
        # Generate and save PDF report
        report.generate_pdf(REPORTS_DIR, scan_name)

        # TODO: Generate and save Netbox services CSV
        # netbox_csv_path = os.path.join(SCAN_REPORTS_DIR, f"{scan_name}_netbox.csv")
        # report.generate_netbox_csv(netbox_csv_path, vulnerabilities)

        # Optional: Store parsed vulnerabilities in Elasticsearch
        # try:
        #     logger.info("Attempting to store vulnerabilities in Elasticsearch")
        #     for host in vulnerability_data.get('hosts', []):
        #         for vuln in host.get('vulnerabilities', []):
        #             self.elastic.store_vulnerability({
        #                 'host_ip': host['ip'],
        #                 'severity': vuln['severity'],
        #                 'plugin_name': vuln['name'],
        #                 'plugin_id': vuln['plugin_id'],
        #                 'scan_name': scan_name,
        #                 'scan_time': datetime.now().isoformat()
        #             })
        #     logger.info("Successfully stored vulnerabilities in Elasticsearch")
        # except Exception as e:
        #     logger.error(f"Failed to store vulnerabilities in Elasticsearch: {e}")

    def run_new_scan(self):
        # Complete scan workflow: targets -> scan -> process -> store -> report
        targets = self._get_scan_targets()
        if not targets:
            return
            
        scan_name = f"Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        scan_id = self.scanner.create_scan(scan_name, targets)
        
        # Launch the scan using the launch endpoint
        if not self.scanner.launch_scan(scan_id):
            logger.error(f"Failed to launch scan {scan_id}")
            return
            
        self._wait_for_scan_completion(scan_id)

        self.process_existing_scan(scan_id)

    def process_existing_scan(self, scan_id):
        # Process an existing scan and generate reports

        # Get scan details
        scan_details = self.scanner.get_scan_details(scan_id)
        scan_name = scan_details.get('info', {}).get('name', f"Scan_{scan_id}")

        # Export CSV data
        csv_data = self.scanner.export_scan_results(scan_id)

        # Generate reports with scan details
        self._generate_reports(scan_name, scan_details, csv_data)

    def process_local_csv(self, csv_file_path, scan_name=None):
        # Process a locally saved CSV file and generate reports
        if not scan_name:
            scan_name = f"Local_Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        with open(csv_file_path, 'rb') as f:
            csv_data = f.read()
            
        # Create empty scan details for local CSV
        scan_details = {
            "info": {
                "name": scan_name,
                "timestamp": int(datetime.now().timestamp()),
                "scan_end": int(datetime.now().timestamp()) + 3600,  # Assume 1hr scan
                "scanner_name": "Nessus",
                "policy": "Local Import"
            }
        }
        
        # Generate reports with basic scan details
        self._generate_reports(scan_name, scan_details, csv_data)

