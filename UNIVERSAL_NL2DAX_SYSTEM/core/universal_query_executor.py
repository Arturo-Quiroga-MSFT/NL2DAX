"""
universal_query_executor.py - Universal Query Execution Engine
==============================================================

This module provides execution capabilities for both SQL and DAX queries generated
by the universal NL2DAX system. It handles database connections, query execution,
result formatting, and error handling in a unified interface.

Key Features:
- SQL execution against any database using pyodbc
- DAX execution against Power BI/Analysis Services using pyadomd
- Unified result formatting for consistent display
- Comprehensive error handling and logging
- Performance monitoring and query timing
- Result limitation and memory management

Author: NL2DAX Pipeline Development Team
Last Updated: August 17, 2025
"""

import os
import time
import json
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from multiple locations
load_dotenv()  # Load from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))  # Load from main project
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))  # Load from Universal system
print(f"[DEBUG] Environment loading - PBI_TENANT_ID: {os.getenv('PBI_TENANT_ID', 'NOT_SET')[:8]}...")
print(f"[DEBUG] Environment loading - PBI_XMLA_ENDPOINT: {os.getenv('PBI_XMLA_ENDPOINT', 'NOT_SET')}")
print(f"[DEBUG] Environment loading - PBI_DATASET_NAME: {os.getenv('PBI_DATASET_NAME', 'NOT_SET')}")

@dataclass
class QueryResult:
    """Result of query execution"""
    success: bool
    query_type: str  # 'SQL' or 'DAX'
    query: str
    execution_time: float
    row_count: int
    data: List[Dict[str, Any]]
    error_message: Optional[str] = None
    column_names: Optional[List[str]] = None

class UniversalQueryExecutor:
    """Universal query executor for both SQL and DAX queries"""
    
    def __init__(self):
        """Initialize the universal query executor"""
        self.sql_connection_string = self._build_sql_connection_string()
        self.xmla_connection_string = self._build_xmla_connection_string()
        
    def _build_sql_connection_string(self) -> Optional[str]:
        """Build SQL database connection string from environment variables"""
        try:
            # Support multiple naming conventions for database credentials
            server = (os.getenv('DB_SERVER') or 
                     os.getenv('AZURE_SQL_SERVER') or 
                     os.getenv('SQL_SERVER'))
            database = (os.getenv('DB_DATABASE') or 
                       os.getenv('AZURE_SQL_DB') or 
                       os.getenv('SQL_DATABASE'))
            username = (os.getenv('DB_USERNAME') or 
                       os.getenv('AZURE_SQL_USER') or 
                       os.getenv('SQL_USERNAME') or 
                       os.getenv('DB_USER'))
            password = (os.getenv('DB_PASSWORD') or 
                       os.getenv('AZURE_SQL_PASSWORD') or 
                       os.getenv('SQL_PASSWORD') or 
                       os.getenv('DB_PASS'))
            driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
            
            if not all([server, database, username, password]):
                print("[WARN] SQL connection: Missing database credentials")
                return None
            
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            )
        except Exception as e:
            print(f"[ERROR] Failed to build SQL connection string: {e}")
            return None
    
    def _build_xmla_connection_string(self) -> Optional[str]:
        """Build XMLA connection string for DAX execution"""
        try:
            # Check for Power BI credentials
            tenant_id = os.getenv('PBI_TENANT_ID') or os.getenv('TENANT_ID')
            client_id = os.getenv('PBI_CLIENT_ID') or os.getenv('CLIENT_ID')
            client_secret = os.getenv('PBI_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
            xmla_endpoint = os.getenv('PBI_XMLA_ENDPOINT')
            
            if not all([tenant_id, client_id, client_secret, xmla_endpoint]):
                print("[WARN] DAX execution: Missing Power BI/XMLA credentials")
                return None
            
            return (
                f"Provider=MSOLAP;"
                f"Data Source={xmla_endpoint};"
                f"User ID=app:{client_id}@{tenant_id};"
                f"Password={client_secret};"
                "Persist Security Info=True;"
                "Impersonation Level=Impersonate;"
            )
        except Exception as e:
            print(f"[ERROR] Failed to build XMLA connection string: {e}")
            return None
    
    def execute_sql_query(self, sql_query: str, limit_rows: int = 100) -> QueryResult:
        """
        Execute SQL query against the database
        
        Args:
            sql_query: SQL query to execute
            limit_rows: Maximum number of rows to return (default 100)
            
        Returns:
            QueryResult with execution details and data
        """
        start_time = time.time()
        
        if not self.sql_connection_string:
            return QueryResult(
                success=False,
                query_type="SQL",
                query=sql_query,
                execution_time=0,
                row_count=0,
                data=[],
                error_message="SQL connection not configured. Please check database credentials."
            )
        
        try:
            import pyodbc
            
            print(f"[DEBUG] Executing SQL query (limit: {limit_rows} rows)")
            
            with pyodbc.connect(self.sql_connection_string) as conn:
                cursor = conn.cursor()
                
                # Add TOP clause to limit results if not already present
                limited_query = self._add_limit_to_sql(sql_query, limit_rows)
                
                cursor.execute(limited_query)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch results
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Handle different data types for JSON serialization
                        if value is None:
                            row_dict[columns[i]] = None
                        elif isinstance(value, (int, float, str, bool)):
                            row_dict[columns[i]] = value
                        else:
                            # Convert datetime, decimal, etc. to string
                            row_dict[columns[i]] = str(value)
                    data.append(row_dict)
                
                execution_time = time.time() - start_time
                
                return QueryResult(
                    success=True,
                    query_type="SQL",
                    query=limited_query,
                    execution_time=execution_time,
                    row_count=len(data),
                    data=data,
                    column_names=columns
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"SQL execution failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            
            return QueryResult(
                success=False,
                query_type="SQL",
                query=sql_query,
                execution_time=execution_time,
                row_count=0,
                data=[],
                error_message=error_msg
            )
    
    def execute_dax_query(self, dax_query: str, limit_rows: int = 100) -> QueryResult:
        """
        Execute DAX query using HTTP/XMLA (proven working method)
        
        Args:
            dax_query: DAX query to execute
            limit_rows: Maximum number of rows to return (default 100)
            
        Returns:
            QueryResult with execution details and data
        """
        start_time = time.time()
        
        try:
            # Import the proven HTTP/XMLA executor from working pipeline
            import sys
            
            # Add the working pipeline directory to path
            pipeline_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       'CODE', 'NL2DAX_PIPELINE')
            if pipeline_path not in sys.path:
                sys.path.insert(0, pipeline_path)
            
            try:
                from xmla_http_executor import execute_dax_via_http
                print(f"[DEBUG] Successfully imported HTTP/XMLA executor from: {pipeline_path}")
            except ImportError as e:
                return QueryResult(
                    success=False,
                    query_type="DAX",
                    query=dax_query,
                    execution_time=time.time() - start_time,
                    row_count=0,
                    data=[],
                    error_message=f"Could not import DAX HTTP/XMLA executor: {str(e)}. Please ensure the NL2DAX pipeline is available."
                )
            
            # Check if required Power BI environment variables are set
            required_vars = ['PBI_TENANT_ID', 'PBI_CLIENT_ID', 'PBI_CLIENT_SECRET', 'PBI_XMLA_ENDPOINT', 'PBI_DATASET_NAME']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                return QueryResult(
                    success=False,
                    query_type="DAX",
                    query=dax_query,
                    execution_time=time.time() - start_time,
                    row_count=0,
                    data=[],
                    error_message=f"DAX execution requires Power BI environment variables: {', '.join(missing_vars)}. Please configure Power BI credentials for HTTP/XMLA execution."
                )
            
            print(f"[DEBUG] Executing DAX query via HTTP/XMLA (limit: {limit_rows} rows)")
            
            # Add TOPN limit if specified and query doesn't already have it
            limited_query = self._add_limit_to_dax(dax_query, limit_rows)
            
            # Execute DAX query using proven HTTP/XMLA method
            data = execute_dax_via_http(limited_query)
            
            # Extract column names from first row (if any data)
            columns = list(data[0].keys()) if data else []
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                query_type="DAX",
                query=limited_query,
                execution_time=execution_time,
                row_count=len(data),
                data=data,
                column_names=columns
            )
                    
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"DAX execution failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            print(f"[DEBUG] Full error traceback:")
            traceback.print_exc()
            
            return QueryResult(
                success=False,
                query_type="DAX",
                query=dax_query,
                execution_time=execution_time,
                row_count=0,
                data=[],
                error_message=error_msg
            )
    
    def _add_limit_to_sql(self, sql_query: str, limit: int) -> str:
        """Add TOP clause to SQL query if not already present"""
        sql_upper = sql_query.upper().strip()
        
        # Check if query already has TOP, LIMIT, or is not a SELECT
        if 'TOP ' in sql_upper or 'LIMIT ' in sql_upper or not sql_upper.startswith('SELECT'):
            return sql_query
        
        # Insert TOP clause after SELECT
        parts = sql_query.split(' ', 1)
        if len(parts) >= 2:
            return f"{parts[0]} TOP {limit} {parts[1]}"
        
        return sql_query
    
    def _add_limit_to_dax(self, dax_query: str, limit: int) -> str:
        """Add row limit to DAX query if not already present"""
        dax_upper = dax_query.upper().strip()
        
        # Check if query already has TOPN
        if 'TOPN(' in dax_upper:
            return dax_query
        
        # Check if it's an EVALUATE statement
        if dax_upper.startswith('EVALUATE'):
            # Wrap the existing query in TOPN
            return f"EVALUATE\nTOPN(\n    {limit},\n    {dax_query[8:].strip()}\n)"
        
        return dax_query
    
    def format_results_as_table(self, result: QueryResult, max_width: int = 80) -> str:
        """
        Format query results as a readable ASCII table
        
        Args:
            result: QueryResult object with data
            max_width: Maximum width for each column
            
        Returns:
            Formatted table string
        """
        if not result.success or not result.data:
            return f"No data returned. {result.error_message or ''}"
        
        data = result.data
        columns = result.column_names or list(data[0].keys())
        
        # Calculate column widths
        col_widths = {}
        for col in columns:
            # Start with column name length
            col_widths[col] = len(col)
            
            # Check data lengths
            for row in data:
                value_str = str(row.get(col, ''))
                col_widths[col] = max(col_widths[col], len(value_str))
            
            # Apply maximum width limit
            col_widths[col] = min(col_widths[col], max_width)
        
        # Create formatted table
        header = " | ".join([col.ljust(col_widths[col]) for col in columns])
        separator = "-+-".join(['-' * col_widths[col] for col in columns])
        
        table_lines = [header, separator]
        
        for row in data:
            formatted_row = []
            for col in columns:
                value_str = str(row.get(col, ''))
                # Truncate if too long
                if len(value_str) > col_widths[col]:
                    value_str = value_str[:col_widths[col]-3] + '...'
                formatted_row.append(value_str.ljust(col_widths[col]))
            table_lines.append(" | ".join(formatted_row))
        
        return '\n'.join(table_lines)
    
    def format_results_as_json(self, result: QueryResult, indent: int = 2) -> str:
        """Format query results as JSON"""
        if not result.success:
            return json.dumps({
                "error": result.error_message,
                "execution_time": result.execution_time
            }, indent=indent)
        
        return json.dumps({
            "success": True,
            "query_type": result.query_type,
            "execution_time": result.execution_time,
            "row_count": result.row_count,
            "data": result.data
        }, indent=indent)
    
    def get_execution_summary(self, result: QueryResult) -> str:
        """Get a summary of query execution"""
        if result.success:
            return (f"✅ {result.query_type} executed successfully: "
                   f"{result.row_count} rows in {result.execution_time:.3f}s")
        else:
            return (f"❌ {result.query_type} execution failed: "
                   f"{result.error_message} ({result.execution_time:.3f}s)")

# Example usage and testing functions
def test_sql_execution():
    """Test SQL execution functionality"""
    executor = UniversalQueryExecutor()
    
    test_query = "SELECT TOP 5 * FROM FIS_CUSTOMER_DIMENSION ORDER BY CUSTOMER_NAME"
    result = executor.execute_sql_query(test_query)
    
    print("SQL Execution Test:")
    print(executor.get_execution_summary(result))
    
    if result.success:
        print("\nData Preview:")
        print(executor.format_results_as_table(result))
    
    return result

def test_dax_execution():
    """Test DAX execution functionality"""
    executor = UniversalQueryExecutor()
    
    test_query = """
    EVALUATE
    TOPN(
        5,
        'FIS_CUSTOMER_DIMENSION',
        'FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME], ASC
    )
    """
    
    result = executor.execute_dax_query(test_query)
    
    print("DAX Execution Test:")
    print(executor.get_execution_summary(result))
    
    if result.success:
        print("\nData Preview:")
        print(executor.format_results_as_table(result))
    
    return result

if __name__ == "__main__":
    print("Universal Query Executor Test")
    print("=" * 40)
    
    # Test SQL execution
    test_sql_execution()
    
    print("\n" + "=" * 40)
    
    # Test DAX execution
    test_dax_execution()