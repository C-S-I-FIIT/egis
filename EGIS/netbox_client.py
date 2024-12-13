import pynetbox
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetboxClient:
    def __init__(self, url, token):
        self.nb = pynetbox.api(url, token=token)
        self.nb.http_session.verify = False
    
    def get_devices_for_scanning(self):
        """Get list of IP addresses tagged with 'vuln-scan' from Netbox"""
        # Get all IP addresses with the vuln-scan tag
        ip_addresses = self.nb.ipam.ip_addresses.filter(tag='vuln-scan')
        scan_targets = []
        
        for ip in ip_addresses:
            if ip.address:  # Ensure IP address exists
                scan_targets.append({
                    'ip': str(ip.address).split('/')[0],  # Remove CIDR notation
                    'name': ip.dns_name or 'Unknown',
                    'description': ip.description or 'No description'
                })
                
        return scan_targets 