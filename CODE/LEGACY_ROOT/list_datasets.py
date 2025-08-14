#!/usr/bin/env python3
"""
List Power BI Datasets in Workspace
Helper script to find available dataset IDs
"""

import os
import requests
import msal
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_token():
    """Get Azure AD token"""
    tenant_id = os.getenv("PBI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET")
    
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}"
    )
    
    scopes = ["https://analysis.windows.net/powerbi/api/.default"]
    result = app.acquire_token_for_client(scopes=scopes)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"❌ Token failed: {result}")
        return None

def list_datasets():
    """List all datasets in the workspace"""
    token = get_token()
    if not token:
        return
        
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            datasets = response.json()
            
            print("📊 AVAILABLE DATASETS IN WORKSPACE")
            print("=" * 50)
            print(f"Workspace ID: {workspace_id}")
            print()
            
            if datasets.get("value"):
                for i, dataset in enumerate(datasets["value"], 1):
                    print(f"{i}. Dataset: {dataset.get('name', 'Unknown')}")
                    print(f"   ID: {dataset.get('id')}")
                    print(f"   Configured By: {dataset.get('configuredBy', 'Unknown')}")
                    print(f"   Is Refreshable: {dataset.get('isRefreshable', False)}")
                    print(f"   Web URL: {dataset.get('webUrl', 'N/A')}")
                    print()
                    
                print("💡 To use a dataset, set POWERBI_DATASET_ID environment variable")
                print("   Example: export POWERBI_DATASET_ID=<dataset_id>")
                
            else:
                print("❌ No datasets found in workspace")
                print("   • Check if service principal has Dataset.Read permissions")
                print("   • Verify workspace contains datasets")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error listing datasets: {e}")

if __name__ == "__main__":
    list_datasets()
