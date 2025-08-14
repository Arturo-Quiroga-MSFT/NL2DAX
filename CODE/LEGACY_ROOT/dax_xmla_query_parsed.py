import requests
import msal
import xml.etree.ElementTree as ET

# Azure AD and Power BI/AAS details
TENANT_ID = "your-tenant-id"
CLIENT_ID = "your-app-client-id"
CLIENT_SECRET = "your-app-client-secret"
XMLA_ENDPOINT = "https://your-xmla-endpoint-url"  # e.g., powerbi://api.powerbi.com/v1.0/myorg/yourworkspace
DATABASE = "your-dataset-name"

# Get Azure AD token
authority = f"https://login.microsoftonline.com/{TENANT_ID}"
app = msal.ConfidentialClientApplication(CLIENT_ID, authority=authority, client_credential=CLIENT_SECRET)
token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
access_token = token["access_token"]

# DAX query
dax_query = "EVALUATE FILTER('Customer', 'Customer'[Country] = \"United States\")"

# XMLA Execute command
xmla_body = f"""
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>{dax_query}</Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{DATABASE}</Catalog>
          <Format>Tabular</Format>
        </PropertyList>
      </Properties>
    </Execute>
  </Body>
</Envelope>
"""

headers = {
    "Content-Type": "text/xml",
    "Authorization": f"Bearer {access_token}"
}

response = requests.post(XMLA_ENDPOINT, data=xmla_body.encode("utf-8"), headers=headers)

# Parse XML response
def parse_xmla_response(xml_text):
    ns = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'xmla': 'urn:schemas-microsoft-com:xml-analysis',
        'm': 'urn:schemas-microsoft-com:xml-analysis:mddataset',
        'x': 'urn:schemas-microsoft-com:xml-analysis:rowset',
    }
    root = ET.fromstring(xml_text)
    # Find all rows in the response
    rows = root.findall('.//x:row', ns)
    results = []
    for row in rows:
        row_data = {child.tag.split('}', 1)[-1]: child.text for child in row}
        results.append(row_data)
    return results

parsed_results = parse_xmla_response(response.text)
print(parsed_results)
