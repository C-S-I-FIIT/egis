from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from loguru import logger
import ipaddress
import os
import tempfile
import shutil

class ReportGenerator:
    def __init__(self, parsed_data):
        """Initialize report generator with parsed data from vulnerability parser"""
        self.parsed_data = parsed_data
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        logger.info("Initializing report generator")
        
    def _process_data(self):
        """Prepare data for the report template"""
        logger.debug("Processing vulnerability data for report")
        
        # Get the hosts and vulnerabilities from parsed data
        hosts_data = self.parsed_data.get('hosts', [])
        vuln_data = self.parsed_data.get('vulnerabilities', [])
        
        hosts = []
        for host in hosts_data:
            # Copy host data to avoid modifying the original
            host_obj = dict(host)
            host_ip = host_obj['ip']
            
            # Find vulnerabilities for this host
            host_vulns = [v for v in vuln_data if v.get('host_ip') == host_ip]
            
            # Add simple metrics for template
            host_obj['vuln_count'] = len(host_vulns)
            
            # Process vulnerabilities for port severity
            severity_map = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1, None: 0}
            for vuln in host_vulns:
                # Add cvss_score for template compatibility
                vuln['cvss_score'] = vuln.get('cvss', {}).get('v3', {}).get('base_score', 0)
            
            # Sort vulnerabilities for better presentation
            host_vulns = sorted(
                host_vulns,
                key=lambda v: (
                    severity_map.get(v.get('severity'), 0),
                    v.get('cvss_score', 0),
                    -int(v.get('port', 0))
                ),
                reverse=True
            )
            
            # Add processed data to host
            host_obj['vulnerabilities'] = host_vulns
            hosts.append(host_obj)
        
        # Sort hosts by IP
        hosts = sorted(hosts, key=lambda h: self._ip_to_int(h.get('ip', '0.0.0.0')))
        
        # Extract data directly from parsed_data
        organization = self.parsed_data.get('organization', {})
        scanner = self.parsed_data.get('scanner', {})
        scan = self.parsed_data.get('scan', {})
        
        # Format timestamps for the template
        scan_start_datetime = ''
        scan_end_datetime = ''
        try:
            if scan.get('start_timestamp'):
                scan_start_datetime = datetime.fromisoformat(scan.get('start_timestamp')).strftime('%Y-%m-%d %H:%M:%S')
            if scan.get('end_timestamp'):
                scan_end_datetime = datetime.fromisoformat(scan.get('end_timestamp')).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing timestamps: {e}")
            scan_start_datetime = ''
            scan_end_datetime = ''
        
        # Format contact information
        contact = organization.get('primary_contact_name', '')
        if organization.get('primary_contact_email'):
            if contact:
                contact += f" ({organization.get('primary_contact_email')})"
            else:
                contact = organization.get('primary_contact_email')
        
        # Create a dictionary with all data for template rendering
        template_data = {
            # Original data objects
            'organization': organization,
            'scanner': scanner,
            'scan': scan,
            'hosts': hosts,
            
            # Computed data for template
            'scan_start_datetime': scan_start_datetime,
            'scan_end_datetime': scan_end_datetime,
            'organization_contact': contact
        }
        
        logger.debug(f"Report data prepared with {len(hosts)} hosts")
        return template_data
        
    def _ip_to_int(self, ip):
        """Convert IP address to integer for sorting"""
        try:
            return int(ipaddress.ip_address(ip))
        except ValueError:
            return 0

    def generate_html(self, data):
        """Generate HTML from template"""
        logger.info("Generating HTML report")
        template = self.env.get_template('report.html.j2')
        return template.render(data)
        
    def generate_css(self, data):
        """Generate CSS from template"""
        logger.info("Generating CSS from template")
        template = self.env.get_template('styles.css.j2')
        return template.render(data)

    def generate_pdf(self, output_dir, report_filename):
        """Generate PDF report, HTML and CSS files"""
        logger.info(f"Generating report: {report_filename}")
        data = self._process_data()
        html_content = self.generate_html(data)
        css_content = self.generate_css(data)
        
        # Get organization name for filename
        org_name = data.get('organization', {}).get('name', '').replace(' ', '_')
        if org_name and not report_filename.startswith(org_name):
            report_filename = f"{org_name}_{report_filename}"
        
        # Save HTML content for debugging
        html_debug_path = f"{os.path.join(output_dir, report_filename)}.html"
        with open(html_debug_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved HTML content to {html_debug_path}")
        
        # Save processed CSS to output directory
        css_path = os.path.join(output_dir, 'styles.css')
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
        logger.info(f"Saved processed CSS to {css_path}")
        
        try:
            # Generate PDF from HTML content with processed CSS
            css = CSS(string=css_content)
            pdf_path = os.path.join(output_dir, report_filename) + ".pdf"
            HTML(string=html_content, base_url=output_dir).write_pdf(
                pdf_path,
                stylesheets=[css]
            )
            logger.info(f"PDF report successfully saved to: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
