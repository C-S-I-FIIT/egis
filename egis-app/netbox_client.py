import pynetbox
import urllib3
from loguru import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetboxClient:
    def __init__(self, url, token):
        self.nb = pynetbox.api(url, token=token)
        self.nb.http_session.verify = False
        logger.info(f"Initializing Netbox client with URL: {url}")

    def test_connection(self):
        try:
            self.nb.dcim.devices.get(1)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Netbox: {e}")
            return False
    
    def get_all_organizations(self):
        """
        Get all organizations (tenants) from Netbox.

        Returns:
            list: A list of organization objects
        """
        logger.info("Fetching all organizations (tenants) from Netbox")
        organizations = []

        try:
            tenants = self.nb.tenancy.tenants.all()
            for tenant in tenants:
                organizations.append(dict(tenant))
            logger.info(f"tenant object type: {type(tenant)}, object: {tenant}")
            logger.info(f"Found {len(organizations)} organizations in Netbox")
        except Exception as e:
            logger.error(f"Failed to get organizations from Netbox: {e}")
        
        return organizations
    
    def get_organization_by_id(self, org_id):
        """
        Get detailed organization info by ID, including contacts.
        
        Args:
            org_id: The ID of the organization to get information for
        
        Returns:
            dict: Organization information with contacts
        """
        logger.info(f"Fetching organization info with ID: {org_id}")
        
        try:
            organization = dict(self.nb.tenancy.tenants.get(org_id))
            if not organization:
                logger.error(f"organization with ID {org_id} not found")
                return None
            
            contacts = self.get_organization_contacts(org_id)
            
            organization.update({
                'contacts': contacts
            })
            
            # Find primary contact
            primary_contact = self._get_primary_contact(contacts)
            if primary_contact:
                organization['primary_contact_name'] = primary_contact.get('name', '')
                organization['primary_contact_email'] = primary_contact.get('email', '')
                organization['primary_contact_phone'] = primary_contact.get('phone', '')
            
            return organization
        
        except Exception as e:
            logger.error(f"Failed to get organization with ID {org_id}: {e}")
            return None
    
    def get_scan_targets_for_organization(self, org_id):
        """
        Get IP addresses with 'vuln-scan' tag for a specific organization.
        
        Args:
            org_id: The ID of the organization to get targets for
            
        Returns:
            tuple: (list of IP strings, list of target objects with enriched information)
        """
        logger.info(f"Fetching IP addresses with 'vuln-scan' tag for organization ID: {org_id}")
        
        scan_targets = []
        ip_list = []
        
        try:
            # Get organization info for enrichment
            org_info = self.get_organization_by_id(org_id)
            if not org_info:
                logger.warning(f"Could not get organization info for organization ID {org_id}")
                return [], []
            
            # Get all IP addresses with the 'vuln-scan' tag and the specified organization
            ip_addresses = self.nb.ipam.ip_addresses.filter(tag='vuln-scan', tenant_id=int(org_id))
            
            for ip in ip_addresses:
                if not ip.address:
                    continue
                
                # Get the IP string without CIDR notation
                ip_str = str(ip.address).split('/')[0]
                ip_list.append(ip_str)
                
                # Create target info dictionary with organization info
                target_info = {
                    'ip': ip_str,
                    'dns_name': ip.dns_name or '',
                    'description': ip.description or '',
                    'device_name': '',
                    'device_role': '',
                    'site_name': '',
                    'rack': '',
                    'organization': org_info
                }
                
                # Get device/VM information
                if ip.assigned_object:
                    if hasattr(ip.assigned_object, 'virtual_machine') and ip.assigned_object.virtual_machine:
                        vm = ip.assigned_object.virtual_machine
                        target_info['device_name'] = vm.name
                        target_info['device_role'] = "Virtual Machine"
                        target_info['site_name'] = vm.site.name if hasattr(vm, 'site') and vm.site else ""
                    elif hasattr(ip.assigned_object, 'device') and ip.assigned_object.device:
                        device = ip.assigned_object.device
                        target_info['device_name'] = device.name
                        target_info['device_role'] = device.device_role.name if hasattr(device, 'device_role') and device.device_role else ""
                        target_info['site_name'] = device.site.name if hasattr(device, 'site') and device.site else ""
                        target_info['rack'] = device.rack.name if hasattr(device, 'rack') and device.rack else ""
                
                scan_targets.append(target_info)
            
            logger.info(f"Found {len(scan_targets)} scan targets for organization ID {org_id}")
        except Exception as e:
            logger.error(f"Error getting scan targets for organization {org_id}: {e}")
        
        return ip_list, scan_targets

    def _get_primary_contact(self, contacts):
        """
        Get the primary contact from a list of contacts.
        
        Args:
            contacts: A list of contact dictionaries
            
        Returns:
            dict: The primary contact, or the first contact if no primary is designated
        """
        if not contacts:
            return None
            
        # First try to find contact explicitly marked as primary
        for contact in contacts:
            if contact.get('priority') == 'primary':
                return contact
        
        # If no explicit primary, find one with primary role
        for contact in contacts:
            if contact.get('role', '').lower() == 'primary':
                return contact
                
        # Default to first contact
        return contacts[0]

    def get_organization_contacts(self, org_id):
        """
        Get all contacts associated with a organization
        
        Args:
            org_id: The ID of the organization to get contacts for
            
        Returns:
            List of contact dictionaries with name, email, and phone
        """
        logger.debug(f"Fetching contacts for organization ID: {org_id}")
        contacts = []
        
        try:
            # Get contact assignments for this organization
            contact_assignments = self.nb.tenancy.contact_assignments.filter(
                content_type="tenancy.tenant", 
                object_id=org_id
            )
            if len(contact_assignments) == 0:
                logger.debug(f"No contact assignments found for organization ID {org_id}")
                return []
            
            for assignment in contact_assignments:
                # print the contact assignment json to debug log
                logger.debug(f"contact assignment: {assignment}")
                if not hasattr(assignment, 'contact') or not assignment.contact:
                    continue
                    
                contact_id = assignment.contact.id
                
                # Get the detailed contact information
                contact = self.nb.tenancy.contacts.get(contact_id)
                if not contact:
                    continue
                    
                contact_info = {
                    'id': contact.id,
                    'name': contact.name,
                    'title': contact.title or '',
                    'phone': contact.phone or '',
                    'email': contact.email or '',
                    'address': contact.address or '',
                    'role': assignment.role.name if hasattr(assignment, 'role') and assignment.role else '',
                    'priority': assignment.priority.value if hasattr(assignment, 'priority') and assignment.priority else ''
                }
                contacts.append(contact_info)
            
            logger.debug(f"Found {len(contacts)} contacts for organization ID {org_id}")
        except Exception as e:
            logger.error(f"Error fetching contacts for organization {org_id}: {e}")
        
        return contacts