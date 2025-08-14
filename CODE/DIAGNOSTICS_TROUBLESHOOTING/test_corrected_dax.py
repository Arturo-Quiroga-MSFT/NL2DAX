#!/usr/bin/env python3
"""
Test the corrected DAX query for US customers
"""

import os
import sys
from dotenv import load_dotenv

# Add the CODE directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'CODE'))

load_dotenv()

def test_corrected_dax():
    """Test the corrected DAX query"""
    # Import after adding to path
    try:
        from xmla_http_executor import execute_dax_via_http
    except ImportError as e:
        print(f"[ERROR] Could not import xmla_http_executor: {e}")
        return False
    
    # Corrected DAX query - simpler version first
    dax_query = '''EVALUATE  
SELECTCOLUMNS(  
    FILTER(  
        'FIS_CUSTOMER_DIMENSION',  
        'FIS_CUSTOMER_DIMENSION'[COUNTRY_DESCRIPTION] = "United States"  
    ),  
    "CustomerKey", 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_KEY],  
    "CustomerID", 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_ID],  
    "CustomerName", 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME],  
    "Country", 'FIS_CUSTOMER_DIMENSION'[COUNTRY_DESCRIPTION]  
)'''
    
    print(f"[DEBUG] Testing corrected DAX query:")
    print(f"[DEBUG] {dax_query}")
    
    try:
        result = execute_dax_via_http(dax_query)
        print(f"[SUCCESS] Query executed successfully!")
        print(f"[INFO] Result count: {len(result) if result else 0}")
        if result:
            print(f"[INFO] First few rows:")
            for i, row in enumerate(result[:3]):
                print(f"  Row {i+1}: {row}")
        return True
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        return False

def test_minimal_dax():
    """Test with a minimal DAX query first"""
    try:
        from xmla_http_executor import execute_dax_via_http
    except ImportError as e:
        print(f"[ERROR] Could not import xmla_http_executor: {e}")
        return False
    
    # Very simple query to test connectivity
    simple_query = 'EVALUATE ROW("Test", "Value")'
    
    print(f"[DEBUG] Testing minimal DAX query: {simple_query}")
    
    try:
        result = execute_dax_via_http(simple_query)
        print(f"[SUCCESS] Minimal query worked: {result}")
        return True
    except Exception as e:
        print(f"[ERROR] Minimal query failed: {e}")
        return False

if __name__ == "__main__":
    print("[INFO] Testing corrected DAX query...")
    
    # First test minimal query
    print("\n=== Testing Minimal Query ===")
    if test_minimal_dax():
        print("\n=== Testing Corrected US Customers Query ===")
        test_corrected_dax()
    else:
        print("[ERROR] Basic connectivity failed. Check your environment variables.")
