#!/usr/bin/env python3
"""
SQL Query Test for Power BI Dataset
Tests SQL query execution against Power BI datasets via REST API
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

class PowerBISQLTester:
    """Test SQL query execution against Power BI datasets"""
    
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
    
    def get_dataset_schema(self):
        """Get dataset schema to understand available tables"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Use DAX to get schema information
        schema_query = """
        EVALUATE 
        ADDCOLUMNS(
            INFO.TABLES(),
            "TableType", "Table"
        )
        """
        
        query_payload = {
            "queries": [{"query": schema_query}],
            "serializerSettings": {"includeNulls": True}
        }
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        try:
            response = requests.post(url, headers=headers, json=query_payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                tables = result['results'][0]['tables'][0]['rows']
                return [row['[Name]'] for row in tables]
            else:
                print(f"⚠️ Schema query failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️ Schema query error: {e}")
            return []
    
    def test_sql_query(self, sql_query, test_name):
        """Test a SQL query against the dataset"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # SQL queries use the same executeQueries endpoint but with SQL syntax
        query_payload = {
            "queries": [{"query": sql_query}],
            "serializerSettings": {"includeNulls": True}
        }
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=query_payload, timeout=30)
            elapsed = time.time() - start_time
            
            result = {
                "test_name": test_name,
                "sql_query": sql_query,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "elapsed_time": elapsed,
                "error": None,
                "row_count": 0,
                "columns": [],
                "sample_data": []
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('results') and data['results'][0].get('tables'):
                        table = data['results'][0]['tables'][0]
                        result["row_count"] = len(table.get('rows', []))
                        result["columns"] = [col['name'] for col in table.get('columns', [])]
                        result["sample_data"] = table.get('rows', [])[:3]  # First 3 rows
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
                "test_name": test_name,
                "sql_query": sql_query,
                "success": False,
                "status_code": None,
                "elapsed_time": None,
                "error": str(e),
                "row_count": 0,
                "columns": [],
                "sample_data": []
            }
    
    def run_sql_tests(self):
        """Run a series of SQL test queries"""
        print("🔍 SQL QUERY TESTING FOR POWER BI DATASET")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("📖 Purpose: Test SQL query execution against Power BI dataset")
        print("   This helps determine if issues are DAX-specific or general")
        print()
        
        if not self.get_token():
            print("❌ Cannot proceed without token")
            return
        
        print("✅ Authentication successful")
        print(f"   Workspace: {self.workspace_id}")
        print(f"   Dataset: {self.dataset_id}")
        print()
        
        # Try to get schema information
        print("📋 Attempting to discover dataset schema...")
        tables = self.get_dataset_schema()
        if tables:
            print(f"✅ Found {len(tables)} tables: {', '.join(tables[:5])}")
            if len(tables) > 5:
                print(f"   ... and {len(tables) - 5} more")
        else:
            print("⚠️ Could not retrieve schema - using generic queries")
        print()
        
        # Define test SQL queries
        sql_tests = [
            {
                "name": "Simple SELECT with literal",
                "sql": "SELECT 1 as TestValue"
            },
            {
                "name": "Current timestamp",
                "sql": "SELECT GETDATE() as CurrentTime"
            },
            {
                "name": "Basic calculation",
                "sql": "SELECT 2 + 2 as Result"
            },
            {
                "name": "String operations", 
                "sql": "SELECT 'Hello' + ' ' + 'World' as Greeting"
            }
        ]
        
        # Add table-specific queries if we found tables
        if tables:
            # Try common table patterns
            common_patterns = ['Customer', 'Product', 'Sales', 'Order', 'Fact', 'Dim']
            
            for table in tables[:3]:  # Test first 3 tables
                sql_tests.append({
                    "name": f"Count rows in {table}",
                    "sql": f"SELECT COUNT(*) as RowCount FROM [{table}]"
                })
                
                sql_tests.append({
                    "name": f"Sample data from {table}",
                    "sql": f"SELECT TOP 5 * FROM [{table}]"
                })
        
        # Run all tests
        results = []
        
        for i, test in enumerate(sql_tests, 1):
            print(f"🧪 TEST {i}: {test['name']}")
            print("=" * 50)
            print(f"📋 SQL Query: {test['sql']}")
            print()
            
            result = self.test_sql_query(test['sql'], test['name'])
            results.append(result)
            
            # Display results
            print(f"   Success: {'✅' if result['success'] else '❌'} {result['success']}")
            print(f"   Status: {result['status_code']}")
            
            if result['elapsed_time']:
                print(f"   Time: {result['elapsed_time']:.2f}s")
            
            if result['error']:
                print(f"   Error: {result['error']}")
            
            if result['success']:
                print(f"   Rows: {result['row_count']}")
                print(f"   Columns: {', '.join(result['columns'])}")
                
                if result['sample_data']:
                    print("   Sample:")
                    for row in result['sample_data']:
                        print(f"     {row}")
            
            print()
        
        # Summary
        print("📋 OVERALL SQL TEST RESULTS")
        print("=" * 50)
        
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]
        
        print(f"✅ Successful: {len(successful_tests)}/{len(results)} tests")
        print(f"❌ Failed: {len(failed_tests)}/{len(results)} tests")
        print()
        
        if successful_tests:
            print("🎯 SQL QUERIES WORK! This suggests:")
            print("   • Service principal has proper execute permissions")
            print("   • Capacity is accessible for query execution")
            print("   • Issue may be DAX-specific syntax or parsing")
            print()
            
            avg_time = sum(r['elapsed_time'] for r in successful_tests) / len(successful_tests)
            print(f"📊 Average query time: {avg_time:.2f}s")
            
        else:
            print("🎯 SQL QUERIES ALSO FAIL - confirms fundamental issue:")
            print("   • Same root cause as DAX failures")
            print("   • Not query language specific")
            print("   • Focus on capacity access and permissions")
            print()
        
        if failed_tests:
            print("❌ Failed test details:")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['error']}")
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return results

def main():
    """Main SQL testing function"""
    tester = PowerBISQLTester()
    results = tester.run_sql_tests()
    
    # Return exit code based on results
    if any(r['success'] for r in results):
        print("\n🎉 At least some SQL queries worked!")
        return 0
    else:
        print("\n❌ All SQL queries failed")
        return 1

if __name__ == "__main__":
    exit(main())
