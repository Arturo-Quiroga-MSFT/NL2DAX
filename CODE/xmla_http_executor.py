"""
xmla_http_executor.py

Cross-platform XMLA execution for DAX over Power BI Premium/AAS using HTTP + AAD token.
Requires: requests, msal
Includes: transient retries, SOAP fault parsing, and a simple health-check helper.
"""
from __future__ import annotations

import os
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

import msal
import requests


class XmlaHttpError(RuntimeError):
  """Custom error for XMLA HTTP failures."""
  def __init__(self, message: str, status_code: Optional[int] = None):
    super().__init__(message)
    self.status_code = status_code


class XmlaHttpClient:
  def __init__(self, tenant_id: str, client_id: str, client_secret: str, xmla_endpoint: str, database: str):
    self.tenant_id = tenant_id
    self.client_id = client_id
    self.client_secret = client_secret
    self.xmla_endpoint = xmla_endpoint
    self.database = database
    self._session = requests.Session()

  def _get_token(self, attempts: int = 3, base_delay: float = 1.0) -> str:
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
    xmla_body = f"""
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
  <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
    <Command>
    <Statement>{dax_query}</Statement>
    </Command>
    <Properties>
    <PropertyList>
      <Catalog>{self.database}</Catalog>
      <Format>Tabular</Format>
    </PropertyList>
    </Properties>
  </Execute>
  </Body>
</Envelope>
"""
    headers = {
      "Content-Type": "text/xml",
      "Authorization": f"Bearer {self._get_token()}",
    }

    last_exc: Optional[Exception] = None
    for i in range(attempts):
      try:
        resp = self._session.post(
          self.xmla_endpoint,
          data=xmla_body.encode("utf-8"),
          headers=headers,
          timeout=60,
        )
        if resp.status_code >= 400:
          fault = try_parse_soap_fault(resp.text)
          extra_hint = hint_for_status(resp.status_code)
          raise XmlaHttpError(
            message=(
              f"HTTP {resp.status_code} calling XMLA endpoint. {extra_hint}\n"
              f"Endpoint: {self.xmla_endpoint}\nDatabase: {self.database}\n"
              f"Details: {fault or resp.text[:500]}"
            ),
            status_code=resp.status_code,
          )
        return parse_xmla_response(resp.text)
      except (requests.Timeout, requests.ConnectionError) as e:
        last_exc = e
      except XmlaHttpError as e:
        if not is_transient_status(e.status_code):
          raise
        last_exc = e
      time.sleep(base_delay * (2 ** i))
    raise RuntimeError(f"XMLA request failed after retries: {last_exc}")


def parse_xmla_response(xml_text: str) -> List[Dict]:
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
  if status_code is None:
    return True
  if status_code in (408, 429):
    return True
  return 500 <= status_code <= 599


def hint_for_status(status_code: int) -> str:
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
  tenant_id = os.getenv("PBI_TENANT_ID")
  client_id = os.getenv("PBI_CLIENT_ID")
  client_secret = os.getenv("PBI_CLIENT_SECRET")
  xmla_endpoint = os.getenv("PBI_XMLA_ENDPOINT")
  database = os.getenv("PBI_DATASET_NAME")
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
  return client.execute_dax(dax_query)


def health_check() -> bool:
  """Simple connectivity check using a model-agnostic DAX query."""
  res = execute_dax_via_http('EVALUATE ROW("ping", 1)')
  return isinstance(res, list) and len(res) == 1 and 'ping' in {k.lower() for k in res[0].keys()}
