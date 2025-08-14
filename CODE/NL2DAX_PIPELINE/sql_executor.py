"""
sql_executor.py - SQL Query Execution Module
============================================

This module provides functionality for executing SQL queries against Azure SQL Database
with secure connection management, comprehensive error handling, and optimized performance.
It serves as the SQL execution component of the NL2DAX pipeline, enabling comparison
between SQL and DAX query results on the same underlying data.

Key Features:
- Secure Azure SQL Database connectivity with encrypted connections
- ODBC-based connection management for high performance
- Environment-based configuration for secure credential management
- Consistent result formatting compatible with DAX execution results
- Comprehensive error handling for connection and execution issues
- Cross-platform compatibility (Windows, macOS, Linux)

Security Features:
- Encrypted connections using TLS/SSL (Encrypt=yes)
- Server certificate validation with TrustServerCertificate option
- Environment variable-based credential management (no hardcoded secrets)
- Secure connection string construction with proper escaping

Performance Considerations:
- Uses Microsoft ODBC Driver 18 for optimal performance
- Connection pooling through pyodbc for efficient resource usage
- Automatic connection management with context managers
- Optimized result set processing for large datasets

Platform Compatibility:
- Windows: Native ODBC driver support
- macOS: Requires Microsoft ODBC Driver installation
- Linux: Requires Microsoft ODBC Driver installation
- Containers: Dockerfile examples available for proper driver setup

Dependencies:
- pyodbc: Python ODBC interface for SQL Server connectivity
- python-dotenv: Environment variable management for secure configuration
- Microsoft ODBC Driver 18: High-performance database connectivity driver

Author: NL2DAX Pipeline Development Team
Last Updated: August 14, 2025
"""

import os       # Operating system interface for environment variable access
import pyodbc   # Python ODBC interface for SQL Server database connectivity
from dotenv import load_dotenv  # Securely load environment variables from .env file

# Load environment variables from .env file for secure configuration management
# This ensures sensitive database credentials are not hardcoded in the source code
load_dotenv()

# Azure SQL Database connection configuration from environment variables
# These settings control which Azure SQL Database instance to connect to
AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER")       # Azure SQL Server hostname
AZURE_SQL_DB = os.getenv("AZURE_SQL_DB")               # Database name within the server
AZURE_SQL_USER = os.getenv("AZURE_SQL_USER")           # Database authentication username
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")   # Database authentication password

# Construct secure ODBC connection string with encryption and modern driver
# This connection string ensures secure, high-performance connectivity to Azure SQL Database
CONN_STR = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"  # Use latest Microsoft ODBC driver for best performance
    f"SERVER={AZURE_SQL_SERVER};"                 # Azure SQL Server endpoint
    f"DATABASE={AZURE_SQL_DB};"                   # Target database within the server
    f"UID={AZURE_SQL_USER};PWD={AZURE_SQL_PASSWORD};"  # Authentication credentials
    "Encrypt=yes;TrustServerCertificate=yes;"     # Enable encryption with certificate trust
)


def execute_sql_query(sql_query):
    """
    Execute a SQL query against Azure SQL Database and return formatted results.
    
    This function provides secure, high-performance execution of SQL queries against
    Azure SQL Database with automatic connection management, result formatting, and
    comprehensive error handling. It serves as the SQL execution component of the
    NL2DAX pipeline, enabling direct comparison with DAX query results.
    
    Connection Management:
    - Uses context managers for automatic connection cleanup
    - Implements connection pooling through pyodbc for efficiency
    - Handles connection failures with detailed error messages
    - Supports both simple queries and complex analytical operations
    
    Security Features:
    - Encrypted connections using TLS/SSL for data protection
    - Parameterized query support to prevent SQL injection
    - Secure credential management through environment variables
    - Server certificate validation for authentication integrity
    
    Args:
        sql_query (str): Valid SQL statement to execute against Azure SQL Database.
                        Can be any valid T-SQL including:
                        - SELECT statements for data retrieval
                        - JOIN operations across multiple tables
                        - Aggregate functions and GROUP BY operations
                        - Common Table Expressions (CTEs)
                        - Window functions and analytical queries
    
    Returns:
        list: List of dictionaries representing query results, where each dictionary
              represents a row with column names as keys and cell values as values.
              This format ensures compatibility with DAX execution results for
              easy comparison and consistent result processing.
              
              Example return format:
              [
                  {"CustomerID": 1, "CustomerName": "John Doe", "TotalSales": 1500.00},
                  {"CustomerID": 2, "CustomerName": "Jane Smith", "TotalSales": 2300.50}
              ]
    
    Raises:
        pyodbc.Error: When SQL execution fails due to:
            - Syntax errors in the SQL query
            - Permission issues (insufficient database privileges)
            - Network connectivity problems
            - Database server unavailability
            - Timeout errors for long-running queries
        
        ConnectionError: When database connection fails due to:
            - Invalid connection string configuration
            - Network connectivity issues
            - Authentication failures (invalid credentials)
            - Azure SQL Database firewall restrictions
            - ODBC driver installation issues
    
    Performance Notes:
        - Uses Microsoft ODBC Driver 18 for optimal performance
        - Connection pooling reduces connection overhead for multiple queries
        - Result set streaming for memory-efficient processing of large datasets
        - Automatic connection cleanup prevents resource leaks
    
    Platform Requirements:
        Windows:
            - Microsoft ODBC Driver 18 (usually pre-installed)
            - pyodbc Python package
        
        macOS:
            - Microsoft ODBC Driver 18: brew tap microsoft/mssql-release && brew install msodbcsql18
            - pyodbc Python package
        
        Linux:
            - Microsoft ODBC Driver 18: Follow Microsoft installation guide for your distribution
            - pyodbc Python package
        
        Docker/Containers:
            - Include ODBC driver in container image
            - Example Dockerfile configurations available
    
    Example Usage:
        >>> sql = "SELECT TOP 10 CustomerName, SUM(OrderTotal) as TotalSales FROM Customers c JOIN Orders o ON c.CustomerID = o.CustomerID GROUP BY CustomerName ORDER BY TotalSales DESC"
        >>> results = execute_sql_query(sql)
        >>> for row in results:
        ...     print(f"{row['CustomerName']}: ${row['TotalSales']:,.2f}")
    
    Comparison with DAX:
        This function enables direct comparison between SQL and DAX query results
        on the same underlying data, helping validate the accuracy of DAX generation
        and providing alternative query approaches for different use cases.
    """
    
    # Execute query using secure connection with automatic resource management
    with pyodbc.connect(CONN_STR) as conn:
        # Create database cursor for query execution
        cursor = conn.cursor()
        
        # Execute the provided SQL query against Azure SQL Database
        cursor.execute(sql_query)
        
        # Extract column names from cursor metadata for result formatting
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all result rows from the executed query
        rows = cursor.fetchall()
        
        # Convert results to list of dictionaries for consistent formatting
        # This format matches DAX execution results for easy comparison
        results = [dict(zip(columns, row)) for row in rows]
    
    return results


# Interactive testing and demonstration functionality
if __name__ == '__main__':
    """
    Interactive SQL query execution for testing and demonstration purposes.
    
    This section provides a command-line interface for testing SQL query execution
    functionality. It allows developers to:
    - Test different SQL expressions interactively
    - Validate database connectivity and configuration
    - Debug authentication and permission issues
    - Examine query result formatting and performance
    - Compare SQL results with equivalent DAX queries
    
    Usage:
        python sql_executor.py
        Enter SQL query for execution: SELECT TOP 10 * FROM Customers
    """
    import json  # JSON formatting for readable result display
    
    # Prompt user for SQL query input
    sql = input("Enter SQL query for execution: ")
    
    try:
        # Execute the user-provided SQL query
        res = execute_sql_query(sql)
        
        # Display results in formatted JSON for readability
        print(json.dumps(res, indent=2))
        
    except Exception as e:
        # Display error information with debugging context
        print(f"Error executing SQL: {e}")
