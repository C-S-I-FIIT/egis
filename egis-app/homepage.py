import streamlit as st
import os
import sys
import base64
from datetime import datetime
from config import REPORTS_DIR, RAW_DATA_DIR, LOGS_DIR, NESSUS_URL, NETBOX_URL, ELASTIC_URL
from app_controller import AppController
from loguru import logger

# Configure page
st.set_page_config(
    page_title="EGIS Vulnerability Assessment Application",
    page_icon="🛡️",
    layout="wide"
)

# Initialize session state for logger configuration
if "logger_configured" not in st.session_state:
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
    logger.info("Logger initialized on application start")
    st.session_state.logger_configured = True

# Initialize app controller in session state if not present
if "controller" not in st.session_state:
    logger.info("Initializing AppController in session state")
    st.session_state.controller = AppController()

def homepage():
    # Main page content
    st.title("🛡️ EGIS Vulnerability Assessment Application")
    
    # Introduction section
    st.markdown("""
    ### Welcome to your centralized vulnerability assessment platform
    
    EGIS helps security teams automate and streamline the vulnerability assessment process through integration
    with industry-standard tools and centralized reporting.
                
    **🚀 Select an option from the sidebar to get started!**
    """)
    
    # Features section
    st.markdown("---")
    st.subheader("🔍 Platform Features")
    
    feature_col1, feature_col2 = st.columns(2)
    
    with feature_col1:
        st.markdown("""
        #### Scan Management 
        
        - 🎯 **Target Discovery**: Automatically identify scan targets from NetBox
        - 📊 **Vulnerability Assessment**: Create and execute Nessus vulnerability scans
        - 📁 **CSV Processing**: Import and process scan results from CSV files
        """)
        
    with feature_col2:
        st.markdown("""
        #### Reports & Analysis
        
        - 📄 **Automated Report Generation**: Create comprehensive PDF reports
        - 🗄️ **Data Persistence**: Store findings in Elasticsearch for long-term analysis
        - 🔎 **Raw Data Access**: View and download raw scan results
        """)
    
    # Integrated systems
    st.markdown("---")
    st.subheader("🔌 Access Integrated Systems")
    
    systems_col1, systems_col2, systems_col3 = st.columns(3)
    
    with systems_col1:
        st.markdown(f"#### Nessus")
        st.image("static/nessus_logo.svg", width=150)
        if NESSUS_URL:
            st.markdown(f"[Access Nessus]({NESSUS_URL})")
    
    with systems_col2:
        st.markdown(f"#### NetBox")
        st.image("static/netbox_logo.svg", width=150)
        if NETBOX_URL:
            st.markdown(f"[Access NetBox]({NETBOX_URL})")
    
    with systems_col3:
        st.markdown(f"#### Kibana")
        st.image("static/kibana_logo.svg", width=150)
        if ELASTIC_URL:
            # Strip the port from the URL if it exists
            kibana_url = ELASTIC_URL.split(':')[0] + ':' + ELASTIC_URL.split(':')[1] if ':' in ELASTIC_URL else ELASTIC_URL
            st.markdown(f"[Access Kibana]({kibana_url})")
    
    # Stats and info
    if "organizations" in st.session_state:
        st.markdown("---")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns([3, 2, 2, 2])
        
        with stats_col1:
            st.subheader("📈 Platform Statistics")
        
        stats_data_col1, stats_data_col2, stats_data_col3 = st.columns(3)
        
        with stats_data_col1:
            st.metric("Organizations Available", len(st.session_state.organizations))
        
        # Count reports
        try:
            report_count = len([f for f in os.listdir(REPORTS_DIR) if f.endswith('.pdf') or f.endswith('.html')])
            with stats_data_col2:
                st.metric("Generated Reports", report_count)
        except:
            pass
        
        # Count raw data files
        try:
            raw_data_count = len([f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.csv')])
            with stats_data_col3:
                st.metric("Raw Data Files", raw_data_count)
        except:
            pass
    
    # Footer
    st.markdown("---")
    st.caption("EGIS Vulnerability Assessment Application • Use the navigation sidebar to access all features")

    logger.debug("Main streamlit UI page rendered") 

# Navigation menu
st.logo("static/egis_logo.png", size="large")
homepage = st.Page(homepage, title = "Home", icon="🏠")
new_assessment_page = st.Page("pages/1_Run_New_Assessment.py", title="Run New Assessment", icon="🚀")
process_existing_scan_page = st.Page("pages/2_Process_Existing_Scan.py", title="Process Existing Scan", icon="🔄")
process_local_csv_page = st.Page("pages/3_Process_Local_CSV.py", title="Process Local CSV", icon="📁")
generated_reports_page = st.Page("pages/4_Generated_Reports.py", title="Generated Reports", icon="📊")
raw_scan_data_page = st.Page("pages/5_Raw_Scan_Data.py", title="Raw Scan Data", icon="📄")
settings_page = st.Page("pages/6_Settings.py", title="Settings", icon="⚙️")

pg = st.navigation(
    {
        "Home": [homepage],
        "Scan Management": [new_assessment_page, process_existing_scan_page, process_local_csv_page],
        "Reports": [generated_reports_page, raw_scan_data_page],
        "Settings": [settings_page]
    }
)
pg.run()

