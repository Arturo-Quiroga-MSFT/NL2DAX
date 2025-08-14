#!/usr/bin/env python3
"""
Fix Capacity Access and Dataset Permissions Check
Focus on resolving 404 capacity access and permission issues
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CapacityAndPermissionsFixer:
    """Fix capacity access and dataset permissions issues"""
    
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
    
    def check_capacity_via_multiple_apis(self, capacity_id):
        """Check capacity using multiple API endpoints"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print(f"🔍 CAPACITY CHECK: {capacity_id}")
        print("-" * 50)
        
        # Method 1: Power BI capacities endpoint
        print("1️⃣ Power BI Capacities API:")
        try:
            response = requests.get(
                f"{self.base_url}/capacities/{capacity_id}",
                headers=headers,
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                capacity = response.json()
                print(f"   ✅ Display name: {capacity.get('displayName', 'Unknown')}")
                print(f"   ✅ Admins: {len(capacity.get('admins', []))}")
                print(f"   ✅ State: {capacity.get('state', 'Unknown')}")
            elif response.status_code == 404:
                print("   ❌ 404 - Capacity not found or no access")
            else:
                print(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Method 2: List all accessible capacities
        print("2️⃣ List All Accessible Capacities:")
        try:
            response = requests.get(
                f"{self.base_url}/capacities",
                headers=headers,
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                capacities = response.json().get('value', [])
                print(f"   ✅ Found {len(capacities)} accessible capacities")
                
                target_found = False
                for cap in capacities:
                    if cap['id'] == capacity_id:
                        target_found = True
                        print(f"   ✅ Target capacity found:")
                        print(f"      Name: {cap.get('displayName', 'Unknown')}")
                        print(f"      State: {cap.get('state', 'Unknown')}")
                        print(f"      SKU: {cap.get('sku', 'Unknown')}")
                        break
                
                if not target_found:
                    print(f"   ❌ Target capacity {capacity_id} not in accessible list")
                    print("   📋 Accessible capacities:")
                    for cap in capacities[:3]:  # Show first 3
                        print(f"      - {cap.get('displayName', 'Unknown')} ({cap['id']})")
            else:
                print(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Method 3: Fabric API (might need different scopes)
        print("3️⃣ Fabric Capacities API:")
        try:
            # Try with current token first
            fabric_url = f"https://api.fabric.microsoft.com/v1/capacities/{capacity_id}"
            response = requests.get(fabric_url, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                capacity = response.json()
                print(f"   ✅ Display name: {capacity.get('displayName', 'Unknown')}")
                print(f"   ✅ State: {capacity.get('state', 'Unknown')}")
                print(f"   ✅ SKU: {capacity.get('sku', 'Unknown')}")
                print(f"   ✅ Region: {capacity.get('region', 'Unknown')}")
            elif response.status_code == 401:
                print("   ❌ 401 - May need different token scope for Fabric API")
            elif response.status_code == 404:
                print("   ❌ 404 - Capacity not found in Fabric API")
            else:
                print(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
    
    def check_dataset_detailed_permissions(self):
        """Check detailed dataset permissions and access patterns"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔐 DETAILED DATASET PERMISSIONS CHECK")
        print("-" * 50)
        
        # Check dataset users/permissions
        print("1️⃣ Dataset Users:")
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/users",
                headers=headers,
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json().get('value', [])
                print(f"   ✅ Found {len(users)} users/permissions")
                for user in users:
                    print(f"      - {user.get('emailAddress', 'Unknown')} ({user.get('datasetUserAccessRight', 'Unknown')})")
            elif response.status_code == 404:
                print("   ❌ 404 - Cannot access dataset users (may be expected)")
            else:
                print(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Check if dataset supports executeQueries
        print("2️⃣ Dataset Capabilities:")
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                dataset = response.json()
                print("   ✅ Dataset properties:")
                print(f"      Name: {dataset.get('name', 'Unknown')}")
                print(f"      Configured by: {dataset.get('configuredBy', 'Unknown')}")
                print(f"      Is refreshable: {dataset.get('isRefreshable', 'Unknown')}")
                print(f"      Is on-premises: {dataset.get('isOnPremGatewayRequired', 'Unknown')}")
                print(f"      Query scale-out: {dataset.get('queryScaleOutSettings', {}).get('autoSyncReadOnlyReplicas', 'Unknown')}")
                print(f"      Datasource type: {dataset.get('datasourceType', 'Unknown')}")
                print(f"      Default mode: {dataset.get('defaultMode', 'Unknown')}")
                
                # Check if it's in Import mode (required for executeQueries)
                default_mode = dataset.get('defaultMode', 'Unknown')
                if default_mode == 'Import':
                    print("   ✅ Dataset is in Import mode (supports executeQueries)")
                elif default_mode == 'DirectQuery':
                    print("   ⚠️  Dataset is in DirectQuery mode (executeQueries may be limited)")
                else:
                    print(f"   ⚠️  Dataset mode '{default_mode}' may not support executeQueries")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Check workspace users/permissions
        print("3️⃣ Workspace Users:")
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/users",
                headers=headers,
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json().get('value', [])
                print(f"   ✅ Found {len(users)} workspace users")
                
                # Look for our service principal
                service_principal_found = False
                for user in users:
                    print(f"      - {user.get('emailAddress', user.get('displayName', 'Unknown'))} ({user.get('groupUserAccessRight', 'Unknown')})")
                    if user.get('identifier') == self.client_id:
                        service_principal_found = True
                        print(f"        🎯 This is our service principal!")
                
                if not service_principal_found:
                    print("   ⚠️  Service principal not found in workspace users")
            else:
                print(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
    
    def test_alternative_query_methods(self):
        """Test alternative ways to execute queries"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("🧪 ALTERNATIVE QUERY METHODS TEST")
        print("-" * 50)
        
        # Method 1: Try without workspace (direct dataset access)
        print("1️⃣ Direct Dataset Access (without workspace):")
        url = f"{self.base_url}/datasets/{self.dataset_id}/executeQueries"
        payload = {
            "queries": [{"query": "EVALUATE { 1 }"}],
            "serializerSettings": {"includeNulls": True}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS with direct dataset access!")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Method 2: Try with different payload structure
        print("2️⃣ Simplified Payload Structure:")
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        simple_payload = {
            "queries": [{"query": "EVALUATE { 1 }"}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=simple_payload, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS with simplified payload!")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Method 3: Try with explicit impersonation (if needed)
        print("3️⃣ With Service Principal Context:")
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        # Add user context header
        headers_with_context = headers.copy()
        headers_with_context["X-PowerBI-User"] = f"app:{self.client_id}"
        
        try:
            response = requests.post(url, headers=headers_with_context, json=payload, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS with service principal context!")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        return False

def main():
    """Main capacity and permissions fixing function"""
    print("🔧 CAPACITY ACCESS & DATASET PERMISSIONS FIXER")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Fix 404 capacity access and dataset permission issues")
    print()
    
    fixer = CapacityAndPermissionsFixer()
    
    if not fixer.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Get workspace to find capacity ID
    headers = {"Authorization": f"Bearer {fixer.token}"}
    try:
        response = requests.get(
            f"{fixer.base_url}/groups/{fixer.workspace_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            workspace = response.json()
            capacity_id = workspace.get('capacityId')
            
            if capacity_id:
                # Check capacity via multiple methods
                fixer.check_capacity_via_multiple_apis(capacity_id)
            else:
                print("❌ No capacity assigned to workspace")
                return 1
        else:
            print(f"❌ Cannot get workspace details: {response.status_code}")
            return 1
            
    except Exception as e:
        print(f"❌ Workspace error: {e}")
        return 1
    
    # Check detailed dataset permissions
    fixer.check_dataset_detailed_permissions()
    
    # Test alternative query methods
    success = fixer.test_alternative_query_methods()
    
    print("📊 SUMMARY & RECOMMENDATIONS")
    print("=" * 40)
    
    if success:
        print("🎉 SUCCESS! Found working query method")
        print("   Update your scripts to use the successful method")
    else:
        print("❌ All query methods failed")
        print("   🔧 Recommendations:")
        print("   1. Verify service principal is added to workspace with appropriate permissions")
        print("   2. Check if dataset is in Import mode (not DirectQuery)")
        print("   3. Ensure capacity is fully active and not paused")
        print("   4. Contact Power BI administrator to verify tenant settings")
        print("   5. Check if 'Service principals can use Power BI APIs' is enabled")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
