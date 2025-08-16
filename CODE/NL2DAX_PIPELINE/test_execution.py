#!/usr/bin/env python3
"""
Test DAX/SQL execution to verify consistent results
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from main import parse_nl_query, generate_sql, generate_dax
from sql_executor import execute_sql_query
from query_executor import execute_dax_query

def test_execution_consistency():
    """Test actual execution to compare row counts and results"""
    
    test_query = "Show me the top 3 customers by total balance"
    
    print("🧪 Testing Execution Consistency")
    print("=" * 40)
    print(f"Query: {test_query}")
    print()
    
    # Parse intent
    intent_entities = parse_nl_query(test_query)
    print("Intent parsed ✓")
    
    # Generate queries
    sql_query = generate_sql(intent_entities)
    dax_query = generate_dax(intent_entities)
    
    print("\n📊 Generated Queries:")
    print("\nSQL:")
    print(sql_query[:200] + "..." if len(sql_query) > 200 else sql_query)
    print("\nDAX:")
    print(dax_query[:200] + "..." if len(dax_query) > 200 else dax_query)
    
    # Execute and compare
    try:
        print("\n🔄 Executing SQL...")
        sql_results = execute_sql_query(sql_query)
        sql_count = len(sql_results) if sql_results else 0
        print(f"SQL returned {sql_count} rows")
        
        print("\n🔄 Executing DAX...")
        dax_results = execute_dax_query(dax_query)
        dax_count = len(dax_results) if dax_results else 0
        print(f"DAX returned {dax_count} rows")
        
        # Compare results
        print(f"\n📊 Comparison:")
        print(f"SQL rows: {sql_count}")
        print(f"DAX rows: {dax_count}")
        
        if sql_count == dax_count:
            print("✅ Row counts match!")
        else:
            print("⚠️  Row counts differ - investigate further")
            
    except Exception as e:
        print(f"❌ Execution error: {e}")

if __name__ == "__main__":
    test_execution_consistency()