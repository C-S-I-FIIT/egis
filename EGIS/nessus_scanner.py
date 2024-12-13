import time
import requests
import urllib3
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NessusScanner:
    def __init__(self, url, access_key, secret_key):
        self.url = url.rstrip('/')
        self.token = self.__get_api_token()
        self.headers = {
            'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}',
            'X-Api-Token': self.token,
            'Content-Type': 'application/json'
        }

    def __get_api_token(self):
        """
        Returns API token from js file. If not found returns None.
        """
        req = requests.get(self.url + '/nessus6.js', verify=False)
        regex = re.search('getApiToken\".*?return"(.*?)\"}}', req.text)

        if regex is not None:
            return regex.group(1)

        return None

    def _request(self, method, endpoint, **kwargs):
        """Make request to Nessus API with SSL verification disabled"""
        kwargs['verify'] = False
        kwargs['headers'] = self.headers
        return requests.request(method, f"{self.url}/{endpoint}", **kwargs)

    def create_scan(self, name, targets):
        """Create a new scan"""
        scan_data = {
            'uuid': '8d07cbb2-27e7-4c1f-b0c7-72dd9707c5a7',  # Basic Network Scan
            'settings': {
                'name': name,
                'text_targets': ','.join(targets),
                'launch': 'ONETIME'
            }
        }
        response = self._request('POST', 'scans', json=scan_data)
        return response.json()['scan']['id']

    def launch_scan(self, scan_id):
        """Launch an existing scan"""
        response = self._request('POST', f'scans/{scan_id}/launch')
        return response.status_code == 200

    def get_scan_status(self, scan_id):
        """Check scan status"""
        response = self._request('GET', f'scans/{scan_id}')
        return response.json()['info']['status']

    def export_results(self, scan_id, format='csv'):
        """Export scan results"""
        # Request export
        response = self._request('POST', f'scans/{scan_id}/export', 
                               json={'format': format})
        file_id = response.json()['file']
        
        # Wait for export
        while True:
            response = self._request('GET', f'scans/{scan_id}/export/{file_id}/status')
            if response.json()['status'] == 'ready':
                break
            time.sleep(2)
            
        # Download results
        response = self._request('GET', f'scans/{scan_id}/export/{file_id}/download')
        return response.content 