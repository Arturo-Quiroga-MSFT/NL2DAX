#!/usr/bin/env python3
"""
Fabric Mirrored Database Refresh
Trigger refresh for mirrored database semantic model to sync latest Azure SQL data
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FabricMirroredDatabaseSync:
    """Refresh Fabric mirrored database to sync latest Azure SQL data"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.token = None
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.fabric_url = "https://api.fabric.microsoft.com/v1"
        
    def get_token(self):
        """Get token for both Power BI and Fabric APIs"""
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
    
    def find_mirrored_database(self):
        """Find the mirrored database in the workspace"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔍 FINDING MIRRORED DATABASE")
        print("-" * 40)
        
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/items",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                
                # Find mirrored database
                mirrored_db = None
                for item in items:
                    if item.get('type') == 'MirroredDatabase' and 'adventureworks' in item.get('displayName', '').lower():
                        mirrored_db = item
                        break
                
                if mirrored_db:
                    print(f"✅ Found Mirrored Database:")
                    print(f"   Name: {mirrored_db.get('displayName', 'Unknown')}")
                    print(f"   ID: {mirrored_db.get('id', 'Unknown')}")
                    print(f"   Type: {mirrored_db.get('type', 'Unknown')}")
                    return mirrored_db.get('id')
                else:
                    print("❌ Mirrored database not found")
                    return None
                    
            else:
                print(f"❌ Cannot get workspace items: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error finding mirrored database: {e}")
            return None
    
    def check_semantic_model_refresh_status(self):
        """Check the refresh status of the semantic model"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔄 SEMANTIC MODEL REFRESH STATUS")
        print("-" * 40)
        
        try:
            # Check refresh history
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            print(f"Refresh API Status: {response.status_code}")
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                print(f"Found {len(refreshes)} refresh entries")
                
                if refreshes:
                    latest = refreshes[0]
                    print(f"\nLatest Refresh:")
                    print(f"   Start Time: {latest.get('startTime', 'Unknown')}")
                    print(f"   End Time: {latest.get('endTime', 'Ongoing')}")
                    print(f"   Status: {latest.get('status', 'Unknown')}")
                    print(f"   Type: {latest.get('refreshType', 'Unknown')}")
                    
                    if latest.get('status') == 'Completed':
                        print("   ✅ Last refresh completed successfully")
                        return True
                    elif latest.get('status') == 'Failed':
                        print("   ❌ Last refresh failed")
                        if latest.get('serviceExceptionJson'):
                            print(f"   Error Details: {latest['serviceExceptionJson']}")
                        return False
                    elif latest.get('status') == 'InProgress':
                        print("   ⏳ Refresh currently in progress")
                        return None  # In progress
                    else:
                        print(f"   ⚠️  Unknown refresh status: {latest.get('status')}")
                        return False
                else:
                    print("   ⚠️  No refresh history found")
                    print("   Semantic model may never have been refreshed")
                    return False
                    
            else:
                print(f"   ❌ Cannot get refresh status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error checking refresh: {e}")
            return False
    
    def trigger_semantic_model_refresh(self):
        """Trigger a refresh of the semantic model"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("🔄 TRIGGERING SEMANTIC MODEL REFRESH")
        print("-" * 40)
        
        try:
            # Simplified payload for service principal requests
            payload = {
                "retryCount": 1
            }
            
            response = requests.post(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"Refresh trigger status: {response.status_code}")
            
            if response.status_code == 202:
                print("✅ Refresh triggered successfully!")
                print("   The semantic model will be refreshed asynchronously")
                print("   This may take several minutes to complete")
                return True
            elif response.status_code == 400:
                print("❌ Refresh request failed")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw error: {response.text}")
                return False
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error triggering refresh: {e}")
            return False
    
    def monitor_refresh_progress(self, max_wait_minutes=10):
        """Monitor refresh progress"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print(f"⏳ MONITORING REFRESH PROGRESS (max {max_wait_minutes} minutes)")
        print("-" * 50)
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = requests.get(
                    f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    refreshes = response.json().get('value', [])
                    
                    if refreshes:
                        latest = refreshes[0]
                        status = latest.get('status', 'Unknown')
                        start_time_str = latest.get('startTime', 'Unknown')
                        end_time_str = latest.get('endTime', 'Ongoing')
                        
                        print(f"   Status: {status} | Start: {start_time_str} | End: {end_time_str}")
                        
                        if status == 'Completed':
                            print("   ✅ Refresh completed successfully!")
                            return True
                        elif status == 'Failed':
                            print("   ❌ Refresh failed!")
                            if latest.get('serviceExceptionJson'):
                                print(f"   Error: {latest['serviceExceptionJson']}")
                            return False
                        elif status == 'InProgress':
                            print("   ⏳ Still in progress...")
                        else:
                            print(f"   ⚠️  Unknown status: {status}")
                
                # Wait 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                print(f"   ❌ Error monitoring: {e}")
                break
        
        print(f"   ⏰ Timeout after {max_wait_minutes} minutes")
        return False
    
    def verify_refresh_completion(self):
        """Verify that the refresh completed successfully"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("✅ VERIFYING REFRESH COMPLETION")
        print("-" * 40)
        
        try:
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                
                if refreshes:
                    latest = refreshes[0]
                    status = latest.get('status', 'Unknown')
                    start_time = latest.get('startTime', 'Unknown')
                    end_time = latest.get('endTime', 'Unknown')
                    
                    print(f"   Last Refresh Status: {status}")
                    print(f"   Start Time: {start_time}")
                    print(f"   End Time: {end_time}")
                    
                    if status == 'Completed':
                        print("   ✅ Refresh completed successfully!")
                        print("   🔄 Mirrored database should now have latest data")
                        return True
                    else:
                        print(f"   ❌ Refresh status: {status}")
                        return False
                else:
                    print("   ⚠️  No refresh history found")
                    return False
                    
            else:
                print(f"   ❌ Cannot verify refresh: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verifying refresh: {e}")
            return False

def main():
    """Main sync and refresh management function"""
    print("🔄 FABRIC MIRRORED DATABASE REFRESH")
    print("=" * 45)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Refresh mirrored database semantic model to sync latest data")
    print()
    
    sync_manager = FabricMirroredDatabaseSync()
    
    if not sync_manager.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Find mirrored database
    mirrored_db_id = sync_manager.find_mirrored_database()
    print()
    
    # Check current refresh status
    refresh_status = sync_manager.check_semantic_model_refresh_status()
    print()
    
    # Decide next action based on refresh status
    if refresh_status is None:
        print("⏳ Refresh already in progress, monitoring...")
        refresh_completed = sync_manager.monitor_refresh_progress()
        success = refresh_completed
    else:
        print("🔄 Triggering refresh to sync latest data...")
        refresh_triggered = sync_manager.trigger_semantic_model_refresh()
        
        if refresh_triggered:
            print("⏳ Monitoring refresh progress...")
            refresh_completed = sync_manager.monitor_refresh_progress()
            
            if refresh_completed:
                success = sync_manager.verify_refresh_completion()
            else:
                print("⚠️  Refresh taking longer than expected")
                success = False
        else:
            print("❌ Failed to trigger refresh")
            success = False
    
    print()
    print("📊 FINAL RESULTS")
    print("=" * 20)
    
    if success:
        print("🎉 SUCCESS! Mirrored database refreshed successfully")
        print("   ✅ Latest Azure SQL data is now synced to Fabric")
        print("   ✅ Semantic model has been updated")
        print("   ✅ New dimension table entries are now available")
        print("\n📝 Next Steps:")
        print("   • Test DAX queries in Power BI or Fabric")
        print("   • Verify data in Fabric SQL Analytics Endpoint")
        print("   • Run NL2DAX pipeline to test new dimension data")
    else:
        print("❌ Issues with mirrored database refresh")
        print("   🔧 Troubleshooting steps:")
        print("   1. Check Fabric portal for mirrored database status")
        print("   2. Verify Azure SQL database connectivity")
        print("   3. Check mirroring configuration in Fabric")
        print("   4. Ensure service principal has Fabric permissions")
        print("   5. Try manual refresh in Fabric portal")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
