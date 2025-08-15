#!/usr/bin/env python3
"""
test_pipeline.py - Quick Test Script for Unified Pipeline
=========================================================

Simple test script to verify that all components of the
unified pipeline work correctly.

Author: Unified Pipeline Team
Date: August 2025
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from unified_pipeline import UnifiedNL2SQLDAXPipeline
        print("  ✅ unified_pipeline imported successfully")
        
        from azure_sql_executor import AzureSQLExecutor
        print("  ✅ azure_sql_executor imported successfully")
        
        from schema_analyzer import SchemaAnalyzer
        print("  ✅ schema_analyzer imported successfully")
        
        from sql_generator import SQLGenerator
        print("  ✅ sql_generator imported successfully")
        
        from dax_generator import DAXGenerator
        print("  ✅ dax_generator imported successfully")
        
        from result_formatter import ResultFormatter
        print("  ✅ result_formatter imported successfully")
        
        from query_cache import QueryCache
        print("  ✅ query_cache imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_environment():
    """Test that required environment variables are set"""
    print("\\n🔧 Testing environment configuration...")
    
    required_vars = [
        'AZURE_SQL_SERVER',
        'AZURE_SQL_DATABASE', 
        'AZURE_SQL_USERNAME',
        'AZURE_SQL_PASSWORD',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_DEPLOYMENT_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * min(len(value), 10)}")
        else:
            print(f"  ❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\\n  ⚠️  Missing required variables: {', '.join(missing_vars)}")
        return False
    
    return True

def test_individual_components():
    """Test individual components"""
    print("\\n🔧 Testing individual components...")
    
    try:
        # Test query cache
        from query_cache import QueryCache
        cache = QueryCache(cache_dir="test_cache_temp")
        print("  ✅ QueryCache initialization successful")
        
        # Test result formatter
        from result_formatter import ResultFormatter
        formatter = ResultFormatter()
        print("  ✅ ResultFormatter initialization successful")
        
        # Test sample formatting
        sample_result = {
            "success": True,
            "columns": ["id", "name"],
            "data": [{"id": 1, "name": "test"}],
            "execution_time": 0.1
        }
        formatted = formatter.format_result(sample_result, "SQL")
        print("  ✅ Result formatting works")
        
        # Cleanup test cache
        import shutil
        if os.path.exists("test_cache_temp"):
            shutil.rmtree("test_cache_temp")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Component test error: {e}")
        return False

def test_database_connection():
    """Test database connection (if credentials are available)"""
    print("\\n🗄️  Testing database connection...")
    
    try:
        from azure_sql_executor import AzureSQLExecutor
        
        executor = AzureSQLExecutor()
        
        # Try a simple connection test
        connection_result = executor.test_connection()
        
        if connection_result.get("success"):
            print("  ✅ Database connection successful")
            return True
        else:
            print(f"  ❌ Database connection failed: {connection_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\\n🤖 Testing OpenAI API connection...")
    
    try:
        from sql_generator import SQLGenerator
        
        generator = SQLGenerator()
        
        # Try a simple test
        test_result = generator.test_connection()
        
        if test_result.get("success"):
            print("  ✅ OpenAI API connection successful")
            return True
        else:
            print(f"  ❌ OpenAI API connection failed: {test_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ OpenAI API connection error: {e}")
        return False

def test_full_pipeline():
    """Test the full pipeline with a simple query"""
    print("\\n🔄 Testing full pipeline...")
    
    try:
        from unified_pipeline import UnifiedNL2SQLDAXPipeline
        
        pipeline = UnifiedNL2SQLDAXPipeline()
        print("  ✅ Pipeline initialization successful")
        
        # Test a simple schema query that should work on any database
        test_query = "Show me the database tables"
        
        print(f"  🔍 Testing query: '{test_query}'")
        
        # Execute just SQL for this test
        results = pipeline.execute_query(test_query)
        
        if results.get("sql_result", {}).get("success"):
            print("  ✅ Pipeline execution successful")
            print(f"  📊 SQL result rows: {len(results['sql_result'].get('data', []))}")
            return True
        else:
            error = results.get("sql_result", {}).get("error", "Unknown error")
            print(f"  ❌ Pipeline execution failed: {error}")
            return False
            
    except Exception as e:
        print(f"  ❌ Full pipeline test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 NL2SQL&DAX Unified Pipeline Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Environment Configuration", test_environment),
        ("Individual Components", test_individual_components),
        ("Database Connection", test_database_connection),
        ("OpenAI API Connection", test_openai_connection),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\\n{'=' * 20} {test_name} {'=' * 20}")
        
        try:
            if test_func():
                passed += 1
                print(f"\\n✅ {test_name}: PASSED")
            else:
                print(f"\\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\\n💥 {test_name}: ERROR - {e}")
    
    print(f"\\n{'=' * 60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Pipeline is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
        return 1

if __name__ == "__main__":
    exit(main())