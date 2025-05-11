import streamlit as st
import sys
import os
from loguru import logger

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from config import REPORTS_DIR, RAW_DATA_DIR, LOGS_DIR
from app_controller import AppController

# Configure page
# st.set_page_config(
#     page_title="Process Existing Scan | EGIS",
#     page_icon="🔄",
#     layout="wide"
# )

# Ensure controller is initialized
if "controller" not in st.session_state:
    logger.info("Initializing AppController in session state (from Process Existing Scan page)")
    st.session_state.controller = AppController()

# Ensure organizations are loaded
if "organizations" not in st.session_state:
    logger.info("Fetching organizations and storing in session state (from Process Existing Scan page)")
    st.session_state.organizations = st.session_state.controller.get_organizations()
    logger.info(f"Cached {len(st.session_state.organizations)} organizations in session state")

# Page header
st.title("Process Existing Scan")
st.markdown("---")

# Introduction
st.info("Process an existing vulnerability scan from Nessus and generate assessment reports.")

# Initialize scan_id in session state if not exists
if "existing_scan_id" not in st.session_state:
    st.session_state.existing_scan_id = ""

# Input for scan ID
scan_id = st.text_input("Enter Nessus Scan ID:", value=st.session_state.existing_scan_id, key="scan_id_input")
# Update session state
st.session_state.existing_scan_id = scan_id


# Optional organization selection for enrichment
if "existing_scan_org" not in st.session_state:
    st.session_state.existing_scan_org = "None"

# Add None option to the list of organizations
none_option = {"name": "- None -", "id": None}

existing_scan_org = st.selectbox(
    "Select Organization for Data Enrichment (Optional):", 
    [none_option] + st.session_state.organizations,
    format_func=lambda x: x['name'],
    key="existing_scan_org_selectbox"
)
st.session_state.existing_scan_org = existing_scan_org

# Log selected organization
if existing_scan_org != "None":
    logger.debug(f"Selected organization for data enrichment: '{existing_scan_org['name']}' (ID: {existing_scan_org['id']})")
else:
    logger.debug("No organization selected for data enrichment")

# Button to process existing scan
if st.button("Process Scan", key="process_scan") and scan_id:
    if existing_scan_org != "None":
        logger.info(f"User initiated processing of existing scan ID: {scan_id} with organization enrichment: '{existing_scan_org['name']}' (ID: {existing_scan_org['id']})")
    else:
        logger.info(f"User initiated processing of existing scan ID: {scan_id} without organization enrichment")
        
    with st.spinner("Processing scan..."):
        st.session_state.controller.process_completed_nessus_scan(scan_id, existing_scan_org['id'])
        logger.info(f"Scan {scan_id} processed successfully")
        st.success(f"Scan {scan_id} processed successfully!")