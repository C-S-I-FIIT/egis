from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from loguru import logger
import ipaddress
import os
import tempfile
import shutil

class ReportGenerator:
    def __init__(self, scan_details):
        self.scan_details = scan_details
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        logger.info("Initializing report generator")
        
    def _process_data(self):
        logger.debug("Processing vulnerability data for report")
        
        # For CSV parser format, use scan_details directly
        # The VulnerabilityParser already excludes Info vulnerabilities from counts
        # but includes all ports regardless of vulnerability severity
        
        # Get the hosts and apply preprocessing
        hosts = self._sort_hosts(self.scan_details.get('hosts', []))
        
        # Preprocess each host to add port severities and sort vulnerabilities
        for host in hosts:
            # Create a dictionary to map ports to their severities
            port_severities = {}
            # Create a set to track which ports have vulnerabilities
            ports_with_vulns = set()
            
            # Initialize severities for all ports
            for port in host.get('open_ports', []):
                port_severities[port] = None
            
            # Map severity to numeric value for comparison
            severity_map = {
                'Critical': 4,
                'High': 3,
                'Medium': 2,
                'Low': 1,
                None: 0
            }
            
            # Check each vulnerability and update port severity if higher
            for vuln in host.get('vulnerabilities', []):
                port = vuln.get('port')
                if port in port_severities:
                    vuln_severity = vuln.get('severity')
                    current_severity = port_severities[port]
                    
                    if severity_map.get(vuln_severity, 0) > severity_map.get(current_severity, 0):
                        port_severities[port] = vuln_severity
                    
                    # Mark this port as having a vulnerability
                    ports_with_vulns.add(port)
            
            # Sort vulnerabilities by severity (highest first), then by CVSS score (highest first),
            # and finally by port number (lowest first)
            host['vulnerabilities'] = sorted(
                host.get('vulnerabilities', []),
                key=lambda v: (
                    severity_map.get(v.get('severity'), 0),  # Primary: severity (highest first)
                    v.get('cvss_score', 0),                  # Secondary: CVSS score (highest first)
                    -int(v.get('port', 0))                   # Tertiary: port (lowest first)
                ),
                reverse=True
            )
            
            # Add port severities to host data
            host['port_severities'] = port_severities
            # Add the set of ports with vulnerabilities
            host['ports_with_vulns'] = list(ports_with_vulns)
        
        # Already processed data can be passed directly to template
        report_data = {
            'scan_name': self.scan_details.get('scan_name', 'Vulnerability Scan'),
            'scan_start_date': self.scan_details.get('scan_start_date', datetime.now().strftime('%Y-%m-%d')),
            'scan_start_time': self.scan_details.get('scan_start_time', datetime.now().strftime('%H:%M')),
            'scan_end_time': self.scan_details.get('scan_end_time', datetime.now().strftime('%H:%M')),
            'scanner_name': self.scan_details.get('scanner_name', 'Nessus'),
            'policy': self.scan_details.get('policy', 'Advanced Scan'),
            'targets': self.scan_details.get('targets', []),
            'vuln_counts': self.scan_details.get('vuln_counts', {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}),
            'hosts': hosts,
            'executive_summary': self.scan_details.get('executive_summary', {})
        }
        
        # Add organization info (this would typically come from configuration)
        report_data['organization'] = {
            'name': 'Organisation X',
            'contact': 'person.x@orgx.com',
            'testing_date': datetime.now().strftime('%d.%m.%Y'),
            'identification_number': datetime.now().strftime('%Y-%m-%d')
        }
        
        logger.debug(f"Report data prepared with {len(report_data['hosts'])} hosts")
        return report_data
    
    def _sort_hosts(self, hosts):
        # Sort hosts by IP address
        return sorted(hosts, key=lambda h: self._ip_to_int(h.get('ip', '0.0.0.0')))
        
    def _ip_to_int(self, ip):
        # Convert IP address to integer for sorting
        try:
            return int(ipaddress.ip_address(ip))
        except ValueError:
            return 0

    def generate_html(self):
        logger.info("Generating HTML report")
        template = self.env.get_template('report.html.j2')
        return template.render(self._process_data())
        
    def generate_css(self):
        logger.info("Generating CSS from template")
        template = self.env.get_template('styles.css.j2')
        return template.render(self._process_data())

    def generate_pdf(self, output_dir, report_filename):
        logger.info(f"Generating PDF report: {os.path.join(output_dir, report_filename)}.pdf")
        html_content = self.generate_html()
        css_content = self.generate_css()
        
        # Save HTML content for debugging
        html_debug_path = f"{os.path.join(output_dir, report_filename)}.html"
        with open(html_debug_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved HTML content to {html_debug_path} for troubleshooting")
        
        # Save processed CSS to output directory
        css_path = os.path.join(output_dir, 'styles.css')
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
        logger.info(f"Saved processed CSS to {css_path}")
        
        try:
            # Generate PDF from HTML content with processed CSS
            css = CSS(string=css_content)
            HTML(string=html_content, base_url=output_dir).write_pdf(
                os.path.join(output_dir, report_filename) + ".pdf",
                stylesheets=[css]
            )
            logger.info(f"PDF report successfully saved to: {os.path.join(output_dir, report_filename)}.pdf")
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
