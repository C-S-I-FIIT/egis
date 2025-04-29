import streamlit as st
import os
import base64
import sys
from datetime import datetime
from config import LOGS_DIR, REPORTS_DIR, RAW_DATA_DIR
from app_controller import AppController
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(
    os.path.join(LOGS_DIR, "egis.log"), 
    rotation="10 MB",  # Rotate when file reaches 10 MB
    retention="1 year",  # Keep logs for 1 year
    compression="bz2",  # Compress rotated logs
    level="DEBUG"
)
logger.info("Logging configured")


# Configure page
st.set_page_config(page_title="EGIS Vulnerability Assessment Application", layout="wide")

# Initialize session state variables if they don't exist
if "controller" not in st.session_state:
    st.session_state.controller = AppController()

# App title and description
st.title("EGIS Vulnerability Assessment Application")
st.markdown("Semi-automate the Vulnerability Assessment process")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", ["Scan Management", "Reports", "Settings"])

# Function to generate download link for files
def get_download_link(file_path, link_text):
    with open(file_path, "rb") as file:
        contents = file.read()
    b64_contents = base64.b64encode(contents).decode()
    return f'<a href="data:application/octet-stream;base64,{b64_contents}" download="{os.path.basename(file_path)}">{link_text}</a>'

# Function to list available reports
def list_reports():
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.pdf') or filename.endswith('.html'):
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
    return reports

# Function to list raw scan data
def list_raw_data():
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
    return raw_files

# Scan Management Page
if page == "Scan Management":
    st.header("Vulnerability Scan Management")
    
    # Create tabs for different scan options
    tab1, tab2, tab3 = st.tabs(["Run New Assessment", "Process Existing Scan", "Process Local CSV"])
    
    with tab1:
        st.subheader("Run New Vulnerability Assessment")
        st.info("This will retrieve targets from Netbox, create and run a new vulnerability scan in Nessus, then generate assessment reports.")
        
        # Button to run new scan
        if st.button("Run New Assessment", key="run_new_scan"):
            with st.spinner("Running new vulnerability assessment... This may take a while."):
                try:
                    st.session_state.controller.run_new_scan()
                    st.success("Assessment scan completed successfully!")
                except Exception as e:
                    st.error(f"Error running assessment: {str(e)}")
    
    with tab2:
        st.subheader("Process Existing Scan")
        st.info("Process an existing vulnerability scan from Nessus and generate assessment reports.")
        
        # Input for scan ID
        scan_id = st.text_input("Enter Nessus Scan ID:")
        
        # Button to process existing scan
        if st.button("Process Scan", key="process_scan") and scan_id:
            with st.spinner("Processing scan..."):
                try:
                    st.session_state.controller.process_existing_scan(scan_id)
                    st.success(f"Scan {scan_id} processed successfully!")
                except Exception as e:
                    st.error(f"Error processing scan: {str(e)}")
    
    with tab3:
        st.subheader("Process Local CSV")
        st.info("Upload and process a Nessus CSV file from your local system.")
        
        # File uploader for CSV
        uploaded_file = st.file_uploader("Upload Nessus CSV file", type="csv")
        scan_name = st.text_input("Enter a name for this assessment (optional):")
        
        if uploaded_file is not None:
            # Create a temporary file
            temp_csv_path = os.path.join(RAW_DATA_DIR, uploaded_file.name)
            with open(temp_csv_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Button to process the uploaded CSV
            if st.button("Process CSV", key="process_csv"):
                with st.spinner("Processing CSV file..."):
                    try:
                        st.session_state.controller.process_local_csv(temp_csv_path, scan_name if scan_name else None)
                        st.success(f"CSV file processed successfully!")
                    except Exception as e:
                        st.error(f"Error processing CSV: {str(e)}")
                        # Clean up temp file on error
                        if os.path.exists(temp_csv_path):
                            os.remove(temp_csv_path)

# Reports Page
elif page == "Reports":
    st.header("Assessment Reports")
    
    # Create tabs for different report types
    tab1, tab2 = st.tabs(["Generated Reports", "Raw Scan Data"])
    
    with tab1:
        st.subheader("Generated Assessment Reports")
        reports = list_reports()
        
        if not reports:
            st.info("No reports found. Run an assessment to generate reports.")
        else:
            for report in reports:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"{report['filename']} - {report['date']}")
                with col2:
                    st.markdown(get_download_link(report['path'], "Download"), unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Raw Scan Data")
        raw_files = list_raw_data()
        
        if not raw_files:
            st.info("No raw scan data found. Run an assessment to generate data.")
        else:
            for file in raw_files:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(file['filename'])
                with col2:
                    st.text(file['date'])
                with col3:
                    st.markdown(get_download_link(file['path'], "Download"), unsafe_allow_html=True)
                    
                # Add option to process this raw CSV
                if st.button("Process", key=f"process_{file['filename']}"):
                    with st.spinner("Processing raw data..."):
                        try:
                            st.session_state.controller.process_local_csv(file['path'])
                            st.success(f"Data processed successfully!")
                        except Exception as e:
                            st.error(f"Error processing data: {str(e)}")

# Settings Page
elif page == "Settings":
    st.header("Application Settings")
    
    # Display configuration info
    st.subheader("Configuration")
    st.info("The application is configured using environment variables through .env file.")
    
    # Add a section for application status
    st.subheader("Application Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reports Directory", REPORTS_DIR)
    with col2:
        st.metric("Raw Data Directory", RAW_DATA_DIR)
    
    # Check connectivity to services
    st.subheader("Service Status")
    
    if st.button("Check Connectivity"):
        try:
            # Check Nessus connectivity
            nessus_status = "Connected" if st.session_state.controller.scanner.token else "Error"
            # Check Netbox connectivity
            netbox_devices = st.session_state.controller.netbox.get_devices_for_scanning()
            netbox_status = "Connected" if netbox_devices is not None else "Error"
            # Check Elasticsearch connectivity
            es_status = "Connected" if st.session_state.controller.es_client else "Error"


            # Display status
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Nessus Scanner", nessus_status)
            with col2:
                st.metric("Netbox", netbox_status)
            
        except Exception as e:
            st.error(f"Error checking connectivity: {str(e)}") 