import csv

def safe_int(value):
    try:
        return int(value)
    except ValueError:
        return 0

def safe_float(value):
    try:
        return float(value)
    except ValueError:
        return 0.0

def openvas_to_nessus(openvas_csv_file, nessus_csv_file):
    with open(openvas_csv_file, mode='r') as openvas_file:
        openvas_reader = csv.DictReader(openvas_file)

        nessus_header = [
            "Plugin ID", "CVE", "CVSS v2.0 Base Score", "Risk", "Host", "Protocol", "Port",
            "Name", "Synopsis", "Description", "Solution", "See Also", "Plugin Output", "STIG Severity",
            "CVSS v3.0 Base Score", "CVSS v2.0 Temporal Score", "CVSS v3.0 Temporal Score", "VPR Score",
            "Risk Factor", "BID", "XREF", "MSKB", "Plugin Publication Date", "Plugin Modification Date",
            "Metasploit", "Core Impact", "CANVAS"
        ]
        
        with open(nessus_csv_file, mode='w', newline='') as nessus_file:
            nessus_writer = csv.writer(nessus_file)
            nessus_writer.writerow(nessus_header)
            
            for row in openvas_reader:
                plugin_id = row.get('NVT OID', '')
                cve = row.get('CVEs', '')
                cvss_v2_score = safe_float(row.get('CVSS', ''))
                risk = row.get('Severity', '')
                host = row.get('IP', '')
                protocol = row.get('Port Protocol', '')
                port = safe_int(row.get('Port', ''))
                name = row.get('NVT Name', '')
                synopsis = row.get('Summary', '')
                description = row.get('Specific Result', '')
                solution = row.get('Solution', '')
                see_also = row.get('Other References', '')
                plugin_output = row.get('Vulnerability Insight', '')
                stig_severity = ''
                cvss_v3_score = ''
                cvss_v2_temporal_score = ''
                cvss_v3_temporal_score = ''
                vpr_score = ''
                risk_factor = row.get('Impact', '')
                bid = row.get('BIDs', '')
                xref = row.get('CERTs', '')
                mskb = ''
                plugin_pub_date = ''
                plugin_mod_date = row.get('Timestamp', '')
                metasploit = ''
                core_impact = ''
                canvas = ''
                
                nessus_writer.writerow([
                    plugin_id, cve, cvss_v2_score, risk, host, protocol, port,
                    name, synopsis, description, solution, see_also, plugin_output, stig_severity,
                    cvss_v3_score, cvss_v2_temporal_score, cvss_v3_temporal_score, vpr_score,
                    risk_factor, bid, xref, mskb, plugin_pub_date, plugin_mod_date,
                    metasploit, core_impact, canvas
                ])

openvas_csv_file = 'openvas_scan_results.csv'
nessus_csv_file = 'egis_scan_results.csv'

try:
    openvas_to_nessus(openvas_csv_file, nessus_csv_file)
    print(f"Conversion complete. Nessus formatted scan saved to {nessus_csv_file}")
except Exception as e:
    print(f"Error processing CSV: {e}")
