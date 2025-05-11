import streamlit as st
import sys
import os
from loguru import logger
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from config import REPORTS_DIR, RAW_DATA_DIR, LOGS_DIR
from app_controller import AppController

# Configure page
# st.set_page_config(
#     page_title="Run New Assessment | EGIS",
#     page_icon="🚀",
#     layout="wide"
# )

# Ensure controller is initialized
if "controller" not in st.session_state:
    logger.info("Initializing AppController in session state (from Run New Assessment page)")
    st.session_state.controller = AppController()

# Ensure organizations are loaded
if "organizations" not in st.session_state:
    logger.info("Fetching organizations and storing in session state (from Run New Assessment page)")
    st.session_state.organizations = st.session_state.controller.get_organizations()
    logger.info(f"Cached {len(st.session_state.organizations)} organizations in session state. Orgs: {st.session_state.organizations}")

# Page header
st.title("Run New Vulnerability Assessment")
st.markdown("---")

# Introduction
st.info("This will retrieve targets from Netbox, create and run a new vulnerability scan in Nessus, then generate assessment reports.")

# Get organizations from session state
organizations = st.session_state.organizations
logger.debug(f"Using {len(organizations)} organizations from session state")

# Initialize selection state if not exists
if "scan_all_orgs" not in st.session_state:
    st.session_state.scan_all_orgs = False

# Checkbox to scan all organizations
scan_all = st.checkbox("Scan All Organizations", value=st.session_state.scan_all_orgs, key="scan_all_checkbox")
# Save state
# st.session_state.scan_all_orgs = scan_all
logger.debug(f"'Scan All Organizations' checkbox state: {scan_all}")

# Initialize and maintain selected orgs in session state
if "selected_orgs" not in st.session_state:
    st.session_state.selected_orgs = []

# Multi-select for organizations if not scanning all
if not scan_all:
    # Show multi-select dropdown
    st.session_state.selected_orgs = st.multiselect(
        "Select Organizations to Scan:", 
        st.session_state.organizations, 
        default=st.session_state.selected_orgs,
        format_func=lambda x: x['name'],
        key="selected_orgs_multiselect"
    )

    # Log selected organizations
    if st.session_state.selected_orgs:
        logger.debug(f"User selected {len(st.session_state.selected_orgs)} organizations: {st.session_state.selected_orgs}")
    else:
        logger.debug("No organizations selected in multiselect")

# Button to run new scan
if st.button("Run Assessment", key="run_new_scan"):
    if scan_all:
        logger.info("User initiated vulnerability assessment for ALL organizations")
    else:
        if st.session_state.selected_orgs:
            org_names_str = ", ".join([org['name'] for org in st.session_state.organizations if org['id'] in st.session_state.selected_orgs])
            logger.info(f"User initiated vulnerability assessment for selected organizations: {org_names_str}")
        else:
            logger.warning("User attempted to run assessment without selecting any organizations")
            st.warning("Please select at least one organization or check 'Scan All Organizations'")
            st.stop()
            
    with st.spinner("Running vulnerability assessment... This may take a while."):
        # Run scan with selected organizations or all if scan_all is checked
        if scan_all:
            logger.debug(f"Calling run_new_scan with org_ids: {st.session_state.organizations['id']}")
            org_ids = [org['id'] for org in st.session_state.organizations]
            results = st.session_state.controller.run_scan_for_selected_orgs(org_ids)
        elif st.session_state.selected_orgs:
            logger.debug(f"Calling run_new_scan with org_ids: {st.session_state.selected_orgs}")
            org_ids = [org['id'] for org in st.session_state.selected_orgs]
            results = st.session_state.controller.run_scan_for_selected_orgs(org_ids)
        logger.info(f"Vulnerability assessment completed successfully for {len(results) if results else 0} organizations")
        st.success(f"Assessment scan completed successfully for {len(results) if results else 0} organizations!")