#!/usr/bin/env python3
"""
Check Dataset Tables and Content
Verify if dataset has tables and what content is available
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class DatasetContentChecker:
    """Check what content is actually in the dataset"""
    
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

def main():
    """Main dataset content checking function"""
    print("📊 DATASET CONTENT CHECKER")
    print("=" * 40)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Check if dataset has tables and content")
    print("🎯 Root Cause: 'DAX queries work only on databases which have at least one tables'")
    print()
    
    checker = DatasetContentChecker()
    
    if not checker.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Check what's in the dataset
    has_tables = checker.check_dataset_tables()
    print()
    
    has_datasources = checker.check_dataset_datasources()
    print()
    
    has_refreshes = checker.check_dataset_refresh_history()
    print()
    
    # Analysis and recommendations
    print("📊 ANALYSIS & RECOMMENDATIONS")
    print("=" * 40)
    
    if has_tables:
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
