#!/usr/bin/env python3
"""
Power BI DAX Execution Prerequisites Check
Comprehensive troubleshooting for DatasetExecuteQueriesError 400 status
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class PowerBIPrerequisitesChecker:
    """Comprehensive checker for Power BI API prerequisites"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.token = None
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
    def get_token(self):
        """Get Azure AD token with detailed validation"""
        print("🔐 AUTHENTICATION CHECK")
        print("-" * 50)
        
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
                print("✅ Token acquired successfully")
                print(f"   Token type: Bearer")
                print(f"   Expires in: {result.get('expires_in', 'Unknown')} seconds")
                print(f"   Token length: {len(self.token)} characters")
                print()
                return True
            else:
                print("❌ Token acquisition failed")
                print(f"   Error: {result.get('error', 'Unknown')}")
                print(f"   Description: {result.get('error_description', 'No description')}")
                print()
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            print()
            return False
    
    def check_workspace_access(self):
        """Check workspace accessibility"""
        print("🏢 WORKSPACE ACCESS CHECK")
        print("-" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # List all workspaces
            response = requests.get(f"{self.base_url}/groups", headers=headers, timeout=30)
            
            if response.status_code == 200:
                workspaces = response.json().get('value', [])
                print(f"✅ Can access {len(workspaces)} workspaces")
                
                # Find our specific workspace
                target_workspace = None
                for ws in workspaces:
                    if ws['id'] == self.workspace_id:
                        target_workspace = ws
                        break
                
                if target_workspace:
                    print(f"✅ Target workspace found")
                    print(f"   Name: {target_workspace.get('name', 'Unknown')}")
                    print(f"   ID: {target_workspace['id']}")
                    print(f"   Type: {target_workspace.get('type', 'Unknown')}")
                    print(f"   State: {target_workspace.get('state', 'Unknown')}")
                    print()
                    return True
                else:
                    print(f"❌ Target workspace not found")
                    print(f"   Looking for: {self.workspace_id}")
                    print(f"   Available workspaces:")
                    for ws in workspaces[:5]:  # Show first 5
                        print(f"     - {ws.get('name', 'Unknown')} ({ws['id']})")
                    print()
                    return False
            else:
                print(f"❌ Cannot list workspaces")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                print()
                return False
                
        except Exception as e:
            print(f"❌ Workspace check error: {e}")
            print()
            return False
    
    def check_dataset_access(self):
        """Check dataset accessibility and properties"""
        print("📊 DATASET ACCESS CHECK")
        print("-" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Check dataset in workspace
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                dataset = response.json()
                print("✅ Dataset accessible")
                print(f"   Name: {dataset.get('name', 'Unknown')}")
                print(f"   ID: {dataset['id']}")
                print(f"   Configured By: {dataset.get('configuredBy', 'Unknown')}")
                print(f"   Is Refreshable: {dataset.get('isRefreshable', 'Unknown')}")
                print(f"   Is On-premises: {dataset.get('isOnPremGatewayRequired', 'Unknown')}")
                print(f"   Query Scale-out: {dataset.get('queryScaleOutSettings', {}).get('autoSyncReadOnlyReplicas', 'Unknown')}")
                print()
                return True
            else:
                print(f"❌ Cannot access dataset")
                print(f"   Status: {response.status_code}")
                if response.status_code == 404:
                    print("   Likely causes:")
                    print("     - Dataset doesn't exist in this workspace")
                    print("     - Incorrect dataset ID")
                    print("     - No permission to view dataset")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                print()
                return False
                
        except Exception as e:
            print(f"❌ Dataset check error: {e}")
            print()
            return False
    
    def check_dataset_permissions(self):
        """Check dataset permissions and capacity"""
        print("🔒 DATASET PERMISSIONS & CAPACITY CHECK")
        print("-" * 50)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Get dataset refresh history to check permissions
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                print(f"✅ Can access refresh history ({len(refreshes)} entries)")
                if refreshes:
                    latest = refreshes[0]
                    print(f"   Latest refresh: {latest.get('endTime', 'Unknown')}")
                    print(f"   Status: {latest.get('status', 'Unknown')}")
            else:
                print(f"⚠️  Cannot access refresh history (Status: {response.status_code})")
            
            # Check workspace capacity
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                workspace = response.json()
                capacity_id = workspace.get('capacityId')
                if capacity_id:
                    print(f"✅ Workspace has capacity assigned")
                    print(f"   Capacity ID: {capacity_id}")
                    
                    # Check capacity details
                    cap_response = requests.get(
                        f"{self.base_url}/capacities/{capacity_id}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if cap_response.status_code == 200:
                        capacity = cap_response.json()
                        print(f"   Capacity admins: {len(capacity.get('admins', []))}")
                        print(f"   Display name: {capacity.get('displayName', 'Unknown')}")
                    else:
                        print(f"   Cannot access capacity details (Status: {cap_response.status_code})")
                else:
                    print("⚠️  Workspace has no capacity assigned")
                    print("   This may cause DatasetExecuteQueriesError")
            
            print()
            return True
            
        except Exception as e:
            print(f"❌ Permissions check error: {e}")
            print()
            return False
    
    def test_minimal_query(self):
        """Test the simplest possible DAX query"""
        print("🧪 MINIMAL DAX QUERY TEST")
        print("-" * 50)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Test increasingly complex queries
        test_queries = [
            ("Empty Evaluation", "EVALUATE { 1 }"),
            ("Row Constructor", "EVALUATE ROW(\"Value\", 1)"),
            ("Calendar Function", "EVALUATE CALENDAR(DATE(2023,1,1), DATE(2023,1,2))"),
        ]
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        for test_name, query in test_queries:
            print(f"Testing: {test_name}")
            print(f"Query: {query}")
            
            payload = {
                "queries": [{"query": query}],
                "serializerSettings": {"includeNulls": True}
            }
            
            try:
                start_time = time.time()
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                elapsed = time.time() - start_time
                
                print(f"   Status: {response.status_code}")
                print(f"   Time: {elapsed:.2f}s")
                
                if response.status_code == 200:
                    print("   Result: ✅ SUCCESS")
                    try:
                        data = response.json()
                        tables = data.get('results', [{}])[0].get('tables', [])
                        if tables:
                            rows = tables[0].get('rows', [])
                            print(f"   Rows returned: {len(rows)}")
                    except:
                        pass
                else:
                    print("   Result: ❌ FAILED")
                    try:
                        error_data = response.json()
                        error_code = error_data.get('error', {}).get('code', 'Unknown')
                        error_msg = error_data.get('error', {}).get('message', 'No message')
                        print(f"   Error code: {error_code}")
                        print(f"   Error message: {error_msg[:100]}...")
                        
                        # Check for specific error patterns
                        if "capacity" in error_msg.lower():
                            print("   🔍 CAPACITY ISSUE DETECTED")
                        elif "permission" in error_msg.lower():
                            print("   🔍 PERMISSION ISSUE DETECTED")
                        elif "authentication" in error_msg.lower():
                            print("   🔍 AUTHENTICATION ISSUE DETECTED")
                        
                    except:
                        print(f"   Raw error: {response.text[:200]}")
                
                print()
                
                # If first query succeeds, we're good
                if response.status_code == 200:
                    return True
                    
            except Exception as e:
                print(f"   Exception: {e}")
                print()
        
        return False

def main():
    """Main prerequisites checking function"""
    print("🔍 POWER BI DAX EXECUTION PREREQUISITES CHECK")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Diagnose DatasetExecuteQueriesError 400 status")
    print("   Check all prerequisites for DAX query execution")
    print()
    
    checker = PowerBIPrerequisitesChecker()
    
    # Configuration check
    print("⚙️  CONFIGURATION CHECK")
    print("-" * 50)
    print(f"Tenant ID: {checker.tenant_id[:8]}..." if checker.tenant_id else "❌ Not set")
    print(f"Client ID: {checker.client_id[:8]}..." if checker.client_id else "❌ Not set")
    print(f"Client Secret: {'✅ Set' if checker.client_secret else '❌ Not set'}")
    print(f"Workspace ID: {checker.workspace_id}")
    print(f"Dataset ID: {checker.dataset_id}")
    print()
    
    if not all([checker.tenant_id, checker.client_id, checker.client_secret, checker.workspace_id, checker.dataset_id]):
        print("❌ Missing required configuration. Cannot proceed.")
        return 1
    
    # Run all checks
    checks = [
        ("Authentication", checker.get_token),
        ("Workspace Access", checker.check_workspace_access),
        ("Dataset Access", checker.check_dataset_access),
        ("Permissions & Capacity", checker.check_dataset_permissions),
        ("DAX Query Execution", checker.test_minimal_query),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        if check_name == "Authentication" or results.get("Authentication", False):
            results[check_name] = check_func()
        else:
            print(f"⏭️  Skipping {check_name} (Authentication failed)")
            results[check_name] = False
    
    # Summary
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("   DAX queries should work correctly")
    else:
        print("🔧 ISSUES FOUND - RECOMMENDATIONS:")
        print("-" * 40)
        
        if not results.get("Authentication"):
            print("• Fix service principal authentication")
            print("  - Verify tenant ID, client ID, and secret")
            print("  - Check Azure AD app registration")
            
        if not results.get("Workspace Access"):
            print("• Fix workspace access")
            print("  - Verify workspace ID")
            print("  - Add service principal to workspace")
            
        if not results.get("Dataset Access"):
            print("• Fix dataset access")
            print("  - Verify dataset ID")
            print("  - Check dataset permissions")
            
        if not results.get("Permissions & Capacity"):
            print("• Fix capacity issues")
            print("  - Check if workspace has assigned capacity")
            print("  - Verify capacity is not paused")
            print("  - Contact Power BI administrator")
            
        if not results.get("DAX Query Execution"):
            print("• DAX execution failing")
            print("  - Review error messages above")
            print("  - Most likely capacity or permission issue")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
