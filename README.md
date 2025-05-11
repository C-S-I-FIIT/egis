# EGIS Vulnerability Assessment Application

A web application to semi-automate the Vulnerability Assessment process, powered by Streamlit.

## Features

- **Integrated Vulnerability Scanning** - Create and launch scans directly from the application
- **Automated Report Generation** - Generate PDF reports with vulnerability findings
- **Asset Discovery** - Integrate with Netbox for target discovery
- **Data Persistence** - Store vulnerability data in Elasticsearch for analysis and tracking
- **Web Interface** - Easy-to-use Streamlit interface for scan management and report generation
- **Organization-Based Scanning & Reporting** - Run vulnerability scans & generate reports from them, based on selected organizations/tenants

## Architecture

The application consists of several key components:

- **App Controller** - Orchestrates the vulnerability assessment process
- **Nessus Integration** - Communicates with Tenable Nessus for vulnerability scanning
- **Netbox Integration** - Retrieves target information from Netbox CMDB
- **Elasticsearch Integration** - Stores structured vulnerability data
- **Report Generator** - Creates PDF and HTML reports from scan data
- **Web Interface** - Streamlit multipage GUI for user interaction

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
python -m streamlit run homepage.py --server.port 80
```

## Directory Structure

- **/egis-app/** - Main application code
  - **app_controller.py** - Orchestrates the vulnerability assessment process
  - **config.py** - Configuration and environment variables
  - **elastic_client.py** - Elasticsearch integration
  - **nessus_scanner.py** - Nessus vulnerability scanner integration
  - **netbox_client.py** - Netbox CMDB integration
  - **net_manager.py** - Network request utilities
  - **report_generator.py** - Report generation utilities
  - **homepage.py** - Web interface homepage, used as the application entrypoint
  - **vulnerability_parser.py** - Parses scan results into structured format
  - **/pages/** - Multipage app pages
    - **1_Run_New_Assessment.py** - Run vulnerability scans for organizations
    - **2_Process_Existing_Scan.py** - Process scans from Nessus by ID
    - **3_Process_Local_CSV.py** - Upload and process CSV scan data
    - **4_Generated_Reports.py** - View and download generated reports
    - **5_Raw_Scan_Data.py** - View and process raw scan data
    - **6_Settings.py** - Application settings and service connectivity
  - **/templates/** - Report templates using Jinja2

- **/data/** - Generated reports and scan data
  - **/raw_data/** - Raw CSV exports from scans
  - **/reports/** - Generated PDF and HTML reports
  - **/logs/** - Application logs

## Application Navigation

The EGIS application uses Streamlit's multipage navigation structure with categorized pages:

- **Home** - Dashboard with quick actions and statistics
- **Scan Management**
  - Run New Assessment - Execute vulnerability scans for selected organizations
  - Process Existing Scan - Process scan results from Nessus by ID
  - Process Local CSV - Upload and process CSV scan results
- **Reports**
  - Generated Reports - View and download PDF/HTML reports
  - Raw Scan Data - View and process raw CSV scan data
- **Settings** - Configure application settings and check service connectivity

## Getting Started

After launching the application, you can:

1. Navigate to "Run New Assessment" to select organizations and start a scan
2. Check "Settings" to verify connectivity to required services
3. View generated reports in the "Reports" section after scans complete

## Troubleshooting

If you encounter issues:

1. Check the logs in the Settings page for error messages
2. Verify service connectivity in the Settings page
3. Ensure your environment variables are correctly set in the .env file

## Screenshots

![EGIS Home Dashboard](https://example.com/screenshots/egis-home.png)
![Organization Selection](https://example.com/screenshots/organization-selection.png)
![Generated Reports](https://example.com/screenshots/reports-view.png)

## Elasticsearch Document Structure

The application stores each vulnerability finding as a separate document in Elasticsearch with the following structure:

```json
{
  "organization": {
    "id": "1",
    "name": "FIIT Academy",
    "description": "FIIT Academy / Cisco NetAcad labs",
    "primary_contact_name": "FIIT Academy - Admin",
    "primary_contact_email": "admin@fiitacademy.fiit.stuba.sk",
    "primary_contact_phone": "",
    "slug": "fiit-academy",
    "contacts": [
      {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1 555-123-4567",
        "title": "Security Engineer",
        "role": "Technical Contact",
        "priority": "high"
      }
    ]
  },
  "scanner": {
    "id": "10.0.220.11",
    "ip": "10.0.220.11",
    "name": "Nessus Professional",
    "version": "10.5.1",
    "os": "Linux",
    "distribution": "Ubuntu 22.04"
  },
  "scan": {
    "id": "EGIS_Assessment_20250501_141500",
    "name": "EGIS_Assessment_20250501_141500",
    "type": "authenticated",
    "start_timestamp": "2025-05-01T14:15:00",
    "end_timestamp": "2025-05-01T14:45:30",
    "duration_seconds": 1830,
    "policy": "Advanced Scan",
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0,
    "total_vulnerabilities": 0,
    "total_hosts": 0
  },
  "host": {
    "ip": "10.0.220.12",
    "dns_name": "dp-broman-vulnerable.fiitacademy.fiit.stuba.sk",
    "os_family": "Linux",
    "os_distribution": "Ubuntu",
    "os_version": "20.04.3 LTS",
    "device_name": "dp-broman-vulnerable",
    "device_role": "Virtual Machine",
    "site_name": "FIIT Academy Lab",
    "rack": "",
    "critical_count": 2,
    "high_count": 5,
    "medium_count": 12,
    "low_count": 8,
    "total_vulnerabilities": 0,
    "open_ports": [
      {
        "port": 22,
        "service": "SSH",
        "version": "OpenSSH 7.9",
        "protocol": "tcp",
        "has_vulnerabilities": true,
        "severity": "Medium"
      },
      {
        "port": 80,
        "service": "HTTP",
        "version": "Apache 2.4.41",
        "protocol": "tcp",
        "has_vulnerabilities": true,
        "severity": "High"
      },
      {
        "port": 443,
        "service": "HTTPS",
        "version": "Apache 2.4.41",
        "protocol": "tcp",
        "has_vulnerabilities": false
      }
    ]
  },
  "vulnerability": {
    "plugin_id": "19506",
    "name": "SSH Weak Algorithms Supported",
    "severity": "Medium",
    "port": 22,
    "protocol": "tcp",
    "service": "SSH",
    "version": "OpenSSH 7.9",
    "cve": "CVE-2019-15907",
    "cvss": {
      "v2": {
        "base_score": 4.3,
        "temporal_score": 3.7
      },
      "v3": {
        "base_score": 5.9,
        "temporal_score": 5.2
      },
      "vpr_score": 5.5
    },
    "synopsis": "The SSH server is configured to use weak encryption algorithms.",
    "description": "The SSH server is configured to allow weak encryption algorithms or no algorithm at all. An attacker can exploit this to conduct man-in-the-middle attacks or recover the plaintext from the ciphertext.",
    "solution": "Configure the SSH server to only use strong encryption algorithms.",
    "plugin_output": "The SSH server is configured to use the following weak algorithms:\n\nCipher algorithms:\naes128-ctr\naes192-ctr\naes256-ctr\narcfour256\narcfour128\naes128-cbc\n3des-cbc\nblowfish-cbc\ncast128-cbc\naes192-cbc\naes256-cbc\narcfour\n\nMAC algorithms:\nhmac-md5\nhmac-sha1\nhmac-sha2-256\nhmac-sha2-512\n\nKey exchange algorithms:\ndiffie-hellman-group-exchange-sha1\ndiffie-hellman-group14-sha1\ndiffie-hellman-group1-sha1",
    "risk_factor": "Medium",
    "see_also": "https://www.openssh.com/security.html\nhttps://www.ssh.com/ssh/protocol/",
    "stig_severity": "Medium",
    "bid": "",
    "xref": "CWE:327",
    "mskb": "",
    "plugin_publication_date": "2005-11-11",
    "plugin_modification_date": "2021-03-03",
    "exploitable": "false"
  },
  "@timestamp": "2025-05-01T14:32:15"
}
```

This structured format allows for efficient querying and visualization in Elasticsearch and Kibana.

The data is also passed from the `vulnerability_parser.py` to `report_generator.py` in the following format, for easy iteration of the hosts and vulnerabilities:
```json
{
  "organization": { ... },  // Organization/tenant details
  "scanner": { ... },       // Scanner information
  "scan": { ... },          // Scan metadata and statistics
  "hosts": [                // List of hosts in the scan
    {
      "ip": "10.0.220.12",
      "dns_name": "example.domain.com",
      "os_family": "Linux",
      "device_name": "example-server",
      // Other host properties
      "open_ports": [       // List of port dictionaries
        {
          "port": 22,
          "service": "SSH",
          "version": "OpenSSH 7.9",
          "protocol": "tcp",
          "has_vulnerabilities": true,
          "severity": "Medium"
        },
        // Other ports
      ]
    },
    // Other hosts
  ],
  "vulnerabilities": [      // List of vulnerabilities found
    {
      "host_ip": "10.0.220.12",
      "plugin_id": "19506",
      "name": "SSH Weak Algorithms Supported",
      "severity": "Medium",
      "port": 22,
      // Other vulnerability properties
    },
    // Other vulnerabilities
  ]
}
```

## Kibana Visualizations

The repository includes a file `kibana_visualizations.json` with example visualizations for vulnerability data. These visualizations help you quickly analyze metrics such as:
- Number of critical vulnerabilities (system-wide and per host)
- CVE density per host
- Vulnerabilities over time
- Most common types of vulnerabilities

### How to Import Visualizations into Kibana

Kibana requires NDJSON format for importing saved objects. To convert the provided JSON array to NDJSON:

**Using jq (recommended):**
```bash
jq -c '.[]' kibana_visualizations.json > kibana_visualizations.ndjson
```

**Using Python:**
```python
import json
with open('kibana_visualizations.json') as f:
    data = json.load(f)
with open('kibana_visualizations.ndjson', 'w') as f:
    for obj in data:
        f.write(json.dumps(obj) + '\n')
```

**Or use an online tool:**
- https://json2ndjson.com/

### Importing into Kibana
1. Go to **Kibana → Stack Management → Saved Objects → Import**
2. Select the `kibana_visualizations.ndjson` file
3. The visualizations will be available for use and can be added to dashboards

## Using the Application

1. **Run a New Assessment**
   - Navigate to the "Scan Management" page
   - Select one or more organizations to scan from the multiselect dropdown
   - Alternatively, check "Scan All Organizations" to include all available organizations
   - Click "Run Assessment" to launch the vulnerability scans
   - Each organization is processed separately with individual scan results

2. **Process Existing Scan**
   - Enter a Nessus scan ID to process an existing scan
   - Optionally select an organization for data enrichment
   - Click "Process Scan" to generate reports

3. **Process Local CSV**
   - Upload a Nessus CSV export file
   - Optionally select an organization for data enrichment
   - Click "Process CSV" to generate reports

4. **View and Download Reports**
   - Navigate to the "Reports" page
   - Download generated PDF reports
   - Alternatively, process raw scan data with organization-specific enrichment

## NetBox Integration

The application integrates with NetBox to retrieve target information and organize reports by tenant:

1. **Target Discovery**
   - IP addresses tagged with 'vuln-scan' in NetBox are automatically discovered
   - Device information is retrieved from NetBox when available

2. **Organization-Based Scanning**
   - Select one or more organizations (tenants) to scan only their IP addresses
   - Each organization is processed individually with separate scans
   - Results include organization-specific information and contact details

3. **Organization-Based Reporting**
   - Tenant information is retrieved from NetBox to organize findings by organization
   - Contact details are included in reports for easy notification of vulnerabilities
   - Report filenames include organization names for easy identification

4. **Contact Management**
   - Primary contacts are identified from tenant assignments in NetBox
   - Contact information is included in reports and Elasticsearch documents
   - Priority contacts can be designated in NetBox for targeted reporting

5. **Setting Up NetBox for EGIS**
   - Tag IP addresses with 'vuln-scan' to include them in vulnerability assessments
   - Associate IP addresses with tenants to enable organization-based scanning and reporting
   - Add contact assignments to tenants to include contact information in reports
