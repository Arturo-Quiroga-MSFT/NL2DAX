#!/usr/bin/env python3
"""
Test script to verify Power BI service principal permissions
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

def test_permissions():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("Testing Power BI permissions...")
    
    # Test 1: List workspaces
    print("\n1. Testing workspace access...")
    resp = requests.get("https://api.powerbi.com/v1.0/myorg/groups", headers=headers)
    if resp.status_code == 200:
        workspaces = resp.json().get("value", [])
        fis_workspace = next((w for w in workspaces if w.get("name") == "FIS"), None)
        if fis_workspace:
            print(f"✅ Found FIS workspace: {fis_workspace['id']}")
            workspace_id = fis_workspace['id']
        else:
            print("❌ FIS workspace not found")
            return
    else:
        print(f"❌ Failed to list workspaces: {resp.status_code} - {resp.text}")
        return
    
    # Test 2: List datasets in workspace
    print("\n2. Testing dataset access...")
    resp = requests.get(f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets", headers=headers)
    if resp.status_code == 200:
        datasets = resp.json().get("value", [])
        fis_dataset = next((d for d in datasets if "FIS-SEMANTIC-MODEL" in d.get("name", "")), None)
        if fis_dataset:
            print(f"✅ Found FIS dataset: {fis_dataset['id']}")
            dataset_id = fis_dataset['id']
        else:
            print("❌ FIS-SEMANTIC-MODEL dataset not found")
            print(f"Available datasets: {[d.get('name') for d in datasets]}")
            return
    else:
        print(f"❌ Failed to list datasets: {resp.status_code} - {resp.text}")
        return
    
    # Test 3: Try to execute a simple query
    print("\n3. Testing query execution...")
    query_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    payload = {
        "queries": [{"query": "EVALUATE ROW(\"test\", 1)"}],
        "serializerSettings": {"includeNulls": True}
    }
    
    resp = requests.post(query_url, headers=headers, json=payload)
    if resp.status_code == 200:
        print("✅ Query execution successful!")
        print(f"Response: {resp.json()}")
    else:
        print(f"❌ Query execution failed: {resp.status_code} - {resp.text}")
        if resp.status_code == 401:
            print("\n🔧 PERMISSION ISSUE: Service principal needs dataset Build permission")
        elif resp.status_code == 403:
            print("\n🔧 ACCESS ISSUE: Service principal needs workspace access")

if __name__ == "__main__":
    try:
        test_permissions()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
