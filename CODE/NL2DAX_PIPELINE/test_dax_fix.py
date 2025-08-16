#!/usr/bin/env python3
"""
Test the improved DAX generation to verify it produces consistent results with SQL
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import the modules
from dax_generator import generate_dax
from main import generate_sql, parse_nl_query

def test_dax_sql_consistency():
    """Test that DAX and SQL generate consistent results for the same query"""
    
    # Test query from the report
    test_query = "Show 5 large borrowers where a large borrower has outstanding loans of $1M USD or more."
    
    print("🔍 Testing DAX/SQL Consistency Fix")
    print("=" * 50)
    print(f"Test Query: {test_query}")
    print()
    
    # Parse intent/entities
    print("1. Parsing intent and entities...")
    intent_entities = parse_nl_query(test_query)
    print(f"Intent/Entities: {intent_entities[:200]}...")
    print()
    
    # Generate SQL
    print("2. Generating SQL...")
    sql_query = generate_sql(intent_entities)
    print("Generated SQL:")
    print(sql_query)
    print()
    
    # Generate DAX with improved prompt
    print("3. Generating DAX with improved prompt...")
    dax_query = generate_dax(intent_entities)
    print("Generated DAX:")
    print(dax_query)
    print()
    
    # Analysis
    print("4. Analysis:")
    print("- Check if DAX uses SUMMARIZECOLUMNS with multiple tables (BAD)")
    print("- Check if DAX uses SELECTCOLUMNS + RELATED or ADDCOLUMNS + LOOKUPVALUE (GOOD)")
    print("- Compare logic patterns between SQL JOINs and DAX relationships")
    
    # Check for problematic patterns
    if "SUMMARIZECOLUMNS" in dax_query and "FIS_CUSTOMER_DIMENSION" in dax_query:
        print("⚠️  WARNING: DAX still uses SUMMARIZECOLUMNS with cross-table columns!")
    elif "SELECTCOLUMNS" in dax_query and ("RELATED" in dax_query or "LOOKUPVALUE" in dax_query):
        print("✅ GOOD: DAX uses proper cross-table pattern")
    elif "ADDCOLUMNS" in dax_query and "LOOKUPVALUE" in dax_query:
        print("✅ GOOD: DAX uses explicit LOOKUPVALUE pattern")
    else:
        print("🤔 UNCLEAR: Check DAX pattern manually")

if __name__ == "__main__":
    test_dax_sql_consistency()