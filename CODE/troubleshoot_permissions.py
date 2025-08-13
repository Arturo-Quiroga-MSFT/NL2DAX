#!/usr/bin/env python3
"""
Comprehensive Power BI Service Principal Troubleshooting Script
"""

import os
import requests
import msal
from dotenv import load_dotenv
import json

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

def check_dataset_permissions():
    """Check specific dataset permissions"""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    workspace_id = "e3fdee99-3aa4-4d71-a530-2964a062e326"
    dataset_id = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"
    
    print("🔍 COMPREHENSIVE PERMISSION ANALYSIS")
    print("=" * 50)
    
    # Check dataset users
    print("\n1. CHECKING DATASET USERS...")
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/users"
    resp = requests.get(users_url, headers=headers)
    
    if resp.status_code == 200:
        users = resp.json().get("value", [])
        print(f"✅ Dataset users retrieved ({len(users)} users)")
        
        client_id = os.getenv("PBI_CLIENT_ID")
        sp_user = next((u for u in users if u.get("identifier") == client_id), None)
        
        if sp_user:
            print(f"✅ Service Principal found in dataset users!")
            print(f"   Permission: {sp_user.get('datasetUserAccessRight', 'Unknown')}")
            print(f"   Principal Type: {sp_user.get('principalType', 'Unknown')}")
        else:
            print("❌ Service Principal NOT found in dataset users")
            print("   This is likely the root cause!")
            print(f"   Looking for Client ID: {client_id}")
            print("   Found users:")
            for user in users[:5]:  # Show first 5 users
                print(f"     - {user.get('identifier', 'N/A')} ({user.get('principalType', 'N/A')}) - {user.get('datasetUserAccessRight', 'N/A')}")
    else:
        print(f"❌ Failed to get dataset users: {resp.status_code} - {resp.text}")
    
    # Check workspace users
    print("\n2. CHECKING WORKSPACE USERS...")
    ws_users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    resp = requests.get(ws_users_url, headers=headers)
    
    if resp.status_code == 200:
        ws_users = resp.json().get("value", [])
        print(f"✅ Workspace users retrieved ({len(ws_users)} users)")
        
        client_id = os.getenv("PBI_CLIENT_ID")
        sp_ws_user = next((u for u in ws_users if u.get("identifier") == client_id), None)
        
        if sp_ws_user:
            print(f"✅ Service Principal found in workspace users!")
            print(f"   Permission: {sp_ws_user.get('groupUserAccessRight', 'Unknown')}")
            print(f"   Principal Type: {sp_ws_user.get('principalType', 'Unknown')}")
        else:
            print("❌ Service Principal NOT found in workspace users")
    else:
        print(f"❌ Failed to get workspace users: {resp.status_code} - {resp.text}")
    
    # Test XMLA connectivity
    print("\n3. TESTING XMLA READ/WRITE SETTINGS...")
    
    # Try to get dataset metadata (requires Read permission)
    metadata_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    resp = requests.get(metadata_url, headers=headers)
    
    if resp.status_code == 200:
        dataset_info = resp.json()
        print("✅ Dataset metadata accessible")
        print(f"   Dataset Name: {dataset_info.get('name', 'N/A')}")
        print(f"   Is Refreshable: {dataset_info.get('isRefreshable', 'N/A')}")
        
        # Check if XMLA endpoint is available
        if 'webUrl' in dataset_info:
            print(f"   Web URL: {dataset_info['webUrl']}")
    else:
        print(f"❌ Cannot access dataset metadata: {resp.status_code}")
    
    print("\n4. RECOMMENDATIONS:")
    print("=" * 30)
    print("Based on the 401 error, you need to:")
    print()
    print("🔧 OPTION 1: Add Service Principal to Dataset (Recommended)")
    print("   1. Go to Power BI Service > Your Dataset > Security")
    print("   2. Add your Service Principal with 'Build' permission")
    print("   3. Use the Client ID as the identifier")
    print()
    print("🔧 OPTION 2: Use PowerShell to grant permissions")
    print("   Install-Module -Name MicrosoftPowerBIMgmt")
    print("   Connect-PowerBIServiceAccount")
    print(f"   Add-PowerBIDatasetUser -DatasetId '{dataset_id}' -UserEmailAddress '{client_id}' -AccessRight 'ReadWrite'")
    print()
    print("🔧 OPTION 3: Check Tenant Settings")
    print("   1. Power BI Admin Portal > Tenant Settings")
    print("   2. Enable 'Service principals can use Power BI APIs'")
    print("   3. Enable 'Service principals can access read-only admin APIs'")
    print("   4. Enable 'Enhance admin APIs responses with detailed metadata'")
    print()
    print("🔧 OPTION 4: Verify API Permissions in Azure AD")
    print("   Required API permissions:")
    print("   - Power BI Service: Dataset.ReadWrite.All (Application)")
    print("   - Power BI Service: Tenant.Read.All (Application)")
    print("   - Make sure permissions are GRANTED by admin")

if __name__ == "__main__":
    try:
        check_dataset_permissions()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
