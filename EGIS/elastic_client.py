from elasticsearch import Elasticsearch
from datetime import datetime
import hashlib
import urllib3
from loguru import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ElasticClient:
    def __init__(self, url, index_prefix, api_key):
        self.es = Elasticsearch(
            [url],
            api_key=api_key,
            verify_certs=False,
            ssl_show_warn=False
        )
        self.index_prefix = index_prefix
        logger.info(f"Initializing Elasticsearch client with URL: {url}")

    def store_vulnerability(self, vuln_data):
        # Store vulnerability data in Elasticsearch
        doc_id = self._generate_doc_id(vuln_data)
        index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m')}"
        
        self.es.index(
            index=index_name,
            id=doc_id,
            document=vuln_data
        )
        logger.debug(f"Storing vulnerability to {index_name}, ID: {doc_id}")

    def _generate_doc_id(self, vuln_data):
        # Generate unique document ID
        key_fields = [
            str(vuln_data.get('host')),
            str(vuln_data.get('plugin_id')),
            str(vuln_data.get('port')),
            vuln_data.get('scan_name')
        ]
        return hashlib.md5(''.join(key_fields).encode()).hexdigest()

    def get_vulnerabilities(self, scan_name):
        # Get vulnerabilities for a specific scan
        index_pattern = f"{self.index_prefix}-*"
        query = {
            "bool": {
                "must": [
                    {"term": {"scan_name.keyword": scan_name}}
                ]
            }
        }
        
        results = self.es.search(
            index=index_pattern,
            query=query,
            size=10000
        )
        
        vulns = [hit["_source"] for hit in results["hits"]["hits"]]
        logger.info(f"Retrieving vulnerabilities for scan: {scan_name}")
        logger.debug(f"Found {len(vulns)} vulnerabilities in Elasticsearch")
        return vulns 