from datetime import datetime
import time
from EGIS.config import *
from EGIS.netbox_client import NetboxClient
from EGIS.nessus_scanner import NessusScanner
from EGIS.elastic_client import ElasticClient
from EGIS.vulnerability_parser import VulnerabilityParser
from EGIS.report_generator import ReportGenerator

class ScanManager:
    def __init__(self):
        self.netbox = NetboxClient(NETBOX_URL, NETBOX_TOKEN)
        self.scanner = NessusScanner(NESSUS_URL, NESSUS_ACCESSKEY, NESSUS_SECRETKEY)
        self.elastic = ElasticClient(ELASTIC_URL, ELASTIC_INDEX, ELASTIC_APIKEY)
        
    def run_scan(self):
        # Get targets from Netbox
        targets = self.netbox.get_devices_for_scanning()
        if not targets:
            print("No targets found in Netbox")
            return
            
        # Create scan
        scan_name = f"Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        scan_id = self.scanner.create_scan(scan_name, [t['ip'] for t in targets])
        print(f"Created scan: {scan_name}")
        
        # Launch and wait for completion
        if not self.scanner.launch_scan(scan_id):
            print("Failed to launch scan")
            return
            
        while self.scanner.get_scan_status(scan_id) != 'completed':
            time.sleep(30)
            
        # Process results
        csv_data = self.scanner.export_results(scan_id)
        parser = VulnerabilityParser(csv_data, scan_name)
        vulns = parser.parse()
        
        # Store in Elasticsearch
        for vuln in vulns:
            self.elastic.store_vulnerability(vuln)
            
        # Generate report
        es_vulns = self.elastic.get_vulnerabilities(scan_name)
        report = ReportGenerator(es_vulns)
        markdown = report.generate_markdown()
        
        # Save reports
        with open(f"{SCAN_REPORTS_DIR}/{scan_name}.csv", 'wb') as f:
            f.write(csv_data)
        with open(f"{MARKDOWN_REPORTS_DIR}/{scan_name}.md", 'w') as f:
            f.write(markdown) 