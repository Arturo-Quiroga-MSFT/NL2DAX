#!/usr/bin/env python3
"""
DAX vs SQL Query Comparison Test
Side-by-side testing of both DAX and SQL queries against Power BI dataset
"""

import os
import requests
import msal
import json
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class DAXvsSQLTester:
    """Compare DAX and SQL query execution against Power BI datasets"""
    
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
    
    def execute_query(self, query, query_type):
        """Execute either DAX or SQL query"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        query_payload = {
            "queries": [{"query": query}],
            "serializerSettings": {"includeNulls": True}
        }
        
        url = f"https://api.powerbi.com/v1.0/myorg/datasets/{self.dataset_id}/executeQueries"
        
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=query_payload, timeout=30)
            elapsed = time.time() - start_time
            
            result = {
                "query_type": query_type,
                "query": query,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "elapsed_time": elapsed,
                "error": None,
                "row_count": 0,
                "result_preview": None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('results') and data['results'][0].get('tables'):
                        table = data['results'][0]['tables'][0]
                        rows = table.get('rows', [])
                        result["row_count"] = len(rows)
                        result["result_preview"] = rows[0] if rows else None
                except Exception as parse_error:
                    result["error"] = f"Parse error: {parse_error}"
            else:
                try:
                    error_data = response.json()
                    error_code = error_data.get('error', {}).get('code', 'Unknown')
                    result["error"] = f"HTTP {response.status_code}: {error_code}"
                except:
                    result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            
            return result
            
        except Exception as e:
            return {
                "query_type": query_type,
                "query": query,
                "success": False,
                "status_code": None,
                "elapsed_time": None,
                "error": str(e),
                "row_count": 0,
                "result_preview": None
            }
    
    def compare_queries(self, test_name, dax_query, sql_query):
        """Compare equivalent DAX and SQL queries"""
        print(f"\n🧪 COMPARISON TEST: {test_name}")
        print("=" * 60)
        print()
        
        # Execute DAX query
        print("🔍 Testing DAX Query:")
        print(f"   Query: {dax_query}")
        dax_result = self.execute_query(dax_query, "DAX")
        
        print(f"   Success: {'✅' if dax_result['success'] else '❌'} {dax_result['success']}")
        print(f"   Status: {dax_result['status_code']}")
        if dax_result['elapsed_time']:
            print(f"   Time: {dax_result['elapsed_time']:.2f}s")
        if dax_result['success']:
            print(f"   Rows: {dax_result['row_count']}")
            print(f"   Result: {dax_result['result_preview']}")
        if dax_result['error']:
            print(f"   Error: {dax_result['error']}")
        
        print()
        
        # Execute SQL query
        print("🔍 Testing SQL Query:")
        print(f"   Query: {sql_query}")
        sql_result = self.execute_query(sql_query, "SQL")
        
        print(f"   Success: {'✅' if sql_result['success'] else '❌'} {sql_result['success']}")
        print(f"   Status: {sql_result['status_code']}")
        if sql_result['elapsed_time']:
            print(f"   Time: {sql_result['elapsed_time']:.2f}s")
        if sql_result['success']:
            print(f"   Rows: {sql_result['row_count']}")
            print(f"   Result: {sql_result['result_preview']}")
        if sql_result['error']:
            print(f"   Error: {sql_result['error']}")
        
        print()
        
        # Comparison analysis
        print("📊 COMPARISON ANALYSIS:")
        if dax_result['success'] and sql_result['success']:
            print("   ✅ Both DAX and SQL work - No query language issues")
            time_diff = abs(dax_result['elapsed_time'] - sql_result['elapsed_time'])
            faster = "DAX" if dax_result['elapsed_time'] < sql_result['elapsed_time'] else "SQL"
            print(f"   ⚡ {faster} was {time_diff:.2f}s faster")
            
        elif dax_result['success'] and not sql_result['success']:
            print("   🎯 DAX works, SQL fails - SQL syntax or compatibility issue")
            
        elif not dax_result['success'] and sql_result['success']:
            print("   🎯 SQL works, DAX fails - DAX syntax or parsing issue")
            
        else:
            print("   ❌ Both fail - Fundamental access or permission issue")
        
        return dax_result, sql_result

def main():
    """Main comparison testing function"""
    print("🚀 DAX vs SQL QUERY COMPARISON TEST")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📖 Purpose: Compare DAX and SQL query execution")
    print("   This helps identify if issues are language-specific")
    print()
    
    tester = DAXvsSQLTester()
    
    if not tester.get_token():
        print("❌ Cannot proceed without token")
        return 1
    
    print("✅ Authentication successful")
    print(f"   Workspace: {tester.workspace_id}")
    print(f"   Dataset: {tester.dataset_id}")
    
    # Define equivalent test queries
    test_cases = [
        {
            "name": "Simple Literal Value",
            "dax": "EVALUATE { 1 }",
            "sql": "SELECT 1 as Value"
        },
        {
            "name": "Basic Arithmetic",
            "dax": "EVALUATE { 2 + 2 }",
            "sql": "SELECT 2 + 2 as Result"
        },
        {
            "name": "Current Date/Time",
            "dax": "EVALUATE { NOW() }",
            "sql": "SELECT GETDATE() as CurrentTime"
        },
        {
            "name": "String Concatenation",
            "dax": "EVALUATE { \"Hello\" & \" \" & \"World\" }",
            "sql": "SELECT 'Hello' + ' ' + 'World' as Greeting"
        },
        {
            "name": "Multiple Values",
            "dax": "EVALUATE { (1, \"Test\", 3.14) }",
            "sql": "SELECT 1 as Number, 'Test' as Text, 3.14 as Decimal"
        }
    ]
    
    # Run comparison tests
    all_results = []
    
    for test_case in test_cases:
        dax_result, sql_result = tester.compare_queries(
            test_case["name"],
            test_case["dax"],
            test_case["sql"]
        )
        all_results.append({
            "test_name": test_case["name"],
            "dax": dax_result,
            "sql": sql_result
        })
    
    # Overall summary
    print("\n📋 OVERALL COMPARISON SUMMARY")
    print("=" * 60)
    
    dax_successes = sum(1 for r in all_results if r["dax"]["success"])
    sql_successes = sum(1 for r in all_results if r["sql"]["success"])
    total_tests = len(all_results)
    
    print(f"📊 DAX Queries: {dax_successes}/{total_tests} successful")
    print(f"📊 SQL Queries: {sql_successes}/{total_tests} successful")
    print()
    
    # Analysis
    if dax_successes > 0 and sql_successes > 0:
        print("🎯 DIAGNOSIS: Both query languages work")
        print("   ✅ Service principal has proper execute permissions")
        print("   ✅ Capacity is accessible for query execution")
        print("   ✅ Both DAX and SQL are supported")
        print("   🔧 Previous 401 errors have been resolved")
        
    elif dax_successes > 0 and sql_successes == 0:
        print("🎯 DIAGNOSIS: DAX works, SQL fails")
        print("   ✅ Query execution permissions are working")
        print("   ❌ SQL syntax may not be supported or enabled")
        print("   🔧 Focus on DAX for your application")
        
    elif dax_successes == 0 and sql_successes > 0:
        print("🎯 DIAGNOSIS: SQL works, DAX fails")
        print("   ✅ Query execution permissions are working")  
        print("   ❌ DAX parsing or execution issues")
        print("   🔧 Consider using SQL as alternative")
        
    else:
        print("🎯 DIAGNOSIS: Both languages fail")
        print("   ❌ Fundamental access issue persists")
        print("   ❌ Capacity access or permission problem")
        print("   🔧 Check capacity status and service principal setup")
    
    print()
    print("🔧 RECOMMENDED NEXT STEPS:")
    
    if dax_successes > 0 or sql_successes > 0:
        print("   ✅ Query execution is working!")
        print("   ✅ Update your main application to use working query type")
        print("   ✅ The 401 errors should be resolved")
        
        if dax_successes > 0:
            print("   🎯 Use DAX queries for your NL2DAX application")
        if sql_successes > 0:
            print("   🎯 SQL queries are also available as alternative")
            
    else:
        print("   🔧 Continue monitoring capacity status")
        print("   🔧 Verify tenant settings for query execution")
        print("   🔧 Contact Power BI administrator if issues persist")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return appropriate exit code
    return 0 if (dax_successes > 0 or sql_successes > 0) else 1

if __name__ == "__main__":
    exit(main())
