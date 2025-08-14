#!/usr/bin/env python3
"""
Script to programmatically add Service Principal to dataset users
"""

import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

def add_service_principal_to_dataset():
    """Add the service principal to dataset users with Build permission"""
    
    # Get token with admin context
    tenant_id = os.getenv("PBI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET")
    
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )
    
    # Use admin scope for adding users
    token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
    if not token or "access_token" not in token:
        raise RuntimeError(f"Failed to get admin token: {token}")
    
    headers = {"Authorization": f"Bearer {token['access_token']}", "Content-Type": "application/json"}
    
    workspace_id = "e3fdee99-3aa4-4d71-a530-2964a062e326"
    dataset_id = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"
    
    # Add service principal to dataset users
    add_user_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/users"
    
    payload = {
        "identifier": client_id,
        "principalType": "App",  # For Service Principal
        "datasetUserAccessRight": "ReadWriteReshareExplore"  # Full permissions
    }
    
    print(f"Adding Service Principal {client_id} to dataset users...")
    print(f"URL: {add_user_url}")
    print(f"Payload: {payload}")
    
    resp = requests.post(add_user_url, headers=headers, json=payload)
    
    if resp.status_code in [200, 201]:
        print("✅ SUCCESS! Service Principal added to dataset users")
        print("You should now be able to execute DAX queries")
    else:
        print(f"❌ FAILED: {resp.status_code} - {resp.text}")
        
        if resp.status_code == 403:
            print("\n🔧 SOLUTION: You need Power BI Admin permissions to add users to datasets")
            print("   Ask your Power BI Admin to add the Service Principal manually")
        elif resp.status_code == 400:
            print("\n🔧 SOLUTION: Check if the Service Principal already exists or payload format")

if __name__ == "__main__":
    try:
        add_service_principal_to_dataset()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
