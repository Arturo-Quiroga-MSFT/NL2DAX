#!/usr/bin/env python3
"""
Debug script to test DAX-to-SQL translation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from azure_sql_executor import AzureSQLExecutor
from schema_analyzer import SchemaAnalyzer

def debug_dax_translation():
    print("🔍 Debugging DAX-to-SQL Translation...")
    
    # Initialize components
    schema_analyzer = SchemaAnalyzer()
    executor = AzureSQLExecutor()
    
    # Get schema info
    print("\n📊 Getting schema info...")
    schema_info = schema_analyzer.get_schema_info()
    print(f"Schema info type: {type(schema_info)}")
    if isinstance(schema_info, dict) and 'tables' in schema_info:
        tables = schema_info['tables']
        if isinstance(tables, dict):
            print(f"Schema tables: {list(tables.keys())}")
        else:
            print(f"Tables type: {type(tables)}, content: {tables}")
    
    # Test DAX query from the screenshot
    dax_query = """EVALUATE
SUMMARIZE(
    FIS_CUSTOMER_DIMENSION,
    FIS_CUSTOMER_DIMENSION[CustomerKey],
    FIS_CUSTOMER_DIMENSION[CustomerID],
    FIS_CUSTOMER_DIMENSION[CustomerName],
    FIS_CUSTOMER_DIMENSION[CustomerTypeDescription],
    FIS_CUSTOMER_DIMENSION[IndustryDescription],
    FIS_CUSTOMER_DIMENSION[CountryDescription],
    FIS_CUSTOMER_DIMENSION[StateDescription],
    FIS_CUSTOMER_DIMENSION[City],
    FIS_CUSTOMER_DIMENSION[PostalCode],
    FIS_CUSTOMER_DIMENSION[Risk_Rating_Description],
    FIS_CUSTOMER_DIMENSION[RelationshipManager]
)"""
    
    print(f"\n📝 Testing DAX Query:")
    print(dax_query)
    
    # Test the translation method directly
    print(f"\n🔧 Testing _translate_dax_to_sql method...")
    sql_result = executor._translate_dax_to_sql(dax_query, schema_info)
    
    if sql_result:
        print(f"✅ Translation successful:")
        print(sql_result)
    else:
        print("❌ Translation failed - returned None")
    
    # Test the full execute_dax_as_sql method
    print(f"\n🗄️ Testing execute_dax_as_sql method...")
    try:
        result = executor.execute_dax_as_sql(dax_query, schema_info)
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_dax_translation()