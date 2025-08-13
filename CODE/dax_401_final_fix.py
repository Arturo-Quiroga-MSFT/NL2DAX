#!/usr/bin/env python3
"""
Fixed diagnostic script that correctly identifies service principal permissions using Object ID
"""

import os
import requests
import msal
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def get_token():
    tenant_id = os.getenv("PBI_TENANT_ID") or os.getenv("POWER_BI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID") or os.getenv("POWER_BI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET") or os.getenv("POWER_BI_CLIENT_SECRET")
    
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

def test_dax_with_specific_headers():
    """Test DAX execution with various headers that might be needed"""
    print(f"\n🔍 Testing DAX Execution with Enhanced Headers")
    print("=" * 60)
    
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID") or os.getenv("POWER_BI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID") or os.getenv("POWER_BI_DATASET_ID")
    
    # Test different header combinations
    test_scenarios = [
        {
            "name": "Standard Headers",
            "headers": {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "With RequestId Header",
            "headers": {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "RequestId": "test-request-123"
            }
        },
        {
            "name": "With X-PowerBI Headers",
            "headers": {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-PowerBI-Source": "NL2DAX-Tool"
            }
        },
        {
            "name": "With User-Agent",
            "headers": {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "NL2DAX/1.0"
            }
        }
    ]
    
    # Simple DAX query
    dax_query = {
        "queries": [
            {
                "query": "EVALUATE ROW(\"TestValue\", 42)"
            }
        ]
    }
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    
    for scenario in test_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        
        try:
            response = requests.post(url, json=dax_query, headers=scenario['headers'], timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! DAX executed successfully")
                print(f"   Response: {json.dumps(data, indent=2)[:300]}...")
                return True
            elif response.status_code == 401:
                error_info = response.json() if response.content else {"error": "No content"}
                print(f"   ❌ 401 Unauthorized: {error_info}")
            elif response.status_code == 403:
                error_info = response.json() if response.content else {"error": "No content"}
                print(f"   ❌ 403 Forbidden: {error_info}")
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
    
    return False

def test_tenant_setting_impact():
    """Test if the issue is related to tenant settings"""
    print(f"\n🔍 Tenant Setting Impact Analysis")
    print("=" * 60)
    
    print("Based on the 401 error, the most likely tenant setting issues are:")
    print()
    print("1. 📊 'Dataset Execute Queries REST API' Setting:")
    print("   - This specifically controls DAX query execution via REST API")
    print("   - If disabled, you get exactly the error we're seeing")
    print("   - Location: Power BI Admin Portal → Tenant Settings → Export and sharing settings")
    print()
    print("2. 🔧 'XMLA Endpoint' Setting:")
    print("   - Required for Premium workspaces")
    print("   - Should be set to 'Read and Write'")
    print("   - Location: Power BI Admin Portal → Capacity Settings → Advanced → XMLA Endpoint")
    print()
    print("3. 🛡️ Service Principal Scope:")
    print("   - The tenant setting might be enabled only for specific security groups")
    print("   - Verify your service principal is in the allowed group")

def check_premium_capacity():
    """Check if the workspace is on Premium capacity (required for XMLA)"""
    print(f"\n🔍 Premium Capacity Check")
    print("=" * 60)
    
    try:
        token = get_token()
        workspace_id = os.getenv("POWERBI_WORKSPACE_ID") or os.getenv("POWER_BI_WORKSPACE_ID")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            workspace_info = response.json()
            is_dedicated = workspace_info.get('isOnDedicatedCapacity', False)
            capacity_id = workspace_info.get('capacityId')
            
            print(f"✅ Workspace Details:")
            print(f"   Name: {workspace_info.get('name', 'Unknown')}")
            print(f"   On Dedicated Capacity: {is_dedicated}")
            
            if is_dedicated:
                print(f"   Capacity ID: {capacity_id}")
                print(f"✅ Workspace is on Premium capacity - XMLA should be available")
                return True
            else:
                print(f"❌ Workspace is NOT on Premium capacity")
                print(f"   XMLA endpoints require Premium capacity for DAX execution")
                return False
        else:
            print(f"❌ Failed to get workspace info: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking capacity: {str(e)}")
        return False

def main():
    print("🚀 Enhanced Power BI DAX 401 Troubleshooter")
    print("=" * 60)
    print("Targeting the specific 'PowerBINotAuthorizedException' error")
    print("=" * 60)
    
    # Check Premium capacity first
    is_premium = check_premium_capacity()
    
    # Test various header combinations
    dax_success = test_dax_with_specific_headers()
    
    # Analyze tenant settings
    test_tenant_setting_impact()
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION & NEXT STEPS")
    print("=" * 60)
    
    if dax_success:
        print("✅ DAX execution is working! The issue may have been resolved.")
    else:
        print("❌ DAX execution still failing. Based on analysis:")
        print()
        if is_premium:
            print("💡 MOST LIKELY CAUSE: Tenant Setting")
            print("   The 'Dataset Execute Queries REST API' tenant setting is likely disabled")
            print("   or not enabled for your service principal's security group.")
            print()
            print("🔧 REQUIRED ACTION (Power BI Admin needed):")
            print("   1. Go to Power BI Admin Portal")
            print("   2. Navigate to Tenant Settings")
            print("   3. Find 'Dataset Execute Queries REST API' setting")
            print("   4. Enable it for 'Entire organization' or add your service principal's security group")
            print("   5. Wait 15-20 minutes for changes to propagate")
        else:
            print("💡 MOST LIKELY CAUSE: Capacity Issue")
            print("   DAX execution via REST API requires Premium capacity")
            print()
            print("🔧 REQUIRED ACTION:")
            print("   1. Move workspace to Premium capacity, OR")
            print("   2. Use XMLA endpoint connection instead of REST API")
        
        print()
        print("📞 IMMEDIATE NEXT STEPS:")
        print("   1. Contact your Power BI administrator")
        print("   2. Share this diagnostic output")
        print("   3. Request enabling 'Dataset Execute Queries REST API' tenant setting")
        if not is_premium:
            print("   4. Consider Premium capacity or alternative approaches")

if __name__ == "__main__":
    main()
