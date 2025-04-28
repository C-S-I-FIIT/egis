import os
from dotenv import load_dotenv

load_dotenv()

# Base URLs and credentials
NESSUS_URL = os.getenv("NESSUS_URL")
NESSUS_ACCESSKEY = os.getenv("NESSUS_ACCESSKEY")
NESSUS_SECRETKEY = os.getenv("NESSUS_SECRETKEY")

NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")

ELASTIC_URL = os.getenv("ELASTIC_URL")
ELASTIC_INDEX = os.getenv("ELASTIC_INDEX")
ELASTIC_APIKEY = os.getenv("ELASTIC_APIKEY")

# File storage
MEDIA_ROOT = "media"
RAW_DATA_DIR = os.path.join(MEDIA_ROOT, "raw_data")
REPORTS_DIR = os.path.join(MEDIA_ROOT, "reports")

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)