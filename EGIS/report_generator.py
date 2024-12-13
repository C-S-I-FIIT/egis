from datetime import datetime

class ReportGenerator:
    def __init__(self, vulnerabilities):
        self.vulnerabilities = vulnerabilities
        
    def generate_markdown(self):
        """Generate markdown report from Elasticsearch vulnerabilities"""
        # Group vulnerabilities by severity
        vulns_by_severity = {
            'Critical': [],
            'High': [],
            'Medium': [],
            'Low': [],
            'Info': []
        }
        
        for vuln in self.vulnerabilities:
            severity = vuln.get('risk', 'Info')
            vulns_by_severity[severity].append(vuln)
            
        # Generate markdown
        markdown = ["# Vulnerability Scan Report\n"]
        markdown.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Add summary section
        markdown.append("\n## Summary\n")
        for severity in vulns_by_severity:
            count = len(vulns_by_severity[severity])
            if count > 0:
                markdown.append(f"- **{severity}**: {count} findings")
        
        # Detailed findings
        for severity in vulns_by_severity:
            vulns = vulns_by_severity[severity]
            if vulns:
                markdown.append(f"\n## {severity} Severity Findings ({len(vulns)})\n")
                for vuln in vulns:
                    markdown.append(f"\n### {vuln.get('name', 'Unknown Vulnerability')}")
                    markdown.append(f"\n- **Host:** {vuln.get('host', 'N/A')}")
                    markdown.append(f"\n- **Port:** {vuln.get('port', 'N/A')}")
                    markdown.append(f"\n- **Protocol:** {vuln.get('protocol', 'N/A')}")
                    markdown.append(f"\n- **CVSS Score:** {vuln.get('cvss3_base_score', vuln.get('cvss_base_score', 'N/A'))}")
                    
                    if vuln.get('cve'):
                        markdown.append(f"\n- **CVE(s):** {', '.join(vuln['cve'])}")
                    
                    markdown.append(f"\n\n**Synopsis:**\n{vuln.get('synopsis', 'N/A')}")
                    markdown.append(f"\n\n**Description:**\n{vuln.get('description', 'N/A')}")
                    markdown.append(f"\n\n**Solution:**\n{vuln.get('solution', 'N/A')}")
                    
                    if vuln.get('see_also'):
                        markdown.append(f"\n\n**References:**")
                        for ref in vuln['see_also']:
                            if ref.strip():
                                markdown.append(f"\n- {ref}")
                    markdown.append("\n")
                    
        return "\n".join(markdown) 