#!/usr/bin/env python3
"""
Check Dataset Tables and Content
Verify if dataset has tables and what content is available
"""

import os
import requests
import msal
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

class DatasetContentChecker:
    """Check what content is actually in the dataset"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        # Try both possible environment variable names for dataset ID
        self.dataset_id = os.getenv("PBI_DATASET_ID") or os.getenv("POWERBI_DATASET_ID")
        self.token = None
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
        # Validate that we have a dataset ID
        if not self.dataset_id:
            raise ValueError("No dataset ID found. Please set PBI_DATASET_ID or POWERBI_DATASET_ID in your .env file")
        
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
    
    def check_dataset_tables(self):
        """Check what tables exist in the dataset"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("📊 DATASET TABLES CHECK")
        print("-" * 40)
        
        try:
            # Get tables in the dataset
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/tables",
                headers=headers,
                timeout=30
            )
            
            print(f"Tables API Status: {response.status_code}")
            
            if response.status_code == 200:
                tables = response.json().get('value', [])
                print(f"✅ Found {len(tables)} tables")
                
                if tables:
                    for i, table in enumerate(tables, 1):
                        print(f"\n{i}. Table: {table.get('name', 'Unknown')}")
                        print(f"   Description: {table.get('description', 'No description')}")
                        print(f"   Hidden: {table.get('isHidden', 'Unknown')}")
                        
                        # Get columns for this table
                        if 'columns' in table:
                            columns = table['columns']
                            print(f"   Columns ({len(columns)}):")
                            for col in columns[:5]:  # Show first 5 columns
                                print(f"     - {col.get('name', 'Unknown')} ({col.get('dataType', 'Unknown')})")
                            if len(columns) > 5:
                                print(f"     ... and {len(columns) - 5} more columns")
                else:
                    print("❌ NO TABLES FOUND - This explains the error!")
                    print("   The dataset exists but contains no tables")
                    
                return len(tables) > 0
                
            else:
                print(f"❌ Cannot get tables: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Tables check error: {e}")
            return False
    
    def check_dataset_datasources(self):
        """Check what data sources are configured"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔌 DATASET DATA SOURCES CHECK")
        print("-" * 40)
        
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/datasources",
                headers=headers,
                timeout=30
            )
            
            print(f"Data Sources API Status: {response.status_code}")
            
            if response.status_code == 200:
                datasources = response.json().get('value', [])
                print(f"✅ Found {len(datasources)} data sources")
                
                for i, ds in enumerate(datasources, 1):
                    print(f"\n{i}. Data Source:")
                    print(f"   ID: {ds.get('datasourceId', 'Unknown')}")
                    print(f"   Type: {ds.get('datasourceType', 'Unknown')}")
                    print(f"   Connection: {ds.get('connectionString', 'Unknown')}")
                    print(f"   Gateway: {ds.get('gatewayId', 'None')}")
                    
                    if 'connectionDetails' in ds:
                        details = ds['connectionDetails']
                        print(f"   Server: {details.get('server', 'Unknown')}")
                        print(f"   Database: {details.get('database', 'Unknown')}")
                        
                return len(datasources) > 0
                
            else:
                print(f"❌ Cannot get data sources: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Data sources check error: {e}")
            return False
    
    def check_dataset_refresh_history(self):
        """Check refresh history to see if dataset has been populated"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔄 DATASET REFRESH HISTORY")
        print("-" * 40)
        
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            print(f"Refresh History API Status: {response.status_code}")
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                print(f"✅ Found {len(refreshes)} refresh entries")
                
                if refreshes:
                    print("\nRecent refreshes:")
                    for i, refresh in enumerate(refreshes[:3], 1):  # Show last 3
                        print(f"{i}. {refresh.get('startTime', 'Unknown')} - {refresh.get('endTime', 'Ongoing')}")
                        print(f"   Status: {refresh.get('status', 'Unknown')}")
                        print(f"   Type: {refresh.get('refreshType', 'Unknown')}")
                        if refresh.get('serviceExceptionJson'):
                            print(f"   Error: {refresh['serviceExceptionJson']}")
                        print()
                else:
                    print("⚠️  No refresh history found")
                    print("   Dataset may never have been refreshed or populated")
                    
                return len(refreshes) > 0
                
            else:
                print(f"❌ Cannot get refresh history: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Refresh history error: {e}")
            return False
    
    def trigger_dataset_refresh(self):
        """Attempt to trigger a dataset refresh"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("🔄 TRIGGERING DATASET REFRESH")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                json={"notifyOption": "MailOnFailure"},
                timeout=30
            )
            
            print(f"Refresh Trigger Status: {response.status_code}")
            
            if response.status_code == 202:
                print("✅ Refresh triggered successfully!")
                print("   The dataset will be refreshed asynchronously")
                print("   Wait a few minutes then check if tables appear")
                return True
            elif response.status_code == 400:
                print("❌ Refresh failed - likely configuration issue")
                print(f"   Response: {response.text}")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                
            return False
                
        except Exception as e:
            print(f"❌ Refresh trigger error: {e}")
            return False
    
    def check_fabric_tables_via_xmla(self):
        """Check tables using XMLA/TMSL for Fabric datasets"""
        print("🏗️  FABRIC DATASET TABLES CHECK (via XMLA)")
        print("-" * 40)
        
        try:
            # Convert PowerBI XMLA endpoint to HTTP endpoint
            xmla_endpoint = os.getenv("PBI_XMLA_ENDPOINT", "powerbi://api.powerbi.com/v1.0/myorg/FIS")
            dataset_name = os.getenv("PBI_DATASET_NAME", "FIS-SEMANTIC-MODEL")
            
            # Convert powerbi:// to https:// endpoint for HTTP XMLA
            if xmla_endpoint.startswith("powerbi://"):
                http_xmla = xmla_endpoint.replace("powerbi://", "https://").replace("/v1.0/myorg", "/xmla")
            else:
                http_xmla = xmla_endpoint
            
            print(f"XMLA Endpoint: {xmla_endpoint}")
            print(f"HTTP XMLA: {http_xmla}")
            print(f"Dataset Name: {dataset_name}")
            
            # XMLA SOAP request to discover tables using DMVs
            dmv_query = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
              <Body>
                <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
                  <Command>
                    <Statement>
                    SELECT 
                        [TABLE_NAME] as TableName,
                        [TABLE_TYPE] as TableType,
                        [DESCRIPTION] as Description
                    FROM $SYSTEM.TMSCHEMA_TABLES
                    ORDER BY [TABLE_NAME]
                    </Statement>
                  </Command>
                  <Properties>
                    <PropertyList>
                      <Catalog>{dataset_name}</Catalog>
                      <Format>Tabular</Format>
                    </PropertyList>
                  </Properties>
                </Execute>
              </Body>
            </Envelope>"""
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "urn:schemas-microsoft-com:xml-analysis:Execute"
            }
            
            print("📡 Sending XMLA DMV query...")
            response = requests.post(http_xmla, data=dmv_query, headers=headers, timeout=30)
            
            print(f"XMLA Response Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ XMLA query successful!")
                print("Raw response (first 1000 chars):")
                print(response.text[:1000])
                
                # Parse XML response
                try:
                    root = ET.fromstring(response.text)
                    
                    # Look for table data in the response
                    tables_found = []
                    
                    # Navigate through XML to find table names
                    for elem in root.iter():
                        if elem.text and isinstance(elem.text, str):
                            text = elem.text.strip()
                            # Look for table-like names (avoid system metadata)
                            if text and not text.startswith('$') and not text.startswith('TMSCHEMA'):
                                if any(keyword in text.upper() for keyword in ['TABLE', 'FACT', 'DIM', 'CUSTOMER', 'SALES']):
                                    tables_found.append(text)
                    
                    if tables_found:
                        print(f"✅ Found {len(tables_found)} potential tables:")
                        for i, table in enumerate(set(tables_found), 1):
                            print(f"   {i}. {table}")
                        return True
                    else:
                        print("⚠️  No recognizable table names found in XMLA response")
                        return False
                        
                except ET.ParseError as e:
                    print(f"❌ XML parsing error: {e}")
                    return False
                    
            else:
                print(f"❌ XMLA query failed: {response.status_code}")
                print("Response content:")
                print(response.text[:500])
                return False
                
        except Exception as e:
            print(f"❌ XMLA table discovery error: {e}")
            return False
    
    def check_fabric_tables_via_rest_api(self):
        """Try Fabric-specific REST APIs for table discovery"""
        print("🏭 FABRIC REST API TABLES CHECK")
        print("-" * 40)
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get Fabric item details
            fabric_item_url = f"https://api.fabric.microsoft.com/v1/workspaces/{self.workspace_id}/items/{self.dataset_id}"
            print(f"Getting Fabric item details: {fabric_item_url}")
            
            response = requests.get(fabric_item_url, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                item_details = response.json()
                print("✅ Fabric item details:")
                print(f"   Name: {item_details.get('displayName', 'Unknown')}")
                print(f"   Type: {item_details.get('type', 'Unknown')}")
                print(f"   Description: {item_details.get('description', 'No description')}")
                
                # Try to execute a simple DAX query to list tables
                print("\n🔍 Attempting DAX query to discover tables...")
                
                # Use Power BI executeQueries endpoint with a table discovery query
                execute_url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
                
                # Simple queries to try to discover table names
                discovery_queries = [
                    "EVALUATE INFO.TABLES()",
                    "EVALUATE SUMMARIZE(INFO.TABLES(), INFO.TABLES()[Name])",
                    "EVALUATE DISTINCT(INFO.TABLES()[Name])"
                ]
                
                for i, query in enumerate(discovery_queries, 1):
                    print(f"\n   Trying query {i}: {query[:50]}...")
                    
                    query_body = {
                        "queries": [{
                            "query": query
                        }],
                        "serializerSettings": {
                            "includeNulls": False
                        }
                    }
                    
                    query_response = requests.post(execute_url, headers=headers, json=query_body, timeout=30)
                    print(f"   Query Status: {query_response.status_code}")
                    
                    if query_response.status_code == 200:
                        result = query_response.json()
                        print("   ✅ Query successful!")
                        
                        # Extract table information from results
                        if 'results' in result and result['results']:
                            query_result = result['results'][0]
                            if 'tables' in query_result and query_result['tables']:
                                table_data = query_result['tables'][0]
                                if 'rows' in table_data:
                                    print(f"   Found {len(table_data['rows'])} table entries:")
                                    for row in table_data['rows'][:10]:  # Show first 10
                                        print(f"     - {row}")
                                    return True
                        
                        print("   Query returned data but no recognizable table structure")
                        
                    else:
                        print(f"   ❌ Query failed: {query_response.text[:200]}")
                
                return False
                
            else:
                print(f"❌ Cannot access Fabric item: {query_response.text[:200]}")
                return False
            
        except Exception as e:
            print(f"❌ Fabric REST API error: {e}")
            return False

def main():
    """Main dataset content checking function"""
    print("📊 DATASET CONTENT CHECKER")
    print("=" * 40)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Check if dataset has tables and content")
    print("🎯 Root Cause: 'DAX queries work only on databases which have at least one tables'")
    print()
    
    try:
        checker = DatasetContentChecker()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        return 1
    
    print(f"🆔 Using Dataset ID: {checker.dataset_id}")
    print(f"🏢 Workspace ID: {checker.workspace_id}")
    print()
    
    if not checker.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Check what's in the dataset using standard APIs
    has_tables = checker.check_dataset_tables()
    print()
    
    has_datasources = checker.check_dataset_datasources()
    print()
    
    # If standard API failed, try Fabric-specific methods
    fabric_tables_found = False
    if not has_tables:
        print("🔍 Standard API failed - trying Fabric-specific methods...")
        print()
        
        # Try XMLA approach
        fabric_tables_found = checker.check_fabric_tables_via_xmla()
        print()
        
        # Try Fabric REST APIs
        if not fabric_tables_found:
            fabric_rest_success = checker.check_fabric_tables_via_rest_api()
            print()
    
    has_refreshes = checker.check_dataset_refresh_history()
    print()
    
    # Analysis and recommendations
    print("📊 ANALYSIS & RECOMMENDATIONS")
    print("=" * 40)
    
    if has_tables or fabric_tables_found:
        print("✅ Dataset has tables - the issue is elsewhere")
        print("   Need to investigate other causes of the DAX error")
    else:
        print("❌ DATASET HAS NO TABLES - This is the root cause!")
        print()
        print("🔧 SOLUTIONS:")
        
        if has_datasources:
            print("1. 🔄 REFRESH DATASET (data sources exist but tables not loaded)")
            print("   The dataset has data sources configured but no tables")
            print("   A refresh should populate the tables")
            print()
            
            # Offer to trigger refresh
            user_input = input("   Would you like to trigger a dataset refresh now? (y/n): ")
            if user_input.lower() == 'y':
                refresh_success = checker.trigger_dataset_refresh()
                if refresh_success:
                    print("\n   ✅ Refresh triggered! Wait 2-5 minutes then test DAX queries again")
                else:
                    print("\n   ❌ Refresh failed - check data source configuration")
        else:
            print("1. 📊 CONFIGURE DATA SOURCES")
            print("   No data sources found - dataset needs to be connected to data")
            print("   - Open Power BI Desktop")
            print("   - Connect to your data sources")
            print("   - Publish the dataset to the workspace")
            print()
            
        print("2. 📁 VERIFY DATASET CONFIGURATION")
        print("   - Check if this is the correct dataset ID")
        print("   - Verify the dataset was published correctly")
        print("   - Ensure data sources are accessible")
        print()
        
        print("3. 🔄 USE A DIFFERENT DATASET")
        print("   - Find a dataset that actually contains tables")
        print("   - Update your configuration to use that dataset")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if has_tables else 1

if __name__ == "__main__":
    exit(main())
