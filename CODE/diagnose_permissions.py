#!/usr/bin/env python3
"""
Comprehensive diagnostic script to check Power BI service principal permissions
"""

import os
import requests
import msal
from dotenv import load_dotenv
import json

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

def test_api_access():
    """Test various Power BI API endpoints to diagnose permissions"""
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    tests = [
        {
            "name": "List Workspaces",
            "url": "https://api.powerbi.com/v1.0/myorg/groups",
            "method": "GET"
        },
        {
            "name": "Get Workspace Details",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}",
            "method": "GET"
        },
        {
            "name": "List Datasets in Workspace",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets",
            "method": "GET"
        },
        {
            "name": "Get Dataset Details",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}",
            "method": "GET"
        },
        {
            "name": "Get Dataset Parameters",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/parameters",
            "method": "GET"
        },
        {
            "name": "Get Dataset Users (Permissions)",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/users",
            "method": "GET"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            if test['method'] == 'GET':
                response = requests.get(test['url'], headers=headers, timeout=30)
            else:
                response = requests.post(test['url'], headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if test['name'] == "List Workspaces":
                    workspaces = data.get('value', [])
                    print(f"   ✅ Found {len(workspaces)} workspaces")
                    for ws in workspaces:
                        print(f"      - {ws.get('name')} ({ws.get('id')})")
                elif test['name'] == "List Datasets in Workspace":
                    datasets = data.get('value', [])
                    print(f"   ✅ Found {len(datasets)} datasets")
                    for ds in datasets:
                        print(f"      - {ds.get('name')} ({ds.get('id')})")
                        print(f"        XMLA Read Enabled: {ds.get('isXmlaEndpointEnabled', 'unknown')}")
                        print(f"        Configured By: {ds.get('configuredBy', 'unknown')}")
                elif test['name'] == "Get Dataset Users (Permissions)":
                    users = data.get('value', [])
                    print(f"   ✅ Found {len(users)} users with dataset permissions")
                    for user in users:
                        print(f"      - {user.get('identifier')} ({user.get('principalType')}) - {user.get('datasetUserAccessRight')}")
                else:
                    print(f"   ✅ Success: {str(data)[:200]}...")
                
                results.append({
                    "test": test['name'],
                    "status": "SUCCESS",
                    "status_code": response.status_code,
                    "data": data
                })
            else:
                error_text = response.text
                print(f"   ❌ Failed: {error_text[:200]}...")
                results.append({
                    "test": test['name'],
                    "status": "FAILED",
                    "status_code": response.status_code,
                    "error": error_text
                })
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
            results.append({
                "test": test['name'],
                "status": "EXCEPTION",
                "error": str(e)
            })
    
    return results

def test_simple_dax():
    """Test a simple DAX query execution"""
    print(f"\n🔍 Testing: Simple DAX Query Execution")
    
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Very simple DAX query
    dax_query = {
        "queries": [
            {
                "query": "EVALUATE ROW(\"TestColumn\", 1)"
            }
        ]
    }
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    
    try:
        response = requests.post(url, json=dax_query, headers=headers, timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ DAX query executed successfully!")
            print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
            return True
        else:
            print(f"   ❌ DAX query failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   💥 Exception during DAX execution: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Power BI Service Principal Diagnostic")
    print("=" * 60)
    
    try:
        # Test basic API access
        results = test_api_access()
        
        # Test DAX execution
        dax_success = test_simple_dax()
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        for result in results:
            status_emoji = "✅" if result['status'] == "SUCCESS" else "❌"
            print(f"{status_emoji} {result['test']}: {result['status']}")
        
        dax_emoji = "✅" if dax_success else "❌"
        print(f"{dax_emoji} DAX Query Execution: {'SUCCESS' if dax_success else 'FAILED'}")
        
        print("\n🔧 RECOMMENDATIONS:")
        
        if not dax_success:
            print("❌ DAX execution failed. Possible issues:")
            print("   1. XMLA endpoint access might not be enabled for the dataset")
            print("   2. Service principal might need Build permissions on the dataset")
            print("   3. Workspace might need 'XMLA read' setting enabled")
            print("   4. Service principal might need to be added directly to dataset permissions")
        else:
            print("✅ All tests passed! Your service principal is properly configured.")
            
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
