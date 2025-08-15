#!/usr/bin/env python3
"""
Check Mirrored Database Status and Fix Issues
Diagnose why tables are not appearing in Fabric mirrored database
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MirroredDatabaseChecker:
    """Check and fix mirrored database replication status"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.fabric_token = None
        self.powerbi_token = None
        self.fabric_url = "https://api.fabric.microsoft.com/v1"
        self.powerbi_url = "https://api.powerbi.com/v1.0/myorg"
        
    def get_tokens(self):
        """Get both Fabric and Power BI tokens"""
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
            
            # Fabric token (try Fabric scope, fallback to Power BI)
            fabric_result = app.acquire_token_for_client(
                scopes=["https://api.fabric.microsoft.com/.default"]
            )
            
            if "access_token" in fabric_result:
                self.fabric_token = fabric_result["access_token"]
                print("✅ Fabric token acquired")
            else:
                print("⚠️  Fabric scope failed, using Power BI token for Fabric APIs")
                self.fabric_token = self.powerbi_token
            
            return True
                
        except Exception as e:
            print(f"❌ Token error: {e}")
            return False
    
    def find_mirrored_database(self):
        """Find the mirrored database in the workspace"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🔍 FINDING MIRRORED DATABASE")
        print("-" * 40)
        
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/items",
                headers=headers,
                timeout=30
            )
            
            print(f"Workspace items status: {response.status_code}")
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                print(f"Found {len(items)} total items")
                
                # Find mirrored databases
                mirrored_dbs = []
                semantic_models = []
                
                for item in items:
                    item_type = item.get('type', 'Unknown')
                    item_name = item.get('displayName', 'Unknown')
                    item_id = item.get('id', 'Unknown')
                    
                    if item_type == 'MirroredDatabase':
                        mirrored_dbs.append(item)
                        print(f"   📊 Mirrored DB: {item_name} (ID: {item_id})")
                    elif item_type == 'SemanticModel':
                        semantic_models.append(item)
                        if item_id == self.dataset_id:
                            print(f"   🎯 Target Semantic Model: {item_name} (ID: {item_id})")
                        else:
                            print(f"   📈 Other Semantic Model: {item_name} (ID: {item_id})")
                
                print(f"\nSummary:")
                print(f"   Mirrored Databases: {len(mirrored_dbs)}")
                print(f"   Semantic Models: {len(semantic_models)}")
                
                return mirrored_dbs, semantic_models
                
            else:
                print(f"❌ Error: {response.text}")
                return [], []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return [], []
    
    def check_mirrored_db_details(self, mirrored_db_id):
        """Get detailed status of a mirrored database"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print(f"🔍 CHECKING MIRRORED DATABASE DETAILS")
        print("-" * 50)
        
        try:
            response = requests.get(
                f"{self.fabric_url}/workspaces/{self.workspace_id}/mirroreddatabases/{mirrored_db_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                db_info = response.json()
                print("✅ Mirrored Database Details:")
                print(f"   Name: {db_info.get('displayName', 'Unknown')}")
                print(f"   ID: {db_info.get('id', 'Unknown')}")
                print(f"   Type: {db_info.get('type', 'Unknown')}")
                print(f"   Workspace: {db_info.get('workspaceId', 'Unknown')}")
                
                # Check if there's status info
                if 'status' in db_info:
                    status = db_info['status']
                    print(f"   Status: {status}")
                
                return db_info
            else:
                print(f"❌ Error getting details: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def check_semantic_model_structure(self):
        """Check if semantic model has any structure"""
        headers = {"Authorization": f"Bearer {self.fabric_token}"}
        
        print("🏗️ SEMANTIC MODEL STRUCTURE CHECK")
        print("-" * 45)
        
        endpoints_to_check = [
            ("Tables", f"/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}/tables"),
            ("Measures", f"/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}/measures"),
            ("Relationships", f"/workspaces/{self.workspace_id}/semanticModels/{self.dataset_id}/relationships"),
        ]
        
        structure_found = False
        
        for name, endpoint in endpoints_to_check:
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
                    items = data.get('value', [])
                    print(f"   ✅ Found {len(items)} {name.lower()}")
                    
                    if items:
                        structure_found = True
                        # Show first few items
                        for i, item in enumerate(items[:3], 1):
                            item_name = item.get('name', item.get('displayName', 'Unknown'))
                            print(f"      {i}. {item_name}")
                        
                        if len(items) > 3:
                            print(f"      ... and {len(items) - 3} more")
                    
                elif response.status_code == 404:
                    print(f"   ❌ {name} not found (404) - likely empty semantic model")
                else:
                    print(f"   ⚠️  Error: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            print()
        
        return structure_found
    
    def check_dataset_refresh_history(self):
        """Check Power BI dataset refresh history"""
        headers = {"Authorization": f"Bearer {self.powerbi_token}"}
        
        print("📊 DATASET REFRESH HISTORY")
        print("-" * 30)
        
        try:
            response = requests.get(
                f"{self.powerbi_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                headers=headers,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                print(f"Found {len(refreshes)} refresh attempts")
                
                if refreshes:
                    print("\nRecent refreshes:")
                    for i, refresh in enumerate(refreshes[:5], 1):
                        status = refresh.get('status', 'Unknown')
                        start_time = refresh.get('startTime', 'Unknown')
                        end_time = refresh.get('endTime', 'In progress')
                        request_id = refresh.get('requestId', 'Unknown')
                        
                        print(f"   {i}. Status: {status}")
                        print(f"      Start: {start_time}")
                        print(f"      End: {end_time}")
                        print(f"      Request: {request_id}")
                        print()
                        
                        if status == "Failed" and 'serviceExceptionJson' in refresh:
                            error = refresh['serviceExceptionJson']
                            print(f"      Error: {error}")
                            print()
                else:
                    print("❌ NO REFRESH HISTORY FOUND")
                    print("   This explains why tables are not available!")
                    print("   The semantic model has never been successfully refreshed")
                
                return refreshes
            else:
                print(f"❌ Error: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []
    
    def try_manual_refresh(self):
        """Try to trigger a manual refresh without problematic parameters"""
        headers = {
            "Authorization": f"Bearer {self.powerbi_token}",
            "Content-Type": "application/json"
        }
        
        print("🔄 ATTEMPTING MANUAL REFRESH")
        print("-" * 35)
        
        # Try different refresh approaches
        refresh_attempts = [
            ("Empty payload", {}),
            ("No notification", {"notifyOption": "NoNotification"}),
            ("Full refresh", {"type": "full"}),
        ]
        
        for attempt_name, payload in refresh_attempts:
            print(f"Trying: {attempt_name}")
            print(f"Payload: {json.dumps(payload)}")
            
            try:
                response = requests.post(
                    f"{self.powerbi_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/refreshes",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 202:
                    print("✅ Refresh triggered successfully!")
                    return True
                elif response.status_code == 409:
                    print("⚠️  Refresh already in progress")
                    return True
                else:
                    print(f"❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
            
            print()
        
        return False

def main():
    """Main diagnostic function"""
    print("🔍 MIRRORED DATABASE STATUS CHECKER")
    print("=" * 45)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Diagnose why semantic model tables return 404")
    print("🎯 Issue: EntityNotFound when accessing /tables endpoint")
    print()
    
    checker = MirroredDatabaseChecker()
    
    if not checker.get_tokens():
        print("❌ Cannot proceed without tokens")
        return 1
    
    print()
    
    # Find mirrored databases
    mirrored_dbs, semantic_models = checker.find_mirrored_database()
    print()
    
    # Check mirrored database details if found
    if mirrored_dbs:
        main_db = mirrored_dbs[0]  # Use first one found
        db_id = main_db.get('id')
        print(f"Checking details for: {main_db.get('displayName', 'Unknown')}")
        db_details = checker.check_mirrored_db_details(db_id)
        print()
    
    # Check semantic model structure
    structure_exists = checker.check_semantic_model_structure()
    print()
    
    # Check refresh history
    refresh_history = checker.check_dataset_refresh_history()
    print()
    
    # Analyze results
    print("🔬 DIAGNOSIS")
    print("=" * 15)
    
    if not refresh_history:
        print("❌ ROOT CAUSE IDENTIFIED: NO REFRESH HISTORY")
        print("   The semantic model has NEVER been refreshed")
        print("   This is why the /tables endpoint returns 404")
        print("   Mirrored databases require at least one successful refresh")
        print("   to populate the semantic model with table metadata")
        print()
        
        # Try to trigger refresh
        print("🔧 ATTEMPTING TO FIX...")
        refresh_triggered = checker.try_manual_refresh()
        
        if refresh_triggered:
            print()
            print("✅ REFRESH TRIGGERED!")
            print("   Wait 5-10 minutes for the refresh to complete")
            print("   Then rerun this script to verify tables are accessible")
        else:
            print()
            print("❌ COULD NOT TRIGGER REFRESH AUTOMATICALLY")
            print("   Manual action required:")
            print("   1. Open Fabric portal (https://app.fabric.microsoft.com)")
            print("   2. Navigate to your workspace")
            print("   3. Find the 'adventureworksdb' semantic model")
            print("   4. Click 'Refresh' button")
            print("   5. Wait for completion")
            print("   6. Rerun this script to verify")
    
    elif not structure_exists:
        print("⚠️  SEMANTIC MODEL EXISTS BUT NO STRUCTURE FOUND")
        print("   Recent refreshes exist but they may have failed")
        print("   Check the refresh error details above")
        print("   The mirrored database connection may be broken")
    
    else:
        print("✅ SEMANTIC MODEL HAS STRUCTURE")
        print("   The 404 error might be intermittent")
        print("   Try the DAX queries again")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0

if __name__ == "__main__":
    exit(main())
