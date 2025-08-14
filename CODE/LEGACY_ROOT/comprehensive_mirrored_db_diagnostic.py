#!/usr/bin/env python3
"""
Comprehensive Mirrored Database Diagnostic
Final troubleshooting to identify exactly why tables aren't appearing
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ComprehensiveMirroredDBDiagnostic:
    """Final diagnostic for mirrored database issues"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.mirrored_db_id = "f5846ddf-df0c-4400-8961-1c1e754c48aa"
        self.sql_endpoint_id = "90dc0d3c-db41-4731-88c2-3bf3bf42ef1b"  # From previous discovery
        self.powerbi_token = None
        self.fabric_token = None
        self.powerbi_url = "https://api.powerbi.com/v1.0/myorg"
        self.fabric_url = "https://api.fabric.microsoft.com/v1"
        
    def get_tokens(self):
        """Get authentication tokens"""
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Power BI token
            pbi_result = app.acquire_token_for_client(
                scopes=["https://analysis.windows.net/powerbi/api/.default"]
            )
            
            if "access_token" in pbi_result:
                self.powerbi_token = pbi_result["access_token"]
                print("✅ Power BI token acquired")
            else:
                print(f"❌ Power BI token failed: {pbi_result.get('error_description', 'Unknown')}")
                return False
            
            # Fabric token
            fabric_result = app.acquire_token_for_client(
                scopes=["https://api.fabric.microsoft.com/.default"]
            )
            
            if "access_token" in fabric_result:
                self.fabric_token = fabric_result["access_token"]
                print("✅ Fabric token acquired")
            else:
                print("⚠️  Using Power BI token for Fabric APIs")
                self.fabric_token = self.powerbi_token
            
            return True
                
        except Exception as e:
            print(f"❌ Token error: {e}")
            return False
    
    def test_sql_endpoint_directly(self):
        """Test the SQL endpoint that was discovered"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔍 SQL ENDPOINT TESTING")
        print("-" * 30)
        print(f"SQL Endpoint ID: {self.sql_endpoint_id}")
        print()
        
        # Try different SQL endpoint approaches
        sql_endpoints = [
            ("SQL Endpoint Details", f"/workspaces/{self.workspace_id}/sqlEndpoints/{self.sql_endpoint_id}"),
            ("SQL Endpoint Tables", f"/workspaces/{self.workspace_id}/sqlEndpoints/{self.sql_endpoint_id}/tables"),
            ("SQL Endpoint Schema", f"/workspaces/{self.workspace_id}/sqlEndpoints/{self.sql_endpoint_id}/schemas"),
        ]
        
        for name, endpoint in sql_endpoints:
            print(f"Testing {name}:")
            
            try:
                response = requests.get(
                    f"{self.fabric_url}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {name} found!")
                    
                    if isinstance(data, dict):
                        if 'value' in data:  # List response
                            items = data['value']
                            print(f"      Found {len(items)} items")
                            for i, item in enumerate(items[:5], 1):
                                name_field = item.get('name', item.get('displayName', f'Item {i}'))
                                print(f"         {i}. {name_field}")
                        else:  # Single object response
                            for key, value in data.items():
                                if not isinstance(value, (dict, list)):
                                    print(f"      {key}: {value}")
                    
                elif response.status_code == 404:
                    print(f"   ❌ {name} not found")
                else:
                    print(f"   ⚠️  Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            print()
    
    def check_onelake_data(self):
        """Check if data exists in OneLake storage"""
        print("📂 ONELAKE DATA CHECK")
        print("-" * 25)
        
        # The OneLake path from earlier: 
        # https://onelake.dfs.fabric.microsoft.com/e3fdee99-3aa4-4d71-a530-2964a062e326/f5846ddf-df0c-4400-8961-1c1e754c48aa/Tables
        
        onelake_url = f"https://onelake.dfs.fabric.microsoft.com/{self.workspace_id}/{self.mirrored_db_id}/Tables"
        
        print(f"OneLake path: {onelake_url}")
        
        # Try to access OneLake data (this might require different auth)
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        try:
            response = requests.get(onelake_url, headers=headers, timeout=30)
            print(f"OneLake access status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ OneLake data accessible!")
                print(f"   Content length: {len(response.content)} bytes")
                print(f"   Content type: {response.headers.get('content-type', 'Unknown')}")
                
                # Try to parse as JSON or show first bit of content
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        data = response.json()
                        print(f"   JSON data: {json.dumps(data, indent=6)[:300]}...")
                    else:
                        content_preview = response.text[:200] if response.text else str(response.content)[:200]
                        print(f"   Content preview: {content_preview}...")
                except:
                    print(f"   Raw content preview: {str(response.content)[:200]}...")
                    
            elif response.status_code == 404:
                print("❌ OneLake data not found")
                print("   This suggests the mirrored database has no data")
            elif response.status_code == 403:
                print("⚠️  OneLake access forbidden")
                print("   May need different authentication or permissions")
            else:
                print(f"⚠️  OneLake response {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ OneLake access exception: {e}")
        
        print()
    
    def force_semantic_model_refresh_with_debug(self):
        """Force refresh with detailed debugging"""
        headers = {
            "Authorization": f"Bearer {self.powerbi_token}",
            "Content-Type": "application/json"
        }
        
        print("🔄 FORCE REFRESH WITH DEBUGGING")
        print("-" * 40)
        
        # Get current refresh status first
        try:
            refresh_response = requests.get(
                f"{self.powerbi_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            if refresh_response.status_code == 200:
                refreshes = refresh_response.json().get('value', [])
                if refreshes:
                    latest = refreshes[0]
                    print(f"Latest refresh status: {latest.get('status')}")
                    print(f"Latest refresh end: {latest.get('endTime', 'N/A')}")
                    
                    # Check for errors
                    if latest.get('status') == 'Failed':
                        error_json = latest.get('serviceExceptionJson', 'No error details')
                        print(f"Latest error: {error_json}")
                    
        except Exception as e:
            print(f"Error checking refresh status: {e}")
        
        print()
        
        # Trigger new refresh
        print("Triggering new refresh...")
        
        try:
            refresh_trigger = requests.post(
                f"{self.powerbi_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                json={},  # Empty payload to avoid service principal issues
                timeout=30
            )
            
            print(f"Refresh trigger status: {refresh_trigger.status_code}")
            
            if refresh_trigger.status_code == 202:
                print("✅ Refresh triggered successfully")
                
                # Wait and monitor the refresh
                print("Monitoring refresh progress...")
                
                for attempt in range(12):  # Check for 2 minutes
                    time.sleep(10)  # Wait 10 seconds
                    
                    try:
                        status_response = requests.get(
                            f"{self.powerbi_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                            headers=headers,
                            timeout=30
                        )
                        
                        if status_response.status_code == 200:
                            current_refreshes = status_response.json().get('value', [])
                            if current_refreshes:
                                current = current_refreshes[0]
                                status = current.get('status', 'Unknown')
                                start_time = current.get('startTime', 'Unknown')
                                
                                print(f"   Attempt {attempt + 1}: Status = {status} (Started: {start_time})")
                                
                                if status == 'Completed':
                                    print("   ✅ Refresh completed successfully!")
                                    
                                    # Now test if tables are available
                                    return self.test_tables_after_refresh()
                                    
                                elif status == 'Failed':
                                    print("   ❌ Refresh failed!")
                                    error_json = current.get('serviceExceptionJson', 'No error details')
                                    print(f"   Error: {error_json}")
                                    return False
                                    
                    except Exception as e:
                        print(f"   Error checking refresh: {e}")
                
                print("⏰ Refresh monitoring timeout")
                return False
                
            else:
                print(f"❌ Refresh trigger failed: {refresh_trigger.text}")
                return False
                
        except Exception as e:
            print(f"❌ Refresh trigger exception: {e}")
            return False
    
    def test_tables_after_refresh(self):
        """Test if tables are accessible after refresh"""
        headers = {
            "Authorization": f"Bearer {self.powerbi_token}",
            "Content-Type": "application/json"
        }
        
        print("\n🧪 TESTING TABLES AFTER REFRESH")
        print("-" * 35)
        
        # Test basic DAX query
        url = f"{self.powerbi_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        test_queries = [
            ("Simple evaluation", "EVALUATE { 1 }"),
            ("Info tables", "EVALUATE INFO.TABLES()"),
            ("Info columns", "EVALUATE INFO.COLUMNS()"),
        ]
        
        for test_name, query in test_queries:
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
                        print(f"Result: {len(rows)} rows returned")
                        
                        # Show first few results
                        for i, row in enumerate(rows[:3], 1):
                            print(f"   {i}. {row}")
                        
                        if query == "EVALUATE INFO.TABLES()" and rows:
                            print(f"\n🎉 TABLES FOUND! {len(rows)} tables in semantic model")
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

def main():
    """Main comprehensive diagnostic"""
    print("🔬 COMPREHENSIVE MIRRORED DATABASE DIAGNOSTIC")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Final troubleshooting for mirrored database table access")
    print("🎯 Goal: Determine exactly why tables return 404 EntityNotFound")
    print()
    
    diagnostic = ComprehensiveMirroredDBDiagnostic()
    
    if not diagnostic.get_tokens():
        print("❌ Cannot proceed without tokens")
        return 1
    
    print()
    
    # Test SQL endpoint directly
    diagnostic.test_sql_endpoint_directly()
    
    # Check OneLake data
    diagnostic.check_onelake_data()
    
    # Force refresh with detailed monitoring
    success = diagnostic.force_semantic_model_refresh_with_debug()
    
    print()
    print("📊 FINAL DIAGNOSIS")
    print("=" * 20)
    
    if success:
        print("🎉 PROBLEM SOLVED!")
        print("   Mirrored database is now working correctly")
        print("   Tables are accessible via DAX queries")
        print("   Your NL2DAX application should now work")
    else:
        print("❌ ISSUE PERSISTS")
        print()
        print("🔧 REMAINING OPTIONS:")
        print("   1. Manual intervention in Fabric portal required")
        print("   2. Check source Azure SQL database accessibility")
        print("   3. Verify mirrored database configuration")
        print("   4. Contact Azure support if issue persists")
        print()
        print("📱 MANUAL STEPS:")
        print("   → Open https://app.fabric.microsoft.com")
        print("   → Go to FIS workspace")
        print("   → Check 'adventureworksdb' mirrored database")
        print("   → Verify connection to source Azure SQL")
        print("   → Check sync/replication status")
        print("   → Try manual refresh/sync if available")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
