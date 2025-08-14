#!/usr/bin/env python3
"""
Focused Service Principal Permission Test
Tests specific permissions step by step
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

def test_permission_levels():
    """Test different levels of permissions"""
    token = get_token()
    if not token:
        return
        
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔍 SERVICE PRINCIPAL PERMISSION DIAGNOSTIC")
    print("=" * 55)
    print()
    
    tests = [
        {
            "name": "1. List Workspaces (Basic Read)",
            "url": "https://api.powerbi.com/v1.0/myorg/groups",
            "method": "GET",
            "expected": "Should work - basic API access"
        },
        {
            "name": "2. Get Workspace Details",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}",
            "method": "GET", 
            "expected": "Should work - workspace access"
        },
        {
            "name": "3. List Datasets in Workspace",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets",
            "method": "GET",
            "expected": "Should work - dataset read access"
        },
        {
            "name": "4. Get Specific Dataset Info",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}",
            "method": "GET",
            "expected": "Should work - dataset metadata access"
        },
        {
            "name": "5. Execute DAX Query (MAIN TEST)",
            "url": f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries",
            "method": "POST",
            "body": {"queries": [{"query": "EVALUATE { 1 }"}], "serializerSettings": {"includeNulls": True}},
            "expected": "May fail - requires execute permission + capacity access"
        }
    ]
    
    for test in tests:
        print(f"🧪 {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            if test['method'] == 'GET':
                response = requests.get(test['url'], headers=headers, timeout=10)
            else:
                response = requests.post(test['url'], headers=headers, json=test.get('body'), timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: {response.status_code}")
                if 'List' in test['name']:
                    data = response.json()
                    count = len(data.get('value', []))
                    print(f"   📊 Found {count} items")
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                try:
                    error_info = response.json()
                    error_code = error_info.get('error', {}).get('code', 'Unknown')
                    print(f"   🔍 Error: {error_code}")
                except:
                    print(f"   🔍 Error: {response.text[:100]}")
            
            print(f"   💡 Expected: {test['expected']}")
            print()
            
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            print(f"   💡 Expected: {test['expected']}")
            print()
    
    print("📋 INTERPRETATION GUIDE:")
    print("-" * 30)
    print("✅ Tests 1-3 succeed, Test 5 fails → Need execute query permissions")
    print("✅ Tests 1-4 succeed, Test 5 fails → Capacity access issue")  
    print("❌ Test 1 fails → Token/authentication issue")
    print("❌ Test 2 fails → Workspace access issue")
    print("❌ Test 3 fails → Dataset read permission issue")
    print("❌ Test 4 fails → Specific dataset access issue")

if __name__ == "__main__":
    test_permission_levels()
