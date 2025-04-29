# EGIS Vulnerability Assessment Application

A web application to semi-automate the Vulnerability Assessment process, powered by Streamlit.

## Setup

1. Copy `.env-example` to `.env` and fill in your credentials:
   ```
   cp .env-example .env
   ```

2. Edit the `.env` file with your specific settings:
   - Nessus scanner credentials
   - Netbox API token
   - Elasticsearch configuration

## Docker Usage

The application is fully containerized for easy deployment:

### Run with Docker Compose

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f egis-app

# Stop all services
docker compose down
```

The EGIS web interface will be available at http://localhost:80

## Running Locally (Without Docker)

To run the application locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
cd egis-app
python main.py --port=8501
```

## Components

The project consists of:

- **EGIS**: Main vulnerability assessment application
  - Web interface for interaction
  - Nessus scanner integration for vulnerability scanning
  - Report generation capabilities for assessment documentation
- **Metasploitable2**: Demo vulnerable system (optional)

## Adding Additional Services

To add more services (e.g., Netbox, Nessus), edit the docker-compose.yml file to include the new services.

## Directory Structure

- **/egis-app** - Main application code
  - app_controller.py - Orchestrates the vulnerability assessment process
  - streamlit_gui.py - Web interface implementation
  - nessus_scanner.py, netbox_client.py, elastic_client.py - External integrations
  - report_generator.py - Report generation utilities
- **data/** - Generated reports and scan data
  - **raw_data/** - Raw CSV exports from scans
  - **reports/** - Generated PDF and HTML reports 