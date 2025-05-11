# EGIS Vulnerability Assessment Application

A web application to semi-automate the Vulnerability Assessment process, powered by Streamlit.

## Features

- **Integrated Vulnerability Scanning** - Create and launch scans directly from the application
- **Automated Report Generation** - Generate PDF reports with vulnerability findings
- **Asset Discovery** - Integrate with Netbox for target discovery
- **Data Persistence** - Store vulnerability data in Elasticsearch for analysis and tracking
- **Web Interface** - Easy-to-use Streamlit interface for scan management and report generation
- **Organization-Based Scanning & Reporting** - Run vulnerability scans & generate reports from them, based on selected organizations/tenants

## Architecture Overview
The application consists of several key components:
- **App Controller** - Orchestrates the vulnerability assessment process
- **Nessus Integration** - Communicates with Tenable Nessus for vulnerability scanning
- **Netbox Integration** - Retrieves target information from Netbox CMDB
- **Elasticsearch Integration** - Stores structured vulnerability data
- **Report Generator** - Creates PDF and HTML reports from scan data
- **Web Interface** - Streamlit multipage GUI for user interaction

## Setup & Configuration
### 1. Environment Setup
- Copy `.env-example` to `.env` and fill in your credentials:
  ```
  cp .env-example .env
  ```
- Edit the `.env` file with your specific settings:
  - Nessus scanner credentials
  - Netbox API token
  - Elasticsearch configuration

### 2. Netbox Integration Requirements
To enable asset discovery and organization-based scanning, the following must be present in your Netbox instance:
- **Tenants (Organizations):**
  - Each organization must be created as a Netbox Tenant (`/api/tenancy/tenants/`).
  - Required fields: `name`, `slug`, and optionally `description`.
  - Example:
    ```json
    {
      "id": 1,
      "name": "Example Organization",
      "slug": "example-org",
      "description": "Example description for organization."
    }
    ```
- **Contacts:**
  - Each organization should have at least one associated Contact (`/api/tenancy/contacts/`), assigned via a Contact Assignment (`/api/tenancy/contact-assignments/`).
  - Required contact fields: `name`, `email` (for notifications/reporting), and optionally `phone`, `title`, `role`, `priority`.
  - The Contact Assignment must link the contact to the tenant, with a `role` (e.g., `Administrator`) and a `priority` (e.g., `primary`).
  - Example Contact Assignment:
    ```json
    {
      "object_id": 1,  // Tenant ID
      "contact": { "name": "Example Admin", "email": "admin@example.org" },
      "role": { "name": "Administrator" },
      "priority": { "value": "primary" }
    }
    ```
- **Scan Targets (IP Addresses):**
  - IP addresses to be scanned must be present in Netbox IPAM (`/api/ipam/ip-addresses/`).
  - Each IP must:
    - Be assigned to the correct tenant (`tenant` field, matching the organization)
    - Have the tag with slug `vuln-scan` (required for discovery by the app)
    - Optionally include `dns_name` and `description` for enrichment
    - Be assigned to a device or virtual machine for best enrichment (fields: `assigned_object`, `device`, `virtual_machine`, `site`, `rack`)
  - Example:
    ```json
    {
      "address": "192.0.2.10/24",
      "tenant": { "id": 1, "name": "Example Organization" },
      "dns_name": "host1.example.org",
      "description": "Example VM for vulnerability scanning.",
      "tags": [ { "slug": "vuln-scan" } ],
      "assigned_object": { "virtual_machine": { "name": "host1-vm" } }
    }
    ```
- **Tag Requirement:**
  - The tag with slug `vuln-scan` must exist in Netbox and be assigned to all IP addresses that should be included in vulnerability scans.

If any of these requirements are not met, the application will not be able to discover or enrich scan targets for the given organization.

### 3. Required CSV Format for Scan Import
When importing scan results from a CSV file (e.g., Nessus export), the file must have the following columns (header row required):
```
Plugin ID,CVE,CVSS v2.0 Base Score,Risk,Host,Protocol,Port,Name,Synopsis,Description,Solution,See Also,Plugin Output,STIG Severity,CVSS v3.0 Base Score,CVSS v2.0 Temporal Score,CVSS v3.0 Temporal Score,VPR Score,Risk Factor,BID,XREF,MSKB,Plugin Publication Date,Plugin Modification Date,Metasploit,Core Impact,CANVAS
```
- Each row represents a single vulnerability finding for a host/port.
- All columns above must be present (even if some values are empty for a given row).
- The most important columns for correct parsing and reporting are:
  - `Host` (IP address of the affected host)
  - `Port`, `Protocol` (service context)
  - `Name`, `Synopsis`, `Description`, `Solution` (vulnerability details)
  - `Risk` or `Risk Factor` (severity)
  - `CVE`, `Plugin ID` (identifiers)
- The parser is designed for Nessus CSV format, but other scanners work if the columns match exactly.

If the CSV format does not match, the import will fail or produce incorrect results.

## Usage
### Docker Deployment
The application is fully containerized for easy deployment:
```bash
# Start all services
docker compose up -d
# View logs
docker compose logs -f egis-app
# Stop all services
docker compose down
```
The EGIS web interface will be available at http://localhost:80

### Running Locally (Without Docker)
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

## Data Formats
### Elasticsearch Document Structure
The application stores each vulnerability finding as a separate document in Elasticsearch with the following structure:
```json
{
  "organization": {
    "id": "1",
    "name": "Example Organization",
    "description": "Example description for organization.",
    "primary_contact_name": "Example Admin",
    "primary_contact_email": "admin@example.org",
    "primary_contact_phone": "",
    "slug": "example-org",
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
    "id": "192.0.2.10",
    "ip": "192.0.2.10",
    "name": "Nessus Professional",
    "version": "10.5.1",
    "os": "Linux",
    "distribution": "Ubuntu 22.04"
  },
  "scan": {
    "id": "EGIS_Assessment_YYYYMMDD_HHMMSS",
    "name": "EGIS_Assessment_YYYYMMDD_HHMMSS",
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
    "ip": "192.0.2.11",
    "dns_name": "host1.example.org",
    "os_family": "Linux",
    "os_distribution": "Ubuntu",
    "os_version": "20.04.3 LTS",
    "device_name": "host1-vm",
    "device_role": "Virtual Machine",
    "site_name": "Example Site",
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

The data is also passed from the `vulnerability_parser.py` to `report_generator.py` in the following format, for easy iteration of the hosts and vulnerabilities:
```json
{
  "organization": { ... },  // Organization/tenant details
  "scanner": { ... },       // Scanner information
  "scan": { ... },          // Scan metadata and statistics
  "hosts": [                // List of hosts in the scan
    {
      "ip": "192.0.2.11",
      "dns_name": "host1.example.org",
      "os_family": "Linux",
      "device_name": "host1-vm",
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
      "host_ip": "192.0.2.11",
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

### Importing Visualizations into Kibana
Kibana requires NDJSON format for importing saved objects. To convert the provided JSON array to NDJSON:
- **Using jq (recommended):**
  ```bash
  jq -c '.[]' kibana_visualizations.json > kibana_visualizations.ndjson
  ```
- **Using Python:**
  ```python
  import json
  with open('kibana_visualizations.json') as f:
      data = json.load(f)
  with open('kibana_visualizations.ndjson', 'w') as f:
      for obj in data:
          f.write(json.dumps(obj) + '\n')
  ```
- **Or use an online tool:**
  - https://json2ndjson.com/

1. Go to **Kibana → Stack Management → Saved Objects → Import**
2. Select the `kibana_visualizations.ndjson` file
3. The visualizations will be available for use and can be added to dashboards
## Troubleshooting
If you encounter issues:
1. Check the logs in the Settings page for error messages
2. Verify service connectivity in the Settings page
3. Ensure your environment variables are correctly set in the .env file

## Using the Application: Typical Workflow
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
