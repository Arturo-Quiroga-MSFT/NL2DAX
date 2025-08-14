#!/usr/bin/env python3
"""
Simple test script to replicate the exact XMLA request from the shell script
"""

import os
import requests
import msal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_token():
    tenant_id = os.getenv("PBI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET")
    
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )
    
    token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
    if token and "access_token" in token:
        return token["access_token"]
    else:
        raise RuntimeError(f"Failed to get token: {token}")

def test_dax_via_rest_api():
    """Test DAX execution via Power BI REST API instead of XMLA"""
    token = get_token()
    dataset_id = os.getenv("PBI_DATASET_ID")
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID", "e3fdee99-3aa4-4d71-a530-2964a062e326")
    
    # Simple DAX query to test
    dax_query = {
        "queries": [
            {
                "query": "EVALUATE TOPN(5, 'DimCustomer')"
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Power BI REST API endpoint for executing DAX queries
    endpoint = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    
    print(f"[DEBUG] Making request to: {endpoint}")
    print(f"[DEBUG] Workspace ID: {workspace_id}")
    print(f"[DEBUG] Dataset ID: {dataset_id}")
    print(f"[DEBUG] DAX Query: {dax_query}")
    
    response = requests.post(
        endpoint,
        json=dax_query,
        headers=headers,
        timeout=60
    )
    
    print(f"[DEBUG] Response status: {response.status_code}")
    print(f"[DEBUG] Response headers: {dict(response.headers)}")
    print(f"[DEBUG] Response body: {response.text[:1000]}")
    
    return response
    
    print(f"[DEBUG] Making request to: {endpoint}")
    print(f"[DEBUG] Catalog: {dataset_name}")
    print(f"[DEBUG] Request body length: {len(xmla_discover)}")
    
    response = requests.post(
        endpoint,
        data=xmla_discover.encode('utf-8'),
        headers=headers,
        timeout=60
    )
    
    print(f"[DEBUG] Response status: {response.status_code}")
    print(f"[DEBUG] Response headers: {dict(response.headers)}")
    print(f"[DEBUG] Response body: {response.text[:1000]}")
    
    return response

if __name__ == "__main__":
    try:
        response = test_dax_via_rest_api()
        if response.status_code == 200:
            print("[SUCCESS] DAX query executed successfully!")
        else:
            print(f"[ERROR] HTTP {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
