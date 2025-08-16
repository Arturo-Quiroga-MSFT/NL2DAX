#!/usr/bin/env python3
"""
Test Enhanced International Data
===============================

This script tests if our enhanced international customer data is accessible through the NL2DAX pipeline.
It executes a simple geographic query to verify that our new international customers are properly integrated.
"""

import re
from main import parse_nl_query, generate_sql
from sql_executor import execute_sql_query

def test_international_customers():
    """Test the enhanced international customer data integration"""
    
    # Test with our enhanced international data
    query = 'Show me all customers by country'
    print(f'Testing query: {query}')
    
    # Parse and generate SQL
    print('\n=== PARSING NATURAL LANGUAGE ===')
    intent_entities = parse_nl_query(query)
    print(intent_entities)
    
    print('\n=== GENERATING SQL ===')
    sql = generate_sql(intent_entities)
    print(sql)
    
    # Extract SQL code (same logic as main.py)
    sql_code = sql
    code_block = re.search(r"```sql\s*([\s\S]+?)```", sql, re.IGNORECASE)
    if not code_block:
        code_block = re.search(r"```([\s\S]+?)```", sql)
    if code_block:
        sql_code = code_block.group(1).strip()
    else:
        select_match = re.search(r'(SELECT[\s\S]+)', sql, re.IGNORECASE)
        if select_match:
            sql_code = select_match.group(1).strip()
    
    # Sanitize quotes
    sql_sanitized = sql_code.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
    
    print('\n=== EXECUTING SQL ===')
    print(f'SQL Query: {sql_sanitized}')
    
    try:
        results = execute_sql_query(sql_sanitized)
        if results:
            print('\n=== RESULTS ===')
            print('Customer Distribution by Country:')
            print('-' * 50)
            for row in results:
                country_code = row.get('COUNTRY_CODE', 'N/A')
                country_desc = row.get('COUNTRY_DESCRIPTION', 'N/A')
                customer_count = row.get('CUSTOMER_COUNT', row.get('CustomerCount', 0))
                print(f'{country_code}: {country_desc} - {customer_count} customers')
            
            # Check if we have international data
            international_countries = [row for row in results if row.get('COUNTRY_CODE') not in ['US', 'USA']]
            if international_countries:
                print(f'\n✅ SUCCESS: Found {len(international_countries)} international countries!')
                print('Enhanced international data is accessible through the pipeline.')
                
                # Show actual customer names from international countries
                print('\n=== SAMPLE INTERNATIONAL CUSTOMERS ===')
                international_query = """
                SELECT CUSTOMER_NAME, COUNTRY_CODE, COUNTRY_DESCRIPTION 
                FROM FIS_CUSTOMER_DIMENSION 
                WHERE CUSTOMER_KEY IS NOT NULL AND COUNTRY_CODE != 'US'
                ORDER BY COUNTRY_CODE
                """
                intl_results = execute_sql_query(international_query)
                if intl_results:
                    for customer in intl_results:
                        name = customer.get('CUSTOMER_NAME', 'N/A')
                        code = customer.get('COUNTRY_CODE', 'N/A')
                        country = customer.get('COUNTRY_DESCRIPTION', 'N/A')
                        print(f'  • {name} ({code} - {country})')
                        
            else:
                print('\n⚠️  WARNING: Only US customers found. International data may not be integrated.')
                
        else:
            print('No results returned')
    except Exception as e:
        print(f'❌ Error executing SQL: {e}')

if __name__ == "__main__":
    test_international_customers()