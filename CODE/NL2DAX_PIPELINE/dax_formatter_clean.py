"""
dax_formatter.py - DAX Query Formatting and Validation Module
============================================================

This module provides functionality to format and validate DAX queries using local
formatting rules. Previously used external DAXFormatter.com API, but now uses local
implementation for better reliability.

Key Features:
- Local DAX formatting without external API dependencies
- Syntax validation and error detection for DAX queries
- Configurable formatting options (line breaks, separators, annotations)
- Robust error handling for various DAX syntax issues
- No network connectivity required

Author: NL2DAX Pipeline Development Team
Last Updated: August 15, 2025
"""

from dax_formatter_local import format_and_validate_dax as format_locally


def format_and_validate_dax(dax_code):
    """
    Format and validate DAX code using local formatting (fallback from external API).
    
    This function now uses local formatting rules instead of the external DAXFormatter.com
    API which was experiencing connectivity issues (HTTP 404). The local implementation
    provides:
    1. Basic syntax validation and error detection
    2. Improved formatting with proper indentation and line breaks  
    3. Common DAX formatting best practices
    4. No dependency on external services
    
    Args:
        dax_code (str): Raw DAX query string to be formatted and validated.
    
    Returns:
        tuple: A 2-tuple containing:
            - formatted_dax (str): Locally formatted DAX code with improved readability
            - errors (list): List of detected syntax errors or validation warnings
    """
    
    # Use local formatting implementation
    return format_locally(dax_code)


# Demonstration and testing code for the DAX formatter functionality
if __name__ == "__main__":
    """
    Example usage and testing of the DAX formatter functionality.
    """
    # Example DAX query for testing - simple SUM aggregation
    dax = "EVALUATE TOPN(5, 'Table', 'Table'[Column], DESC)"
    
    print("Testing DAX Formatter:")
    print(f"Original: {dax}")
    
    formatted, errors = format_and_validate_dax(dax)
    print(f"Formatted:\n{formatted}")
    
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No errors detected.")
