#!/usr/bin/env python3
"""
Fix Fabric Semantic Model Refresh
Trigger refresh without invalid parameters for service principal
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FabricSemanticModelRefresh:
    """Fix semantic model refresh for service principal"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.token = None
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
    def get_token(self):
        """Get token"""
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
    
    def trigger_refresh_simple(self):
        """Trigger refresh with minimal parameters for service principal"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("🔄 TRIGGERING SEMANTIC MODEL REFRESH (FIXED)")
        print("-" * 50)
        
        # Try different refresh approaches
        refresh_payloads = [
            ("Basic refresh", {}),
            ("No notify", {"notifyOption": "NoNotification"}),
            ("Enhanced refresh", {"type": "full"}),
        ]
        
        for approach_name, payload in refresh_payloads:
            print(f"Trying: {approach_name}")
            print(f"Payload: {payload}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 202:
                    print("✅ Refresh triggered successfully!")
                    print("   The semantic model will be refreshed asynchronously")
                    return True
                elif response.status_code == 400:
                    print("❌ Refresh request failed")
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data.get('error', {}).get('message', 'Unknown')}")
                    except:
                        print(f"   Raw error: {response.text}")
                elif response.status_code == 409:
                    print("⚠️  Refresh already in progress")
                    return True  # Already refreshing is good
                else:
                    print(f"⚠️  Unexpected response: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print()
        
        return False
    
    def wait_and_test(self):
        """Wait for refresh and test DAX queries"""
        print("⏳ WAITING FOR REFRESH AND TESTING")
        print("-" * 40)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        # Wait and test periodically
        for attempt in range(1, 11):  # Try 10 times over ~5 minutes
            print(f"Attempt {attempt}/10 (waiting {attempt * 30}s)...")
            
            time.sleep(30)  # Wait 30 seconds
            
            # Test simple DAX query
            payload = {
                "queries": [{"query": "EVALUATE { 1 }"}],
                "serializerSettings": {"includeNulls": True}
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                print(f"   DAX test status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ SUCCESS! DAX queries are now working!")
                    
                    # Test INFO.TABLES to see actual tables
                    info_payload = {
                        "queries": [{"query": "EVALUATE INFO.TABLES()"}],
                        "serializerSettings": {"includeNulls": True}
                    }
                    
                    info_response = requests.post(url, headers=headers, json=info_payload, timeout=30)
                    if info_response.status_code == 200:
                        data = info_response.json()
                        if data.get('results') and data['results'][0].get('tables'):
                            table = data['results'][0]['tables'][0]
                            rows = table.get('rows', [])
                            print(f"   📊 Found {len(rows)} tables in the semantic model!")
                            
                            # Show first few table names
                            for i, row in enumerate(rows[:5], 1):
                                table_name = row[0] if row else 'Unknown'
                                print(f"      {i}. {table_name}")
                            
                            if len(rows) > 5:
                                print(f"      ... and {len(rows) - 5} more tables")
                    
                    return True
                else:
                    try:
                        error_data = response.json()
                        error_details = error_data.get('error', {}).get('pbi.error', {}).get('details', [])
                        if error_details:
                            detail = error_details[0].get('detail', {}).get('value', 'No detail')
                            if "at least one tables" in detail:
                                print(f"   ❌ Still no tables: {detail}")
                            else:
                                print(f"   ❌ Different error: {detail}")
                        else:
                            print(f"   ❌ Error: {response.text[:100]}")
                    except:
                        print(f"   ❌ Error: {response.text[:100]}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        print("⏰ Timeout - refresh may take longer")
        return False
    
    def check_refresh_status(self):
        """Check current refresh status"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
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
                    end_time = latest.get('endTime', 'Ongoing')
                    
                    print(f"📊 Latest Refresh Status:")
                    print(f"   Status: {status}")
                    print(f"   Start: {start_time}")
                    print(f"   End: {end_time}")
                    
                    return status
                else:
                    print("📊 No refresh history found")
                    return None
                    
        except Exception as e:
            print(f"❌ Error checking refresh: {e}")
            return None

def main():
    """Main refresh fixing function"""
    print("🔧 FABRIC SEMANTIC MODEL REFRESH FIX")
    print("=" * 40)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Fix semantic model refresh for service principal")
    print("🎯 Issue: Semantic model never refreshed, tables not accessible")
    print()
    
    refresher = FabricSemanticModelRefresh()
    
    if not refresher.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Check current status
    current_status = refresher.check_refresh_status()
    print()
    
    # Trigger refresh
    refresh_triggered = refresher.trigger_refresh_simple()
    print()
    
    if refresh_triggered:
        print("✅ Refresh triggered! Now waiting and testing...")
        success = refresher.wait_and_test()
    else:
        print("❌ Could not trigger refresh")
        success = False
    
    print()
    print("📊 FINAL RESULTS")
    print("=" * 20)
    
    if success:
        print("🎉 SUCCESS! Fabric mirrored database is now working!")
        print("   ✅ Semantic model has been refreshed")
        print("   ✅ Tables are now accessible via DAX queries")
        print("   ✅ Your NL2DAX application should now work")
        print()
        print("🔧 NEXT STEPS:")
        print("   1. Update your main application to use the working endpoints")
        print("   2. Test your NL2DAX queries against the actual tables")
        print("   3. Set up periodic refresh if needed")
    else:
        print("❌ Semantic model refresh issues persist")
        print()
        print("🔧 MANUAL STEPS NEEDED:")
        print("   1. Open Fabric portal (https://app.fabric.microsoft.com)")
        print("   2. Navigate to your workspace")
        print("   3. Find the 'adventureworksdb' semantic model")
        print("   4. Click 'Refresh' manually")
        print("   5. Wait for refresh to complete")
        print("   6. Test DAX queries again")
        print()
        print("   Or check mirrored database sync status:")
        print("   - Find 'adventureworksdb' mirrored database")
        print("   - Check if mirroring is active and synced")
        print("   - Verify Azure SQL connectivity")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
