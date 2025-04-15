import time
import urllib3
import re

from loguru import logger

from net_manager import NetManager

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NessusScanner:
    def __init__(self, url, access_key, secret_key):
        self.session = NetManager.get_session(proxy=False)
        self.url = url.rstrip('/')
        self.token = self.__get_api_token()
        self.headers = {
            'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}',
            'X-Api-Token': self.token,
            'Content-Type': 'application/json'
        }
        logger.info(f"Initializing Nessus scanner with URL: {url}")

    def __get_api_token(self):
        # Returns API token from js file. If not found returns None.
        req = self.session.get(self.url + '/nessus6.js', verify=False)
        regex = re.search('getApiToken\".*?return"(.*?)\"}}', req.text)

        if regex is not None:
            return regex.group(1)

        return None

    def _request(self, method, endpoint, **kwargs):
        # Make request to Nessus API with SSL verification disabled
        kwargs['verify'] = False
        kwargs['headers'] = self.headers
        return self.session.request(method, f"{self.url}/{endpoint}", **kwargs)

    def create_scan(self, name, targets):
        # Create a new scan
        scan_data = {
            'uuid': "ad629e16-03b6-8c1d-cef6-ef8c9dd3c658d24bd260ef5f9e66",  # EGIS-ScanTemplate
            'settings': {
                'name': name,
                'text_targets': ','.join(targets),
                'launch': 'ONETIME'
            }
        }
        response = self._request('POST', 'scans', json=scan_data)
        scan_id = response.json()['scan']['id']
        logger.info(f"Creating scan '{name}' with {len(targets)} targets")
        logger.debug(f"Scan created with ID: {scan_id}")
        return scan_id

    def launch_scan(self, scan_id):
        # Launch an existing scan
        response = self._request('POST', f'scans/{scan_id}/launch')
        logger.info(f"Launching scan with ID: {scan_id}")
        if response.status_code == 200:
            logger.info(f"Scan {scan_id} launched successfully")
        else:
            logger.error(f"Failed to launch scan {scan_id}: {response.status_code}")
        return response.status_code == 200

    def get_scan_status(self, scan_id):
        response = self._request('GET', f'scans/{scan_id}/latest-status')
        logger.debug(f"Checking status of scan {scan_id}")
        if response.status_code == 200:
            return response.json()['status']
        else:
            logger.error(f"Error retrieving scan status: {response.status_code}")
            return None

    def get_scan_details(self, scan_id):
        response = self._request('GET', f'scans/{scan_id}')
        return response.json()

    def export_scan_results(self, scan_id, format='csv'):
        # Request export
        response = self._request('POST', f'scans/{scan_id}/export', json={'format': format})
        file_id = response.json()['file']
        logger.info(f"Exporting scan {scan_id} results as {format}")
        logger.debug(f"Export file ID: {file_id}")
        
        # Wait for export
        while True:
            response = self._request('GET', f'scans/{scan_id}/export/{file_id}/status')
            if response.json()['status'] == 'ready':
                break
            time.sleep(2)
            
        # Download results
        response = self._request('GET', f'scans/{scan_id}/export/{file_id}/download')
        logger.info(f"Downloaded scan results: {len(response.content)} bytes")
        return response.content 