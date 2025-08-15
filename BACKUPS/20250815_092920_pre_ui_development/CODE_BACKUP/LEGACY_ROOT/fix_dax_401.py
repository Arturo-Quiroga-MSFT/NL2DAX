#!/usr/bin/env python3
"""
Advanced diagnostic and fix script for Power BI DAX execution 401 errors
Based on Microsoft documentation and best practices
"""

import os
import requests
import msal
from dotenv import load_dotenv
import json
import jwt
from datetime import datetime

# Load environment variables
load_dotenv()

class PowerBIDAXTroubleshooter:
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID") or os.getenv("POWER_BI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID") or os.getenv("POWER_BI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET") or os.getenv("POWER_BI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID") or os.getenv("POWER_BI_WORKSPACE_ID")
        self.dataset_id = os.getenv("PBI_DATASET_ID") or os.getenv("POWER_BI_DATASET_ID")
        
        print(f"🔧 Configuration Check:")
        print(f"   Tenant ID: {self.tenant_id[:8] + '...' if self.tenant_id else 'NOT SET'}")
        print(f"   Client ID: {self.client_id[:8] + '...' if self.client_id else 'NOT SET'}")
        print(f"   Workspace ID: {self.workspace_id[:8] + '...' if self.workspace_id else 'NOT SET'}")
        print(f"   Dataset ID: {self.dataset_id[:8] + '...' if self.dataset_id else 'NOT SET'}")
        
    def get_token(self, scope="https://analysis.windows.net/powerbi/api/.default"):
        """Get access token with proper scope"""
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret,
        )
        
        result = app.acquire_token_for_client(scopes=[scope])
        if result and "access_token" in result:
            return result["access_token"]
        else:
            raise RuntimeError(f"Failed to get token: {result}")
    
    def analyze_token(self):
        """Analyze the JWT token for issues"""
        print(f"\n🔍 JWT Token Analysis")
        print("=" * 50)
        
        try:
            token = self.get_token()
            
            # Decode JWT without verification to inspect claims
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            print(f"✅ Token acquired successfully")
            print(f"   Issuer (iss): {decoded.get('iss', 'NOT SET')}")
            print(f"   Audience (aud): {decoded.get('aud', 'NOT SET')}")
            print(f"   Application ID (appid): {decoded.get('appid', 'NOT SET')}")
            print(f"   Object ID (oid): {decoded.get('oid', 'NOT SET')}")
            print(f"   Tenant ID (tid): {decoded.get('tid', 'NOT SET')}")
            print(f"   Expires: {datetime.fromtimestamp(decoded.get('exp', 0))}")
            
            # Check for common issues
            issues = []
            
            if decoded.get('aud') != "https://analysis.windows.net/powerbi/api":
                issues.append("❌ Incorrect audience - should be https://analysis.windows.net/powerbi/api")
            else:
                print("✅ Audience is correct")
                
            if not decoded.get('oid'):
                issues.append("❌ Missing Object ID (oid) claim - service principal not properly configured")
            else:
                print("✅ Object ID (oid) present")
                
            if decoded.get('tid') != self.tenant_id:
                issues.append("❌ Token tenant ID doesn't match configured tenant ID")
            else:
                print("✅ Tenant ID matches")
                
            if issues:
                print("\n⚠️  TOKEN ISSUES FOUND:")
                for issue in issues:
                    print(f"   {issue}")
            else:
                print("\n✅ Token appears valid")
                
            return token, decoded
            
        except Exception as e:
            print(f"❌ Token analysis failed: {str(e)}")
            return None, None
    
    def check_dataset_permissions(self):
        """Check specific dataset permissions for service principal"""
        print(f"\n🔍 Dataset Permission Analysis")
        print("=" * 50)
        
        try:
            token = self.get_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Get dataset details
            dataset_url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}"
            response = requests.get(dataset_url, headers=headers)
            
            if response.status_code == 200:
                dataset_info = response.json()
                print(f"✅ Dataset accessible: {dataset_info.get('name', 'Unknown')}")
                print(f"   Created by: {dataset_info.get('configuredBy', 'Unknown')}")
                print(f"   Is refreshable: {dataset_info.get('isRefreshable', 'Unknown')}")
                
                # Check XMLA endpoint setting
                xmla_enabled = dataset_info.get('isXmlaEndpointEnabled')
                if xmla_enabled is not None:
                    if xmla_enabled:
                        print(f"✅ XMLA endpoint is enabled")
                    else:
                        print(f"❌ XMLA endpoint is disabled")
                else:
                    print(f"⚠️  XMLA endpoint status unknown")
            
            # Get dataset permissions
            permissions_url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/users"
            response = requests.get(permissions_url, headers=headers)
            
            if response.status_code == 200:
                permissions = response.json().get('value', [])
                print(f"\n📋 Dataset Permissions ({len(permissions)} users):")
                
                service_principal_found = False
                service_principal_permissions = None
                
                for perm in permissions:
                    identifier = perm.get('identifier', '')
                    principal_type = perm.get('principalType', '')
                    access_right = perm.get('datasetUserAccessRight', '')
                    
                    print(f"   - {identifier} ({principal_type}): {access_right}")
                    
                    # Check if this is our service principal
                    if principal_type == 'App' and identifier == self.client_id:
                        service_principal_found = True
                        service_principal_permissions = access_right
                
                if service_principal_found:
                    print(f"\n✅ Service principal found with permissions: {service_principal_permissions}")
                    
                    # Check if permissions are sufficient for DAX queries
                    if service_principal_permissions in ['ReadWriteReshareExplore', 'Build']:
                        print(f"✅ Permissions sufficient for DAX execution")
                    else:
                        print(f"❌ Insufficient permissions for DAX execution")
                        print(f"   Current: {service_principal_permissions}")
                        print(f"   Required: Build or ReadWriteReshareExplore")
                        return False
                else:
                    print(f"\n❌ Service principal not found in dataset permissions")
                    print(f"   Looking for Client ID: {self.client_id}")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"❌ Permission check failed: {str(e)}")
            return False
    
    def test_alternative_scopes(self):
        """Test different token scopes that might work for DAX execution"""
        print(f"\n🔍 Testing Alternative Token Scopes")
        print("=" * 50)
        
        scopes_to_test = [
            "https://analysis.windows.net/powerbi/api/.default",
            "https://analysis.windows.net/powerbi/api/Dataset.ReadWrite.All",
            "https://analysis.windows.net/powerbi/api/Dataset.Read.All",
            "https://analysis.windows.net/powerbi/api/Workspace.ReadWrite.All",
        ]
        
        for scope in scopes_to_test:
            try:
                print(f"\n🔄 Testing scope: {scope}")
                token = self.get_token(scope)
                
                # Test DAX execution with this scope
                success = self._test_dax_with_token(token)
                if success:
                    print(f"✅ DAX execution successful with scope: {scope}")
                    return scope
                else:
                    print(f"❌ DAX execution failed with scope: {scope}")
                    
            except Exception as e:
                print(f"❌ Failed to get token with scope {scope}: {str(e)}")
        
        return None
    
    def _test_dax_with_token(self, token):
        """Test DAX execution with a specific token"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Very simple DAX query
        dax_query = {
            "queries": [
                {
                    "query": "EVALUATE ROW(\"Test\", 1)"
                }
            ]
        }
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        try:
            response = requests.post(url, json=dax_query, headers=headers, timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def check_tenant_settings(self):
        """Check relevant tenant settings that might block DAX execution"""
        print(f"\n🔍 Tenant Settings Analysis")
        print("=" * 50)
        
        print("❓ Cannot automatically check tenant settings (requires admin API access)")
        print("   Please verify the following tenant settings in Power BI Admin Portal:")
        print("   1. ✅ 'Allow service principals to use Power BI APIs' - ENABLED")
        print("   2. ✅ 'Dataset Execute Queries REST API' - ENABLED")
        print("   3. ✅ 'XMLA endpoint' - ENABLED for Premium workspaces")
        print("   4. ✅ 'Embed content in apps' - ENABLED (if using embedded scenarios)")
        
        print("\n📝 To check these settings:")
        print("   1. Go to Power BI Admin Portal → Tenant Settings")
        print("   2. Look for 'Developer settings' section")
        print("   3. Ensure 'Allow service principals to use Power BI APIs' is enabled")
        print("   4. Look for 'Dataset Execute Queries REST API' and ensure it's enabled")
    
    def suggest_fixes(self):
        """Provide specific fix suggestions based on findings"""
        print(f"\n🔧 Recommended Fixes")
        print("=" * 50)
        
        print("Based on the analysis, here are the recommended fixes:")
        
        print("\n1. 🔑 DATASET PERMISSIONS:")
        print("   Add service principal with 'Build' permission to the dataset:")
        print(f"   - Go to Power BI Service → Workspace → Dataset Settings")
        print(f"   - Add your service principal: {self.client_id}")
        print(f"   - Grant 'Build' permission (minimum required for DAX execution)")
        
        print("\n2. 🏢 TENANT SETTINGS:")
        print("   Ensure these tenant settings are enabled (requires Power BI Admin):")
        print("   - Allow service principals to use Power BI APIs")
        print("   - Dataset Execute Queries REST API")
        print("   - XMLA endpoint (for Premium workspaces)")
        
        print("\n3. 🔗 XMLA ENDPOINT:")
        print("   For Premium workspaces, ensure XMLA read-write is enabled:")
        print("   - Power BI Admin Portal → Capacity Settings → Workloads")
        print("   - XMLA Endpoint: Enable (Read-Write)")
        
        print("\n4. 📋 ALTERNATIVE APPROACH:")
        print("   If direct dataset permissions don't work, try:")
        print("   - Add service principal as Workspace Member/Admin")
        print("   - Use workspace-level permissions for dataset access")
        
        print("\n5. 🧪 TESTING:")
        print("   After making changes, wait 15-20 minutes for propagation")
        print("   Then run: python xmla_status_check.py")
    
    def run_comprehensive_diagnosis(self):
        """Run all diagnostic checks"""
        print("🚀 Power BI DAX Execution Troubleshooter")
        print("=" * 60)
        print("Based on Microsoft documentation and best practices")
        print("=" * 60)
        
        # 1. Token analysis
        token, decoded = self.analyze_token()
        if not token:
            print("❌ Cannot proceed without valid token")
            return
        
        # 2. Dataset permissions
        permissions_ok = self.check_dataset_permissions()
        
        # 3. Test alternative scopes
        working_scope = self.test_alternative_scopes()
        
        # 4. Check tenant settings
        self.check_tenant_settings()
        
        # 5. Provide fixes
        self.suggest_fixes()
        
        print("\n" + "=" * 60)
        print("📊 DIAGNOSIS SUMMARY")
        print("=" * 60)
        
        if working_scope:
            print(f"✅ Found working token scope: {working_scope}")
        else:
            print("❌ No working token scope found")
            
        if permissions_ok:
            print("✅ Dataset permissions appear correct")
        else:
            print("❌ Dataset permissions need attention")
        
        print("\n🎯 NEXT STEPS:")
        if not permissions_ok:
            print("1. ⚡ URGENT: Add service principal to dataset with 'Build' permission")
            print("2. 🔧 Verify tenant settings (requires admin)")
            print("3. ⏱️  Wait 15-20 minutes for changes to propagate")
            print("4. 🧪 Test again with: python xmla_status_check.py")
        elif not working_scope:
            print("1. 🔧 Check tenant settings with Power BI Admin")
            print("2. 📞 Contact admin to enable 'Dataset Execute Queries REST API'")
            print("3. 🔗 Verify XMLA endpoint is enabled for Premium capacity")
        else:
            print("✅ Setup appears correct - issue may be temporary")
            print("🔄 Try running the main application again")

if __name__ == "__main__":
    troubleshooter = PowerBIDAXTroubleshooter()
    troubleshooter.run_comprehensive_diagnosis()
