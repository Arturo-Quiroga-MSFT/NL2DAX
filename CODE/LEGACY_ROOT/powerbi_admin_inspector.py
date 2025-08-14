#!/usr/bin/env python3
"""
Power BI Admin API Dataset Inspector
Use admin APIs to get detailed dataset information that regular APIs don't provide
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class PowerBIAdminInspector:
    """Use Power BI Admin APIs to inspect dataset details"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.token = None
        self.admin_url = "https://api.powerbi.com/v1.0/myorg/admin"
        
    def get_token_with_admin_scope(self):
        """Get token with admin scope (Tenant.Read.All)"""
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # For service principal, use the standard Power BI scope
            # Admin permissions are granted through Azure AD app permissions
            scopes = ["https://analysis.windows.net/powerbi/api/.default"]
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self.token = result["access_token"]
                print("✅ Token acquired with admin scope")
                return True
            else:
                print(f"❌ Admin token failed: {result.get('error_description', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"❌ Admin token error: {e}")
            return False
    
    def get_datasets_in_workspace_admin(self):
        """Get all datasets in workspace using admin API"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔍 ADMIN API: DATASETS IN WORKSPACE")
        print("-" * 45)
        
        # Basic admin call
        try:
            response = requests.get(
                f"{self.admin_url}/groups/{self.workspace_id}/datasets",
                headers=headers,
                timeout=30
            )
            
            print(f"Admin datasets status: {response.status_code}")
            
            if response.status_code == 200:
                datasets_data = response.json()
                datasets = datasets_data.get('value', [])
                
                print(f"✅ Found {len(datasets)} datasets in workspace")
                print()
                
                for i, dataset in enumerate(datasets, 1):
                    dataset_id = dataset.get('id', 'Unknown')
                    dataset_name = dataset.get('name', 'Unknown')
                    is_target = "🎯" if dataset_id == self.dataset_id else "📊"
                    
                    print(f"{is_target} Dataset {i}: {dataset_name}")
                    print(f"   ID: {dataset_id}")
                    
                    # Show key admin properties
                    admin_properties = [
                        'configuredBy', 'isRefreshable', 'isOnPremGatewayRequired',
                        'isEffectiveIdentityRequired', 'isEffectiveIdentityRolesRequired',
                        'addRowsAPIEnabled', 'isInPlaceSharingEnabled', 'targetStorageMode',
                        'contentProviderType', 'createdDate', 'description'
                    ]
                    
                    for prop in admin_properties:
                        if prop in dataset:
                            value = dataset[prop]
                            print(f"   {prop}: {value}")
                    
                    # Check for dataflows and dependencies
                    if 'upstreamDataflows' in dataset:
                        dataflows = dataset['upstreamDataflows']
                        if dataflows:
                            print(f"   upstreamDataflows: {len(dataflows)} dependencies")
                            for df in dataflows:
                                print(f"      → {df.get('targetDataflowId', 'Unknown')}")
                        else:
                            print(f"   upstreamDataflows: None")
                    
                    print()
                
                return datasets
                
            elif response.status_code == 403:
                print("❌ 403 Forbidden - Service principal may not have admin permissions")
                print("   Check Azure AD app registration for Tenant.Read.All permission")
                print("   And ensure admin consent has been granted")
            elif response.status_code == 401:
                print("❌ 401 Unauthorized - Token may not have admin scope")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        return []
    
    def get_dataset_details_with_expand(self):
        """Get dataset details with expanded properties"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔍 ADMIN API: DATASET DETAILS WITH EXPAND")
        print("-" * 50)
        
        # Try different expand options
        expand_options = [
            ("encryption", "encryption"),
            ("users", "users"),
            ("queryScaleOutSettings", "queryScaleOutSettings"),
            ("upstreamDataflows", "upstreamDataflows"),
            ("all", "encryption,users,queryScaleOutSettings,upstreamDataflows")
        ]
        
        for expand_name, expand_value in expand_options:
            print(f"Getting dataset with expand={expand_name}:")
            
            try:
                response = requests.get(
                    f"{self.admin_url}/groups/{self.workspace_id}/datasets",
                    headers=headers,
                    params={"$expand": expand_value, "$filter": f"id eq '{self.dataset_id}'"},
                    timeout=30
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    datasets = data.get('value', [])
                    
                    if datasets:
                        dataset = datasets[0]
                        print(f"   ✅ Dataset found with {expand_name} details")
                        
                        # Show expanded properties
                        if expand_name == "encryption" and 'encryption' in dataset:
                            encryption = dataset['encryption']
                            print(f"      Encryption Status: {encryption.get('encryptionStatus', 'Unknown')}")
                        
                        elif expand_name == "users" and 'users' in dataset:
                            users = dataset['users']
                            print(f"      Users: {len(users)} user entries")
                            for user in users[:3]:  # Show first 3
                                display_name = user.get('displayName', 'Unknown')
                                access_right = user.get('datasetUserAccessRight', 'Unknown')
                                principal_type = user.get('principalType', 'Unknown')
                                print(f"         → {display_name} ({principal_type}): {access_right}")
                        
                        elif expand_name == "queryScaleOutSettings" and 'queryScaleOutSettings' in dataset:
                            scale_out = dataset['queryScaleOutSettings']
                            print(f"      Auto Sync: {scale_out.get('autoSyncReadOnlyReplicas', 'Unknown')}")
                            print(f"      Max Replicas: {scale_out.get('maxReadOnlyReplicas', 'Unknown')}")
                        
                        elif expand_name == "upstreamDataflows" and 'upstreamDataflows' in dataset:
                            dataflows = dataset['upstreamDataflows']
                            print(f"      Upstream Dataflows: {len(dataflows)}")
                            for df in dataflows:
                                group_id = df.get('groupId', 'Unknown')
                                df_id = df.get('targetDataflowId', 'Unknown')
                                print(f"         → {df_id} (in {group_id})")
                        
                        elif expand_name == "all":
                            print("      Full dataset with all expansions:")
                            # Show any additional properties not shown in basic call
                            basic_props = {'id', 'name', 'configuredBy', 'isRefreshable', 'targetStorageMode'}
                            for key, value in dataset.items():
                                if key not in basic_props:
                                    if isinstance(value, (dict, list)):
                                        print(f"         {key}: {json.dumps(value, indent=12)[:150]}...")
                                    else:
                                        print(f"         {key}: {value}")
                    else:
                        print(f"   ❌ Target dataset not found with {expand_name}")
                        
                else:
                    print(f"   ❌ Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            print()
    
    def check_workspace_admin_info(self):
        """Get workspace information using admin API"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🏢 ADMIN API: WORKSPACE INFORMATION")
        print("-" * 42)
        
        try:
            response = requests.get(
                f"{self.admin_url}/groups/{self.workspace_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"Workspace admin info status: {response.status_code}")
            
            if response.status_code == 200:
                workspace = response.json()
                print("✅ Workspace Admin Details:")
                
                # Show all workspace properties
                for key, value in workspace.items():
                    if isinstance(value, (dict, list)):
                        print(f"   {key}: {json.dumps(value, indent=6)[:100]}...")
                    else:
                        print(f"   {key}: {value}")
                        
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    def check_mirrored_database_through_admin(self):
        """Try to find mirrored database info through admin APIs"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("🔍 ADMIN API: MIRRORED DATABASE DETECTION")
        print("-" * 50)
        
        # Check if there are any admin endpoints for mirrored databases
        admin_endpoints = [
            ("Workspace Info", f"/groups/{self.workspace_id}"),
            ("All Items", f"/groups/{self.workspace_id}/datasets"),  # Already called but check for other info
            ("Dataflows", f"/groups/{self.workspace_id}/dataflows"),
        ]
        
        for name, endpoint in admin_endpoints:
            if name == "All Items":
                continue  # Skip duplicate
                
            print(f"Checking {name}:")
            
            try:
                response = requests.get(
                    f"{self.admin_url}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'value' in data:  # List response
                        items = data['value']
                        print(f"   ✅ Found {len(items)} items")
                        
                        # Look for anything related to mirrored databases
                        for item in items:
                            item_type = item.get('type', item.get('objectType', 'Unknown'))
                            item_name = item.get('name', item.get('displayName', 'Unknown'))
                            
                            if 'mirror' in item_name.lower() or 'mirror' in str(item).lower():
                                print(f"      🔍 Potential mirrored item: {item_name} (type: {item_type})")
                            
                            # Check for specific properties that might indicate mirrored database
                            if any(key in item for key in ['oneLakeTablesPath', 'sqlEndpointProperties', 'mirroredDatabase']):
                                print(f"      🎯 Mirrored DB indicator found in: {item_name}")
                                for key in ['oneLakeTablesPath', 'sqlEndpointProperties', 'mirroredDatabase']:
                                    if key in item:
                                        print(f"         {key}: {item[key]}")
                    
                    else:  # Single object response
                        print(f"   ✅ Single object response")
                        # Check for mirrored database indicators
                        mirrored_indicators = ['oneLakeTablesPath', 'sqlEndpointProperties', 'mirroredDatabase']
                        for indicator in mirrored_indicators:
                            if indicator in data:
                                print(f"      {indicator}: {data[indicator]}")
                
                elif response.status_code == 404:
                    print(f"   ❌ {name} not available via admin API")
                else:
                    print(f"   ⚠️  Error {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            print()

def main():
    """Main admin API inspection function"""
    print("🔧 POWER BI ADMIN API DATASET INSPECTOR")
    print("=" * 45)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Use admin APIs to get detailed dataset information")
    print("🎯 Goal: Find clues about why mirrored database has no tables")
    print()
    
    inspector = PowerBIAdminInspector()
    
    if not inspector.get_token_with_admin_scope():
        print("❌ Cannot proceed without admin token")
        return 1
    
    print()
    
    # Get all datasets in workspace using admin API
    datasets = inspector.get_datasets_in_workspace_admin()
    print()
    
    # Get detailed dataset information with expand options
    inspector.get_dataset_details_with_expand()
    
    # Check workspace admin info
    inspector.check_workspace_admin_info()
    print()
    
    # Try to detect mirrored database through admin APIs
    inspector.check_mirrored_database_through_admin()
    
    print("🔍 ADMIN API INSIGHTS")
    print("=" * 25)
    print("Admin APIs provide additional dataset properties that may reveal:")
    print("   ✅ Configuration details not visible in regular APIs")
    print("   ✅ Storage mode and connection information") 
    print("   ✅ Dependency relationships with dataflows")
    print("   ✅ Refresh capabilities and requirements")
    print("   ✅ User access and permission details")
    print()
    print("Key properties to check:")
    print("   • targetStorageMode: Should show storage type")
    print("   • isOnPremGatewayRequired: Gateway dependency")
    print("   • upstreamDataflows: Data source dependencies")
    print("   • contentProviderType: May indicate mirrored source")
    print("   • isRefreshable: Refresh capability status")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0

if __name__ == "__main__":
    exit(main())
