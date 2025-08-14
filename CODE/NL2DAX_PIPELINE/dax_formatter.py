"""
dax_formatter.py - DAX Query Formatting and Validation Module
============================================================

This module provides functionality to format and validate DAX queries using the external
DAXFormatter.com API service. It ensures DAX queries are properly formatted, syntactically
correct, and follow best practices for readability and maintainability.

Key Features:
- External API integration with DAXFormatter.com for professional DAX formatting
- Syntax validation and error detection for DAX queries
- Configurable formatting options (line breaks, separators, annotations)
- Robust error handling for network and API failures
- Graceful fallback when formatting service is unavailable

Dependencies:
- requests: HTTP client for API communication
- Internet connectivity for DAXFormatter.com API access

Author: NL2DAX Pipeline Development Team
Last Updated: August 14, 2025
"""

import requests  # HTTP client for DAXFormatter.com API communication


def format_and_validate_dax(dax_code):
    """
    Format and validate DAX code using the external DAXFormatter.com API service.
    
    This function sends DAX code to the professional DAXFormatter.com service for:
    1. Syntax validation and error detection
    2. Professional formatting with proper indentation and line breaks  
    3. Best practice compliance checking
    4. Improved readability and maintainability
    
    The DAXFormatter.com service is widely used in the Power BI community and provides
    enterprise-grade DAX formatting capabilities that would be difficult to replicate
    locally. It handles complex DAX syntax, nested functions, and formatting edge cases.
    
    Args:
        dax_code (str): Raw DAX query string to be formatted and validated.
                       Can contain any valid DAX expressions, measures, or calculated columns.
    
    Returns:
        tuple: A 2-tuple containing:
            - formatted_dax (str): Professionally formatted DAX code with proper indentation,
                                  line breaks, and spacing. Returns original code if formatting fails.
            - errors (list): List of syntax errors, warnings, or validation messages.
                           Empty list indicates no syntax errors detected.
    
    Example:
        >>> dax_query = "SUM(Sales[Amount])"
        >>> formatted, errors = format_and_validate_dax(dax_query)
        >>> print(formatted)
        SUM ( Sales[Amount] )
        >>> print(errors)
        []
    
    API Configuration:
        The function uses specific formatting options optimized for readability:
        - Separator: "," (comma separation for function parameters)
        - Annotations: False (excludes metadata annotations for cleaner output)
        - ShortenNames: False (preserves full table/column names for clarity)
        - AddLineBreaks: True (adds line breaks for improved readability)
        - IncludeErrors: True (returns syntax errors and validation warnings)
    
    Error Handling:
        - Network failures: Returns original DAX with error message
        - API errors: Returns original DAX with HTTP error details
        - JSON parsing errors: Returns original DAX with parsing error details
        - Timeout: 10-second timeout prevents hanging on slow connections
    
    Performance Notes:
        - External API call adds network latency (typically 100-500ms)
        - Consider caching formatted results for repeated queries
        - Timeout set to 10 seconds to balance responsiveness and reliability
    """
    # DAXFormatter.com API endpoint for professional DAX formatting service
    url = "https://www.daxformatter.com/api/daxformatter/"
    
    # Configure formatting options for optimal readability and validation
    payload = {
        "Dax": dax_code,                    # The raw DAX code to format and validate
        "Separator": ",",                   # Use comma separation for function parameters
        "Annotations": False,               # Exclude metadata annotations for cleaner output
        "ShortenNames": False,              # Preserve full table/column names for clarity
        "AddLineBreaks": True,              # Add line breaks for improved readability
        "IncludeErrors": True               # Return syntax errors and validation warnings
    }
    
    try:
        # Send DAX code to external formatting service with 10-second timeout
        # Timeout prevents hanging on slow connections while allowing reasonable processing time
        response = requests.post(url, json=payload, timeout=10)
        
        # Check for successful HTTP response with valid content
        if response.status_code == 200 and response.text.strip():
            try:
                # Parse JSON response from DAXFormatter.com API
                result = response.json()
                
                # Extract formatted DAX and any syntax errors from API response
                formatted_dax = result.get("FormattedDax", "")
                errors = result.get("Errors", [])
                
                # Handle edge case where API returns empty results
                if not formatted_dax and not errors:
                    return dax_code, ["DAX Formatter API returned no formatted DAX and no errors."]
                
                return formatted_dax, errors
                
            except Exception as e:
                # Handle JSON parsing errors from malformed API responses
                return dax_code, [f"DAX Formatter API returned invalid JSON: {e}"]
        else:
            # Handle HTTP errors, API downtime, or invalid responses
            return dax_code, [f"DAX Formatter API error: HTTP {response.status_code} - {response.text.strip()}"]
            
    except Exception as e:
        # Handle network errors, timeouts, and other connection issues
        # Gracefully fallback to original DAX code when external service unavailable
        return dax_code, [f"Exception during DAX Formatter API call: {e}"]


# Demonstration and testing code for the DAX formatter functionality
if __name__ == "__main__":
    """
    Example usage and testing of the DAX formatter functionality.
    
    This section demonstrates how to use the format_and_validate_dax function
    and provides a simple test case that can be run independently.
    """
    # Example DAX query for testing - simple SUM aggregation
    dax = "SUM('Table'[Column])"
    
    # Format and validate the example DAX query
    formatted, errors = format_and_validate_dax(dax)
    
    # Display the formatted result
    print("Formatted DAX:", formatted)
    
    # Display any syntax errors or validation warnings
    if errors:
        print("Errors:", errors)
    else:
        print("No syntax errors detected.")
