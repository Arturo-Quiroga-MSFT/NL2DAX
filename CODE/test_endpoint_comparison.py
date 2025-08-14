#!/usr/bin/env python3
"""
Power BI REST API Endpoint Comparison Test
Tests both endpoints as per Microsoft documentation
"""

import os
import requests
import msal
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class EndpointComparisonTester:
    """Compare both Power BI REST API endpoints for executeQueries"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007")
        self.token = None
        
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
    
    def test_endpoint(self, endpoint_type, url, dax_query):
        """Test a specific endpoint"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        query_payload = {
            "queries": [{"query": dax_query}],
            "serializerSettings": {"includeNulls": True}
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=query_payload, timeout=30)
            elapsed = time.time() - start_time
            
            result = {
                "endpoint_type": endpoint_type,
                "url": url,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "elapsed_time": elapsed,
                "error": None,
                "response_preview": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('results') and data['results'][0].get('tables'):
                        table = data['results'][0]['tables'][0]
                        rows = table.get('rows', [])
                        result["response_preview"] = rows[0] if rows else "No data"
                except Exception as parse_error:
                    result["error"] = f"Parse error: {parse_error}"
            else:
                try:
                    error_data = response.json()
                    error_code = error_data.get('error', {}).get('code', 'Unknown')
                    result["error"] = f"HTTP {response.status_code}: {error_code}"
                    # Get more detailed error info
                    if 'error' in error_data and 'message' in error_data['error']:
                        result["error"] += f" - {error_data['error']['message']}"
                except:
                    result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            
            return result
            
        except Exception as e:
            return {
                "endpoint_type": endpoint_type,
                "url": url,
                "success": False,
                "status_code": None,
                "elapsed_time": None,
                "error": str(e),
                "response_preview": None
            }

def main():
    """Main endpoint comparison function"""
    print("🧪 POWER BI REST API ENDPOINT COMPARISON TEST")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📖 Purpose: Test both executeQueries endpoints per Microsoft docs")
    print("   Compare direct dataset vs workspace-based access")
    print()
    
    tester = EndpointComparisonTester()
    
    if not tester.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print(f"   Workspace: {tester.workspace_id}")
    print(f"   Dataset: {tester.dataset_id}")
    print()
    
    # Define test query
    test_query = "EVALUATE { 1 }"
    
    # Define endpoints according to Microsoft documentation
    endpoints = [
        {
            "name": "Direct Dataset Access (My Workspace)",
            "url": f"https://api.powerbi.com/v1.0/myorg/datasets/{tester.dataset_id}/executeQueries",
            "description": "For datasets in user's personal workspace",
            "documentation": "https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries"
        },
        {
            "name": "Workspace Dataset Access (Shared Workspace)",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{tester.workspace_id}/datasets/{tester.dataset_id}/executeQueries",
            "description": "For datasets in shared/organizational workspaces",
            "documentation": "https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries-in-group"
        }
    ]
    
    # Test both endpoints
    results = []
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"🔍 TEST {i}: {endpoint['name']}")
        print("=" * 60)
        print(f"📋 Description: {endpoint['description']}")
        print(f"🌐 URL: {endpoint['url']}")
        print(f"📚 Documentation: {endpoint['documentation']}")
        print(f"🔍 Query: {test_query}")
        print()
        
        result = tester.test_endpoint(endpoint['name'], endpoint['url'], test_query)
        results.append(result)
        
        # Display results
        print(f"   Success: {'✅' if result['success'] else '❌'} {result['success']}")
        print(f"   Status: {result['status_code']}")
        
        if result['elapsed_time']:
            print(f"   Time: {result['elapsed_time']:.2f}s")
        
        if result['error']:
            print(f"   Error: {result['error']}")
        
        if result['success'] and result['response_preview']:
            print(f"   Result: {result['response_preview']}")
        
        print()
    
    # Analysis
    print("📊 ENDPOINT COMPARISON ANALYSIS")
    print("=" * 50)
    
    direct_success = results[0]['success']
    workspace_success = results[1]['success']
    
    print(f"📋 Direct Dataset Access: {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
    print(f"📋 Workspace Dataset Access: {'✅ SUCCESS' if workspace_success else '❌ FAILED'}")
    print()
    
    if direct_success and workspace_success:
        print("🎯 CONCLUSION: Both endpoints work")
        print("   • Dataset accessible via both personal and workspace context")
        print("   • Use workspace endpoint for consistency with documentation")
        
    elif not direct_success and workspace_success:
        print("🎯 CONCLUSION: Only workspace endpoint works (EXPECTED)")
        print("   • Dataset is in shared workspace, not personal 'My workspace'")
        print("   • Microsoft documentation recommends workspace endpoint for shared datasets")
        print("   • ✅ RECOMMENDATION: Use workspace-based endpoint")
        
    elif direct_success and not workspace_success:
        print("🎯 CONCLUSION: Only direct endpoint works (UNEXPECTED)")
        print("   • May indicate permission issues with workspace access")
        print("   • Check service principal workspace permissions")
        
    else:
        print("🎯 CONCLUSION: Both endpoints fail")
        print("   • Fundamental permission or configuration issue")
        print("   • Check tenant settings and service principal setup")
    
    print()
    print("📋 MICROSOFT DOCUMENTATION GUIDANCE:")
    print("-" * 45)
    print("• Direct Dataset Endpoint: For datasets in user's personal workspace")
    print("• Workspace Dataset Endpoint: For datasets in shared workspaces")
    print("• Our datasets are in shared workspace → Use workspace endpoint")
    print()
    
    print("🔧 RECOMMENDED ENDPOINT FOR OUR USE CASE:")
    print(f"   POST {endpoints[1]['url']}")
    print()
    
    print("📞 NEXT STEPS:")
    if workspace_success:
        print("   ✅ Update all scripts to use workspace-based endpoint")
        print("   ✅ Workspace endpoint is working correctly")
    elif direct_success:
        print("   🔍 Investigate workspace permission configuration")
        print("   🔧 Verify service principal has workspace access")
    else:
        print("   🔧 Focus on resolving fundamental permission issues")
        print("   📞 Contact Power BI administrator for tenant settings")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return appropriate exit code
    return 0 if (direct_success or workspace_success) else 1

if __name__ == "__main__":
    exit(main())
