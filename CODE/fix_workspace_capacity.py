#!/usr/bin/env python3
"""
Fix Workspace Capacity Assignment
Move workspace to accessible capacity
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class WorkspaceCapacityFixer:
    """Fix workspace capacity assignment to use accessible capacity"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.token = None
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
    def get_token(self):
        """Get Azure AD token"""
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            scopes = ["https://analysis.windows.net/powerbi/api/.default"]
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self.token = result["access_token"]
                return True
            else:
                print(f"❌ Token failed: {result.get('error_description', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"❌ Token error: {e}")
            return False
    
    def get_accessible_capacities(self):
        """Get list of accessible capacities"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{self.base_url}/capacities",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                capacities = response.json().get('value', [])
                return capacities
            else:
                print(f"❌ Cannot list capacities: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Capacities error: {e}")
            return []
    
    def assign_workspace_to_capacity(self, capacity_id):
        """Assign workspace to a specific capacity"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {"capacityId": capacity_id}
        
        try:
            response = requests.post(
                f"{self.base_url}/groups/{self.workspace_id}/AssignToCapacity",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            return response.status_code, response.text
            
        except Exception as e:
            return None, str(e)
    
    def test_query_after_capacity_change(self):
        """Test DAX query after capacity change"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        payload = {
            "queries": [{"query": "EVALUATE { 1 }"}],
            "serializerSettings": {"includeNulls": True}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            return response.status_code == 200, response.status_code, response.text[:200]
            
        except Exception as e:
            return False, None, str(e)

def main():
    """Main workspace capacity fixing function"""
    print("🔧 WORKSPACE CAPACITY ASSIGNMENT FIXER")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Move workspace to accessible capacity")
    print()
    
    fixer = WorkspaceCapacityFixer()
    
    if not fixer.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Get accessible capacities
    capacities = fixer.get_accessible_capacities()
    
    if not capacities:
        print("❌ No accessible capacities found")
        return 1
    
    print("📊 ACCESSIBLE CAPACITIES:")
    print("-" * 30)
    for i, cap in enumerate(capacities, 1):
        print(f"{i}. {cap.get('displayName', 'Unknown')}")
        print(f"   ID: {cap['id']}")
        print(f"   State: {cap.get('state', 'Unknown')}")
        print(f"   SKU: {cap.get('sku', 'Unknown')}")
        print()
    
    # Try the first accessible capacity (usually the most suitable)
    target_capacity = capacities[0]
    target_capacity_id = target_capacity['id']
    target_capacity_name = target_capacity.get('displayName', 'Unknown')
    
    print(f"🎯 ATTEMPTING TO ASSIGN WORKSPACE TO:")
    print(f"   Capacity: {target_capacity_name}")
    print(f"   ID: {target_capacity_id}")
    print()
    
    # Assign workspace to capacity
    print("🔄 Assigning workspace to capacity...")
    status_code, response_text = fixer.assign_workspace_to_capacity(target_capacity_id)
    
    if status_code is None:
        print(f"❌ Assignment failed: {response_text}")
        return 1
    elif status_code == 200:
        print("✅ Workspace assigned successfully!")
    elif status_code == 202:
        print("✅ Assignment accepted (processing asynchronously)")
    else:
        print(f"⚠️  Assignment status: {status_code}")
        print(f"   Response: {response_text}")
    
    print()
    
    # Wait a moment for assignment to take effect
    print("⏳ Waiting 10 seconds for assignment to take effect...")
    import time
    time.sleep(10)
    
    # Test DAX query after capacity change
    print("🧪 Testing DAX query after capacity assignment...")
    success, test_status, test_response = fixer.test_query_after_capacity_change()
    
    print(f"   Status: {test_status}")
    
    if success:
        print("   ✅ SUCCESS! DAX query works after capacity assignment")
        return 0
    else:
        print(f"   ❌ Still failing: {test_response}")
        
        # If still failing, try the other capacity
        if len(capacities) > 1:
            print()
            print("🔄 Trying second accessible capacity...")
            
            second_capacity = capacities[1]
            second_capacity_id = second_capacity['id']
            second_capacity_name = second_capacity.get('displayName', 'Unknown')
            
            print(f"   Capacity: {second_capacity_name}")
            print(f"   ID: {second_capacity_id}")
            
            status_code, response_text = fixer.assign_workspace_to_capacity(second_capacity_id)
            
            if status_code in [200, 202]:
                print("✅ Second assignment successful!")
                
                time.sleep(10)
                
                success, test_status, test_response = fixer.test_query_after_capacity_change()
                print(f"   Test status: {test_status}")
                
                if success:
                    print("   ✅ SUCCESS! DAX query works with second capacity")
                    return 0
                else:
                    print(f"   ❌ Still failing: {test_response}")
    
    print()
    print("📊 FINAL RECOMMENDATIONS:")
    print("-" * 30)
    print("• Capacity assignment completed but DAX queries still failing")
    print("• This suggests the issue is not capacity-related")
    print("• Possible causes:")
    print("  - Dataset mode incompatibility")
    print("  - Power BI tenant settings")
    print("  - Service principal permissions at tenant level")
    print("  - Dataset refresh or configuration issues")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 1

if __name__ == "__main__":
    exit(main())
