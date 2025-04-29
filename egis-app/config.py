import os
from dotenv import load_dotenv
from loguru import logger
# EGIS Vulnerability Assessment Application
# Configuration module for application settings

try:
    load_dotenv()
except IOError as e:
    logger.warning(f"No .env file found. Using system environment variables.")

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
DATA_ROOT = "/data"
RAW_DATA_DIR = os.path.join(DATA_ROOT, "raw_data")
REPORTS_DIR = os.path.join(DATA_ROOT, "reports")
LOGS_DIR = os.path.join(DATA_ROOT, "logs")

# Ensure all directories exist
os.makedirs(DATA_ROOT, exist_ok=True)
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
