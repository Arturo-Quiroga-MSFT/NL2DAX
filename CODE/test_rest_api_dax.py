#!/usr/bin/env python3
"""
Power BI REST API DAX Testbed
Direct testing of executeQueries endpoint without XMLA dependency
This bypasses XMLA endpoint issues and tests pure REST API access
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

class PowerBIRestAPITester:
    """Test Power BI DAX execution via REST API executeQueries endpoint"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID")
        self.token = None
        
    def get_token(self):
        """Get Azure AD token for Power BI API"""
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
                print("✅ Successfully obtained Power BI access token")
                return True
            else:
                print(f"❌ Token acquisition failed: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Token error: {e}")
            return False
    
    def test_basic_connectivity(self):
        """Test basic Power BI API connectivity"""
        print("\n🔍 TESTING BASIC POWER BI API CONNECTIVITY")
        print("=" * 50)
        
        if not self.token:
            print("❌ No token available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Get workspaces
        print("📋 Test 1: List accessible workspaces...")
        url = "https://api.powerbi.com/v1.0/myorg/groups"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            workspaces = response.json().get('value', [])
            print(f"✅ Success: Found {len(workspaces)} workspaces")
            
            # Find target workspace
            target_workspace = next((w for w in workspaces if w.get('id') == self.workspace_id), None)
            if target_workspace:
                print(f"✅ Target workspace found: {target_workspace.get('name')}")
            else:
                print(f"❌ Target workspace not found: {self.workspace_id}")
                return False
        else:
            print(f"❌ Failed to list workspaces: {response.status_code}")
            return False
        
        # Test 2: Get datasets in workspace
        print("\n📊 Test 2: List datasets in target workspace...")
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            datasets = response.json().get('value', [])
            print(f"✅ Success: Found {len(datasets)} datasets")
            
            # Find target dataset
            target_dataset = next((d for d in datasets if d.get('id') == self.dataset_id), None)
            if target_dataset:
                print(f"✅ Target dataset found: {target_dataset.get('name')}")
                print(f"   Web URL: {target_dataset.get('webUrl', 'N/A')}")
            else:
                print(f"❌ Target dataset not found: {self.dataset_id}")
                return False
        else:
            print(f"❌ Failed to list datasets: {response.status_code}")
            return False
        
        return True
    
    def test_dataset_permissions(self):
        """Test dataset-level permissions"""
        print("\n🔐 TESTING DATASET PERMISSIONS")
        print("=" * 40)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Test dataset metadata access
        print("📋 Testing dataset metadata access...")
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            dataset = response.json()
            print(f"✅ Dataset metadata accessible")
            print(f"   Name: {dataset.get('name')}")
            print(f"   Configured By: {dataset.get('configuredBy')}")
            print(f"   Is Refreshable: {dataset.get('isRefreshable')}")
            return True
        else:
            print(f"❌ Dataset metadata failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
    
    def test_simple_dax_queries(self):
        """Test simple DAX queries via executeQueries endpoint"""
        print("\n🧪 TESTING DAX EXECUTEQUERY ENDPOINT")
        print("=" * 50)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Define test queries in order of complexity
        test_queries = [
            {
                "name": "Basic Literal",
                "description": "Simple literal value test",
                "dax": "EVALUATE { 1 }",
                "expected_rows": 1
            },
            {
                "name": "System Info",
                "description": "DAX system information",
                "dax": "EVALUATE { NOW() }",
                "expected_rows": 1
            },
            {
                "name": "Table Count",
                "description": "Count rows in a table",
                "dax": "EVALUATE TOPN(1, SUMMARIZE(ALLSELECTED(), 'FIS-SEMANTIC-MODEL'[Column1], \"Count\", COUNT('FIS-SEMANTIC-MODEL'[Column1])))",
                "expected_rows": 1,
                "may_fail": True
            }
        ]
        
        base_url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        for i, test_query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {test_query['name']}")
            print(f"   Description: {test_query['description']}")
            print(f"   DAX: {test_query['dax']}")
            
            query_payload = {
                "queries": [
                    {
                        "query": test_query['dax']
                    }
                ],
                "serializerSettings": {
                    "includeNulls": True
                }
            }
            
            start_time = time.time()
            response = requests.post(base_url, headers=headers, json=query_payload, timeout=60)
            elapsed_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {elapsed_time:.2f}s")
            print(f"   📡 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'results' in result and len(result['results']) > 0:
                        query_result = result['results'][0]
                        if 'tables' in query_result and len(query_result['tables']) > 0:
                            table = query_result['tables'][0]
                            row_count = len(table.get('rows', []))
                            print(f"   ✅ SUCCESS: {row_count} rows returned")
                            
                            # Show sample data
                            if row_count > 0:
                                print(f"   📊 Sample data: {table['rows'][0]}")
                        else:
                            print(f"   ⚠️  No table data in response")
                    else:
                        print(f"   ⚠️  No results in response")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                    
            elif response.status_code == 400:
                print(f"   ❌ BAD REQUEST (400)")
                try:
                    error_detail = response.json()
                    error_code = error_detail.get('error', {}).get('code', 'Unknown')
                    error_message = error_detail.get('error', {}).get('message', 'No message')
                    print(f"   📋 Error Code: {error_code}")
                    print(f"   📋 Error Message: {error_message}")
                    
                    if 'PowerBINotAuthorizedException' in str(error_detail):
                        print(f"   💡 This indicates authorization/permission issues")
                    elif 'DatasetExecuteQueriesNotSupportedException' in str(error_detail):
                        print(f"   💡 Dataset Execute Queries not supported - check tenant settings")
                        
                except:
                    print(f"   📋 Raw response: {response.text[:200]}...")
                    
            elif response.status_code == 401:
                print(f"   ❌ UNAUTHORIZED (401)")
                print(f"   💡 Token may be invalid or insufficient permissions")
                break
                
            elif response.status_code == 403:
                print(f"   ❌ FORBIDDEN (403)")
                print(f"   💡 Service principal lacks dataset permissions")
                break
                
            else:
                print(f"   ❌ UNEXPECTED ERROR ({response.status_code})")
                print(f"   📋 Response: {response.text[:200]}...")
                
                if test_query.get('may_fail'):
                    print(f"   💡 This query was expected to potentially fail")
                else:
                    break
            
            # Small delay between tests
            time.sleep(1)
    
    def test_alternative_endpoints(self):
        """Test alternative Power BI endpoints for data access"""
        print("\n🔄 TESTING ALTERNATIVE ENDPOINTS")
        print("=" * 40)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Dataset refresh history (Premium feature)
        print("📊 Test 1: Dataset refresh history...")
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            refreshes = response.json().get('value', [])
            print(f"   ✅ Refresh history accessible ({len(refreshes)} entries)")
        else:
            print(f"   ❌ Refresh history failed: {response.status_code}")
        
        # Test 2: Dataset parameters
        print("\n📋 Test 2: Dataset parameters...")
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/parameters"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            parameters = response.json().get('value', [])
            print(f"   ✅ Parameters accessible ({len(parameters)} parameters)")
        else:
            print(f"   ❌ Parameters failed: {response.status_code}")
        
        # Test 3: Dataset datasources
        print("\n🔗 Test 3: Dataset datasources...")
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/datasources"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            datasources = response.json().get('value', [])
            print(f"   ✅ Datasources accessible ({len(datasources)} sources)")
            for ds in datasources[:2]:  # Show first 2
                print(f"     - {ds.get('datasourceType', 'Unknown')} source")
        else:
            print(f"   ❌ Datasources failed: {response.status_code}")
    
    def generate_comparison_report(self):
        """Generate a comparison report of findings"""
        print("\n📋 DIAGNOSIS SUMMARY")
        print("=" * 40)
        
        print("🎯 KEY FINDINGS:")
        print("• This testbed bypasses XMLA endpoint completely")
        print("• Uses direct Power BI REST API executeQueries endpoint")
        print("• If DAX works here but not via XMLA, the issue is XMLA-specific")
        print("• If DAX fails here too, the issue is more fundamental")
        print()
        
        print("🔧 COMPARISON WITH XMLA APPROACH:")
        print("• XMLA Endpoint: powerbi://api.powerbi.com/v1.0/myorg/FIS")
        print("• REST Endpoint: https://api.powerbi.com/v1.0/myorg/groups/{workspace}/datasets/{dataset}/executeQueries")
        print("• XMLA requires capacity-level XMLA Endpoint = 'Read Write'")
        print("• REST API requires tenant-level 'Dataset Execute Queries REST API' = Enabled")
        print()
        
        print("📞 NEXT STEPS:")
        print("• If REST API works: Focus on XMLA endpoint configuration")
        print("• If REST API fails: Check service principal permissions and tenant settings")
        print("• If both fail: Verify capacity status and basic authentication")

def main():
    """Main testing flow"""
    print("🚀 POWER BI REST API DAX TESTBED")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📖 Purpose: Test DAX execution via REST API (bypassing XMLA)")
    print("   This helps isolate whether issues are XMLA-specific or general")
    print()
    
    # Initialize tester
    tester = PowerBIRestAPITester()
    
    # Validate configuration
    missing_configs = []
    if not tester.tenant_id:
        missing_configs.append("PBI_TENANT_ID")
    if not tester.client_id:
        missing_configs.append("PBI_CLIENT_ID")
    if not tester.client_secret:
        missing_configs.append("PBI_CLIENT_SECRET")
    if not tester.workspace_id:
        missing_configs.append("POWERBI_WORKSPACE_ID")
    if not tester.dataset_id:
        missing_configs.append("POWERBI_DATASET_ID")
    
    if missing_configs:
        print(f"❌ Missing configuration: {', '.join(missing_configs)}")
        print("   Please check your .env file")
        return
    
    print(f"✅ Configuration validated")
    print(f"   Workspace ID: {tester.workspace_id}")
    print(f"   Dataset ID: {tester.dataset_id}")
    
    # Step 1: Get token
    if not tester.get_token():
        print("❌ Cannot proceed without valid token")
        return
    
    # Step 2: Test basic connectivity
    if not tester.test_basic_connectivity():
        print("❌ Basic connectivity failed - cannot proceed with DAX tests")
        return
    
    # Step 3: Test dataset permissions
    if not tester.test_dataset_permissions():
        print("❌ Dataset permissions failed - DAX queries likely to fail")
    
    # Step 4: Test DAX queries
    tester.test_simple_dax_queries()
    
    # Step 5: Test alternative endpoints
    tester.test_alternative_endpoints()
    
    # Step 6: Generate report
    tester.generate_comparison_report()
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
