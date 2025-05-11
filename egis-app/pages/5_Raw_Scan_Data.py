import streamlit as st
import sys
import os
import base64
from datetime import datetime
from loguru import logger

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from config import REPORTS_DIR, RAW_DATA_DIR, LOGS_DIR
from app_controller import AppController

# Configure page
# st.set_page_config(
#     page_title="Raw Scan Data | EGIS",
#     page_icon="📄",
#     layout="wide"
# )

# Ensure controller is initialized
if "controller" not in st.session_state:
    logger.info("Initializing AppController in session state (from Raw Scan Data page)")
    st.session_state.controller = AppController()

# Ensure organizations are loaded
if "organizations" not in st.session_state:
    logger.info("Fetching organizations and storing in session state (from Raw Scan Data page)")
    st.session_state.organizations = st.session_state.controller.get_organizations()
    logger.info(f"Cached {len(st.session_state.organizations)} organizations in session state")

# Page header
st.title("Raw Scan Data")
st.markdown("---")

# Function to generate download link for files
def get_download_link(file_path, link_text):
    logger.debug(f"Generating download link for: {file_path}")
    with open(file_path, "rb") as file:
        contents = file.read()
    b64_contents = base64.b64encode(contents).decode()
    return f'<a href="data:application/octet-stream;base64,{b64_contents}" download="{os.path.basename(file_path)}">{link_text}</a>'

# Function to list raw scan data
#@st.cache_data(ttl=60, show_spinner=False)
def list_raw_data():
    logger.debug("Listing available raw scan data (with caching)")
    raw_files = []
    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith('.csv'):
            file_path = os.path.join(RAW_DATA_DIR, filename)
            mod_time = os.path.getmtime(file_path)
            raw_files.append({
                'filename': filename,
                'path': file_path,
                'mod_time': mod_time,
                'date': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Sort by modification time (newest first)
    raw_files.sort(key=lambda x: x['mod_time'], reverse=True)
    logger.debug(f"Found {len(raw_files)} raw data files")
    return raw_files

# Initialize search term in session state if not exists
if "raw_data_search_term" not in st.session_state:
    st.session_state.raw_data_search_term = ""

# List raw data files
raw_files = list_raw_data()

if not raw_files:
    st.info("No raw scan data found. Run an assessment to generate data.")
else:
    # Search filter for raw data files
    search_term = st.text_input(
        "Search raw data:", 
        value=st.session_state.raw_data_search_term,
        placeholder="Filter by filename"
    )
    # Update session state
    st.session_state.raw_data_search_term = search_term
    
    filtered_files = raw_files
    if search_term:
        filtered_files = [f for f in raw_files if search_term.lower() in f['filename'].lower()]
        logger.debug(f"Filtered raw files to {len(filtered_files)} items matching '{search_term}'")
    
    # Show file count
    st.write(f"Showing {len(filtered_files)} of {len(raw_files)} raw data files")
    
    # Show filtered raw data files
    for idx, file in enumerate(filtered_files):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1], gap="small")
            with col1:
                st.markdown(f"<div style='padding:2px 0 2px 0;font-size:15px'>{file['filename']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='padding:2px 0 2px 0;font-size:14px;color:#aaa'>{file['date']}</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(get_download_link(file['path'], "Download"), unsafe_allow_html=True)
            with col4:
                if st.button("Process", key=f"process_{file['filename']}"):
                    logger.info(f"User initiated processing of existing raw file: {file['filename']}")
                    organizations = st.session_state.organizations
                    with st.spinner("Processing raw data..."):
                        try:
                            st.session_state.controller.process_local_csv(file['path'])
                            logger.info(f"Raw data {file['filename']} processed successfully")
                            st.success(f"Data processed successfully!")
                            list_raw_data.clear()
                        except Exception as e:
                            logger.error(f"Error processing raw data {file['filename']}: {str(e)}")
                            st.error(f"Error processing data: {str(e)}")
        if idx < len(filtered_files) - 1:
            st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True) 