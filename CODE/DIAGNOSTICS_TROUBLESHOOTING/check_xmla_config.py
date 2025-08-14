#!/usr/bin/env python3
"""
Check and help enable XMLA endpoint settings for Power BI workspace
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

def check_workspace_settings():
    """Check workspace-level settings that affect XMLA access"""
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Checking workspace settings...")
    
    # Get workspace details with more information
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        workspace = response.json()
        print(f"✅ Workspace Name: {workspace.get('name')}")
        print(f"✅ Workspace ID: {workspace.get('id')}")
        print(f"✅ On Dedicated Capacity: {workspace.get('isOnDedicatedCapacity')}")
        print(f"✅ Capacity ID: {workspace.get('capacityId')}")
        print(f"✅ Type: {workspace.get('type')}")
        
        # Check if on Premium capacity (required for XMLA)
        if not workspace.get('isOnDedicatedCapacity'):
            print("⚠️  WARNING: Workspace is not on dedicated capacity. XMLA endpoints require Premium or Premium Per User.")
            return False
        else:
            print("✅ Workspace is on dedicated capacity (Premium) - XMLA endpoints are supported")
            return True
    else:
        print(f"❌ Failed to get workspace details: {response.text}")
        return False

def check_dataset_xmla_status():
    """Check if the dataset supports XMLA queries"""
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🔍 Checking dataset XMLA capabilities...")
    
    # Get detailed dataset information
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        dataset = response.json()
        print(f"✅ Dataset Name: {dataset.get('name')}")
        print(f"✅ Dataset ID: {dataset.get('id')}")
        print(f"✅ Configured By: {dataset.get('configuredBy')}")
        print(f"✅ Is Refreshable: {dataset.get('isRefreshable')}")
        print(f"✅ Target Storage Mode: {dataset.get('targetStorageMode')}")
        
        # Check XMLA endpoint status
        xmla_enabled = dataset.get('isXmlaEndpointEnabled')
        if xmla_enabled is not None:
            if xmla_enabled:
                print("✅ XMLA Endpoint: ENABLED")
                return True
            else:
                print("❌ XMLA Endpoint: DISABLED")
                print("   This is likely the root cause of the 401 error!")
                return False
        else:
            print("⚠️  XMLA Endpoint Status: UNKNOWN (not returned by API)")
            print("   This field might not be available for all dataset types")
            return None
    else:
        print(f"❌ Failed to get dataset details: {response.text}")
        return False

def test_alternative_approach():
    """Test if we can use the REST API instead of XMLA"""
    print("\n🔍 Testing alternative approach: Power BI REST API query...")
    
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try a different API endpoint that might work
    try:
        # First, try to get dataset schema/tables
        schema_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"
        schema_response = requests.get(schema_url, headers=headers, timeout=30)
        
        print(f"   Dataset Datasources API: {schema_response.status_code}")
        if schema_response.status_code == 200:
            datasources = schema_response.json()
            print(f"   ✅ Found {len(datasources.get('value', []))} datasources")
            
        # Try to get refresh history (another way to verify access)
        refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        refresh_response = requests.get(refresh_url, headers=headers, timeout=30)
        
        print(f"   Dataset Refresh History API: {refresh_response.status_code}")
        if refresh_response.status_code == 200:
            refreshes = refresh_response.json()
            print(f"   ✅ Found {len(refreshes.get('value', []))} refresh records")
            
    except Exception as e:
        print(f"   💥 Exception during alternative tests: {str(e)}")

def provide_solutions():
    """Provide step-by-step solutions to enable XMLA access"""
    print("\n🔧 SOLUTIONS TO ENABLE XMLA ACCESS:")
    print("=" * 60)
    
    print("\n1️⃣  POWER BI ADMIN PORTAL SETTINGS:")
    print("   • Go to Power BI Admin Portal (admin.powerbi.com)")
    print("   • Navigate to 'Tenant settings'")
    print("   • Find 'XMLA endpoint and Analyze in Excel with on-premises datasets'")
    print("   • Ensure it's ENABLED for your organization or specific security groups")
    
    print("\n2️⃣  WORKSPACE SETTINGS:")
    print("   • Open the workspace in Power BI Service")
    print("   • Go to Workspace Settings")
    print("   • Under 'Premium' tab, ensure XMLA endpoint is set to 'Read' or 'Read Write'")
    
    print("\n3️⃣  DATASET SETTINGS:")
    print("   • Open the dataset in Power BI Service")
    print("   • Go to Dataset Settings")
    print("   • Look for XMLA endpoint settings and enable read access")
    
    print("\n4️⃣  ALTERNATIVE: USE DIFFERENT API ENDPOINT:")
    print("   • Instead of executeQueries, try using:")
    print("   • POST /datasets/{id}/daxQueries (if available)")
    print("   • Or implement custom solution using dataset export APIs")
    
    print("\n5️⃣  VERIFY PREMIUM CAPACITY:")
    print("   • Ensure workspace is assigned to Premium capacity")
    print("   • XMLA endpoints only work with Premium workspaces")

if __name__ == "__main__":
    print("🚀 Power BI XMLA Configuration Checker")
    print("=" * 60)
    
    try:
        # Check workspace settings
        workspace_ok = check_workspace_settings()
        
        # Check dataset XMLA status
        dataset_xmla_ok = check_dataset_xmla_status()
        
        # Test alternative approaches
        test_alternative_approach()
        
        # Provide solutions
        provide_solutions()
        
        print("\n" + "=" * 60)
        print("📊 DIAGNOSIS SUMMARY")
        print("=" * 60)
        
        if workspace_ok and dataset_xmla_ok:
            print("✅ Configuration looks good - the issue might be elsewhere")
        elif not workspace_ok:
            print("❌ Workspace is not on Premium capacity - XMLA not supported")
        elif dataset_xmla_ok is False:
            print("❌ XMLA endpoint is disabled for the dataset")
        else:
            print("⚠️  Unable to determine XMLA configuration status")
            
        print("\n🎯 NEXT STEPS:")
        print("   1. Check the solutions above")
        print("   2. Contact your Power BI administrator")
        print("   3. Consider using alternative APIs if XMLA cannot be enabled")
            
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
