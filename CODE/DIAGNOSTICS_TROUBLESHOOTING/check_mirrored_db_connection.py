#!/usr/bin/env python3
"""
Check Mirrored Database Connection Status
Verify if the mirrored database is actually connected to Azure SQL
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MirroredDatabaseConnectionChecker:
    """Check mirrored database connection to Azure SQL"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.mirrored_db_id = "f5846ddf-df0c-4400-8961-1c1e754c48aa"  # From previous discovery
        self.fabric_token = None
        self.fabric_url = "https://api.fabric.microsoft.com/v1"
        
    def get_token(self):
        """Get Fabric token"""
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Try Fabric scope first
            result = app.acquire_token_for_client(
                scopes=["https://api.fabric.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                self.fabric_token = result["access_token"]
                print("✅ Fabric token acquired")
                return True
            
            # Fallback to Power BI scope
            result = app.acquire_token_for_client(
                scopes=["https://analysis.windows.net/powerbi/api/.default"]
            )
            
            if "access_token" in result:
                self.fabric_token = result["access_token"]
                print("✅ Power BI token acquired (for Fabric APIs)")
                return True
            
            print(f"❌ Token failed: {result.get('error_description', 'Unknown')}")
            return False
                
        except Exception as e:
            print(f"❌ Token error: {e}")
            return False
    
    def check_mirrored_database_status(self):
        """Get comprehensive mirrored database status"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔍 MIRRORED DATABASE CONNECTION STATUS")
        print("-" * 50)
        
        # Get basic info
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"Basic info status: {response.status_code}")
            
            if response.status_code == 200:
                db_info = response.json()
                print("✅ Mirrored Database Found:")
                print(f"   Name: {db_info.get('displayName', 'Unknown')}")
                print(f"   Description: {db_info.get('description', 'No description')}")
                
                # Look for connection properties
                for key, value in db_info.items():
                    if key not in ['id', 'displayName', 'type', 'workspaceId']:
                        print(f"   {key}: {value}")
                        
            else:
                print(f"❌ Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
        
        print()
        
        # Try to get connection details or status
        status_endpoints = [
            ("Connection Details", f"/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}/status"),
            ("Tables", f"/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}/tables"),
            ("Sync Status", f"/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}/sync"),
            ("Replication", f"/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}/replication"),
        ]
        
        for name, endpoint in status_endpoints:
            print(f"Checking {name}:")
            
            try:
                response = requests.get(
                    f"{self.fabric_url}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {name} found:")
                    
                    # Pretty print the response
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, (dict, list)):
                                print(f"      {key}: {json.dumps(value, indent=8)[:200]}...")
                            else:
                                print(f"      {key}: {value}")
                    elif isinstance(data, list):
                        print(f"      Found {len(data)} items")
                        for i, item in enumerate(data[:3], 1):
                            if isinstance(item, dict):
                                name_key = item.get('name', item.get('displayName', f'Item {i}'))
                                print(f"         {i}. {name_key}")
                            else:
                                print(f"         {i}. {item}")
                    
                elif response.status_code == 404:
                    print(f"   ❌ {name} not available (404)")
                elif response.status_code == 400:
                    print(f"   ⚠️  {name} bad request (400) - may not be supported")
                    try:
                        error = response.json()
                        error_msg = error.get('message', response.text[:100])
                        print(f"      Error: {error_msg}")
                    except:
                        print(f"      Raw error: {response.text[:100]}")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
                    print(f"      Response: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            print()
    
    def check_workspace_capacity(self):
        """Check if workspace has proper capacity for mirrored databases"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("⚡ WORKSPACE CAPACITY CHECK")
        print("-" * 35)
        
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"Workspace info status: {response.status_code}")
            
            if response.status_code == 200:
                workspace = response.json()
                print("✅ Workspace Details:")
                print(f"   Name: {workspace.get('displayName', 'Unknown')}")
                print(f"   ID: {workspace.get('id', 'Unknown')}")
                
                # Check capacity assignment
                capacity_id = workspace.get('capacityId')
                if capacity_id:
                    print(f"   ✅ Capacity ID: {capacity_id}")
                    print("   Workspace has capacity (required for mirrored databases)")
                else:
                    print("   ❌ NO CAPACITY ASSIGNED!")
                    print("   Mirrored databases require Premium/Fabric capacity")
                    print("   This could be why replication is not working")
                
                # Check other relevant properties
                for key, value in workspace.items():
                    if key in ['type', 'state', 'isReadOnly', 'licenseMode']:
                        print(f"   {key}: {value}")
                        
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    def test_manual_sync(self):
        """Try to manually trigger sync if possible"""
        headers = {
            "Authorization": f"Bearer {self.fabric_token}",
            "Content-Type": "application/json"
        }
        
        print("🔄 TESTING MANUAL SYNC")
        print("-" * 25)
        
        sync_endpoints = [
            ("Start Sync", "POST", f"/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}/sync"),
            ("Refresh Mirrored DB", "POST", f"/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}/refresh"),
            ("Update Schema", "POST", f"/workspaces/{self.workspace_id}/mirroreddatabases/{self.mirrored_db_id}/updateSchema"),
        ]
        
        for name, method, endpoint in sync_endpoints:
            print(f"Trying {name} ({method}):")
            
            try:
                if method == "POST":
                    response = requests.post(
                        f"{self.fabric_url}{endpoint}",
                        headers=headers,
                        json={},  # Empty payload
                        timeout=30
                    )
                else:
                    response = requests.get(
                        f"{self.fabric_url}{endpoint}",
                        headers=headers,
                        timeout=30
                    )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code in [200, 202]:
                    print(f"   ✅ {name} successful!")
                    try:
                        data = response.json()
                        print(f"   Response: {json.dumps(data, indent=6)[:200]}")
                    except:
                        print(f"   Response: {response.text[:100]}")
                elif response.status_code == 404:
                    print(f"   ❌ {name} not available")
                elif response.status_code == 400:
                    print(f"   ⚠️  {name} bad request")
                    try:
                        error = response.json()
                        print(f"      Error: {error.get('message', response.text[:100])}")
                    except:
                        print(f"      Raw error: {response.text[:100]}")
                else:
                    print(f"   ⚠️  Status {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            print()

def main():
    """Main connection checker function"""
    print("🔌 MIRRORED DATABASE CONNECTION CHECKER")
    print("=" * 45)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Check if mirrored database is properly connected to Azure SQL")
    print("🎯 Issue: Refreshes succeed but no tables are created")
    print()
    
    checker = MirroredDatabaseConnectionChecker()
    
    if not checker.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print()
    
    # Check workspace capacity first
    checker.check_workspace_capacity()
    print()
    
    # Check mirrored database status
    checker.check_mirrored_database_status()
    print()
    
    # Test manual sync options
    checker.test_manual_sync()
    print()
    
    print("🔧 RECOMMENDATIONS")
    print("=" * 20)
    print("1. ✅ Check workspace capacity assignment")
    print("2. 🔍 Verify Azure SQL database connectivity") 
    print("3. 🔌 Check mirrored database connection string")
    print("4. 🔄 Try manual sync/refresh in Fabric portal")
    print("5. 📊 Verify source tables exist in Azure SQL")
    print("6. 🛡️  Check Azure SQL firewall and authentication")
    print()
    print("Next: Open Fabric portal to manually inspect the mirrored database configuration")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0

if __name__ == "__main__":
    exit(main())
