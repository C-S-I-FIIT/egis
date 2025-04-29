import pynetbox
import urllib3
from loguru import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetboxClient:
    def __init__(self, url, token):
        self.nb = pynetbox.api(url, token=token)
        self.nb.http_session.verify = False
        logger.info(f"Initializing Netbox client with URL: {url}")
    
    def get_devices_for_scanning(self):
        # Get all IP addresses with the 'vuln-scan' tag from NetBox
        ip_addresses = self.nb.ipam.ip_addresses.filter(tag='vuln-scan')
        scan_targets = []
        
        logger.info("Fetching IP addresses tagged with 'vuln_scan' from Netbox")
        
        for ip in ip_addresses:
            if ip.address:  # Ensure IP address exists
                scan_targets.append({
                    'ip': str(ip.address).split('/')[0],  # Remove CIDR notation
                    'name': ip.dns_name or 'Unknown',
                    'description': ip.description or 'No description'
                })
                
        logger.debug(f"Found {len(ip_addresses)} IP addresses with 'vuln_scan' tag")
        logger.info(f"Prepared {len(scan_targets)} targets for scanning")
        
        return scan_targets 