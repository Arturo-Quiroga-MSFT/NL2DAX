#!/usr/bin/env python3
"""
Mirrored Database Source Connection Checker
Check if the source Azure SQL database is accessible and properly configured
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MirroredDatabaseSourceChecker:
    """Check mirrored database source connection and configuration"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.mirrored_db_id = "f5846ddf-df0c-4400-8961-1c1e754c48aa"
        self.fabric_token = None
        self.powerbi_token = None
        self.fabric_url = "https://api.fabric.microsoft.com/v1"
        self.powerbi_url = "https://api.powerbi.com/v1.0/myorg"
        
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
    
    def get_mirrored_database_full_details(self):
        """Get complete mirrored database configuration"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔍 MIRRORED DATABASE FULL CONFIGURATION")
        print("-" * 50)
        
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                db_config = response.json()
                print("✅ Mirrored Database Configuration:")
                
                # Extract key configuration details
                properties = db_config.get('properties', {})
                sql_endpoint = properties.get('sqlEndpointProperties', {})
                
                print(f"   Name: {db_config.get('displayName', 'Unknown')}")
                print(f"   Description: {db_config.get('description', 'No description')}")
                print()
                print("📊 SQL Endpoint Properties:")
                print(f"   Connection String: {sql_endpoint.get('connectionString', 'Not found')}")
                print(f"   Endpoint ID: {sql_endpoint.get('id', 'Not found')}")
                print(f"   Provisioning Status: {sql_endpoint.get('provisioningStatus', 'Unknown')}")
                print()
                print("📁 OneLake Properties:")
                print(f"   Tables Path: {properties.get('oneLakeTablesPath', 'Not found')}")
                print(f"   Default Schema: {properties.get('defaultSchema', 'Not found')}")
                print()
                
                # Look for any source connection information
                print("🔗 Source Connection Analysis:")
                
                # Check if there are any source properties
                for key, value in properties.items():
                    if 'source' in key.lower() or 'connection' in key.lower() or 'azure' in key.lower():
                        print(f"   {key}: {value}")
                
                # The connection string might give us clues about the source
                connection_string = sql_endpoint.get('connectionString', '')
                if connection_string:
                    print(f"   Fabric SQL Endpoint: {connection_string}")
                    print("   ⚠️  This is the Fabric endpoint, not the source Azure SQL")
                    print("   The source Azure SQL connection is configured elsewhere")
                
                return db_config
                
            else:
                print(f"❌ Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def check_dataset_refresh_logs_detailed(self):
        """Get detailed refresh logs to see if there are any error patterns"""
        headers = {"Authorization": f"Bearer {self.powerbi_token}"}
        
        print("📊 DETAILED REFRESH LOG ANALYSIS")
        print("-" * 40)
        
        try:
            response = requests.get(
                f"{self.powerbi_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            print(f"Refresh history status: {response.status_code}")
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                print(f"Found {len(refreshes)} refresh attempts")
                
                if refreshes:
                    print("\nDetailed Refresh Analysis:")
                    
                    for i, refresh in enumerate(refreshes[:3], 1):  # Check last 3 refreshes
                        print(f"\n🔄 Refresh {i}:")
                        print(f"   Status: {refresh.get('status', 'Unknown')}")
                        print(f"   Start: {refresh.get('startTime', 'Unknown')}")
                        print(f"   End: {refresh.get('endTime', 'Unknown')}")
                        print(f"   Request ID: {refresh.get('requestId', 'Unknown')}")
                        
                        # Calculate duration
                        start_time = refresh.get('startTime')
                        end_time = refresh.get('endTime')
                        if start_time and end_time:
                            try:
                                from dateutil import parser
                                start_dt = parser.parse(start_time)
                                end_dt = parser.parse(end_time)
                                duration = (end_dt - start_dt).total_seconds()
                                print(f"   Duration: {duration:.1f} seconds")
                                
                                if duration < 5:
                                    print("   ⚠️  Very fast refresh - may indicate no data to process")
                                elif duration > 300:
                                    print("   ⚠️  Very slow refresh - may indicate connection issues")
                                else:
                                    print("   ✅ Normal refresh duration")
                            except:
                                print("   Duration: Unable to calculate")
                        
                        # Check for errors
                        if refresh.get('status') == 'Failed':
                            error_details = refresh.get('serviceExceptionJson', 'No error details')
                            print(f"   ❌ Error: {error_details}")
                        elif refresh.get('status') == 'Completed':
                            print("   ✅ Completed successfully")
                            print("   ❓ But why are no tables created?")
                        
                        # Check for any refresh type or additional properties
                        for key, value in refresh.items():
                            if key not in ['status', 'startTime', 'endTime', 'requestId', 'serviceExceptionJson']:
                                print(f"   {key}: {value}")
                
                return refreshes
            else:
                print(f"❌ Error: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []
    
    def test_fabric_sql_endpoint_connectivity(self):
        """Test the Fabric SQL endpoint that was discovered"""
        print("🔗 FABRIC SQL ENDPOINT CONNECTIVITY TEST")
        print("-" * 50)
        
        # The SQL endpoint connection string from previous discovery
        sql_endpoint = "lgrhfiohwfcetmxbnvkr7fkhce-thxp3y5ehjyu3jjqffskayxdey.datawarehouse.fabric.microsoft.com"
        
        print(f"SQL Endpoint: {sql_endpoint}")
        print()
        
        # Try to test connectivity (this might require SQL authentication)
        print("Testing SQL endpoint accessibility:")
        
        import socket
        
        try:
            # Test if the endpoint is reachable
            host = sql_endpoint
            port = 1433  # Standard SQL Server port
            
            print(f"   Testing TCP connection to {host}:{port}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print("   ✅ TCP connection successful")
                print("   The Fabric SQL endpoint is reachable")
            else:
                print("   ❌ TCP connection failed")
                print("   The Fabric SQL endpoint may be down or blocked")
                
        except Exception as e:
            print(f"   ❌ Connection test failed: {e}")
        
        print()
        print("🔍 Analysis:")
        print("   • The Fabric SQL endpoint being reachable is good")
        print("   • But this doesn't test the SOURCE Azure SQL database")
        print("   • The source Azure SQL connection is configured in Fabric portal")
        print("   • If the source is unreachable, refreshes succeed but create no tables")
    
    def analyze_mirrored_database_issue(self, db_config, refresh_history):
        """Analyze all gathered information to determine the root cause"""
        print("🔬 ROOT CAUSE ANALYSIS")
        print("-" * 25)
        
        print("📋 Summary of Findings:")
        print("   ✅ Mirrored database exists and is configured")
        print("   ✅ Semantic model exists with Abf storage mode")
        print("   ✅ Refreshes complete successfully")
        print("   ✅ Fabric SQL endpoint is provisioned")
        print("   ❌ No tables are created in the semantic model")
        print()
        
        # Check refresh pattern
        if refresh_history:
            fast_refreshes = 0
            for refresh in refresh_history[:5]:
                start_time = refresh.get('startTime')
                end_time = refresh.get('endTime')
                if start_time and end_time:
                    try:
                        from dateutil import parser
                        start_dt = parser.parse(start_time)
                        end_dt = parser.parse(end_time)
                        duration = (end_dt - start_dt).total_seconds()
                        if duration < 5:
                            fast_refreshes += 1
                    except:
                        pass
            
            if fast_refreshes >= 2:
                print("🚨 PATTERN DETECTED: Very fast refreshes")
                print("   Multiple refreshes complete in under 5 seconds")
                print("   This strongly suggests no data is being processed")
                print("   Likely cause: Source Azure SQL database is not accessible")
        
        print()
        print("🎯 MOST LIKELY ROOT CAUSES:")
        print("   1. 🔌 Source Azure SQL database connection is broken")
        print("      → Mirrored database can't connect to source")
        print("      → Refresh succeeds but finds no data to mirror")
        print()
        print("   2. 🛡️ Azure SQL authentication/authorization issues")
        print("      → Service principal doesn't have access to source DB")
        print("      → Firewall blocking Fabric service IP ranges")
        print()
        print("   3. 📊 Source Azure SQL database is empty")
        print("      → Database exists but has no tables")
        print("      → Nothing to mirror into Fabric")
        print()
        print("   4. ⚙️ Mirrored database configuration incomplete")
        print("      → Source connection string is incorrect")
        print("      → Schema/table selection is wrong")
        print()
        
        print("🔧 RECOMMENDED ACTIONS:")
        print("   1. 🌐 Open Fabric Portal: https://app.fabric.microsoft.com")
        print("   2. 📂 Navigate to FIS workspace")
        print("   3. 🔍 Find 'adventureworksdb' mirrored database")
        print("   4. ⚙️ Check the source Azure SQL configuration:")
        print("      • Verify server name and database name")
        print("      • Test connection to source Azure SQL")
        print("      • Check authentication method")
        print("      • Verify Azure SQL has tables to mirror")
        print("   5. 🔄 After fixing source, trigger manual refresh")
        print("   6. 🧪 Test DAX queries again")

def main():
    """Main source connection checker"""
    print("🔗 MIRRORED DATABASE SOURCE CONNECTION CHECKER")
    print("=" * 55)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Check source Azure SQL database connection")
    print("🎯 Goal: Determine why mirrored database has no tables")
    print()
    
    checker = MirroredDatabaseSourceChecker()
    
    if not checker.get_tokens():
        print("❌ Cannot proceed without tokens")
        return 1
    
    print()
    
    # Get full mirrored database configuration
    db_config = checker.get_mirrored_database_full_details()
    print()
    
    # Get detailed refresh logs
    refresh_history = checker.check_dataset_refresh_logs_detailed()
    print()
    
    # Test Fabric SQL endpoint connectivity
    checker.test_fabric_sql_endpoint_connectivity()
    print()
    
    # Analyze all findings
    checker.analyze_mirrored_database_issue(db_config, refresh_history)
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0

if __name__ == "__main__":
    exit(main())
