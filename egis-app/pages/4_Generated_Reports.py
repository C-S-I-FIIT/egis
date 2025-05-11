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

# Configure page
# st.set_page_config(
#     page_title="Generated Reports | EGIS",
#     page_icon="📊",
#     layout="wide"
# )

# Page header
st.title("Generated Assessment Reports")
st.markdown("---")

# Function to generate download link for files
def get_download_link(file_path, link_text):
    logger.debug(f"Generating download link for: {file_path}")
    with open(file_path, "rb") as file:
        contents = file.read()
    b64_contents = base64.b64encode(contents).decode()
    return f'<a href="data:application/octet-stream;base64,{b64_contents}" download="{os.path.basename(file_path)}">{link_text}</a>'

# Function to list available reports
#@st.cache_data(ttl=60, show_spinner=False)
def list_reports():
    logger.debug("Listing available reports (with caching)")
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.pdf'):
            file_path = os.path.join(REPORTS_DIR, filename)
            mod_time = os.path.getmtime(file_path)
            reports.append({
                'filename': filename,
                'path': file_path,
                'mod_time': mod_time,
                'date': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Sort by modification time (newest first)
    reports.sort(key=lambda x: x['mod_time'], reverse=True)
    logger.debug(f"Found {len(reports)} reports")
    return reports

# Initialize search term in session state if not exists
if "report_search_term" not in st.session_state:
    st.session_state.report_search_term = ""

# List and display reports
reports = list_reports()

if not reports:
    st.info("No reports found. Run an assessment to generate reports.")
else:
    # Search filter for reports
    search_term = st.text_input(
        "Search reports:", 
        value=st.session_state.report_search_term,
        placeholder="Filter by filename"
    )
    # Update session state
    st.session_state.report_search_term = search_term
    
    filtered_reports = reports
    if search_term:
        filtered_reports = [r for r in reports if search_term.lower() in r['filename'].lower()]
        logger.debug(f"Filtered reports to {len(filtered_reports)} items matching '{search_term}'")
    
    # Show report count
    st.write(f"Showing {len(filtered_reports)} of {len(reports)} reports")
    
    # Show filtered reports
    for idx, report in enumerate(filtered_reports):
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1], gap="small")
            with col1:
                st.markdown(f"<div style='padding:2px 0 2px 0;font-size:15px'>{report['filename']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='padding:2px 0 2px 0;font-size:14px;color:#aaa'>{report['date']}</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(get_download_link(report['path'], "Download"), unsafe_allow_html=True)
        if idx < len(filtered_reports) - 1:
            st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True) 