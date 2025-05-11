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
#     page_title="Settings | EGIS",
#     page_icon="⚙️",
#     layout="wide"
# )

# Ensure controller is initialized
if "controller" not in st.session_state:
    logger.info("Initializing AppController in session state (from Settings page)")
    st.session_state.controller = AppController()

# Page header
st.title("Application Settings")
st.markdown("---")

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

# Initialize log viewer state
if "show_logs" not in st.session_state:
    st.session_state.show_logs = False

# Logs section
st.subheader("Logs")
logs_exist = os.path.exists(os.path.join(LOGS_DIR, "egis.log"))
if logs_exist:
    st.metric("Logs Directory", LOGS_DIR)
    
    # Show log file preview
    log_path = os.path.join(LOGS_DIR, "egis.log")
    
    # Get log file size
    log_size = os.path.getsize(log_path) / (1024 * 1024)  # Convert to MB
    st.text(f"Log file size: {log_size:.2f} MB")
    
    # Option to view logs
    show_logs = st.checkbox("View recent logs", value=st.session_state.show_logs)
    st.session_state.show_logs = show_logs
    
    if show_logs:
        try:
            with open(log_path, "r") as f:
                # Read last 100 lines
                lines = f.readlines()[-100:]
                log_content = "".join(lines)
            st.code(log_content, language="text")
        except Exception as e:
            st.error(f"Error reading log file: {str(e)}")
else:
    st.warning(f"No log file found in {LOGS_DIR}")

# Initialize connectivity status in session state
if "connection_status" not in st.session_state:
    st.session_state.connection_status = {
        "checked": False,
        "nessus": "Unknown",
        "netbox": "Unknown",
        "elasticsearch": "Unknown"
    }

# Check connectivity to services
st.subheader("Service Status")

# Display current status if already checked
if st.session_state.connection_status["checked"]:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nessus Scanner", st.session_state.connection_status["nessus"])
    with col2:
        st.metric("Netbox", st.session_state.connection_status["netbox"])
    with col3:
        st.metric("Elasticsearch", st.session_state.connection_status["elasticsearch"])

if st.button("Check Connectivity"):
    logger.info("User initiated connectivity check")
    try:
        # Check Nessus connectivity
        try:
            nessus_status = "Connected" if st.session_state.controller.scanner.token else "Error"
            logger.debug(f"Nessus connectivity status: {nessus_status}")
            st.session_state.connection_status["nessus"] = nessus_status
        except Exception as e:
            logger.error(f"Error checking Nessus connectivity: {str(e)}")
            st.session_state.connection_status["nessus"] = "Error"
            
        # Check Netbox connectivity
        try:
            netbox_status = "Connected" if st.session_state.controller.netbox.test_connection() else "Error"
            logger.debug(f"Netbox connectivity status: {netbox_status}")
            st.session_state.connection_status["netbox"] = netbox_status
        except Exception as e:
            logger.error(f"Error checking Netbox connectivity: {str(e)}")
            st.session_state.connection_status["netbox"] = "Error"
            
        # Check Elasticsearch connectivity
        try:
            es_status = "Connected" if st.session_state.controller.elastic.test_connection() else "Error"
            logger.debug(f"Elasticsearch connectivity status: {es_status}")
            st.session_state.connection_status["elasticsearch"] = es_status
        except Exception as e:
            logger.error(f"Error checking Elasticsearch connectivity: {str(e)}")
            st.session_state.connection_status["elasticsearch"] = "Error"

        # Mark as checked
        st.session_state.connection_status["checked"] = True

        # Display status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nessus Scanner", st.session_state.connection_status["nessus"])
        with col2:
            st.metric("Netbox", st.session_state.connection_status["netbox"])
        with col3:
            st.metric("Elasticsearch", st.session_state.connection_status["elasticsearch"])
        
        logger.info("Connectivity check completed")
    except Exception as e:
        logger.error(f"Error during connectivity check: {str(e)}")
        st.error(f"Error checking connectivity: {str(e)}")

# Footer
st.markdown("---")
st.caption("EGIS Vulnerability Assessment Application - Settings") 