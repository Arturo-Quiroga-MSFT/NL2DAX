"""
query_executor.py - DAX Query Execution Coordinator
==================================================

This module serves as the main coordinator for executing DAX queries against Power BI
semantic models and Analysis Services tabular models. It provides intelligent routing
between different execution methods based on platform capabilities and configuration.

Key Features:
- Multi-platform DAX execution support (Windows, macOS, Linux)
- Intelligent routing between HTTP/XMLA and native pyadomd execution
- Environment-based configuration for execution method selection
- Comprehensive error handling and platform-specific error messages
- Cross-platform compatibility with fallback mechanisms

Execution Methods:
1. HTTP/XMLA (Recommended): Cross-platform execution using REST APIs and Azure AD
2. pyadomd (Legacy): Native .NET execution requiring Mono on non-Windows platforms

Platform Compatibility:
- Windows: Full support for both HTTP/XMLA and pyadomd execution
- macOS: HTTP/XMLA (native), pyadomd (requires Mono installation)
- Linux: HTTP/XMLA (native), pyadomd (requires Mono installation)
- Containers: HTTP/XMLA preferred for cloud-native deployments

Configuration:
The execution method is controlled by the USE_XMLA_HTTP environment variable:
- USE_XMLA_HTTP=true: Use HTTP/XMLA execution (recommended for cross-platform)
- USE_XMLA_HTTP=false: Use pyadomd execution (requires platform-specific setup)

Dependencies:
- xmla_http_executor: HTTP-based XMLA execution (cross-platform)
- pyadomd: .NET-based DAX execution (Windows native, Mono on other platforms)
- pythonnet: Python-.NET interop layer (required for pyadomd on non-Windows)

Author: NL2DAX Pipeline Development Team
Last Updated: August 14, 2025
"""

import os  # Operating system interface for environment variable access

# Environment-based configuration for DAX execution method selection
# This setting determines whether to use HTTP/XMLA (cross-platform) or pyadomd (native .NET)
USE_XMLA_HTTP = os.getenv("USE_XMLA_HTTP", "false").lower() in ("1", "true", "yes")


def execute_dax_query(dax_query):
    """
    Execute a DAX query against a Power BI semantic model or Analysis Services tabular model.
    
    This function serves as the main entry point for DAX query execution, intelligently
    routing between different execution methods based on platform capabilities and
    configuration. It provides a unified interface that abstracts the complexity of
    different execution approaches.
    
    Execution Method Selection:
    The function automatically selects the appropriate execution method based on the
    USE_XMLA_HTTP environment variable:
    
    1. HTTP/XMLA Execution (USE_XMLA_HTTP=true):
       - Cross-platform compatibility (Windows, macOS, Linux)
       - Uses REST APIs with Azure AD authentication
       - No additional runtime dependencies required
       - Recommended for cloud deployments and containers
       - Handles authentication via service principal or user credentials
    
    2. pyadomd Execution (USE_XMLA_HTTP=false):
       - Native .NET execution with optimal performance
       - Requires platform-specific setup (Mono on non-Windows)
       - Direct XMLA protocol communication
       - Legacy approach with additional dependencies
    
    Args:
        dax_query (str): Valid DAX expression to execute against the tabular model.
                        Should be a complete DAX statement, typically starting with
                        EVALUATE for table expressions or containing measure definitions.
    
    Returns:
        list: List of dictionaries representing query results, where each dictionary
              represents a row with column names as keys and cell values as values.
              
              Example return format:
              [
                  {"CustomerName": "John Doe", "TotalSales": 1500.00},
                  {"CustomerName": "Jane Smith", "TotalSales": 2300.50}
              ]
    
    Raises:
        RuntimeError: When DAX execution fails due to:
            - Authentication failures (invalid credentials or permissions)
            - Network connectivity issues (unreachable XMLA endpoint)
            - Missing runtime dependencies (Mono, pythonnet, pyadomd)
            - Invalid DAX syntax or semantic errors
            - Power BI service or Analysis Services unavailability
        
        ValueError: When required configuration is missing:
            - XMLA_CONNECTION_STRING not set for pyadomd execution
            - Required Power BI environment variables missing for HTTP execution
    
    Platform Requirements:
    
    HTTP/XMLA Execution (Cross-platform):
        - Python requests library
        - Valid Azure AD credentials (service principal or user)
        - Network access to Power BI service or Analysis Services
        - Power BI Premium capacity with XMLA endpoints enabled
    
    pyadomd Execution:
        Windows:
            - .NET Framework or .NET Core
            - pyadomd Python package
            - pythonnet for Python-.NET interop
        
        macOS/Linux:
            - Mono runtime environment
            - pyadomd Python package
            - pythonnet for Python-.NET interop
            - Additional setup: brew install mono (macOS)
    
    Error Handling:
        The function provides comprehensive error handling with platform-specific
        guidance for resolving common issues:
        
        - Missing dependencies: Clear installation instructions
        - Authentication failures: Credential validation guidance
        - Network issues: Connectivity troubleshooting steps
        - Configuration errors: Environment variable validation
    
    Performance Considerations:
        - HTTP/XMLA: Network latency, authentication token overhead
        - pyadomd: Native performance, but platform setup complexity
        - Choose HTTP/XMLA for cloud deployments, pyadomd for on-premises performance
    
    Example Usage:
        >>> dax = "EVALUATE TOPN(10, 'Customers', 'Customers'[TotalSales], DESC)"
        >>> results = execute_dax_query(dax)
        >>> for row in results:
        ...     print(f"{row['CustomerName']}: {row['TotalSales']}")
    """
    
    # Route to HTTP/XMLA execution for cross-platform compatibility
    if USE_XMLA_HTTP:
        try:
            # Import HTTP-based XMLA executor (cross-platform implementation)
            from xmla_http_executor import execute_dax_via_http
            return execute_dax_via_http(dax_query)
        except Exception as e:
            # Provide detailed error message with troubleshooting guidance
            raise RuntimeError(
                "DAX over HTTP/XMLA failed. Check PBI_* env vars, XMLA endpoint, dataset name, and permissions. "
                f"Root error: {e}"
            )

    # Route to pyadomd execution for native .NET performance
    # Delay import to avoid module load crashes if dependencies are missing
    try:
        from pyadomd import Pyadomd  # .NET-based DAX execution library
    except Exception as e:
        # Provide platform-specific installation guidance for missing dependencies
        raise RuntimeError(
            "Cannot execute DAX: pyadomd import failed. "
            "Install Mono (`brew install mono`) and pythonnet (`pip install pyadomd pythonnet`)."
        )
    
    # Retrieve XMLA connection string from environment configuration
    xmla_conn_str = os.getenv("XMLA_CONNECTION_STRING")
    if not xmla_conn_str:
        raise ValueError("XMLA_CONNECTION_STRING is not set in environment")
    
    # Execute DAX query using native pyadomd connection
    with Pyadomd(xmla_conn_str) as conn:
        with conn.cursor() as cur:
            # Execute the DAX query against the tabular model
            cur.execute(dax_query)
            
            # Extract column names from cursor description
            columns = [desc[0] for desc in cur.description]
            
            # Fetch all result rows from the executed query
            rows = cur.fetchall()
            
            # Convert results to list of dictionaries for consistent return format
            results = [dict(zip(columns, row)) for row in rows]
    
    return results


# Interactive testing and demonstration functionality
if __name__ == '__main__':
    """
    Interactive DAX query execution for testing and demonstration purposes.
    
    This section provides a command-line interface for testing DAX query execution
    functionality. It allows developers to:
    - Test different DAX expressions interactively
    - Validate execution method configuration
    - Debug authentication and connectivity issues
    - Examine query result formatting
    
    Usage:
        python query_executor.py
        Enter DAX query for execution: EVALUATE 'Customers'
    """
    import json  # JSON formatting for readable result display
    
    # Prompt user for DAX query input
    dax = input("Enter DAX query for execution: ")
    
    try:
        # Execute the user-provided DAX query
        res = execute_dax_query(dax)
        
        # Display results in formatted JSON for readability
        print(json.dumps(res, indent=2))
        
    except Exception as e:
        # Display error information with debugging context
        print(f"Error executing DAX: {e}")
