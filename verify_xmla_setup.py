#!/usr/bin/env python3
"""
Verification script to check all XMLA configuration steps
"""

import os
import requests
import msal
from dotenv import load_dotenv
import json
import time

load_dotenv()

def get_token():
    tenant_id = os.getenv("PBI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET")
    
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )
    
    token = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
    if token and "access_token" in token:
        return token["access_token"]
    else:
        raise RuntimeError(f"Failed to get token: {token}")

def test_multiple_dax_queries():
    """Test different types of DAX queries to isolate the issue"""
    print("🧪 Testing multiple DAX query approaches...")
    
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test different DAX queries
    test_queries = [
        {
            "name": "Simple ROW query",
            "dax": "EVALUATE ROW(\"TestColumn\", 1)"
        },
        {
            "name": "Basic calculation",
            "dax": "EVALUATE ROW(\"Result\", 1+1)"
        },
        {
            "name": "Current date",
            "dax": "EVALUATE ROW(\"Today\", TODAY())"
        }
    ]
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    
    for test in test_queries:
        print(f"\n   🔍 Testing: {test['name']}")
        print(f"      DAX: {test['dax']}")
        
        payload = {
            "queries": [{"query": test['dax']}],
            "serializerSettings": {"includeNulls": True}
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ SUCCESS!")
                print(f"      Response: {json.dumps(result, indent=2)[:200]}...")
                return True
            else:
                print(f"      ❌ Failed: {response.text[:200]}...")
        except Exception as e:
            print(f"      💥 Exception: {str(e)}")
    
    return False

def check_xmla_alternative_endpoints():
    """Check if there are alternative XMLA endpoints we can use"""
    print("\n🔍 Checking alternative API endpoints...")
    
    token = get_token()
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try different API endpoints
    endpoints_to_test = [
        {
            "name": "Dataset Discovery",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/discovery",
            "method": "GET"
        },
        {
            "name": "Dataset Schema",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/tables",
            "method": "GET"
        },
        {
            "name": "Dataset Measures",
            "url": f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/measures",
            "method": "GET"
        }
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n   🔍 Testing: {endpoint['name']}")
        print(f"      URL: {endpoint['url']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], headers=headers, timeout=30)
            else:
                response = requests.post(endpoint['url'], headers=headers, timeout=30)
            
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"      ✅ SUCCESS!")
                data = response.json()
                if 'value' in data:
                    print(f"      Found {len(data['value'])} items")
                else:
                    print(f"      Response: {str(data)[:100]}...")
            elif response.status_code == 404:
                print(f"      ℹ️  Endpoint not available")
            else:
                print(f"      ❌ Failed: {response.text[:100]}...")
                
        except Exception as e:
            print(f"      💥 Exception: {str(e)}")

def provide_next_steps():
    """Provide specific next steps based on current status"""
    print("\n🎯 NEXT STEPS TO RESOLVE XMLA ACCESS:")
    print("=" * 60)
    
    print("\n1️⃣  VERIFY SECURITY GROUP MEMBERSHIP:")
    print("   • Go to Azure Portal: https://portal.azure.com")
    print("   • Navigate: Azure AD → Groups → [Your Security Group]")
    print("   • Check members include:")
    print("     - Your service principal (App ID: 20c5495d-b98c-410b-aa7b-9ea13dd70f61)")
    print("     - Object ID: 41c1b8cc-b650-4313-9543-3527e362694d")
    
    print("\n2️⃣  VERIFY POWER BI ADMIN PORTAL SETTINGS:")
    print("   • Go to: https://admin.powerbi.com")
    print("   • Navigate: Tenant settings")
    print("   • Find: 'XMLA endpoint and Analyze in Excel with on-premises datasets'")
    print("   • Verify:")
    print("     - Status: ENABLED ✅")
    print("     - Apply to: Specific security groups")
    print("     - Group name is correctly entered")
    
    print("\n3️⃣  ENABLE WORKSPACE-LEVEL XMLA:")
    print("   • Go to: https://app.powerbi.com")
    print("   • Navigate to: FIS workspace")
    print("   • Settings → Workspace settings → Premium tab")
    print("   • Set: XMLA Endpoint to 'Read Write'")
    
    print("\n4️⃣  WAIT FOR PROPAGATION:")
    print("   • Changes can take 5-15 minutes to propagate")
    print("   • Try testing again in a few minutes")
    
    print("\n5️⃣  ALTERNATIVE AUTHENTICATION SCOPES:")
    print("   • Try different token scopes if issues persist:")
    print("     - https://analysis.windows.net/powerbi/api/.default")
    print("     - https://powerbi.microsoft.com/.default")
    
    print("\n6️⃣  CONTACT SUPPORT IF ISSUES PERSIST:")
    print("   • Microsoft Power BI Support")
    print("   • Provide these details:")
    print("     - Tenant ID: a172a259-b1c7-4944-b2e1-6d551f954711")
    print("     - Workspace ID: e3fdee99-3aa4-4d71-a530-2964a062e326")
    print("     - Dataset ID: 3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007")
    print("     - Service Principal ID: 20c5495d-b98c-410b-aa7b-9ea13dd70f61")

def wait_and_retry_test():
    """Wait a bit and retry the DAX test"""
    print("\n⏰ Waiting for settings to propagate...")
    
    for i in range(3):
        print(f"\n   Attempt {i+1}/3 - waiting 30 seconds...")
        time.sleep(30)
        
        print("   🧪 Testing DAX query...")
        if test_multiple_dax_queries():
            print("   ✅ SUCCESS! XMLA endpoints are now working!")
            return True
        else:
            print("   ❌ Still not working...")
    
    print("   ⏰ Settings may need more time to propagate")
    return False

if __name__ == "__main__":
    print("🔍 XMLA CONFIGURATION VERIFICATION")
    print("=" * 60)
    
    try:
        # Test current status
        success = test_multiple_dax_queries()
        
        if not success:
            # Check alternative endpoints
            check_xmla_alternative_endpoints()
            
            # Wait and retry
            print(f"\n{'='*60}")
            print("Since DAX queries are still failing, let's wait and retry...")
            success = wait_and_retry_test()
        
        if success:
            print("\n🎉 CONGRATULATIONS!")
            print("✅ XMLA endpoints are working!")
            print("✅ Your NL2DAX application should now work correctly!")
            print("\nYou can now test with:")
            print("   python CODE/smoke_test_xmla.py")
            print("   python CODE/main.py")
        else:
            provide_next_steps()
            
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
