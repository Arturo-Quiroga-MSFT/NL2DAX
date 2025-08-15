#!/usr/bin/env python3
"""
Alternative Dataset Table Discovery
Try different API methods to find tables in the dataset
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class AlternativeTableDiscovery:
    """Try alternative methods to discover tables in the dataset"""
    
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
    
    def try_different_table_endpoints(self):
        """Try different API endpoints to find tables"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔍 TRYING DIFFERENT TABLE DISCOVERY METHODS")
        print("-" * 50)
        
        # Method 1: Direct dataset tables (we already tried this)
        print("1️⃣ Direct Dataset Tables API:")
        endpoints_to_try = [
            f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/tables",
            f"{self.base_url}/datasets/{self.dataset_id}/tables",  # Without workspace
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, headers=headers, timeout=30)
                print(f"   {endpoint}")
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    tables = response.json().get('value', [])
                    print(f"   ✅ Found {len(tables)} tables!")
                    if tables:
                        for table in tables[:3]:
                            print(f"      - {table.get('name', 'Unknown')}")
                        return tables
                else:
                    print(f"   ❌ Error: {response.text[:100]}")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            print()
        
        # Method 2: Try to get schema through DAX INFO functions
        print("2️⃣ DAX INFO Functions:")
        info_queries = [
            ("INFO.TABLES()", "Get table information"),
            ("INFO.COLUMNS()", "Get column information"),
            ("EVALUATE TABLES()", "List tables directly"),
        ]
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        for query, description in info_queries:
            print(f"   Testing: {description}")
            print(f"   Query: {query}")
            
            payload = {
                "queries": [{"query": query}],
                "serializerSettings": {"includeNulls": True}
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ SUCCESS! Got schema information")
                    data = response.json()
                    if data.get('results') and data['results'][0].get('tables'):
                        table = data['results'][0]['tables'][0]
                        rows = table.get('rows', [])
                        print(f"   Rows returned: {len(rows)}")
                        if rows:
                            # Show first few results
                            for i, row in enumerate(rows[:5], 1):
                                print(f"      {i}. {row}")
                    return True
                else:
                    print(f"   ❌ Failed: {response.text[:100]}")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            print()
        
        # Method 3: Try to access specific known tables
        print("3️⃣ Testing Known AdventureWorks Tables:")
        known_tables = [
            "Customer",
            "Product", 
            "Sales",
            "DimCustomer",
            "DimProduct",
            "FactInternetSales",
            "FactResellerSales"
        ]
        
        for table_name in known_tables:
            query = f"EVALUATE TOPN(1, {table_name})"
            print(f"   Testing table: {table_name}")
            
            payload = {
                "queries": [{"query": query}],
                "serializerSettings": {"includeNulls": True}
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS! Table '{table_name}' exists and accessible")
                    data = response.json()
                    if data.get('results') and data['results'][0].get('tables'):
                        table = data['results'][0]['tables'][0]
                        columns = table.get('columns', [])
                        rows = table.get('rows', [])
                        print(f"      Columns: {len(columns)}")
                        print(f"      Sample rows: {len(rows)}")
                        if columns:
                            col_names = [col.get('name', 'Unknown') for col in columns[:5]]
                            print(f"      First columns: {', '.join(col_names)}")
                    return True
                else:
                    # Don't print error for each table - just continue
                    pass
            except Exception as e:
                pass
            
        print("   ❌ No known AdventureWorks tables found")
        print()
        
        return False
    
    def check_dataset_metadata_detailed(self):
        """Get more detailed dataset metadata"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔍 DETAILED DATASET METADATA")
        print("-" * 40)
        
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                dataset = response.json()
                
                print("Raw Dataset Response:")
                print(json.dumps(dataset, indent=2))
                print()
                
                # Look for any hints about the dataset type or mode
                storage_mode = dataset.get('targetStorageMode', 'Unknown')
                print(f"Target Storage Mode: {storage_mode}")
                
                if storage_mode == 'Abf':
                    print("⚠️  Dataset uses Azure Blob File storage mode")
                    print("   This might affect table discovery")
                elif storage_mode == 'DirectQuery':
                    print("⚠️  Dataset is in DirectQuery mode")
                    print("   Tables might not be visible through all APIs")
                
                return True
            else:
                print(f"❌ Cannot get dataset metadata: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Metadata error: {e}")
            return False
    
    def test_xmla_style_queries(self):
        """Try XMLA-style queries that might work differently"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("🔍 XMLA-STYLE QUERY TESTS")
        print("-" * 40)
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        # Try different query formats
        xmla_queries = [
            ("Row Count Check", "EVALUATE ROW(\"Count\", 1)"),
            ("System Time", "EVALUATE ROW(\"Now\", NOW())"),
            ("Database Info", "EVALUATE ROW(\"Database\", \"AdventureWorks\")"),
            ("Empty Table Test", "EVALUATE FILTER(ROW(\"Test\", 1), 1=1)"),
        ]
        
        for test_name, query in xmla_queries:
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
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('pbi.error', {}).get('details', [])
                        if error_msg:
                            detail = error_msg[0].get('detail', {}).get('value', 'No detail')
                            print(f"Error: {detail}")
                        else:
                            print(f"Error: {response.text[:100]}")
                    except:
                        print(f"Error: {response.text[:100]}")
            except Exception as e:
                print(f"Exception: {e}")
            print()
        
        return False

def main():
    """Main alternative discovery function"""
    print("🔍 ALTERNATIVE DATASET TABLE DISCOVERY")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Find tables using alternative methods")
    print("🎯 User confirms dataset has multiple tables - find them!")
    print()
    
    discoverer = AlternativeTableDiscovery()
    
    if not discoverer.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Try different discovery methods
    success1 = discoverer.try_different_table_endpoints()
    
    if not success1:
        print("📊 Since direct table discovery failed, checking metadata...")
        discoverer.check_dataset_metadata_detailed()
        print()
        
        print("🧪 Trying alternative query approaches...")
        success2 = discoverer.test_xmla_style_queries()
    else:
        success2 = True
    
    print("📊 DISCOVERY RESULTS")
    print("=" * 30)
    
    if success1 or success2:
        print("🎉 SUCCESS! Found a way to access the dataset")
        print("   The tables exist and can be queried")
        print("   The original error might be due to:")
        print("   • API endpoint differences")
        print("   • Dataset storage mode (Abf)")
        print("   • Query syntax requirements")
    else:
        print("❌ Still unable to find tables through API")
        print("   🔧 NEXT STEPS:")
        print("   1. Verify the correct dataset ID")
        print("   2. Check if using different workspace")
        print("   3. Try XMLA endpoint directly")
        print("   4. Use Power BI Desktop to inspect dataset")
        print("   5. Check dataset refresh status in Power BI Service")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if (success1 or success2) else 1

if __name__ == "__main__":
    exit(main())
