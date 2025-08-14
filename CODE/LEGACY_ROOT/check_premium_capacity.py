#!/usr/bin/env python3
"""
Premium Capacity Configuration Checker for Power BI DAX Execution
Comprehensive diagnostic for capacity-level settings that affect XMLA/DAX access
"""

import os
import requests
import msal
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def get_token():
    """Get Azure AD token for Power BI service"""
    try:
        app = msal.ConfidentialClientApplication(
            client_id=os.getenv("PBI_CLIENT_ID"),
            client_credential=os.getenv("PBI_CLIENT_SECRET"),
            authority=f"https://login.microsoftonline.com/{os.getenv('PBI_TENANT_ID')}"
        )
        
        scopes = ["https://analysis.windows.net/powerbi/api/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            print(f"❌ Failed to get token: {result.get('error_description', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ Token acquisition error: {e}")
        return None

def check_workspace_capacity_details():
    """Check detailed workspace and capacity information"""
    print("🏢 CHECKING WORKSPACE CAPACITY CONFIGURATION")
    print("=" * 60)
    
    token = get_token()
    if not token:
        return False
    
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get workspace details
    print("🔍 Fetching workspace details...")
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Failed to get workspace: {response.status_code} - {response.text}")
        return False
    
    workspace = response.json()
    print(f"✅ Workspace Name: {workspace.get('name')}")
    print(f"✅ Workspace ID: {workspace.get('id')}")
    print(f"✅ Workspace Type: {workspace.get('type')}")
    print(f"✅ On Dedicated Capacity: {workspace.get('isOnDedicatedCapacity')}")
    
    capacity_id = workspace.get('capacityId')
    if capacity_id:
        print(f"✅ Capacity ID: {capacity_id}")
        return check_capacity_xmla_settings(token, capacity_id)
    else:
        print("❌ No Capacity ID found - workspace may not be on Premium")
        return False

def check_capacity_xmla_settings(token, capacity_id):
    """Check capacity-specific XMLA settings"""
    print(f"\n🔧 CHECKING CAPACITY XMLA SETTINGS")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try to get capacity workload settings
    print("🔍 Checking capacity workload settings...")
    
    # Method 1: Try admin API for capacity details
    url = f"https://api.powerbi.com/v1.0/myorg/admin/capacities/{capacity_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        capacity = response.json()
        print(f"✅ Capacity Name: {capacity.get('displayName')}")
        print(f"✅ Capacity SKU: {capacity.get('sku')}")
        print(f"✅ Capacity State: {capacity.get('state')}")
        print(f"✅ Capacity Region: {capacity.get('region')}")
        
        # Check for XMLA settings in capacity
        if 'workloads' in capacity:
            workloads = capacity['workloads']
            print(f"\n📊 Available workloads: {list(workloads.keys())}")
            
            # Look for XMLA-related settings
            if 'Datasets' in workloads:
                datasets_config = workloads['Datasets']
                print(f"✅ Datasets workload: {datasets_config}")
            
            if 'XMLA' in workloads:
                xmla_config = workloads['XMLA']
                print(f"✅ XMLA workload: {xmla_config}")
        
        return True
    else:
        print(f"⚠️  Admin API not accessible ({response.status_code}), trying alternative methods...")
        return check_capacity_alternative_methods(token, capacity_id)

def check_capacity_alternative_methods(token, capacity_id):
    """Alternative methods to check capacity settings"""
    print("\n🔄 TRYING ALTERNATIVE CAPACITY CHECKS")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Method 2: Check capacity from user perspective
    print("🔍 Checking accessible capacities...")
    url = "https://api.powerbi.com/v1.0/myorg/capacities"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        capacities = response.json().get('value', [])
        print(f"✅ Found {len(capacities)} accessible capacities")
        
        for capacity in capacities:
            if capacity.get('id') == capacity_id:
                print(f"✅ Target capacity found:")
                print(f"   Name: {capacity.get('displayName')}")
                print(f"   SKU: {capacity.get('sku')}")
                print(f"   State: {capacity.get('state')}")
                return True
        
        print(f"❌ Target capacity {capacity_id} not found in accessible list")
        return False
    else:
        print(f"❌ Failed to list capacities: {response.status_code}")
        return False

def check_xmla_endpoint_direct():
    """Test XMLA endpoint directly"""
    print(f"\n🌐 TESTING XMLA ENDPOINT DIRECTLY")
    print("=" * 50)
    
    xmla_endpoint = os.getenv("PBI_XMLA_ENDPOINT")
    if not xmla_endpoint:
        print("❌ PBI_XMLA_ENDPOINT not configured")
        return False
    
    print(f"🔍 XMLA Endpoint: {xmla_endpoint}")
    
    # Extract workspace from XMLA endpoint
    if "myorg/" in xmla_endpoint:
        workspace_name = xmla_endpoint.split("myorg/")[-1]
        print(f"✅ Workspace from XMLA: {workspace_name}")
    
    # Test if endpoint is reachable (basic connectivity)
    try:
        import socket
        import urllib.parse
        
        parsed = urllib.parse.urlparse(xmla_endpoint.replace("powerbi://", "https://"))
        host = parsed.hostname
        port = 443  # XMLA uses HTTPS port
        
        print(f"🔍 Testing connectivity to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connectivity to XMLA endpoint successful")
            return True
        else:
            print(f"❌ Network connectivity failed to XMLA endpoint")
            return False
            
    except Exception as e:
        print(f"❌ XMLA connectivity test failed: {e}")
        return False

def check_premium_features():
    """Check if Premium features are enabled"""
    print(f"\n💎 CHECKING PREMIUM FEATURE AVAILABILITY")
    print("=" * 50)
    
    token = get_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("POWERBI_DATASET_ID")
    
    # Test 1: Try to access dataset refresh history (Premium feature)
    print("🔍 Testing dataset refresh history access...")
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        refreshes = response.json().get('value', [])
        print(f"✅ Refresh history accessible ({len(refreshes)} entries)")
    else:
        print(f"⚠️  Refresh history not accessible: {response.status_code}")
    
    # Test 2: Try to get dataset parameters (Premium feature)
    print("🔍 Testing dataset parameters access...")
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/parameters"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        parameters = response.json().get('value', [])
        print(f"✅ Dataset parameters accessible ({len(parameters)} parameters)")
    else:
        print(f"⚠️  Dataset parameters not accessible: {response.status_code}")
    
    # Test 3: Try enhanced dataset metadata (Premium feature)
    print("🔍 Testing enhanced dataset metadata...")
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        dataset = response.json()
        print(f"✅ Dataset metadata accessible")
        print(f"   Name: {dataset.get('name')}")
        print(f"   Web URL: {dataset.get('webUrl')}")
        print(f"   Configured By: {dataset.get('configuredBy')}")
        
        if 'queryScaleOutSettings' in dataset:
            print(f"   Scale-out Settings: {dataset['queryScaleOutSettings']}")
        
        return True
    else:
        print(f"❌ Dataset metadata not accessible: {response.status_code}")
        return False

def provide_capacity_recommendations():
    """Provide specific recommendations for capacity configuration"""
    print(f"\n💡 CAPACITY CONFIGURATION RECOMMENDATIONS")
    print("=" * 60)
    
    print("🎯 CRITICAL CAPACITY SETTINGS FOR DAX EXECUTION:")
    print()
    print("1. 🏢 WORKSPACE ASSIGNMENT:")
    print("   • Workspace MUST be assigned to Premium capacity")
    print("   • Premium Per User (PPU) also supports XMLA")
    print("   • Shared capacity does NOT support XMLA endpoints")
    print()
    print("2. 🔧 CAPACITY WORKLOAD SETTINGS:")
    print("   • Go to Power BI Admin Portal")
    print("   • Capacity Settings → Your Premium capacity")
    print("   • Workloads tab → XMLA Endpoint")
    print("   • Set to 'Read Write' (required for DAX execution)")
    print()
    print("3. 📊 DATASET WORKLOAD:")
    print("   • Ensure 'Datasets' workload is enabled")
    print("   • Max memory should be sufficient (usually 70-80%)")
    print("   • Query scale-out can be enabled for better performance")
    print()
    print("4. 🌐 NETWORK CONSIDERATIONS:")
    print("   • XMLA endpoint uses port 443 (HTTPS)")
    print("   • Ensure firewall allows outbound HTTPS to *.powerbi.com")
    print("   • Corporate proxies may interfere with XMLA connections")
    print()
    print("5. ⚡ ALTERNATIVE APPROACHES:")
    print("   • If XMLA is blocked, use REST API executeQueries endpoint")
    print("   • REST API doesn't require XMLA but has same auth requirements")
    print("   • Consider using Power BI Embedded for programmatic access")

def main():
    """Main diagnostic flow"""
    print("🚀 PREMIUM CAPACITY CONFIGURATION CHECKER")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check 1: Workspace and capacity details
    capacity_ok = check_workspace_capacity_details()
    
    # Check 2: XMLA endpoint connectivity
    xmla_ok = check_xmla_endpoint_direct()
    
    # Check 3: Premium features availability
    premium_ok = check_premium_features()
    
    # Provide recommendations
    provide_capacity_recommendations()
    
    # Summary
    print(f"\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 40)
    print(f"✅ Capacity Configuration: {'✅ OK' if capacity_ok else '❌ ISSUES'}")
    print(f"✅ XMLA Connectivity: {'✅ OK' if xmla_ok else '❌ ISSUES'}")
    print(f"✅ Premium Features: {'✅ OK' if premium_ok else '❌ ISSUES'}")
    print()
    
    if all([capacity_ok, xmla_ok, premium_ok]):
        print("🎉 Premium capacity appears to be correctly configured!")
        print("🔍 If DAX queries still fail, the issue is likely in:")
        print("   • Service principal permissions")
        print("   • Tenant settings propagation")
        print("   • Network/firewall configurations")
    else:
        print("⚠️  Premium capacity configuration needs attention.")
        print("🔧 Review the recommendations above and fix identified issues.")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
