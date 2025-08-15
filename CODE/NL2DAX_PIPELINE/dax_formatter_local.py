"""
dax_formatter_local.py - Local DAX Query Formatting and Validation Module
=========================================================================

This module provides local DAX formatting and validation without depending on external APIs.
It includes basic formatting rules, syntax validation, and error detection for DAX queries.

Key Features:
- Local DAX formatting without external API dependencies
- Basic syntax validation and error detection
- Improved readability with proper indentation
- Robust error handling and graceful fallbacks
- No network connectivity required

Author: NL2DAX Pipeline Development Team
Last Updated: August 15, 2025
"""

import re


def format_and_validate_dax(dax_code):
    """
    Format and validate DAX code using local formatting rules.
    
    This function provides basic DAX formatting and validation without relying
    on external APIs. It handles:
    1. Basic syntax validation
    2. Indentation and line breaks
    3. Common formatting improvements
    4. Error detection for obvious syntax issues
    
    Args:
        dax_code (str): Raw DAX query string to be formatted and validated.
    
    Returns:
        tuple: A 2-tuple containing:
            - formatted_dax (str): Locally formatted DAX code with improved readability
            - errors (list): List of detected syntax errors or validation warnings
    
    Example:
        >>> formatted, errors = format_and_validate_dax("EVALUATE TOPN(5,'Table','Column',DESC)")
        >>> print(formatted)
        EVALUATE
        TOPN(
            5,
            'Table',
            'Column',
            DESC
        )
    """
    
    # Handle None or empty input
    if not dax_code or not dax_code.strip():
        return "", ["DAX code is empty or None"]
    
    # --- Step 1: Extract DAX code from LLM output ---
    # Clean up the input by removing markdown code fences and explanatory text
    extracted_dax = dax_code.strip()
    
    # Remove code fences if present
    if extracted_dax.startswith('```'):
        lines = extracted_dax.split('\n')
        # Remove first line (opening fence) and last line if it's a closing fence
        lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        extracted_dax = '\n'.join(lines).strip()
    
    # If we still have multiple lines, try to extract just the DAX part
    if '\n' in extracted_dax:
        lines = extracted_dax.split('\n')
        # Look for lines that contain DAX keywords
        dax_lines = []
        found_dax = False
        for line in lines:
            # Skip explanatory lines
            if any(phrase in line.lower() for phrase in ['here\'s', 'here is', 'following', 'below', 'query', 'returns']):
                continue
            # Look for DAX keywords
            if any(keyword in line.upper() for keyword in ['EVALUATE', 'SELECTCOLUMNS', 'FILTER', 'ADDCOLUMNS', 'TOPN', 'SUMMARIZE']):
                found_dax = True
            if found_dax:
                dax_lines.append(line)
        if dax_lines:
            extracted_dax = '\n'.join(dax_lines).strip()
    
    # Replace smart quotes with standard quotes for DAX execution
    extracted_dax = extracted_dax.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
    
    print(f"[DEBUG] DAX Formatter - Extracted code: {extracted_dax[:100]}...")
    
    # --- Step 2: Local DAX Formatting ---
    formatted_dax, errors = _format_dax_locally(extracted_dax)
    
    return formatted_dax, errors


def _format_dax_locally(dax_code):
    """
    Apply local DAX formatting rules for improved readability.
    
    Args:
        dax_code (str): Raw DAX code to format
        
    Returns:
        tuple: (formatted_dax, errors)
    """
    errors = []
    
    # Basic validation checks
    if 'ORDER BY' in dax_code.upper():
        errors.append("Invalid DAX syntax: 'ORDER BY' is not valid in DAX. Use TOPN for sorting.")
    
    if not dax_code.strip().upper().startswith('EVALUATE'):
        errors.append("DAX query should start with EVALUATE")
    
    # Check for balanced parentheses
    open_count = dax_code.count('(')
    close_count = dax_code.count(')')
    if open_count != close_count:
        errors.append(f"Unbalanced parentheses: {open_count} opening, {close_count} closing")
    
    # Basic formatting improvements
    formatted = dax_code
    
    # Add line breaks after EVALUATE
    formatted = formatted.replace('EVALUATE', 'EVALUATE\n')
    
    # Format common DAX functions with proper indentation
    formatted = _add_function_formatting(formatted)
    
    # Clean up extra whitespace
    lines = formatted.split('\n')
    formatted_lines = []
    for line in lines:
        if line.strip():  # Skip empty lines
            formatted_lines.append(line.rstrip())
    
    formatted = '\n'.join(formatted_lines)
    
    return formatted, errors


def _add_function_formatting(dax_code):
    """Add basic formatting for common DAX functions."""
    
    # Format TOPN function
    if 'TOPN(' in dax_code:
        # Simple pattern to add line breaks in TOPN
        dax_code = re.sub(r'TOPN\(\s*(\d+),\s*', r'TOPN(\n    \1,\n    ', dax_code)
    
    # Format SELECTCOLUMNS
    if 'SELECTCOLUMNS(' in dax_code:
        dax_code = re.sub(r'SELECTCOLUMNS\(\s*', r'SELECTCOLUMNS(\n    ', dax_code)
    
    # Format SUMMARIZE
    if 'SUMMARIZE(' in dax_code:
        dax_code = re.sub(r'SUMMARIZE\(\s*', r'SUMMARIZE(\n    ', dax_code)
    
    # Add indentation for nested functions
    lines = dax_code.split('\n')
    formatted_lines = []
    indent_level = 0
    
    for line in lines:
        # Count opening and closing parentheses to determine indentation
        stripped = line.strip()
        if stripped:
            # Adjust indent based on parentheses
            open_parens = line.count('(')
            close_parens = line.count(')')
            
            # Apply current indentation
            formatted_lines.append('    ' * indent_level + stripped)
            
            # Update indent level for next line
            indent_level += open_parens - close_parens
            indent_level = max(0, indent_level)  # Don't go negative
    
    return '\n'.join(formatted_lines)


# Demonstration and testing code for the local DAX formatter
if __name__ == "__main__":
    """
    Example usage and testing of the local DAX formatter functionality.
    """
    # Example DAX query for testing
    test_dax = "EVALUATE TOPN(5, 'FIS_CUSTOMER_DIMENSION', 'FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME], DESC)"
    
    print("Original DAX:")
    print(test_dax)
    print("\nFormatted DAX:")
    
    formatted, errors = format_and_validate_dax(test_dax)
    print(formatted)
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
    else:
        print("\nNo errors detected.")
