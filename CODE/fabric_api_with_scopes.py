#!/usr/bin/env python3
"""
Fabric API with Correct Scopes
Use proper Fabric scopes to access mirrored database tables
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FabricAPIHandler:
    """Handle Fabric API with correct authentication scopes"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.powerbi_token = None
        self.fabric_token = None
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.fabric_url = "https://api.fabric.microsoft.com/v1"
        
    def get_powerbi_token(self):
        """Get Power BI token"""
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            scopes = ["https://analysis.windows.net/powerbi/api/.default"]
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self.powerbi_token = result["access_token"]
                return True
            else:
                print(f"❌ Power BI token failed: {result.get('error_description', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"❌ Power BI token error: {e}")
            return False
    
    def get_fabric_token(self):
        """Get Fabric token with proper scope"""
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Try Fabric-specific scope
            fabric_scopes = ["https://api.fabric.microsoft.com/.default"]
            result = app.acquire_token_for_client(scopes=fabric_scopes)
            
            if "access_token" in result:
                self.fabric_token = result["access_token"]
                print("✅ Fabric token acquired successfully")
                return True
            else:
                print(f"❌ Fabric token failed: {result.get('error_description', 'Unknown')}")
                print("   Trying with Power BI scope for Fabric APIs...")
                
                # Fallback to Power BI scope
                self.fabric_token = self.powerbi_token
                return True
                
        except Exception as e:
            print(f"❌ Fabric token error: {e}")
            return False
    
    def explore_fabric_semantic_model(self):
        """Explore the Fabric semantic model structure"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔍 FABRIC SEMANTIC MODEL EXPLORATION")
        print("-" * 50)
        
        # Get semantic model details
        print("1️⃣ Semantic Model Details:")
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                model = response.json()
                print("   ✅ Semantic Model Found:")
                print(f"      Name: {model.get('displayName', 'Unknown')}")
                print(f"      Type: {model.get('type', 'Unknown')}")
                print(f"      ID: {model.get('id', 'Unknown')}")
                print(f"      Workspace: {model.get('workspaceId', 'Unknown')}")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        
        # Try to get tables
        print("2️⃣ Tables in Semantic Model:")
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}/tables",
                headers=headers,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                tables_data = response.json()
                tables = tables_data.get('value', [])
                print(f"   ✅ Found {len(tables)} tables!")
                
                for i, table in enumerate(tables[:5], 1):  # Show first 5 tables
                    print(f"      {i}. {table.get('name', 'Unknown')}")
                    print(f"         Description: {table.get('description', 'No description')}")
                    print(f"         Hidden: {table.get('isHidden', False)}")
                
                if len(tables) > 5:
                    print(f"      ... and {len(tables) - 5} more tables")
                    
                return tables
                
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
        return []
    
    def try_dax_with_actual_tables(self, tables):
        """Try DAX queries with actual table names from Fabric"""
        if not tables:
            print("⚠️  No tables found to query")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.powerbi_token}",
            "Content-Type": "application/json"
        }
        
        print("🧪 DAX QUERIES WITH ACTUAL TABLE NAMES")
        print("-" * 50)
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        # Try queries with actual table names
        for i, table in enumerate(tables[:3], 1):  # Test first 3 tables
            table_name = table.get('name', 'Unknown')
            
            test_queries = [
                (f"Count rows in {table_name}", f"EVALUATE ROW(\"TableRowCount\", COUNTROWS({table_name}))"),
                (f"Top 1 from {table_name}", f"EVALUATE TOPN(1, {table_name})"),
                (f"Column count in {table_name}", f"EVALUATE ROW(\"ColumnCount\", COLUMNCOUNT({table_name}))")
            ]
            
            print(f"Testing Table {i}: {table_name}")
            
            for test_name, query in test_queries:
                print(f"   {test_name}")
                print(f"   Query: {query}")
                
                payload = {
                    "queries": [{"query": query}],
                    "serializerSettings": {"includeNulls": True}
                }
                
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("   ✅ SUCCESS!")
                        data = response.json()
                        if data.get('results') and data['results'][0].get('tables'):
                            result_table = data['results'][0]['tables'][0]
                            rows = result_table.get('rows', [])
                            if rows:
                                print(f"   Result: {rows[0]}")
                        return True
                    else:
                        try:
                            error_data = response.json()
                            error_details = error_data.get('error', {}).get('pbi.error', {}).get('details', [])
                            if error_details:
                                detail = error_details[0].get('detail', {}).get('value', 'No detail')
                                print(f"   Error: {detail}")
                            else:
                                print(f"   Error: {response.text[:100]}")
                        except:
                            print(f"   Error: {response.text[:100]}")
                            
                except Exception as e:
                    print(f"   Exception: {e}")
                print()
        
        return False
    
    def check_mirrored_database_sync(self):
        """Check if the mirrored database is properly synced"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔄 MIRRORED DATABASE SYNC CHECK")
        print("-" * 40)
        
        try:
            # Check workspace items to find the mirrored database
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/items",
                headers=headers,
                timeout=30
            )
            
            print(f"Workspace items status: {response.status_code}")
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                print(f"Found {len(items)} items in workspace")
                
                # Look for mirrored databases
                mirrored_dbs = [item for item in items if item.get('type') == 'MirroredDatabase']
                semantic_models = [item for item in items if item.get('type') == 'SemanticModel']
                
                print(f"   Mirrored Databases: {len(mirrored_dbs)}")
                print(f"   Semantic Models: {len(semantic_models)}")
                
                for db in mirrored_dbs:
                    print(f"      Mirrored DB: {db.get('displayName', 'Unknown')}")
                    
                for model in semantic_models:
                    print(f"      Semantic Model: {model.get('displayName', 'Unknown')}")
                    if model.get('id') == self.dataset_id:
                        print(f"         🎯 This is our target semantic model!")
                        
            else:
                print(f"   ❌ Error getting workspace items: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def main():
    """Main Fabric API handler function"""
    print("🏗️ FABRIC API WITH CORRECT SCOPES")
    print("=" * 40)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Access Fabric mirrored database with proper API scopes")
    print()
    
    handler = FabricAPIHandler()
    
    # Get both tokens
    if not handler.get_powerbi_token():
        print("❌ Cannot proceed without Power BI token")
        return 1
    
    if not handler.get_fabric_token():
        print("❌ Cannot proceed without Fabric token")
        return 1
    
    print("✅ Both tokens acquired successfully")
    print()
    
    # Check mirrored database sync status
    handler.check_mirrored_database_sync()
    print()
    
    # Explore semantic model structure
    tables = handler.explore_fabric_semantic_model()
    print()
    
    # Try DAX queries with actual table names
    if tables:
        success = handler.try_dax_with_actual_tables(tables)
    else:
        success = False
        print("❌ No tables found in semantic model")
    
    print("📊 FABRIC MIRRORED DATABASE RESULTS")
    print("=" * 40)
    
    if success:
        print("🎉 SUCCESS! DAX queries work with Fabric mirrored database")
        print("   The semantic model is properly configured and accessible")
        print("   Tables are available and can be queried")
    elif tables:
        print("⚠️  Tables found but DAX queries still failing")
        print("   This suggests the mirrored database may not be fully synced")
        print("   or there are specific query syntax requirements")
    else:
        print("❌ No tables found in semantic model")
        print("   The mirrored database may not be fully synced")
        print("   or the semantic model needs to be refreshed")
    
    print()
    print("🔧 RECOMMENDATIONS:")
    print("1. Check Fabric portal for mirrored database sync status")
    print("2. Verify semantic model refresh/update status") 
    print("3. Ensure all Azure SQL tables are properly mirrored")
    print("4. Check if mirrored database replication is complete")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
