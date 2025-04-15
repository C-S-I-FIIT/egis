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
        
    def run_scan(self):
        # Get targets from Netbox
        targets = self.netbox.get_devices_for_scanning()
        if not targets:
            logger.error("No targets found in Netbox")
            return
            
        # Create scan
        scan_name = f"Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        scan_id = self.scanner.create_scan(scan_name, [t['ip'] for t in targets])
        logger.info(f"Created scan: {scan_name}")
        
        # Launch and wait for completion
        while self.scanner.get_scan_status(scan_id) != 'completed':
            time.sleep(30)
            
        # Process results
        csv_data = self.scanner.export_scan_results(scan_id)
        #parser = VulnerabilityParser(csv_data, scan_name)
        #vulns = parser.parse()
        
        # # Store in Elasticsearch
        # for vuln in vulns:
        #     self.elastic.store_vulnerability(vuln)
            
        # Generate report
        #es_vulns = self.elastic.get_vulnerabilities(scan_name)
        #report = ReportGenerator(vulns)
        #markdown = report.generate_markdown()
        
        # Save reports
        with open(f"{SCAN_REPORTS_DIR}/{scan_name}.csv", 'wb') as f:
            f.write(csv_data)
        #with open(f"{MARKDOWN_REPORTS_DIR}/{scan_name}.md", 'w') as f:
        #    f.write(markdown)
        
        # Generate PDF
        #pdf_path = os.path.join(MARKDOWN_REPORTS_DIR, f"{scan_name}.pdf")
        #report.generate_pdf(f"{MARKDOWN_REPORTS_DIR}/{scan_name}.md", pdf_path)
        
        #logger.info(f"Generated reports:\nMarkdown: {f"{MARKDOWN_REPORTS_DIR}/{scan_name}.md"}\nPDF: {pdf_path}") 

    def process_scan_results(self, scan_id):
        # Get raw data from Nessus
        scan_details = self.scanner.get_scan_details(scan_id)
        
        # Generate report
        report = ReportGenerator(scan_details)
        report.generate_pdf(f"reports/scan_{scan_id}.pdf")

    def debug_post_scan(self, csv_file_path):
        # Debug method to test post-scanning functionality
        logger.info("Starting post-scan debug...")
        
        # Read existing CSV file
        with open(csv_file_path, 'rb') as f:
            csv_content = f.read()
        
        # Create scan name for testing
        scan_name = f"Debug_Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Processing scan results for: {scan_name}")
        
        # Parse vulnerabilities
        parser = VulnerabilityParser(csv_content, scan_name)
        vulnerabilities = parser.parse()
        logger.info(f"Parsed {len(vulnerabilities)} vulnerabilities")
        
        # Store in Elasticsearch
        # for vuln in vulnerabilities:
        #     self.elastic.store_vulnerability(vuln)
        # print("Stored vulnerabilities in Elasticsearch")
        
        # Generate report from Elasticsearch data
        #es_vulns = self.elastic.get_vulnerabilities(scan_name)
        report = ReportGenerator(vulnerabilities)
        markdown = report.generate_markdown()
        
        # Save markdown report
        markdown_path = os.path.join(MARKDOWN_REPORTS_DIR, f"{scan_name}.md")
        with open(markdown_path, 'w') as f:
            f.write(markdown)
        
        # Generate PDF
        pdf_path = os.path.join(MARKDOWN_REPORTS_DIR, f"{scan_name}.pdf")
        report.generate_pdf(markdown_path, pdf_path)
        
        logger.info(f"Generated reports:\nMarkdown: {markdown_path}\nPDF: {pdf_path}") 
