#!/usr/bin/env python3
"""
debug_generators.py - Debug script to test SQL and DAX generators with real schema
================================================================

This script helps diagnose issues with query generation by testing both
generators independently with the actual database schema.

Author: Unified Pipeline Team  
Date: August 2025
"""

import os
import sys
from sql_generator import SQLGenerator
from dax_generator import DAXGenerator
from schema_analyzer import SchemaAnalyzer

def test_generators():
    """Test both SQL and DAX generators with real schema"""
    print("🔍 Testing Generators with Real Schema")
    print("=" * 50)
    
    # Get real schema
    schema_analyzer = SchemaAnalyzer()
    print("📊 Reading real database schema...")
    try:
        schema_info = schema_analyzer.get_schema_info()
        print(f"✅ Schema loaded successfully")
        print(f"📋 Schema contains {len(schema_info.get('tables', []))} tables")
        
        # Show first few tables for context
        tables = schema_info.get('tables', [])[:3]
        for table in tables:
            print(f"   - {table.get('name', 'Unknown')}: {len(table.get('columns', []))} columns")
    except Exception as e:
        print(f"❌ Schema loading failed: {str(e)}")
        return
    
    # Test queries
    test_queries = [
        "show me the customers with the lowest risk ratings",
        "what is the average loan amount",
        "list the top 5 customers by credit limit"
    ]
    
    for i, test_query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test {i}: {test_query}")
        print('='*60)
        
        # Test SQL Generator
        print(f"\n🔧 Testing SQL Generator...")
        sql_generator = SQLGenerator()
        try:
            sql_result = sql_generator.generate_sql(test_query, schema_info)
            print(f"✅ SQL Result length: {len(sql_result)}")
            if sql_result and not sql_result.startswith("--"):
                print(f"✅ SQL Query:\n{sql_result}")
            else:
                print(f"❌ SQL Generation failed: '{sql_result}'")
        except Exception as e:
            print(f"❌ SQL Generator exception: {str(e)}")
            sql_result = ""
        
        # Test DAX Generator  
        print(f"\n⚡ Testing DAX Generator...")
        dax_generator = DAXGenerator()
        try:
            dax_result = dax_generator.generate_dax(test_query, schema_info)
            print(f"✅ DAX Result length: {len(dax_result)}")
            if dax_result and not dax_result.startswith("//"):
                print(f"✅ DAX Query:\n{dax_result}")
            else:
                print(f"❌ DAX Generation failed: '{dax_result}'")
        except Exception as e:
            print(f"❌ DAX Generator exception: {str(e)}")
            dax_result = ""
        
        # Summary for this test
        sql_success = sql_result and len(sql_result) > 0 and not sql_result.startswith("--")
        dax_success = dax_result and len(dax_result) > 0 and not dax_result.startswith("//")
        
        print(f"\n📊 Test {i} Summary:")
        print(f"   SQL: {'✅ SUCCESS' if sql_success else '❌ FAILED'}")
        print(f"   DAX: {'✅ SUCCESS' if dax_success else '❌ FAILED'}")

def test_openai_connection():
    """Test OpenAI connection independently"""
    print("\n🔌 Testing OpenAI Connection")
    print("-" * 30)
    
    try:
        sql_generator = SQLGenerator()
        if sql_generator.test_openai_connection():
            print("✅ OpenAI connection successful")
        else:
            print("❌ OpenAI connection failed")
    except Exception as e:
        print(f"❌ OpenAI connection error: {str(e)}")

def main():
    """Main test function"""
    print("🧪 NL2SQL & DAX Generator Debug Tool")
    print("=" * 60)
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Path: {sys.executable}")
    
    # Test OpenAI connection first
    test_openai_connection()
    
    # Test generators
    test_generators()
    
    print("\n🏁 Debug session completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()