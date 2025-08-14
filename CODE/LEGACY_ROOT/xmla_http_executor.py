

from __future__ import annotations
"""
Cross-platform XMLA execution for DAX over Power BI Premium/AAS using HTTP + AAD token.

Requires: requests, msal
Includes: transient retries, SOAP fault parsing, and a simple health-check helper.
"""

# Standard library imports
import os  # For environment variable access
import time  # For retry delays
import xml.etree.ElementTree as ET  # For XML parsing
from typing import List, Dict, Optional

# Third-party imports
import msal  # Microsoft Authentication Library for Azure AD
import requests  # For HTTP requests
import json  # For JSON encoding/decoding
from dotenv import load_dotenv  # For loading environment variables from .env file

# Load environment variables from .env file
load_dotenv()



# Custom exception for XMLA HTTP failures
class XmlaHttpError(RuntimeError):
  """Custom error for XMLA HTTP failures."""
  def __init__(self, message: str, status_code: Optional[int] = None):
    super().__init__(message)
    self.status_code = status_code



# Client for executing DAX queries over XMLA HTTP or Power BI REST API
class XmlaHttpClient:
  def __init__(self, tenant_id: str, client_id: str, client_secret: str, xmla_endpoint: str, database: str):
    # Store credentials and connection info
    self.tenant_id = tenant_id
    self.client_id = client_id
    self.client_secret = client_secret
    self.xmla_endpoint = xmla_endpoint
    self.database = database
    self._session = requests.Session()

  def _get_token(self, attempts: int = 3, base_delay: float = 1.0) -> str:
    """
    Acquire an Azure AD access token for the Power BI Service API, with retries.
    """
    authority = f"https://login.microsoftonline.com/{self.tenant_id}"
    app = msal.ConfidentialClientApplication(
      self.client_id,
      authority=authority,
      client_credential=self.client_secret,
    )
    last_err = None
    for i in range(attempts):
      token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
      if token and "access_token" in token:
        return token["access_token"]
      last_err = token
      time.sleep(base_delay * (2 ** i))
    raise RuntimeError(
      "Failed to acquire Azure AD token after retries. "
      f"Details: {last_err}. Verify tenant/client/secret and API permissions (Power BI Service)."
    )

  def execute_dax(self, dax_query: str, attempts: int = 3, base_delay: float = 1.0) -> List[Dict]:
    """
    Execute a DAX query against the XMLA endpoint or Power BI REST API.
    If the endpoint is powerbi://, use the REST API; otherwise, use SOAP-over-HTTP.
    """
    # Use REST API if endpoint is powerbi://
    if self.xmla_endpoint.lower().startswith("powerbi://"):
      print(f"[DEBUG] Using Power BI REST API for endpoint: {self.xmla_endpoint}")
      return rest_execute_dax_via_api(
        tenant_id=self.tenant_id,
        client_id=self.client_id,
        client_secret=self.client_secret,
        workspace_connection=self.xmla_endpoint,
        dataset_name=self.database,
        dax_query=dax_query,
      )

    print(f"[DEBUG] Using XMLA SOAP over HTTP for endpoint: {self.xmla_endpoint}")
    # Build XMLA SOAP request body
    xmla_body = f"""<?xml version="1.0" encoding="utf-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Discover xmlns="urn:schemas-microsoft-com:xml-analysis">
      <RequestType>DISCOVER_DATASOURCES</RequestType>
      <Restrictions />
      <Properties>
        <PropertyList>
          <Catalog>{self.database}</Catalog>
        </PropertyList>
      </Properties>
    </Discover>
  </Body>
</Envelope>"""
    headers = {
      "Content-Type": "text/xml",
      "Authorization": f"Bearer {self._get_token()}",
    }
    
    print(f"[DEBUG] XMLA SOAP request to: {self.xmla_endpoint}")
    print(f"[DEBUG] Using database/catalog: {self.database}")
    print(f"[DEBUG] XMLA request body: {xmla_body[:500]}...")

    last_exc: Optional[Exception] = None
    for i in range(attempts):
      try:
        # Send the XMLA request
        resp = self._session.post(
          self.xmla_endpoint,
          data=xmla_body.encode("utf-8"),
          headers=headers,
          timeout=60,
        )
        # Handle HTTP errors and parse SOAP faults
        if resp.status_code >= 400:
          fault = try_parse_soap_fault(resp.text)
          extra_hint = hint_for_status(resp.status_code)
          print(f"[DEBUG] Full XMLA error response: {resp.text[:1000]}")
          raise XmlaHttpError(
            message=(
              f"HTTP {resp.status_code} calling XMLA endpoint. {extra_hint}\n"
              f"Endpoint: {self.xmla_endpoint}\nDatabase: {self.database}\n"
              f"Details: {fault or resp.text[:500]}"
            ),
            status_code=resp.status_code,
          )
        # Parse and return the result
        return parse_xmla_response(resp.text)
      except (requests.Timeout, requests.ConnectionError) as e:
        last_exc = e
      except XmlaHttpError as e:
        if not is_transient_status(e.status_code):
          raise
        last_exc = e
      time.sleep(base_delay * (2 ** i))
    raise RuntimeError(f"XMLA request failed after retries: {last_exc}")


def get_access_token(tenant_id: str, client_id: str, client_secret: str, attempts: int = 3, base_delay: float = 1.0) -> str:
  """
  Acquire an Azure AD access token for the Power BI Service API, with retries.
  """
  authority = f"https://login.microsoftonline.com/{tenant_id}"
  app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
  last_err = None
  for i in range(attempts):
    token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
    if token and "access_token" in token:
      return token["access_token"]
    last_err = token
    time.sleep(base_delay * (2 ** i))
  raise RuntimeError(
    "Failed to acquire Azure AD token after retries. "
    f"Details: {last_err}. Verify tenant/client/secret and API permissions (Power BI Service)."
  )


def rest_execute_dax_via_api(tenant_id: str, client_id: str, client_secret: str, workspace_connection: str, dataset_name: str, dax_query: str, dataset_id: Optional[str] = None) -> List[Dict]:
  """
  Execute a DAX query using the Power BI REST Execute Queries API.
  Resolves workspace and dataset, then posts the query and parses the result.
  """
  """Execute a DAX query using the Power BI REST Execute Queries API.

  Steps:
  - Acquire token
  - Resolve workspace (group) ID from workspace name in powerbi:// connection
  - Resolve dataset ID by dataset_name in that workspace
  - POST executeQueries
  """
  if not workspace_connection.lower().startswith("powerbi://"):
    raise ValueError("REST execution expects a powerbi:// workspace connection")

  # Parse workspace name from powerbi://.../myorg/<workspace>
  try:
    ws_name = workspace_connection.rsplit('/', 1)[-1]
  except Exception:
    raise ValueError(f"Unable to parse workspace name from connection: {workspace_connection}")

  token = get_access_token(tenant_id, client_id, client_secret)
  sess = requests.Session()
  headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

  # Find workspace (group) by name
  groups_url = "https://api.powerbi.com/v1.0/myorg/groups"
  resp = sess.get(groups_url, headers=headers, timeout=60)
  resp.raise_for_status()
  groups = resp.json().get("value", [])
  group = next((g for g in groups if g.get("name") == ws_name), None)
  if not group:
    # Case-insensitive fallback
    group = next((g for g in groups if str(g.get("name", "")).lower() == ws_name.lower()), None)
  if not group:
    raise RuntimeError(f"Workspace not found by name: {ws_name}")
  group_id = group.get("id")
  print(f"[DEBUG] Found workspace '{ws_name}' with ID: {group_id}")

  # Find dataset by ID (preferred) or name in workspace
  ds_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets"
  ds_resp = sess.get(ds_url, headers=headers, timeout=60)
  ds_resp.raise_for_status()
  datasets = ds_resp.json().get("value", [])
  if dataset_id:
    dataset = next((d for d in datasets if d.get("id") == dataset_id), None)
    if not dataset:
      ids = ", ".join(sorted(d.get("id", "?") for d in datasets))
      raise RuntimeError(f"Dataset ID '{dataset_id}' not found in workspace '{ws_name}'. Available IDs: {ids}")
  else:
    dataset = next((d for d in datasets if d.get("name") == dataset_name), None)
    if not dataset:
      dataset = next((d for d in datasets if str(d.get("name", "")).lower() == dataset_name.lower()), None)
    if not dataset:
      names = ", ".join(sorted(d.get("name", "?") for d in datasets))
      raise RuntimeError(f"Dataset '{dataset_name}' not found in workspace '{ws_name}'. Available: {names}")
    dataset_id = dataset.get("id")

  print(f"[DEBUG] Found dataset '{dataset_name}' with ID: {dataset_id}")
  
  # Execute DAX
  exec_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
  print(f"[DEBUG] Making executeQueries request to: {exec_url}")
  payload = {"queries": [{"query": dax_query}], "serializerSettings": {"includeNulls": True}}
  ex_resp = sess.post(exec_url, headers=headers, data=json.dumps(payload), timeout=120)
  if ex_resp.status_code >= 400:
    raise RuntimeError(f"ExecuteQueries failed HTTP {ex_resp.status_code}: {ex_resp.text[:500]}")
  data = ex_resp.json()
  # Parse first table rows
  try:
    results = data.get("results", [])
    if not results:
      return []
    tables = results[0].get("tables", [])
    if not tables:
      return []
    rows = tables[0].get("rows", [])
    return rows  # rows are already list of dicts
  except Exception as e:
    raise RuntimeError(f"Failed to parse ExecuteQueries response: {e}. Raw: {str(data)[:500]}")


def parse_xmla_response(xml_text: str) -> List[Dict]:
  """
  Parse the XMLA SOAP response and extract rows as a list of dictionaries.
  """
  ns = {
    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
    'xmla': 'urn:schemas-microsoft-com:xml-analysis',
    'm': 'urn:schemas-microsoft-com:xml-analysis:mddataset',
    'x': 'urn:schemas-microsoft-com:xml-analysis:rowset',
  }
  root = ET.fromstring(xml_text)
  rows = root.findall('.//x:row', ns)
  results: List[Dict] = []
  for row in rows:
    row_data = {child.tag.split('}', 1)[-1]: (child.text or "") for child in row}
    results.append(row_data)
  return results


def try_parse_soap_fault(xml_text: str) -> Optional[str]:
  """
  Try to parse a SOAP fault from the XMLA response for error reporting.
  """
  try:
    root = ET.fromstring(xml_text)
    ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
    fault = root.find('.//soap:Fault', ns)
    if fault is None:
      return None
    faultcode = fault.findtext('faultcode') or ''
    faultstring = fault.findtext('faultstring') or ''
    return f"{faultcode}: {faultstring}"
  except Exception:
    return None


def is_transient_status(status_code: Optional[int]) -> bool:
  """
  Determine if an HTTP status code is likely transient (retryable).
  """
  if status_code is None:
    return True
  if status_code in (408, 429):
    return True
  return 500 <= status_code <= 599


def hint_for_status(status_code: int) -> str:
  """
  Return a human-readable hint for a given HTTP status code.
  """
  if status_code == 401:
    return "Unauthorized: check token scope and that the principal has Build access to the dataset/workspace."
  if status_code == 403:
    return "Forbidden: ensure the service principal/user is a Member/Contributor and XMLA read is enabled."
  if status_code == 404:
    return "Not Found: verify XMLA endpoint URL and dataset (Catalog) name."
  if status_code == 400:
    return "Bad Request: likely invalid DAX. Validate the query syntax and model references."
  if status_code == 429:
    return "Throttled: reduce request rate or add backoff."
  if 500 <= status_code <= 599:
    return "Server error: transient issue; retry with backoff."
  return ""


def execute_dax_via_http(dax_query: str) -> List[Dict]:
  """
  Execute a DAX query using environment variables for credentials and connection info.
  Uses XMLA HTTP or Power BI REST API depending on endpoint.
  """
  tenant_id = os.getenv("PBI_TENANT_ID")
  client_id = os.getenv("PBI_CLIENT_ID")
  client_secret = os.getenv("PBI_CLIENT_SECRET")
  xmla_endpoint = os.getenv("PBI_XMLA_ENDPOINT")
  database = os.getenv("PBI_DATASET_NAME")
  dataset_id = os.getenv("PBI_DATASET_ID")
  missing = [k for k, v in {
    'PBI_TENANT_ID': tenant_id,
    'PBI_CLIENT_ID': client_id,
    'PBI_CLIENT_SECRET': client_secret,
    'PBI_XMLA_ENDPOINT': xmla_endpoint,
    'PBI_DATASET_NAME': database,
  }.items() if not v]
  if missing:
    raise ValueError(f"Missing required env vars for XMLA HTTP: {', '.join(missing)}")
  client = XmlaHttpClient(tenant_id, client_id, client_secret, xmla_endpoint, database)
  # If powerbi://, rest_execute_dax_via_api will be used internally; pass dataset_id via env using a closure.
  if xmla_endpoint.lower().startswith("powerbi://"):
    return rest_execute_dax_via_api(
      tenant_id=tenant_id,
      client_id=client_id,
      client_secret=client_secret,
      workspace_connection=xmla_endpoint,
      dataset_name=database,
      dax_query=dax_query,
      dataset_id=dataset_id,
    )
  return client.execute_dax(dax_query)


def health_check() -> bool:
  """
  Simple connectivity check using a model-agnostic DAX query.
  Returns True if the query succeeds and returns the expected result.
  """
  """Simple connectivity check using a model-agnostic DAX query."""
  res = execute_dax_via_http('EVALUATE ROW("ping", 1)')
  return isinstance(res, list) and len(res) == 1 and 'ping' in {k.lower() for k in res[0].keys()}


# Main block at the very end of the file, after all function and class definitions
if __name__ == "__main__":
    print("[DEBUG] Starting xmla_http_executor.py...")
    import sys
    try:
        # Example: run a health check or a sample DAX query
        print("[DEBUG] Running health check...")
        result = health_check()
        print(f"[DEBUG] Health check result: {result}")
        # Optionally, run a sample DAX query
        print("[DEBUG] Running sample DAX query...")
        rows = execute_dax_via_http('EVALUATE ROW("Test", 1+1)')
        print(f"[DEBUG] DAX query result: {rows}")
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("[DEBUG] xmla_http_executor.py completed.")
