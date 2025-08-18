"""
main_universal.py - Universal NL2SQL & NL2DAX Pipeline
======================================================

This is the new main entry point that uses the universal, database-agnostic
query generation system. It replaces hardcoded schema dependencies with
intelligent AI-powered analysis that works with any database.

Key Features:
- Works with any SQL database schema
- Adapts to any Power BI/Fabric semantic model
- Business intent-driven query generation
- Automatic schema discovery and pattern recognition
- Embedded best practices in AI prompts

Usage:
    python main_universal.py

Author: NL2DAX Pipeline Development Team
Last Updated: August 16, 2025
"""

import os
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# Import the new universal interface
from universal_query_interface import UniversalQueryInterface, QueryType, AnalysisType
from sql_executor import execute_sql_query
from query_executor import execute_dax_query

# Load environment variables
load_dotenv()

def colored_banner(title, color_code="94"):
    """Create colored ASCII banner for output sections"""
    banner_text = f"\n{'='*10} {title} {'='*10}\n"
    return f"\033[{color_code}m{banner_text}\033[0m"

def plain_banner(title):
    """Plain banner for file output"""
    return f"\n{'='*10} {title} {'='*10}\n"

def sanitize_query(query_text):
    """Sanitize query by removing smart quotes and extra formatting"""
    if not query_text:
        return ""
    
    # Replace smart quotes with standard quotes
    sanitized = query_text.replace(''', "'").replace(''', "'")
    sanitized = sanitized.replace('"', '"').replace('"', '"')
    
    # Clean up extra whitespace
    sanitized = re.sub(r'\n\s*\n', '\n', sanitized)
    
    return sanitized.strip()

def format_results_table(results):
    """Format query results as a readable table"""
    if not results:
        return "No results returned."
    
    # Get column names
    columns = list(results[0].keys())
    
    # Calculate optimal column widths
    col_widths = {}
    for col in columns:
        col_widths[col] = max(len(col), max(len(str(row[col])) for row in results))
    
    # Create formatted table
    header = " | ".join([col.ljust(col_widths[col]) for col in columns])
    separator = "-+-".join(['-' * col_widths[col] for col in columns])
    
    table_lines = [header, separator]
    for row in results:
        table_lines.append(" | ".join([str(row[col]).ljust(col_widths[col]) for col in columns]))
    
    return '\n'.join(table_lines)

def main():
    """Main pipeline execution using universal interface"""
    # Performance tracking
    start_time = time.time()
    output_lines = []
    
    print("[DEBUG] Starting Universal NL2DAX Pipeline...")
    
    # Initialize universal interface
    try:
        interface = UniversalQueryInterface()
        print("[DEBUG] Universal Query Interface initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize interface: {e}")
        return
    
    # Display schema summary
    print(colored_banner("DISCOVERED SCHEMA ANALYSIS", "96"))
    summary = interface.get_schema_summary()
    
    schema_info = f"""Database Schema Discovery:
• Total Tables: {summary['total_tables']}
• Fact Tables: {summary['fact_tables']}
• Dimension Tables: {summary['dimension_tables']}
• Business Areas: {', '.join(summary['business_areas'])}
• Schema Complexity: {summary['complexity_assessment']}

Suggested Query Patterns:
{chr(10).join(f'• {pattern}' for pattern in summary['suggested_patterns'])}"""
    
    print(schema_info)
    output_lines.append(plain_banner("DISCOVERED SCHEMA ANALYSIS"))
    output_lines.append(schema_info + "\n")
    
    # Show business suggestions
    suggestions = interface.get_business_suggestions()
    if suggestions:
        print(colored_banner("AI-GENERATED QUERY SUGGESTIONS", "93"))
        suggestions_text = "Based on schema analysis, here are some suggested queries:\n"
        for i, suggestion in enumerate(suggestions, 1):
            suggestions_text += f"{i}. {suggestion['query']} (Complexity: {suggestion['complexity']})\n"
        
        print(suggestions_text)
        output_lines.append(plain_banner("AI-GENERATED QUERY SUGGESTIONS"))
        output_lines.append(suggestions_text + "\n")
    
    # Get user input
    print(colored_banner("NATURAL LANGUAGE QUERY INPUT", "94"))
    user_query = input("Enter your natural language query (or press Enter for demo): ").strip()
    
    if not user_query:
        # Use a demo query
        user_query = "Show me customers with highest risk ratings and their geographic distribution"
        print(f"Using demo query: {user_query}")
    
    print(f"[DEBUG] Processing query: {user_query}")
    output_lines.append(plain_banner("NATURAL LANGUAGE QUERY"))
    output_lines.append(f"{user_query}\n")
    
    # Generate queries using universal interface
    print(colored_banner("UNIVERSAL QUERY GENERATION", "95"))
    try:
        # Generate both SQL and DAX
        result = interface.generate_query_from_intent(user_query, QueryType.BOTH)
        
        print(f"Analysis Type: {result.analysis_type.value}")
        print(f"Estimated Complexity: {result.estimated_complexity}")
        
        if result.execution_notes:
            print(f"Notes: {result.execution_notes}")
        
        generation_info = f"""Query Generation Results:
• Analysis Type: {result.analysis_type.value}
• Query Complexity: {result.estimated_complexity}
• Business Intent: {result.business_intent}
"""
        if result.execution_notes:
            generation_info += f"• Notes: {result.execution_notes}\n"
        
        output_lines.append(plain_banner("UNIVERSAL QUERY GENERATION"))
        output_lines.append(generation_info + "\n")
        
    except Exception as e:
        error_msg = f"[ERROR] Query generation failed: {e}"
        print(colored_banner("QUERY GENERATION ERROR", "91"))
        print(error_msg)
        output_lines.append(plain_banner("QUERY GENERATION ERROR"))
        output_lines.append(error_msg + "\n")
        return
    
    # Execute SQL query
    if result.sql_query:
        print(colored_banner("GENERATED SQL QUERY", "92"))
        print(result.sql_query)
        output_lines.append(plain_banner("GENERATED SQL QUERY"))
        output_lines.append(f"{result.sql_query}\n")
        
        # Sanitize and execute
        sql_sanitized = sanitize_query(result.sql_query)
        
        try:
            print(colored_banner("EXECUTING SQL QUERY", "92"))
            sql_results = execute_sql_query(sql_sanitized)
            
            if sql_results:
                formatted_table = format_results_table(sql_results)
                print(colored_banner("SQL QUERY RESULTS", "93"))
                print(formatted_table)
                
                output_lines.append(plain_banner("SQL QUERY RESULTS"))
                output_lines.append(formatted_table + "\n")
            else:
                no_results_msg = "No SQL results returned."
                print(colored_banner("SQL QUERY RESULTS", "93"))
                print(no_results_msg)
                output_lines.append(plain_banner("SQL QUERY RESULTS"))
                output_lines.append(no_results_msg + "\n")
                
        except Exception as e:
            sql_error = f"[ERROR] SQL execution failed: {e}"
            print(colored_banner("SQL EXECUTION ERROR", "91"))
            print(sql_error)
            output_lines.append(plain_banner("SQL EXECUTION ERROR"))
            output_lines.append(sql_error + "\n")
    
    # Execute DAX query
    if result.dax_query:
        print(colored_banner("GENERATED DAX QUERY", "95"))
        print(result.dax_query)
        output_lines.append(plain_banner("GENERATED DAX QUERY"))
        output_lines.append(f"{result.dax_query}\n")
        
        # Sanitize and execute
        dax_sanitized = sanitize_query(result.dax_query)
        
        try:
            print(colored_banner("EXECUTING DAX QUERY", "95"))
            dax_results = execute_dax_query(dax_sanitized)
            
            if dax_results:
                formatted_table = format_results_table(dax_results)
                print(colored_banner("DAX QUERY RESULTS", "93"))
                print(formatted_table)
                
                output_lines.append(plain_banner("DAX QUERY RESULTS"))
                output_lines.append(formatted_table + "\n")
            else:
                no_results_msg = "No DAX results returned."
                print(colored_banner("DAX QUERY RESULTS", "93"))
                print(no_results_msg)
                output_lines.append(plain_banner("DAX QUERY RESULTS"))
                output_lines.append(no_results_msg + "\n")
                
        except Exception as e:
            dax_error = f"[ERROR] DAX execution failed: {e}"
            print(colored_banner("DAX EXECUTION ERROR", "91"))
            print(dax_error)
            output_lines.append(plain_banner("DAX EXECUTION ERROR"))
            output_lines.append(dax_error + "\n")
    
    # Show performance metrics
    end_time = time.time()
    duration = end_time - start_time
    duration_str = f"Pipeline Duration: {duration:.2f} seconds"
    
    print(colored_banner("PERFORMANCE METRICS", "96"))
    print(duration_str)
    print(f"Database Schema: Automatically discovered and analyzed")
    print(f"Query Generation: AI-powered, database-agnostic")
    print(f"Adaptability: Works with any SQL database or Power BI model")
    
    output_lines.append(plain_banner("PERFORMANCE METRICS"))
    output_lines.append(duration_str + "\n")
    output_lines.append("Database Schema: Automatically discovered and analyzed\n")
    output_lines.append("Query Generation: AI-powered, database-agnostic\n")
    output_lines.append("Adaptability: Works with any SQL database or Power BI model\n")
    
    # Save results to file
    safe_query = re.sub(r'[^\w\s-]', '', user_query).strip()[:40]
    safe_query = re.sub(r'\s+', '_', safe_query)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"universal_nl2dax_run_{safe_query}_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines([line if line.endswith('\n') else line + '\n' for line in output_lines])
        print(f"[INFO] Results saved to {filename}")
    except Exception as e:
        print(f"[WARN] Could not save results: {e}")
    
    print(colored_banner("UNIVERSAL PIPELINE COMPLETE", "96"))
    print("✅ Successfully demonstrated database-agnostic query generation!")
    print("🔄 The system automatically adapts to any database schema.")
    print("🚀 Ready to work with different databases without code changes.")

if __name__ == "__main__":
    main()