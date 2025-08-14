#!/usr/bin/env python3
"""
Fabric Mirrored Database Semantic Model Handler
Handle DAX queries against Fabric mirrored Azure SQL databases
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FabricMirroredDatabaseHandler:
    """Handle Fabric mirrored database semantic models"""
    
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
    
    def check_fabric_semantic_model_status(self):
        """Check the status of the Fabric semantic model"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🏗️ FABRIC SEMANTIC MODEL STATUS")
        print("-" * 40)
        
        try:
            # Get detailed dataset information
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                dataset = response.json()
                
                print("✅ Semantic Model Properties:")
                print(f"   Name: {dataset.get('name', 'Unknown')}")
                print(f"   Storage Mode: {dataset.get('targetStorageMode', 'Unknown')}")
                print(f"   Created: {dataset.get('createdDate', 'Unknown')}")
                print(f"   Configured by: {dataset.get('configuredBy', 'Unknown')}")
                print(f"   Is Refreshable: {dataset.get('isRefreshable', 'Unknown')}")
                print(f"   Add Rows API: {dataset.get('addRowsAPIEnabled', 'Unknown')}")
                print()
                
                # Check if it's a mirrored database (Abf storage mode)
                storage_mode = dataset.get('targetStorageMode', '')
                if storage_mode == 'Abf':
                    print("🎯 CONFIRMED: This is a Fabric mirrored database!")
                    print("   Storage mode 'Abf' indicates Azure Blob File storage")
                    print("   This requires special handling for DAX queries")
                    return True
                else:
                    print(f"⚠️  Unexpected storage mode: {storage_mode}")
                    
            else:
                print(f"❌ Cannot get dataset details: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking dataset: {e}")
            return False
    
    def try_fabric_specific_endpoints(self):
        """Try Fabric-specific API endpoints"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔍 FABRIC-SPECIFIC API ENDPOINTS")
        print("-" * 40)
        
        # Try Fabric API endpoints
        fabric_endpoints = [
            f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}",
            f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}/tables",
        ]
        
        for endpoint in fabric_endpoints:
            print(f"Testing: {endpoint}")
            try:
                response = requests.get(endpoint, headers=headers, timeout=30)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ SUCCESS!")
                    print(json.dumps(data, indent=2)[:500] + "...")
                    return True
                elif response.status_code == 401:
                    print("❌ 401 - May need different token scope for Fabric API")
                elif response.status_code == 404:
                    print("❌ 404 - Endpoint not found or accessible")
                else:
                    print(f"❌ Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
            print()
        
        return False
    
    def try_sql_style_queries(self):
        """Try SQL-style queries which might work better with mirrored databases"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("🔍 SQL-STYLE QUERY TESTS")
        print("-" * 40)
        print("Mirrored databases might support SQL queries better than DAX")
        print()
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        # Try SQL-style queries that might work with mirrored databases
        sql_queries = [
            ("Simple SELECT", "EVALUATE SQLSELECT(\"SELECT 1 as TestValue\")"),
            ("Information Schema", "EVALUATE SQLSELECT(\"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES\")"),
            ("System Tables", "EVALUATE SQLSELECT(\"SELECT name FROM sys.tables\")"),
            ("Top 1 from any table", "EVALUATE SQLSELECT(\"SELECT TOP 1 * FROM (SELECT 1 as col) t\")"),
        ]
        
        for test_name, query in sql_queries:
            print(f"Testing: {test_name}")
            print(f"Query: {query}")
            
            payload = {
                "queries": [{"query": query}],
                "serializerSettings": {"includeNulls": True}
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ SUCCESS!")
                    data = response.json()
                    if data.get('results') and data['results'][0].get('tables'):
                        table = data['results'][0]['tables'][0]
                        rows = table.get('rows', [])
                        columns = table.get('columns', [])
                        print(f"Columns: {len(columns)}")
                        print(f"Rows: {len(rows)}")
                        if rows:
                            print(f"Sample: {rows[0]}")
                    return True
                else:
                    try:
                        error_data = response.json()
                        error_details = error_data.get('error', {}).get('pbi.error', {}).get('details', [])
                        if error_details:
                            detail = error_details[0].get('detail', {}).get('value', 'No detail')
                            print(f"Error: {detail}")
                        else:
                            print(f"Error: {response.text[:100]}")
                    except:
                        print(f"Error: {response.text[:100]}")
                        
            except Exception as e:
                print(f"Exception: {e}")
            print()
        
        return False
    
    def try_fabric_dax_queries(self):
        """Try DAX queries specifically designed for Fabric mirrored databases"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("🔍 FABRIC-SPECIFIC DAX QUERIES")
        print("-" * 40)
        print("Try DAX patterns that work with Fabric semantic models")
        print()
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        # DAX queries that might work with Fabric mirrored databases
        fabric_dax_queries = [
            ("Database Name", "EVALUATE ROW(\"DatabaseName\", \"AdventureWorks\")"),
            ("Current User", "EVALUATE ROW(\"User\", USERNAME())"),
            ("System Info", "EVALUATE ROW(\"Info\", \"System\")"),
            ("Empty Table with Schema", "EVALUATE ADDCOLUMNS(ROW(\"ID\", 1), \"Name\", \"Test\")"),
        ]
        
        for test_name, query in fabric_dax_queries:
            print(f"Testing: {test_name}")
            print(f"Query: {query}")
            
            payload = {
                "queries": [{"query": query}],
                "serializerSettings": {"includeNulls": True}
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ SUCCESS!")
                    data = response.json()
                    if data.get('results') and data['results'][0].get('tables'):
                        table = data['results'][0]['tables'][0]
                        rows = table.get('rows', [])
                        if rows:
                            print(f"Result: {rows[0]}")
                    return True
                else:
                    # Check if error message changed
                    try:
                        error_data = response.json()
                        error_details = error_data.get('error', {}).get('pbi.error', {}).get('details', [])
                        if error_details:
                            detail = error_details[0].get('detail', {}).get('value', 'No detail')
                            if "at least one tables" not in detail:
                                print(f"Different Error: {detail}")
                            else:
                                print(f"Same Error: {detail}")
                        else:
                            print(f"Error: {response.text[:100]}")
                    except:
                        print(f"Error: {response.text[:100]}")
                        
            except Exception as e:
                print(f"Exception: {e}")
            print()
        
        return False
    
    def check_mirrored_database_refresh_status(self):
        """Check if the mirrored database is synced and ready"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔄 MIRRORED DATABASE SYNC STATUS")
        print("-" * 40)
        
        try:
            # Check refresh history
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                print(f"Refresh entries: {len(refreshes)}")
                
                if refreshes:
                    latest = refreshes[0]
                    print(f"Latest refresh:")
                    print(f"   Start: {latest.get('startTime', 'Unknown')}")
                    print(f"   End: {latest.get('endTime', 'Ongoing')}")
                    print(f"   Status: {latest.get('status', 'Unknown')}")
                    print(f"   Type: {latest.get('refreshType', 'Unknown')}")
                    
                    if latest.get('status') == 'Completed':
                        print("✅ Latest refresh completed successfully")
                    elif latest.get('status') == 'Failed':
                        print("❌ Latest refresh failed")
                        if latest.get('serviceExceptionJson'):
                            print(f"   Error: {latest['serviceExceptionJson']}")
                    else:
                        print(f"⏳ Refresh status: {latest.get('status', 'Unknown')}")
                else:
                    print("⚠️  No refresh history found")
                    print("   Mirrored database may not be synced yet")
                    
            else:
                print(f"❌ Cannot get refresh status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking refresh: {e}")

def main():
    """Main Fabric mirrored database handler"""
    print("🏗️ FABRIC MIRRORED DATABASE SEMANTIC MODEL HANDLER")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Handle Fabric mirrored Azure SQL database semantic model")
    print("🎯 Target: Semantic model from mirrored Azure SQL DB")
    print()
    
    handler = FabricMirroredDatabaseHandler()
    
    if not handler.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Check if this is indeed a Fabric mirrored database
    is_fabric_mirrored = handler.check_fabric_semantic_model_status()
    print()
    
    # Check sync status
    handler.check_mirrored_database_refresh_status()
    print()
    
    # Try different approaches
    success1 = handler.try_fabric_specific_endpoints()
    success2 = handler.try_sql_style_queries() if not success1 else False
    success3 = handler.try_fabric_dax_queries() if not (success1 or success2) else False
    
    print("📊 FABRIC MIRRORED DATABASE ANALYSIS")
    print("=" * 45)
    
    if success1 or success2 or success3:
        print("🎉 SUCCESS! Found working approach for Fabric mirrored database")
        if success1:
            print("   ✅ Fabric API endpoints work")
        if success2:
            print("   ✅ SQL-style queries work")
        if success3:
            print("   ✅ Fabric DAX queries work")
    else:
        print("❌ Fabric mirrored database challenges identified")
        print()
        print("🔧 FABRIC MIRRORED DATABASE SOLUTIONS:")
        print("1. 🔄 SYNC STATUS: Ensure mirrored database is fully synced")
        print("   - Check Azure SQL mirror status in Fabric portal")
        print("   - Verify data replication is complete")
        print()
        print("2. 🎛️ SEMANTIC MODEL CONFIGURATION:")
        print("   - Mirrored databases may need semantic model refresh")
        print("   - Check if automatic semantic model creation completed")
        print()
        print("3. 🔌 API COMPATIBILITY:")
        print("   - Fabric mirrored DBs may require different API patterns")
        print("   - Consider using XMLA endpoint directly")
        print("   - Check if service principal has Fabric permissions")
        print()
        print("4. 📊 TABLE VISIBILITY:")
        print("   - Mirrored tables might not appear in standard APIs")
        print("   - Tables may be in different schema/namespace")
        print("   - Check Fabric admin portal for semantic model status")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if (success1 or success2 or success3) else 1

if __name__ == "__main__":
    exit(main())
