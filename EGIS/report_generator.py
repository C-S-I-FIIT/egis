from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from loguru import logger

class ReportGenerator:
    def __init__(self, scan_details):
        self.scan_details = scan_details
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        logger.info("Initializing report generator")
        
    def _process_data(self):
        logger.debug("Processing scan data for report")
        
        # Process scan info
        scan_info = self.scan_details.get('info', {})
        scan_start = datetime.fromtimestamp(int(scan_info.get('scan_start', 0)))
        scan_end = datetime.fromtimestamp(int(scan_info.get('scan_end', 0)))
        
        # Process vulnerability counts
        vuln_counts = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0,
            'Info': 0
        }
        
        # Process hosts and their vulnerabilities
        hosts = {}
        for host in self.scan_details.get('hosts', []):
            host_ip = host.get('hostname')
            hosts[host_ip] = {
                'ip': host_ip,
                'vuln_count': host.get('info', 0) + host.get('low', 0) + 
                            host.get('medium', 0) + host.get('high', 0) + 
                            host.get('critical', 0),
                'vulnerabilities': []
            }
            
        # Process vulnerabilities
        for vuln in self.scan_details.get('vulnerabilities', []):
            severity = self._get_severity_text(vuln.get('severity', 0))
            if severity in vuln_counts:
                vuln_counts[severity] += 1
                
            # Add vulnerability to each affected host
            for host_ip in hosts:
                hosts[host_ip]['vulnerabilities'].append({
                    'name': vuln.get('plugin_name'),
                    'severity': severity,
                    'description': vuln.get('description', ''),
                    'solution': vuln.get('solution', ''),
                    'plugin_id': vuln.get('plugin_id'),
                    'plugin_family': vuln.get('plugin_family')
                })
        
        # Process scan notes/warnings
        notes = []
        for note in self.scan_details.get('notes', {}).get('note', []):
            notes.append({
                'title': note.get('title'),
                'message': note.get('message'),
                'severity': note.get('severity')
            })
        
        return {
            'scan_name': scan_info.get('name'),
            'scan_start_date': scan_start.strftime('%Y-%m-%d'),
            'scan_start_time': scan_start.strftime('%H:%M'),
            'scan_end_time': scan_end.strftime('%H:%M'),
            'scanner_name': scan_info.get('scanner_name', 'Unknown'),
            'policy': scan_info.get('policy', 'Unknown'),
            'targets': scan_info.get('targets', '').split(','),
            'vuln_counts': vuln_counts,
            'hosts': list(hosts.values()),
            'notes': notes
        }

    def _get_severity_text(self, severity_level):
        severity_map = {
            0: 'Info',
            1: 'Low',
            2: 'Medium',
            3: 'High',
            4: 'Critical'
        }
        return severity_map.get(severity_level, 'Info')

    def generate_html(self):
        logger.info("Generating HTML report")
        template = self.env.get_template('main.html.j2')
        return template.render(self._process_data())

    def generate_pdf(self, output_path):
        logger.info(f"Generating PDF report: {output_path}")
        html_content = self.generate_html()
        HTML(string=html_content).write_pdf(output_path)
        logger.info(f"PDF report saved to: {output_path}") 