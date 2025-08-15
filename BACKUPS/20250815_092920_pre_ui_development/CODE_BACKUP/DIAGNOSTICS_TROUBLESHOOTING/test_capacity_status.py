#!/usr/bin/env python3
"""
Check Fabric Capacity Status After Resume
Wait for capacity to be fully active
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CapacityStatusChecker:
    """Check capacity status and wait for it to be ready"""
    
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
    
    def get_workspace_capacity(self):
        """Get workspace capacity ID"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                workspace = response.json()
                return workspace.get('capacityId')
            else:
                print(f"❌ Cannot get workspace: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Workspace error: {e}")
            return None
    
    def check_capacity_status_via_fabric(self, capacity_id):
        """Check capacity status using Fabric APIs"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Try Fabric capacity management API
        fabric_url = f"https://api.fabric.microsoft.com/v1/capacities/{capacity_id}"
        
        try:
            response = requests.get(fabric_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                capacity = response.json()
                return {
                    "accessible": True,
                    "state": capacity.get('state', 'Unknown'),
                    "sku": capacity.get('sku', 'Unknown'),
                    "region": capacity.get('region', 'Unknown'),
                    "source": "Fabric API"
                }
            else:
                return {
                    "accessible": False,
                    "error": f"HTTP {response.status_code}",
                    "source": "Fabric API"
                }
                
        except Exception as e:
            return {
                "accessible": False,
                "error": str(e),
                "source": "Fabric API"
            }
    
    def test_simple_query_with_retry(self):
        """Test simple query with retry logic"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        payload = {
            "queries": [{"query": "EVALUATE { 1 }"}],
            "serializerSettings": {"includeNulls": True}
        }
        
        print("🔄 Testing DAX query with retry logic...")
        
        for attempt in range(1, 6):  # 5 attempts
            print(f"   Attempt {attempt}/5...", end="")
            
            try:
                start_time = time.time()
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                elapsed = time.time() - start_time
                
                print(f" {response.status_code} ({elapsed:.2f}s)")
                
                if response.status_code == 200:
                    print("   ✅ SUCCESS! DAX query executed successfully")
                    try:
                        data = response.json()
                        tables = data.get('results', [{}])[0].get('tables', [])
                        if tables and tables[0].get('rows'):
                            print(f"   📊 Result: {tables[0]['rows'][0]}")
                    except:
                        pass
                    return True
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_code = error_data.get('error', {}).get('code', 'Unknown')
                        error_message = error_data.get('error', {}).get('message', 'No message')
                        print(f"   ❌ Error: {error_code}")
                        if error_message and error_message != 'No message':
                            print(f"      Message: {error_message}")
                    except:
                        print(f"   ❌ Raw error: {response.text[:100]}")
                else:
                    print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                
                if attempt < 5:
                    wait_time = attempt * 10  # Progressive wait
                    print(f"   ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                if attempt < 5:
                    time.sleep(10)
        
        return False

def main():
    """Main capacity status checking function"""
    print("🏗️  FABRIC CAPACITY STATUS CHECK")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Verify capacity is ready after resume")
    print()
    
    checker = CapacityStatusChecker()
    
    if not checker.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    
    # Get capacity ID
    capacity_id = checker.get_workspace_capacity()
    if not capacity_id:
        print("❌ Cannot get capacity ID")
        return 1
    
    print(f"📊 Workspace capacity ID: {capacity_id}")
    print()
    
    # Check capacity status via Fabric
    print("🔍 CAPACITY STATUS CHECK")
    print("-" * 40)
    
    fabric_status = checker.check_capacity_status_via_fabric(capacity_id)
    print(f"Fabric API Status: {fabric_status}")
    print()
    
    # Test DAX execution with retry
    print("🧪 DAX EXECUTION TEST WITH RETRY")
    print("-" * 40)
    
    success = checker.test_simple_query_with_retry()
    
    print()
    print("📊 FINAL RESULT")
    print("-" * 20)
    
    if success:
        print("🎉 SUCCESS! Capacity is ready and DAX queries work")
        print("   You can now proceed with your DAX operations")
    else:
        print("❌ FAILED: DAX queries still not working")
        print("   Possible causes:")
        print("   • Capacity still spinning up (try again in a few minutes)")
        print("   • Dataset configuration issue")
        print("   • Power BI tenant settings")
        print("   • Service principal permissions")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
