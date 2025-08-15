#!/usr/bin/env python3
"""
Investigate DatasetExecuteQueriesError Details
Get full error messages and check dataset compatibility
"""

import os
import requests
import msal
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class DatasetExecuteQueriesInvestigator:
    """Investigate DatasetExecuteQueriesError in detail"""
    
    def __init__(self):
        self.tenant_id = os.getenv("PBI_TENANT_ID")
        self.client_id = os.getenv("PBI_CLIENT_ID")
        self.client_secret = os.getenv("PBI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWERBI_DATASET_ID", "fc4d80c8-090e-4441-8336-217490bde820")
        self.token = None
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
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
    
    def get_full_error_details(self):
        """Get full error details from executeQueries"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        payload = {
            "queries": [{"query": "EVALUATE { 1 }"}],
            "serializerSettings": {"includeNulls": True}
        }
        
        print("🔍 FULL ERROR INVESTIGATION")
        print("-" * 40)
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print()
            
            if response.status_code != 200:
                print("Raw Response Body:")
                print(response.text)
                print()
                
                try:
                    error_data = response.json()
                    print("Parsed Error Details:")
                    print(json.dumps(error_data, indent=2))
                    print()
                    
                    # Extract detailed error information
                    if 'error' in error_data:
                        error = error_data['error']
                        print("Error Analysis:")
                        print(f"  Code: {error.get('code', 'Unknown')}")
                        print(f"  Message: {error.get('message', 'No message')}")
                        
                        if 'pbi.error' in error:
                            pbi_error = error['pbi.error']
                            print(f"  PBI Error Code: {pbi_error.get('code', 'Unknown')}")
                            print(f"  PBI Parameters: {pbi_error.get('parameters', {})}")
                            
                            if 'details' in pbi_error:
                                print("  Details:")
                                for detail in pbi_error['details']:
                                    print(f"    {detail.get('code', 'Unknown')}: {detail.get('detail', {})}")
                        
                except Exception as parse_error:
                    print(f"Could not parse error JSON: {parse_error}")
            else:
                print("✅ Query succeeded!")
                return True
                
        except Exception as e:
            print(f"Request error: {e}")
        
        return False
    
    def check_dataset_compatibility(self):
        """Check if dataset is compatible with executeQueries"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print("📊 DATASET COMPATIBILITY CHECK")
        print("-" * 40)
        
        try:
            # Get detailed dataset information
            response = requests.get(
                f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                dataset = response.json()
                
                print("Dataset Properties:")
                for key, value in dataset.items():
                    print(f"  {key}: {value}")
                print()
                
                # Check specific compatibility factors
                compatibility_issues = []
                
                # Check dataset mode
                default_mode = dataset.get('defaultMode')
                if default_mode == 'DirectQuery':
                    compatibility_issues.append("Dataset is in DirectQuery mode - may not support all DAX queries")
                elif default_mode == 'Composite':
                    compatibility_issues.append("Dataset is in Composite mode - may have limitations")
                elif default_mode not in ['Import', 'Push']:
                    compatibility_issues.append(f"Unknown dataset mode: {default_mode}")
                
                # Check if on-premises
                if dataset.get('isOnPremGatewayRequired'):
                    compatibility_issues.append("Dataset requires on-premises gateway")
                
                # Check refresh status
                if not dataset.get('isRefreshable'):
                    compatibility_issues.append("Dataset is not refreshable")
                
                print("Compatibility Analysis:")
                if compatibility_issues:
                    for issue in compatibility_issues:
                        print(f"  ⚠️  {issue}")
                else:
                    print("  ✅ No obvious compatibility issues found")
                
                print()
                
        except Exception as e:
            print(f"Dataset check error: {e}")
    
    def test_different_dax_queries(self):
        """Test different types of DAX queries to isolate the issue"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        print("🧪 DIFFERENT DAX QUERY TESTS")
        print("-" * 40)
        
        test_queries = [
            ("Simple Value", "EVALUATE { 1 }"),
            ("ROW Constructor", "EVALUATE ROW(\"Test\", 1)"),
            ("BLANK Function", "EVALUATE { BLANK() }"),
            ("TODAY Function", "EVALUATE { TODAY() }"),
            ("Simple Table", "EVALUATE SUMMARIZE(CALENDAR(DATE(2023,1,1), DATE(2023,1,2)), [Date])"),
            ("INFO.TABLES", "EVALUATE INFO.TABLES()"),
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
                    print("Result: ✅ SUCCESS")
                    try:
                        data = response.json()
                        if data.get('results'):
                            tables = data['results'][0].get('tables', [])
                            if tables:
                                rows = tables[0].get('rows', [])
                                print(f"Rows returned: {len(rows)}")
                    except:
                        pass
                else:
                    print("Result: ❌ FAILED")
                    try:
                        error_data = response.json()
                        error_code = error_data.get('error', {}).get('code', 'Unknown')
                        print(f"Error: {error_code}")
                        
                        # Look for specific error patterns
                        error_text = str(error_data).lower()
                        if "table" in error_text and "not found" in error_text:
                            print("  🔍 Suggests missing table/column reference")
                        elif "permission" in error_text:
                            print("  🔍 Suggests permission issue")
                        elif "syntax" in error_text:
                            print("  🔍 Suggests syntax issue")
                        
                    except:
                        print(f"Raw error: {response.text[:100]}")
                
                print()
                
                # If any query succeeds, we know the basic functionality works
                if response.status_code == 200:
                    return True
                    
            except Exception as e:
                print(f"Exception: {e}")
                print()
        
        return False

def main():
    """Main investigation function"""
    print("🔍 DATASET EXECUTE QUERIES ERROR INVESTIGATOR")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Purpose: Get full error details and check dataset compatibility")
    print()
    
    investigator = DatasetExecuteQueriesInvestigator()
    
    if not investigator.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print()
    
    # Get full error details
    success1 = investigator.get_full_error_details()
    
    # Check dataset compatibility
    investigator.check_dataset_compatibility()
    
    # Test different DAX queries
    success2 = investigator.test_different_dax_queries()
    
    print("📊 INVESTIGATION SUMMARY")
    print("=" * 30)
    
    if success1 or success2:
        print("🎉 Some queries succeeded!")
        print("   The issue may be query-specific or intermittent")
    else:
        print("❌ All queries failed consistently")
        print("   This indicates a fundamental configuration issue")
        print()
        print("🔧 Next Steps:")
        print("1. Review the full error details above")
        print("2. Check Power BI Admin Portal tenant settings")
        print("3. Verify service principal has 'Developer' API permissions")
        print("4. Ensure dataset is properly refreshed and active")
        print("5. Contact Power BI administrator for tenant-level settings")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if (success1 or success2) else 1

if __name__ == "__main__":
    exit(main())
