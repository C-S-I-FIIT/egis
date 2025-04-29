import requests
import os

from loguru import logger

class NetManager:
    @classmethod
    def get_session(cls, proxy=False):
        session = requests.Session()
        
        if proxy:
            if os.getenv('HTTP_PROXY') and os.getenv('HTTPS_PROXY'):
                session.proxies = {
                    'http': os.getenv('HTTP_PROXY'),
                    'https': os.getenv('HTTPS_PROXY')
                }
            else:
                logger.warning("No proxy environment variables found")

        return requests.Session()