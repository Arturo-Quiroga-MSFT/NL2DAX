#!/usr/bin/env python3
"""
Simple XMLA endpoint checker - run this after admin settings propagate
"""

import os
import requests
import msal
from dotenv import load_dotenv
import time
from datetime import datetime

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

def test_xmla_quick():
    """Quick test of XMLA endpoint"""
    try:
        token = get_token()
        workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        dataset_id = os.getenv("PBI_DATASET_ID")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Simple DAX query
        payload = {
            "queries": [{"query": "EVALUATE ROW(\"Test\", 1)"}]
        }
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! XMLA endpoints are working!")
            result = response.json()
            print(f"📊 DAX query result: {result}")
            return True
        else:
            print(f"❌ Still waiting... Status: {response.status_code}")
            if response.status_code == 401:
                print("   (401 = settings still propagating)")
            return False
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("⏰ XMLA Endpoint Status Checker")
    print("=" * 40)
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("⏳ Waiting for Power BI admin settings to propagate...")
    print("   (This typically takes 5-15 minutes)")
    print("\n🔍 Testing XMLA endpoint status...")
    
    if test_xmla_quick():
        print("\n🎉 Your NL2DAX application is ready to use!")
    else:
        print("\n⏳ Settings are still propagating. You can:")
        print("   • Wait a few more minutes")
        print("   • Run this script again: python xmla_status_check.py")
        print("   • Or run the full diagnostic: python diagnose_permissions.py")
