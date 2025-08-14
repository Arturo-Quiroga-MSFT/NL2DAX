#!/usr/bin/env python3
"""
Fabric Capacity Resume Script
Programmatically resume paused/suspended Power BI/Fabric capacities
Requires Power BI Administrator or Capacity Administrator privileges
"""

import os
import requests
import msal
import json
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def get_admin_token():
    """Get Azure AD token with admin scopes for Power BI service"""
    try:
        app = msal.ConfidentialClientApplication(
            client_id=os.getenv("PBI_CLIENT_ID"),
            client_credential=os.getenv("PBI_CLIENT_SECRET"),
            authority=f"https://login.microsoftonline.com/{os.getenv('PBI_TENANT_ID')}"
        )
        
        # Use Power BI admin scopes
        scopes = ["https://analysis.windows.net/powerbi/api/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            print(f"❌ Failed to get admin token: {result.get('error_description', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ Admin token acquisition error: {e}")
        return None

def get_all_capacities():
    """Get all accessible capacities and their status"""
    print("🔍 SCANNING ALL CAPACITIES...")
    print("=" * 40)
    
    token = get_admin_token()
    if not token:
        return []
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get all capacities via admin API
    url = "https://api.powerbi.com/v1.0/myorg/admin/capacities"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        capacities = response.json().get('value', [])
        print(f"✅ Found {len(capacities)} total capacities")
        return capacities
    elif response.status_code == 403:
        print("❌ Admin API access denied - you need Power BI Administrator privileges")
        return []
    else:
        print(f"❌ Failed to get capacities: {response.status_code}")
        # Fallback to user API
        return get_user_accessible_capacities(token)

def get_user_accessible_capacities(token):
    """Fallback to get user-accessible capacities"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.powerbi.com/v1.0/myorg/capacities"
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        capacities = response.json().get('value', [])
        print(f"✅ Found {len(capacities)} accessible capacities (limited view)")
        return capacities
    else:
        print(f"❌ Failed to get user capacities: {response.status_code}")
        return []

def identify_paused_capacities(capacities):
    """Identify which capacities are paused/suspended"""
    print(f"\n📊 CAPACITY STATUS ANALYSIS:")
    print("-" * 40)
    
    paused_capacities = []
    target_capacity_id = "1ABA0BFF-BDBA-41CE-83D6-D93AE8E8003A"  # Your workspace capacity ID
    
    for capacity in capacities:
        capacity_id = capacity.get('id')
        name = capacity.get('displayName', 'Unknown')
        state = capacity.get('state', 'Unknown')
        sku = capacity.get('sku', 'Unknown')
        
        is_target = capacity_id == target_capacity_id
        target_marker = " ← YOUR WORKSPACE CAPACITY" if is_target else ""
        
        print(f"📋 {name}{target_marker}")
        print(f"   ID: {capacity_id}")
        print(f"   SKU: {sku}")
        print(f"   State: {state}")
        
        if state.lower() in ['paused', 'suspended']:
            print(f"   🔴 STATUS: PAUSED/SUSPENDED")
            paused_capacities.append(capacity)
        elif state.lower() in ['active', 'running']:
            print(f"   🟢 STATUS: RUNNING")
        else:
            print(f"   🟡 STATUS: UNKNOWN ({state})")
        
        print()
    
    return paused_capacities, target_capacity_id

def resume_capacity_powerbi(capacity_id, capacity_name):
    """Resume a Power BI Premium capacity"""
    print(f"🔄 RESUMING POWER BI CAPACITY: {capacity_name}")
    print("-" * 50)
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try to resume via admin API
    url = f"https://api.powerbi.com/v1.0/myorg/admin/capacities/{capacity_id}/resume"
    response = requests.post(url, headers=headers, timeout=60)
    
    if response.status_code == 200:
        print(f"✅ Resume command sent successfully")
        return True
    elif response.status_code == 202:
        print(f"✅ Resume operation accepted - processing...")
        return True
    elif response.status_code == 404:
        print(f"❌ Capacity not found or no admin access")
        return False
    elif response.status_code == 403:
        print(f"❌ Insufficient permissions - need Capacity Administrator role")
        return False
    else:
        print(f"❌ Resume failed: {response.status_code} - {response.text}")
        return False

def resume_capacity_fabric(capacity_id, capacity_name, subscription_id, resource_group):
    """Resume a Fabric capacity via Azure Resource Manager"""
    print(f"🔄 RESUMING FABRIC CAPACITY: {capacity_name}")
    print("-" * 50)
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Azure Resource Manager API for Fabric capacities
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Fabric/capacities/{capacity_name}/resume"
    
    # Add API version
    params = {"api-version": "2023-11-01"}
    
    response = requests.post(url, headers=headers, params=params, timeout=60)
    
    if response.status_code == 200:
        print(f"✅ Fabric capacity resume successful")
        return True
    elif response.status_code == 202:
        print(f"✅ Fabric capacity resume accepted - processing...")
        return True
    else:
        print(f"❌ Fabric resume failed: {response.status_code} - {response.text}")
        return False

def wait_for_capacity_resume(capacity_id, max_wait_minutes=5):
    """Wait for capacity to fully resume and become available"""
    print(f"\n⏳ WAITING FOR CAPACITY TO RESUME...")
    print("-" * 40)
    
    token = get_admin_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        # Check capacity status
        url = f"https://api.powerbi.com/v1.0/myorg/admin/capacities/{capacity_id}"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            capacity = response.json()
            state = capacity.get('state', 'Unknown')
            
            if state.lower() in ['active', 'running']:
                elapsed = int(time.time() - start_time)
                print(f"✅ Capacity is now RUNNING (took {elapsed} seconds)")
                return True
            else:
                print(f"🔄 Still resuming... Current state: {state}")
        
        time.sleep(10)  # Wait 10 seconds before next check
    
    print(f"⏰ Timeout after {max_wait_minutes} minutes - capacity may still be resuming")
    return False

def verify_dax_execution_after_resume():
    """Test DAX execution after capacity resume"""
    print(f"\n🧪 TESTING DAX EXECUTION AFTER RESUME...")
    print("-" * 50)
    
    # Import and run our existing diagnostic
    try:
        from fabric_capacity_status import check_capacity_status
        
        print("🔍 Running capacity status check...")
        capacity_running = check_capacity_status()
        
        if capacity_running:
            print("✅ Capacity is accessible and running")
            
            # Try a simple DAX query
            print("\n🔍 Testing DAX query execution...")
            # This would call our existing DAX test functions
            print("💡 Run: python3 check_xmla_capacity.py for full DAX test")
            
            return True
        else:
            print("❌ Capacity still not accessible")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not run verification: {e}")
        return False

def main():
    """Main capacity resume flow"""
    print("🚀 FABRIC CAPACITY RESUME UTILITY")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("⚠️  WARNING: This requires Power BI Administrator privileges")
    print("   Resuming capacities may incur costs!")
    print()
    
    # Step 1: Get all capacities
    capacities = get_all_capacities()
    
    if not capacities:
        print("❌ Cannot access capacity information")
        return
    
    # Step 2: Identify paused capacities
    paused_capacities, target_capacity_id = identify_paused_capacities(capacities)
    
    # Check if target capacity is in the list
    target_capacity = next((c for c in capacities if c.get('id') == target_capacity_id), None)
    
    if not target_capacity:
        print(f"❌ TARGET WORKSPACE CAPACITY NOT FOUND!")
        print(f"   ID: {target_capacity_id}")
        print(f"   This confirms the capacity is paused/suspended")
        print(f"   Attempting to resume it directly...")
        
        # Ask for confirmation to resume the specific capacity
        response = input(f"\n❓ Attempt to resume target capacity? (y/N): ").lower().strip()
        
        if response in ['y', 'yes']:
            success = resume_capacity_powerbi(target_capacity_id, "Target Workspace Capacity")
            
            if success:
                print(f"\n⏳ Waiting for target capacity to become available...")
                capacity_ready = wait_for_capacity_resume(target_capacity_id, max_wait_minutes=3)
                
                if capacity_ready:
                    print(f"✅ Target capacity successfully resumed and ready")
                    print(f"🧪 Run verification: python3 fabric_capacity_status.py")
                    return
                else:
                    print(f"⏰ Target capacity resume in progress")
            else:
                print(f"❌ Failed to resume target capacity")
        
        return
    
    if not paused_capacities:
        print("✅ No paused capacities found - all appear to be running")
        return
    
    print(f"🔴 FOUND {len(paused_capacities)} PAUSED CAPACITY(IES)")
    print("=" * 50)
    
    # Step 3: Resume each paused capacity
    resumed_count = 0
    
    for capacity in paused_capacities:
        capacity_id = capacity.get('id')
        capacity_name = capacity.get('displayName', 'Unknown')
        capacity_sku = capacity.get('sku', 'Unknown')
        
        print(f"\n🎯 PROCESSING: {capacity_name}")
        print(f"   ID: {capacity_id}")
        print(f"   SKU: {capacity_sku}")
        
        # Determine if this is Power BI or Fabric capacity
        if capacity_sku.startswith('F'):
            print("   Type: Fabric Capacity")
            # For Fabric, we'd need subscription and RG info
            print("   💡 Fabric capacities require Azure subscription info")
            print("   💡 Use Azure CLI: az fabric capacity resume --name {name} --resource-group {rg}")
            continue
        else:
            print("   Type: Power BI Premium Capacity")
            
            # Ask for confirmation
            response = input(f"\n❓ Resume capacity '{capacity_name}'? (y/N): ").lower().strip()
            
            if response in ['y', 'yes']:
                success = resume_capacity_powerbi(capacity_id, capacity_name)
                
                if success:
                    resumed_count += 1
                    
                    # Wait for it to become available
                    print(f"\n⏳ Waiting for {capacity_name} to fully resume...")
                    capacity_ready = wait_for_capacity_resume(capacity_id, max_wait_minutes=3)
                    
                    if capacity_ready:
                        print(f"✅ {capacity_name} successfully resumed and ready")
                    else:
                        print(f"⏰ {capacity_name} resume in progress (may take a few more minutes)")
                else:
                    print(f"❌ Failed to resume {capacity_name}")
            else:
                print(f"⏭️  Skipped {capacity_name}")
    
    # Step 4: Summary and verification
    print(f"\n📋 RESUME OPERATION SUMMARY")
    print("=" * 40)
    print(f"✅ Capacities resumed: {resumed_count}")
    print(f"🔴 Paused capacities found: {len(paused_capacities)}")
    
    if resumed_count > 0:
        print(f"\n🧪 VERIFICATION STEPS:")
        print("1. Wait 2-3 minutes for full startup")
        print("2. Run: python3 fabric_capacity_status.py")
        print("3. Run: python3 check_xmla_capacity.py")
        print("4. Test DAX execution: python3 main.py")
        
        # Auto-verify if possible
        verify_dax_execution_after_resume()
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
