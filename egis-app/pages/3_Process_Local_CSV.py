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
#     page_title="Process Local CSV | EGIS",
#     page_icon="📁",
#     layout="wide"
# )

# Ensure controller is initialized
if "controller" not in st.session_state:
    logger.info("Initializing AppController in session state (from Process Local CSV page)")
    st.session_state.controller = AppController()

# Ensure organizations are loaded
if "organizations" not in st.session_state:
    logger.info("Fetching organizations and storing in session state (from Process Local CSV page)")
    st.session_state.organizations = st.session_state.controller.get_organizations()
    logger.info(f"Cached {len(st.session_state.organizations)} organizations in session state")

# Page header
st.title("Process Local CSV")
st.markdown("---")

# Introduction
st.info("Upload and process a Nessus CSV file from your local system.")

# Initialize CSV scan name in session state if not exists
if "csv_scan_name" not in st.session_state:
    st.session_state.csv_scan_name = ""

# Initialize selected CSV organization in session state if not exists
if "csv_selected_org" not in st.session_state:
    st.session_state.csv_selected_org = "None"

# File uploader for CSV
uploaded_file = st.file_uploader("Upload Nessus CSV file", type="csv")

# Get organizations from session state
organizations = st.session_state.organizations
org_options = [(org['id'], org['name']) for org in organizations]
org_names = ["None"] + [org['name'] for org in organizations]

# Optional organization selection for enrichment
selected_org = st.selectbox(
    "Select Organization for Data Enrichment (Optional):", 
    org_names, 
    index=org_names.index(st.session_state.csv_selected_org) if st.session_state.csv_selected_org in org_names else 0,
    key="csv_org_select"
)
# Update session state
st.session_state.csv_selected_org = selected_org

# Map selected organization name back to ID
org_id = None
if selected_org != "None":
    for i, org_name in enumerate(org_names[1:]):  # Skip "None"
        if org_name == selected_org:
            org_id = organizations[i]['id']
            logger.debug(f"Selected organization for CSV enrichment: '{selected_org}' (ID: {org_id})")
else:
    logger.debug("No organization selected for CSV enrichment")

# Input for scan name
scan_name = st.text_input("Enter a name for this assessment (optional):", value=st.session_state.csv_scan_name)
# Update session state
st.session_state.csv_scan_name = scan_name

if uploaded_file is not None:
    logger.info(f"User uploaded CSV file: {uploaded_file.name}")
    # Create a temporary file
    temp_csv_path = os.path.join(RAW_DATA_DIR, uploaded_file.name)
    with open(temp_csv_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # Button to process the uploaded CSV
    if st.button("Process CSV", key="process_csv"):
        if org_id:
            logger.info(f"User initiated processing of uploaded CSV file: {uploaded_file.name} with organization enrichment: '{selected_org}' (ID: {org_id})")
        else:
            logger.info(f"User initiated processing of uploaded CSV file: {uploaded_file.name} without organization enrichment")
        
        with st.spinner("Processing CSV file..."):
            try:
                st.session_state.controller.process_local_csv(temp_csv_path, org_id)
                logger.info("CSV file processed successfully")
                st.success(f"CSV file processed successfully!")
            except Exception as e:
                logger.error(f"Error processing CSV file: {str(e)}")
                st.error(f"Error processing CSV: {str(e)}")
                # Clean up temp file on error
                if os.path.exists(temp_csv_path):
                    logger.debug(f"Removing temporary CSV file after error: {temp_csv_path}")
                    os.remove(temp_csv_path) 