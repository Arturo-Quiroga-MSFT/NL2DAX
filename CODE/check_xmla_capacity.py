#!/usr/bin/env python3
"""
XMLA Endpoint Capacity Settings Checker and Guide
Based on Microsoft documentation - focuses on the critical capacity-level XMLA settings
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

def check_current_workspace_capacity():
    """Check if workspace is properly assigned to Premium capacity"""
    print("🏢 CHECKING WORKSPACE CAPACITY ASSIGNMENT")
    print("=" * 60)
    
    token = get_token()
    if not token:
        return None
    
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get workspace details
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        workspace = response.json()
        print(f"✅ Workspace: {workspace.get('name')}")
        print(f"✅ On Dedicated Capacity: {workspace.get('isOnDedicatedCapacity')}")
        
        capacity_id = workspace.get('capacityId')
        if capacity_id:
            print(f"✅ Capacity ID: {capacity_id}")
            return capacity_id
        else:
            print("❌ No capacity ID - workspace not on Premium/Premium Per User")
            return None
    else:
        print(f"❌ Failed to get workspace details: {response.status_code}")
        return None

def check_fabric_capacity_status(capacity_id):
    """Check if Fabric capacity is running and available"""
    print(f"\n⚡ CHECKING FABRIC CAPACITY STATUS AND AVAILABILITY")
    print("=" * 60)
    
    token = get_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Check accessible capacities and their status
    print("🔍 Step 1: Checking accessible capacities...")
    url = "https://api.powerbi.com/v1.0/myorg/capacities"
    response = requests.get(url, headers=headers, timeout=30)
    
    capacity_found = False
    capacity_status = None
    
    if response.status_code == 200:
        capacities = response.json().get('value', [])
        print(f"✅ Found {len(capacities)} accessible capacities")
        
        for capacity in capacities:
            if capacity.get('id') == capacity_id:
                capacity_found = True
                capacity_status = capacity.get('state', 'Unknown')
                print(f"✅ Target capacity found:")
                print(f"   📊 Name: {capacity.get('displayName')}")
                print(f"   🏷️  SKU: {capacity.get('sku')}")
                print(f"   🟢 State: {capacity_status}")
                print(f"   🌍 Region: {capacity.get('region', 'Unknown')}")
                print(f"   👥 Admins: {len(capacity.get('admins', []))}")
                
                # Check if capacity is active/running
                if capacity_status and capacity_status.lower() in ['active', 'running']:
                    print(f"   ✅ Capacity is ACTIVE and running")
                elif capacity_status and capacity_status.lower() in ['paused', 'suspended']:
                    print(f"   ⚠️  Capacity is PAUSED/SUSPENDED - this will cause DAX failures!")
                    print(f"   💡 Contact capacity admin to resume the capacity")
                    return False
                else:
                    print(f"   ⚠️  Capacity state unclear: {capacity_status}")
                
                break
        
        if not capacity_found:
            print(f"❌ Target capacity {capacity_id} not found in accessible list")
            print(f"   This could indicate:")
            print(f"   • Capacity is paused/suspended")
            print(f"   • Service principal lacks capacity access")
            print(f"   • Capacity has been deleted or moved")
            return False
    else:
        print(f"❌ Failed to list capacities: {response.status_code}")
        return False
    
    # Test 2: Try admin API to get more detailed capacity info
    print(f"\n🔍 Step 2: Checking detailed capacity information...")
    url = f"https://api.powerbi.com/v1.0/myorg/admin/capacities/{capacity_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        capacity = response.json()
        print(f"✅ Detailed capacity info accessible:")
        print(f"   📊 Display Name: {capacity.get('displayName')}")
        print(f"   🟢 State: {capacity.get('state')}")
        print(f"   🌍 Region: {capacity.get('region')}")
        print(f"   💾 Tenant Key Id: {capacity.get('tenantKeyId', 'None')}")
        
        # Check for suspension reasons
        if capacity.get('state', '').lower() in ['paused', 'suspended']:
            print(f"   ⚠️  CAPACITY IS SUSPENDED/PAUSED!")
            print(f"   📋 This explains DAX execution failures")
            print(f"   🔧 Resolution: Contact capacity admin to resume")
            return False
        
        # Check workload configurations
        if 'workloads' in capacity:
            workloads = capacity.get('workloads', {})
            print(f"   📊 Workloads configured: {list(workloads.keys())}")
            
            # Check for Datasets workload (required for DAX)
            if 'Datasets' in workloads:
                datasets_config = workloads['Datasets']
                print(f"   ✅ Datasets workload: {datasets_config}")
            else:
                print(f"   ⚠️  Datasets workload not found - may be disabled")
        
        return True
    elif response.status_code == 404:
        print(f"⚠️  Admin API access not available (need admin privileges)")
        print(f"   This is normal for non-admin service principals")
        
        # If we found the capacity in step 1, that's sufficient
        return capacity_found and (capacity_status and capacity_status.lower() in ['active', 'running'])
    else:
        print(f"❌ Failed to get detailed capacity info: {response.status_code}")
        return capacity_found
    
    # Test 3: Test capacity availability through workspace operations
    print(f"\n🔍 Step 3: Testing capacity availability through workspace operations...")
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    
    # Try to list datasets in the workspace (this should work if capacity is running)
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        datasets = response.json().get('value', [])
        print(f"✅ Workspace operations successful - capacity appears available")
        print(f"   📊 Found {len(datasets)} datasets in workspace")
        return True
    elif response.status_code == 503:
        print(f"❌ Service unavailable (503) - capacity may be overloaded or suspended")
        return False
    elif response.status_code == 429:
        print(f"⚠️  Rate limited (429) - capacity may be under heavy load")
        return True  # Still available, just busy
    else:
        print(f"⚠️  Workspace operations returned {response.status_code}")
        return False

def provide_capacity_availability_guide():
    """Provide guidance for capacity availability issues"""
    print(f"\n🔧 FABRIC CAPACITY AVAILABILITY TROUBLESHOOTING")
    print("=" * 60)
    
    print("🚨 COMMON CAPACITY AVAILABILITY ISSUES:")
    print()
    print("1. 💤 CAPACITY PAUSED/SUSPENDED:")
    print("   • Cause: Cost management, inactivity, or admin action")
    print("   • Symptoms: All DAX queries return 401/503 errors")
    print("   • Fix: Contact capacity admin to resume capacity")
    print("   • Check: Power BI Admin Portal → Capacity Settings")
    print()
    print("2. 🔥 CAPACITY OVERLOADED:")
    print("   • Cause: Too many concurrent operations")
    print("   • Symptoms: 429 rate limiting, slow responses")
    print("   • Fix: Reduce concurrent queries, scale up capacity")
    print("   • Monitor: Capacity metrics app")
    print()
    print("3. 🌍 REGION AVAILABILITY:")
    print("   • Cause: Regional service issues")
    print("   • Symptoms: Intermittent 503 errors")
    print("   • Fix: Check Azure Status page, wait for resolution")
    print("   • Monitor: https://status.powerbi.com")
    print()
    print("4. 🔑 ACCESS PERMISSIONS:")
    print("   • Cause: Service principal not added to capacity admins")
    print("   • Symptoms: Cannot see capacity in API calls")
    print("   • Fix: Add service principal to capacity admin list")
    print("   • Location: Capacity Settings → Admins")
    print()
    
    print("📋 VERIFICATION COMMANDS:")
    print("=" * 30)
    print()
    print("PowerShell (Capacity Admin):")
    print("```powershell")
    print("Connect-PowerBIServiceAccount")
    print("Get-PowerBICapacity | Format-Table DisplayName, State, Region")
    print("```")
    print()
    print("Azure CLI (if using Fabric Capacity):")
    print("```bash")
    print("az account show")
    print("az resource list --resource-type Microsoft.Fabric/capacities")
    print("```")

def provide_xmla_capacity_fix_guide(capacity_id):
    """Provide step-by-step guide to fix XMLA endpoint settings"""
    print(f"\n🔧 XMLA ENDPOINT CONFIGURATION GUIDE")
    print("=" * 60)
    
    print("📋 CRITICAL: Based on Microsoft documentation, the most likely")
    print("   cause of DAX 401 errors is XMLA endpoint not set to 'Read Write'")
    print("   at the capacity level.")
    print()
    
    print("🎯 CAPACITY-LEVEL XMLA SETTINGS TO CHECK:")
    print("=" * 50)
    print()
    print("1. 🏢 FOR PREMIUM CAPACITY:")
    print("   • Go to: https://app.powerbi.com")
    print("   • Settings → Admin portal")
    print("   • Capacity settings → Power BI Premium → [Your Capacity]")
    print("   • Expand 'Power BI Workloads'")
    print("   • Find 'XMLA Endpoint' setting")
    print("   • MUST be set to: 'Read Write' (not just 'Read')")
    print("   • Click 'Apply'")
    print()
    print("2. 🔄 FOR PREMIUM PER USER:")
    print("   • Go to: https://app.powerbi.com")
    print("   • Settings → Admin portal")
    print("   • Premium Per User")
    print("   • Expand 'Semantic model workload settings'")
    print("   • Find 'XMLA Endpoint' setting")
    print("   • MUST be set to: 'Read Write'")
    print("   • Click 'Apply'")
    print()
    print("3. 🟦 FOR FABRIC CAPACITY:")
    print("   • Go to: https://app.powerbi.com")
    print("   • Settings → Admin portal")
    print("   • Capacity settings → Fabric Capacity → [Your Capacity]")
    print("   • Expand 'Power BI Workloads'")
    print("   • Find 'XMLA Endpoint' setting")
    print("   • MUST be set to: 'Read Write'")
    print("   • Click 'Apply'")
    print()
    
    print("🔍 VERIFICATION METHODS:")
    print("=" * 30)
    print()
    print("Method 1 - PowerShell (requires admin access):")
    print("```powershell")
    print("# Connect to Power BI")
    print("Connect-PowerBIServiceAccount")
    print()
    print("# Check capacity settings")
    print(f"Get-PowerBICapacity -Id '{capacity_id}' | Format-List")
    print("```")
    print()
    print("Method 2 - Admin Portal Manual Check:")
    print("• Navigate to the capacity settings as described above")
    print("• Look for current XMLA Endpoint setting value")
    print("• If it shows 'Read' or 'Off', change to 'Read Write'")
    print()
    
    print("⚠️  IMPORTANT NOTES:")
    print("=" * 25)
    print("• Only capacity admins can change these settings")
    print("• Changes may take 5-10 minutes to propagate")
    print("• XMLA endpoint = 'Read Write' is REQUIRED for DAX execution")
    print("• The 'Read' setting only allows metadata access, not query execution")
    print("• These settings apply to ALL workspaces on the capacity")

def test_xmla_specific_issue():
    """Test for specific XMLA endpoint configuration issues"""
    print(f"\n🧪 TESTING XMLA-SPECIFIC CONFIGURATION")
    print("=" * 60)
    
    token = get_token()
    if not token:
        return False
    
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("POWERBI_DATASET_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Try to get XMLA metadata (should work with Read access)
    print("🔍 Test 1: XMLA metadata access...")
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        dataset = response.json()
        print(f"✅ Basic dataset metadata accessible")
        print(f"   Dataset: {dataset.get('name')}")
        print(f"   Web URL: {dataset.get('webUrl')}")
    else:
        print(f"❌ Basic dataset metadata failed: {response.status_code}")
        return False
    
    # Test 2: Try DAX query execution (requires Read Write)
    print("\n🔍 Test 2: DAX query execution (the critical test)...")
    dax_query = {
        "queries": [
            {
                "query": "EVALUATE { 1 }"
            }
        ],
        "serializerSettings": {
            "includeNulls": True
        }
    }
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    response = requests.post(url, headers=headers, json=dax_query, timeout=30)
    
    if response.status_code == 200:
        print(f"✅ DAX query execution successful!")
        print(f"   XMLA endpoint appears to be correctly configured")
        return True
    elif response.status_code == 401:
        print(f"❌ DAX query failed with 401 - XMLA endpoint likely set to 'Read' only")
        print(f"   This confirms the capacity XMLA setting needs to be 'Read Write'")
        return False
    elif response.status_code == 400:
        error_details = response.json().get('error', {})
        error_code = error_details.get('code', 'Unknown')
        print(f"❌ DAX query failed with 400 - Error: {error_code}")
        if 'PowerBINotAuthorizedException' in str(error_details):
            print(f"   This indicates XMLA endpoint permissions issue")
        return False
    else:
        print(f"❌ DAX query failed with {response.status_code}: {response.text}")
        return False

def provide_next_steps():
    """Provide clear next steps based on findings"""
    print(f"\n📋 NEXT STEPS")
    print("=" * 30)
    
    print("🎯 PRIMARY ACTION REQUIRED:")
    print("   1. Contact your Power BI administrator")
    print("   2. Ask them to verify XMLA Endpoint = 'Read Write' for your capacity")
    print("   3. If it's set to 'Read' or 'Off', change it to 'Read Write'")
    print("   4. Wait 5-10 minutes for changes to propagate")
    print("   5. Re-test with: python check_xmla_capacity.py")
    print()
    print("🔄 ALTERNATIVE APPROACHES:")
    print("   • If XMLA can't be enabled, consider using Power BI Embedded")
    print("   • Use paginated reports for tabular data export")
    print("   • Implement solution using Power BI REST API export endpoints")
    print()
    print("📞 ESCALATION:")
    print("   • If admin confirms XMLA = 'Read Write' but DAX still fails")
    print("   • Open Microsoft support ticket with Power BI team")
    print("   • Reference capacity configuration and XMLA endpoint settings")

def main():
    """Main diagnostic and guide flow"""
    print("🚀 XMLA ENDPOINT CAPACITY SETTINGS CHECKER")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📖 Based on Microsoft documentation:")
    print("   - DAX execution requires XMLA Endpoint = 'Read Write' at capacity level")
    print("   - This is the most common cause of DAX 401 errors")
    print("   - Only capacity admins can modify this setting")
    print("   - Capacity must be running and available")
    print()
    
    # Step 1: Check workspace capacity
    capacity_id = check_current_workspace_capacity()
    
    if not capacity_id:
        print("\n❌ Cannot proceed - workspace not on Premium capacity")
        return
    
    # Step 2: Check Fabric capacity status and availability
    capacity_available = check_fabric_capacity_status(capacity_id)
    
    if not capacity_available:
        print(f"\n❌ CAPACITY AVAILABILITY ISSUE DETECTED")
        print(f"   The capacity appears to be paused, suspended, or unavailable")
        print(f"   This explains why DAX queries are failing")
        provide_capacity_availability_guide()
        provide_next_steps()
        return
    
    # Step 3: Test XMLA configuration (only if capacity is available)
    xmla_working = test_xmla_specific_issue()
    
    # Step 4: Provide guidance
    if not xmla_working:
        provide_xmla_capacity_fix_guide(capacity_id)
    else:
        print(f"\n🎉 XMLA endpoint appears to be correctly configured!")
        print(f"   If you're still experiencing issues, they may be related to:")
        print(f"   • Network connectivity")
        print(f"   • Service principal permissions")
        print(f"   • Tenant setting propagation delays")
    
    # Step 5: Next steps
    provide_next_steps()
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def provide_next_steps():
    """Provide clear next steps based on findings"""
    print(f"\n📋 NEXT STEPS")
    print("=" * 30)
    
    print("🎯 PRIMARY ACTION REQUIRED:")
    print("   1. Contact your Power BI administrator")
    print("   2. Ask them to verify:")
    print("      • Capacity is RUNNING (not paused/suspended)")
    print("      • XMLA Endpoint = 'Read Write' for your capacity")
    print("   3. If capacity is paused, ask them to resume it")
    print("   4. If XMLA is set to 'Read' or 'Off', change it to 'Read Write'")
    print("   5. Wait 5-10 minutes for changes to propagate")
    print("   6. Re-test with: python check_xmla_capacity.py")
    print()
    print("🔄 ALTERNATIVE APPROACHES:")
    print("   • If XMLA can't be enabled, consider using Power BI Embedded")
    print("   • Use paginated reports for tabular data export")
    print("   • Implement solution using Power BI REST API export endpoints")
    print()
    print("📞 ESCALATION:")
    print("   • If admin confirms capacity is running AND XMLA = 'Read Write'")
    print("   • But DAX still fails, open Microsoft support ticket")
    print("   • Reference capacity configuration and XMLA endpoint settings")
    print("   • Include capacity ID and error details")

if __name__ == "__main__":
    main()
