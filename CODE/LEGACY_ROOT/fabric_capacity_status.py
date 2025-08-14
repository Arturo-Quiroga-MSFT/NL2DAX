#!/usr/bin/env python3
"""
Fabric Capacity Status Checker
Quick utility to check if your Power BI/Fabric capacity is running and available
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

def get_workspace_capacity_id():
    """Get the capacity ID for the configured workspace"""
    token = get_token()
    if not token:
        return None
    
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        workspace = response.json()
        return workspace.get('capacityId')
    return None

def check_capacity_status():
    """Check the status of all accessible capacities"""
    print("⚡ FABRIC CAPACITY STATUS CHECKER")
    print("=" * 50)
    print(f"🕐 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    token = get_token()
    if not token:
        print("❌ Unable to authenticate")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get workspace capacity ID
    workspace_capacity_id = get_workspace_capacity_id()
    
    # List all accessible capacities
    print("📊 CHECKING ALL ACCESSIBLE CAPACITIES:")
    print("-" * 45)
    
    url = "https://api.powerbi.com/v1.0/myorg/capacities"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Failed to get capacities: {response.status_code}")
        return False
    
    capacities = response.json().get('value', [])
    
    if not capacities:
        print("❌ No accessible capacities found")
        return False
    
    target_capacity_found = False
    target_capacity_running = False
    
    for i, capacity in enumerate(capacities, 1):
        capacity_id = capacity.get('id')
        name = capacity.get('displayName', 'Unknown')
        sku = capacity.get('sku', 'Unknown')
        state = capacity.get('state', 'Unknown')
        region = capacity.get('region', 'Unknown')
        
        # Determine status icon and color
        if state.lower() in ['active', 'running']:
            status_icon = "🟢"
            status_text = "RUNNING"
        elif state.lower() in ['paused', 'suspended']:
            status_icon = "🔴"
            status_text = "PAUSED/SUSPENDED"
        else:
            status_icon = "🟡"
            status_text = f"UNKNOWN ({state})"
        
        # Check if this is the target workspace capacity
        is_target = capacity_id == workspace_capacity_id
        target_marker = " ← YOUR WORKSPACE" if is_target else ""
        
        if is_target:
            target_capacity_found = True
            target_capacity_running = state.lower() in ['active', 'running']
        
        print(f"{i}. {status_icon} {name}")
        print(f"   📋 ID: {capacity_id}")
        print(f"   🏷️  SKU: {sku}")
        print(f"   🟢 Status: {status_text}")
        print(f"   🌍 Region: {region}{target_marker}")
        print()
    
    # Summary for target capacity
    print("🎯 TARGET WORKSPACE CAPACITY SUMMARY:")
    print("-" * 40)
    
    if workspace_capacity_id:
        if target_capacity_found:
            if target_capacity_running:
                print("✅ Your workspace capacity is RUNNING")
                print("✅ DAX execution should work (if other settings correct)")
            else:
                print("❌ Your workspace capacity is PAUSED/SUSPENDED")
                print("❌ This will prevent DAX execution")
                print("💡 Contact capacity admin to resume the capacity")
        else:
            print("❌ Your workspace capacity not found in accessible list")
            print("💡 Capacity may be paused or you lack access")
    else:
        print("❌ Unable to determine workspace capacity ID")
        print("💡 Check workspace configuration and permissions")
    
    return target_capacity_running

def provide_capacity_status_actions():
    """Provide next steps based on capacity status"""
    print("\n📋 NEXT ACTIONS:")
    print("-" * 20)
    print("🔧 If capacity is PAUSED/SUSPENDED:")
    print("   1. Contact your Power BI administrator")
    print("   2. Ask them to resume the capacity in Admin Portal")
    print("   3. Wait 2-3 minutes after resuming")
    print("   4. Re-run this checker: python fabric_capacity_status.py")
    print()
    print("📊 If capacity is RUNNING but DAX still fails:")
    print("   1. Run full diagnostic: python check_xmla_capacity.py")
    print("   2. Check XMLA endpoint settings")
    print("   3. Verify service principal permissions")
    print()
    print("📞 Need help?")
    print("   • Power BI Admin Portal: https://app.powerbi.com")
    print("   • Microsoft Support: https://powerbi.microsoft.com/support/")
    print("   • Power BI Status: https://powerbi.microsoft.com/status/")

def main():
    """Main execution flow"""
    try:
        capacity_running = check_capacity_status()
        provide_capacity_status_actions()
        
        # Exit code for automation
        exit_code = 0 if capacity_running else 1
        
        print(f"\n⏰ Check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔄 Exit code: {exit_code} ({'Success' if exit_code == 0 else 'Capacity Issue'})")
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 2

if __name__ == "__main__":
    exit(main())
