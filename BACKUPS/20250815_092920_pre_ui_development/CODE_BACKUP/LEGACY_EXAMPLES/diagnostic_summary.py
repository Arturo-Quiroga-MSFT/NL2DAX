#!/usr/bin/env python3
"""
Complete Power BI Query Diagnostic Summary
Consolidates all test results and provides final diagnosis
"""

import os
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_test_script(script_name, description):
    """Run a test script and capture results"""
    print(f"🔍 Running {description}...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return {
            "script": script_name,
            "description": description,
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "description": description,
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Test timed out after 60 seconds"
        }
    except Exception as e:
        return {
            "script": script_name,
            "description": description,
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }

def main():
    """Run complete diagnostic suite and provide summary"""
    
    print("🩺 COMPLETE POWER BI QUERY DIAGNOSTIC SUITE")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📖 Purpose: Comprehensive diagnosis of Power BI query execution issues")
    print("   This suite tests all aspects: permissions, capacity, DAX, and SQL")
    print()
    
    # Test configuration
    workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
    dataset_id = os.getenv("POWERBI_DATASET_ID", "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007")
    
    print("📋 CONFIGURATION:")
    print(f"   Workspace ID: {workspace_id}")
    print(f"   Dataset ID: {dataset_id}")
    print()
    
    # Define test suite
    tests = [
        {
            "script": "fabric_capacity_status.py",
            "description": "Capacity Access Status",
            "category": "Infrastructure"
        },
        {
            "script": "test_permissions_detailed.py", 
            "description": "Service Principal Permissions",
            "category": "Authentication"
        },
        {
            "script": "test_sql_queries.py",
            "description": "SQL Query Execution",
            "category": "Query Testing"
        },
        {
            "script": "compare_dax_methods.py",
            "description": "DAX Query Execution (REST API vs XMLA)",
            "category": "Query Testing"
        }
    ]
    
    # Run all tests
    results = []
    
    for test in tests:
        print(f"⚡ EXECUTING: {test['description']}")
        print("-" * 50)
        
        result = run_test_script(test["script"], test["description"])
        results.append(result)
        
        if result["success"]:
            print("✅ COMPLETED SUCCESSFULLY")
        else:
            print(f"❌ FAILED (Exit Code: {result['returncode']})")
            if result["stderr"]:
                print(f"   Error: {result['stderr']}")
        
        print()
    
    # Analyze results
    print("📊 DIAGNOSTIC ANALYSIS")
    print("=" * 50)
    
    # Check capacity status
    capacity_test = next((r for r in results if "capacity" in r["script"]), None)
    capacity_ok = capacity_test and capacity_test["success"]
    
    # Check permissions
    permissions_test = next((r for r in results if "permissions" in r["script"]), None)
    permissions_basic_ok = permissions_test and permissions_test["success"]
    
    # Check query execution (need to parse output, not just exit codes)
    sql_test = next((r for r in results if "sql" in r["script"]), None)
    sql_works = sql_test and sql_test["success"] and "Successful: 0/" not in sql_test["stdout"]
    
    dax_test = next((r for r in results if "dax" in r["script"]), None) 
    dax_works = dax_test and sql_test and "REST API: 0/" not in dax_test["stdout"] and "XMLA: 0/" not in dax_test["stdout"]
    
    print("🔍 INDIVIDUAL TEST RESULTS:")
    print(f"   Capacity Access: {'✅' if capacity_ok else '❌'}")
    print(f"   Basic Permissions: {'✅' if permissions_basic_ok else '❌'}")
    print(f"   SQL Query Execution: {'✅' if sql_works else '❌'}")
    print(f"   DAX Query Execution: {'✅' if dax_works else '❌'}")
    print()
    
    # Overall diagnosis
    print("🎯 OVERALL DIAGNOSIS:")
    print("-" * 30)
    
    if sql_works or dax_works:
        print("🎉 RESOLUTION ACHIEVED!")
        print("   ✅ Query execution is now working")
        print("   ✅ Previous 401 errors have been resolved")
        print("   ✅ Your NL2DAX application should now function properly")
        
        if sql_works and dax_works:
            print("   🎯 Both SQL and DAX queries work - full functionality")
        elif sql_works:
            print("   🎯 SQL queries work - consider SQL as alternative to DAX")
        else:
            print("   🎯 DAX queries work - proceed with original DAX approach")
            
    elif permissions_basic_ok and not capacity_ok:
        print("🔧 CAPACITY ACCESS ISSUE (Expected)")
        print("   ✅ Service principal authentication works")
        print("   ✅ Basic permissions are correct")
        print("   ❌ Capacity not accessible via user API")
        print("   💡 This is the root cause of 401 errors")
        print()
        print("   📋 SOLUTION:")
        print("   1. Capacity is running in admin API but not visible in user API")
        print("   2. Wait for capacity propagation (can take 5-15 minutes)")
        print("   3. Monitor with: python3 fabric_capacity_status.py")
        print("   4. When capacity appears, all queries should work")
        
    elif not permissions_basic_ok:
        print("🔧 AUTHENTICATION/PERMISSION ISSUE")
        print("   ❌ Service principal setup needs attention") 
        print("   ❌ Check Azure AD app registration")
        print("   ❌ Verify service principal permissions in Power BI")
        
    else:
        print("🔧 MIXED RESULTS - REVIEW INDIVIDUAL TESTS")
        print("   📋 Check detailed output above for specific issues")
    
    print()
    print("🔧 RECOMMENDED NEXT STEPS:")
    
    if sql_works or dax_works:
        print("   1. ✅ Update your NL2DAX application to use working query method")
        print("   2. ✅ Test with your actual business queries")
        print("   3. ✅ Deploy to production environment")
        
    elif capacity_ok and permissions_basic_ok:
        print("   1. 🔍 Investigate specific query execution settings")
        print("   2. 🔍 Check tenant admin settings for query APIs")
        print("   3. 🔍 Verify dataset-specific permissions")
        
    else:
        print("   1. 🔧 Continue monitoring capacity status every 5-10 minutes")
        print("   2. 🔧 Re-run this diagnostic: python3 diagnostic_summary.py")
        print("   3. 🔧 Contact Power BI administrator if issue persists > 30 minutes")
    
    print()
    print("📞 SUPPORT RESOURCES:")
    print("   • Re-run diagnostics: python3 diagnostic_summary.py")
    print("   • Check capacity: python3 fabric_capacity_status.py")
    print("   • Test queries: python3 compare_dax_sql.py")
    print("   • Power BI Admin Portal: https://app.powerbi.com")
    print("   • Microsoft Support: https://powerbi.microsoft.com/support/")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return appropriate exit code
    if sql_works or dax_works:
        print("\n🎉 SUCCESS: Query execution is working!")
        return 0
    elif capacity_ok and permissions_basic_ok:
        print("\n⚠️  PARTIAL: Infrastructure OK, but queries still fail")
        return 2
    else:
        print("\n❌ ISSUES: Fundamental problems remain")
        return 1

if __name__ == "__main__":
    exit(main())
