from elasticsearch import Elasticsearch
from datetime import datetime
import hashlib
import urllib3
from loguru import logger
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ElasticClient:
    def __init__(self, url, index_prefix, api_key):
        self.es = Elasticsearch(
            [url],
            api_key=api_key,
            verify_certs=False,
            ssl_show_warn=False,
            timeout=60  # or higher, default is 10
        )
        self.index_prefix = index_prefix
        logger.info(f"Initializing Elasticsearch client with URL: {url}")

    def test_connection(self):
        try:
            # Test connection by checking cluster info
            info = self.es.info()
            logger.info(f"Elasticsearch cluster: {info['cluster_name']} successfully connected")
            return True
        except Exception as e:
            logger.error(f"Elasticsearch connection failed: {e}")
            return False

    def store_vulnerability(self, vuln_data):
        # Store vulnerability data in Elasticsearch
        doc_id = self._generate_doc_id(vuln_data)
        index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m')}"
        
        self.es.index(
            index=index_name,
            id=doc_id,
            document=vuln_data
        )
        logger.debug(f"Stored vulnerability to {index_name}, ID: {doc_id}")
        return doc_id

    def store_vulnerabilities_bulk(self, documents):
        """
        Store multiple vulnerability documents in Elasticsearch using bulk operations
        """
        if not documents:
            logger.warning("No documents to store in Elasticsearch")
            return []
            
        index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m')}"
        logger.info(f"Preparing to bulk store {len(documents)} documents to index: {index_name}")
        # Optionally log the first document for debugging
        logger.debug(f"First document sample: {json.dumps(documents[0], indent=2, default=str) if documents else 'N/A'}")

        bulk_data = []
        doc_ids = []
        
        for doc in documents:
            doc_id = self._generate_doc_id(doc)
            doc_ids.append(doc_id)
            bulk_data.append({"index": {"_index": index_name, "_id": doc_id}})
            bulk_data.append(doc)
        
        try:
            response = self.es.bulk(operations=bulk_data, refresh=True)
            # Check for errors
            if response.get("errors", False):
                error_items = [item for item in response.get("items", []) if item.get("index", {}).get("error")]
                logger.error(f"Bulk operation completed with {len(error_items)} errors out of {len(documents)} documents")
                # Log the first 3 errors for inspection
                for i, error in enumerate(error_items[:3]):
                    logger.error(f"Error {i+1}: {json.dumps(error, indent=2)}")
            else:
                logger.info(f"Successfully stored {len(documents)} vulnerabilities in Elasticsearch")
            return doc_ids
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}")
            return []

    def _generate_doc_id(self, vuln_data):
        """
        Generate unique document ID based on the document structure.
        """
        if 'host' in vuln_data and 'vulnerability' in vuln_data and 'scan' in vuln_data:
            host_ip = vuln_data.get('host', {}).get('ip', '')
            plugin_id = vuln_data.get('vulnerability', {}).get('plugin_id', '')
            port = vuln_data.get('vulnerability', {}).get('port', '')
            scan_name = vuln_data.get('scan', {}).get('name', '')
        
        # Create a unique ID based on these fields
        key_fields = [
            str(host_ip),
            str(plugin_id),
            str(port),
            str(scan_name)
        ]
        
        return hashlib.md5(''.join(key_fields).encode()).hexdigest()

    def get_vulnerabilities(self, scan_name):
        """
        Get vulnerabilities for a specific scan
        
        Args:
            scan_name: The name of the scan to retrieve vulnerabilities for
            
        Returns:
            list: The vulnerability documents
        """
        index_pattern = f"{self.index_prefix}-*"
        query = {
            "bool": {
                "must": [
                    {"term": {"scan.name.keyword": scan_name}}
                ]
            }
        }
        
        results = self.es.search(
            index=index_pattern,
            query=query,
            size=10000
        )
        
        vulns = [hit["_source"] for hit in results["hits"]["hits"]]
        logger.info(f"Retrieved {len(vulns)} vulnerabilities for scan: {scan_name}")
        return vulns
