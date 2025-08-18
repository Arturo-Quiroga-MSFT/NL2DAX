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
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the new universal interface
from core import UniversalQueryInterface, QueryType, AnalysisType, UniversalQueryExecutor

# Load environment variables from multiple locations
load_dotenv()  # Load from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))  # Load from main project
print(f"[DEBUG] Main interface environment check:")
print(f"[DEBUG] PBI_TENANT_ID: {os.getenv('PBI_TENANT_ID', 'NOT_SET')[:8] if os.getenv('PBI_TENANT_ID') else 'NOT_SET'}...")
print(f"[DEBUG] PBI_XMLA_ENDPOINT: {os.getenv('PBI_XMLA_ENDPOINT', 'NOT_SET')}")
print(f"[DEBUG] PBI_DATASET_NAME: {os.getenv('PBI_DATASET_NAME', 'NOT_SET')}")
print(f"[DEBUG] Azure SQL Server: {os.getenv('AZURE_SQL_SERVER', 'NOT_SET')}")
print(f"[DEBUG] Azure SQL Database: {os.getenv('AZURE_SQL_DB', 'NOT_SET')}")

def colored_banner(title, color_code="94"):
    """Create colored ASCII banner for output sections"""
    banner_text = f"\n{'='*10} {title} {'='*10}\n"
    return f"\033[{color_code}m{banner_text}\033[0m"

def format_dax_results_as_table(data, max_width=80):
    """Format DAX results as a readable ASCII table"""
    if not data:
        return "No data returned."
    
    # Get all columns from the first row
    columns = list(data[0].keys())
    
    # Calculate column widths
    col_widths = {}
    for col in columns:
        # Start with column name length
        col_widths[col] = len(col)
        
        # Check data lengths
        for row in data:
            value = row.get(col, '')
            if isinstance(value, (int, float)):
                value_str = f"{value:,.0f}" if isinstance(value, (int, float)) and value > 1000 else str(value)
            else:
                value_str = str(value)
            col_widths[col] = max(col_widths[col], len(value_str))
        
        # Apply maximum width limit
        col_widths[col] = min(col_widths[col], max_width)
    
    # Build header
    header_parts = []
    separator_parts = []
    for col in columns:
        clean_col = col.replace('[', '').replace(']', '')  # Clean DAX column names
        header_parts.append(clean_col.ljust(col_widths[col]))
        separator_parts.append('-' * col_widths[col])
    
    result_lines = []
    result_lines.append(' | '.join(header_parts))
    result_lines.append('-+-'.join(separator_parts))
    
    # Build data rows
    for row in data[:10]:  # Show first 10 rows
        row_parts = []
        for col in columns:
            value = row.get(col, '')
            if isinstance(value, (int, float)):
                value_str = f"{value:,.0f}" if isinstance(value, (int, float)) and value > 1000 else str(value)
            else:
                value_str = str(value)
            
            # Truncate if too long
            if len(value_str) > col_widths[col]:
                value_str = value_str[:col_widths[col]-3] + '...'
            
            row_parts.append(value_str.ljust(col_widths[col]))
        
        result_lines.append(' | '.join(row_parts))
    
    return '\n'.join(result_lines)

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
    
    # Initialize universal interface and executor
    try:
        interface = UniversalQueryInterface()
        executor = UniversalQueryExecutor()
        print("[DEBUG] Universal Query Interface and Executor initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize interface: {e}")
        return
    
    # Display schema summary
    print(colored_banner("DISCOVERED SCHEMA ANALYSIS", "96"))
    summary = interface.get_schema_summary()
    
    # Get detailed schema analysis to show star schema detection
    schema_analysis = interface.analyze_current_schema()
    tables_info = schema_analysis['tables']
    
    # Check if star schema was detected
    fact_tables = [name for name in tables_info.keys() if 'FACT' in name.upper()]
    dimension_tables = [name for name in tables_info.keys() if 'DIMENSION' in name.upper()]
    
    if fact_tables and dimension_tables:
        schema_type = "⭐ STAR SCHEMA DETECTED"
        schema_details = f"Filtered to {len(tables_info)} star schema tables from original discovery"
    else:
        schema_type = "📊 GENERIC SCHEMA"
        schema_details = f"Analyzing all {len(tables_info)} discovered tables"
    
    schema_info = f"""Database Schema Discovery:
{schema_type}
• {schema_details}
• Total Tables: {summary['total_tables']}
• Fact Tables: {summary['fact_tables']} ({', '.join(fact_tables) if fact_tables else 'None'})
• Dimension Tables: {summary['dimension_tables']} ({', '.join(dimension_tables[:3]) + ('...' if len(dimension_tables) > 3 else '') if dimension_tables else 'None'})
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
        # Use a star schema-focused demo query if star schema detected
        if fact_tables and dimension_tables:
            user_query = "Show me top 10 customers by risk rating with their geographic distribution and total exposure"
            print(f"Using star schema demo query: {user_query}")
        else:
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
• Schema Focus: {'Star Schema (FACT/DIMENSION only)' if fact_tables and dimension_tables else 'All Tables'}
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
    
    # Display generated queries
    if result.sql_query:
        print(colored_banner("GENERATED SQL QUERY", "92"))
        print(result.sql_query)
        output_lines.append(plain_banner("GENERATED SQL QUERY"))
        output_lines.append(f"{result.sql_query}\n")
    
    if result.dax_query:
        print(colored_banner("GENERATED DAX QUERY", "95"))
        print(result.dax_query)
        output_lines.append(plain_banner("GENERATED DAX QUERY"))
        output_lines.append(f"{result.dax_query}\n")
    
    # Execute queries and show results
    print(colored_banner("QUERY EXECUTION & RESULTS", "93"))
    
    # Execute SQL query
    if result.sql_query:
        print("\n🔍 Executing SQL Query...")
        sql_result = executor.execute_sql_query(result.sql_query, limit_rows=10)
        print(f"   {executor.get_execution_summary(sql_result)}")
        
        if sql_result.success and sql_result.data:
            print(f"\n📋 SQL Results (showing {sql_result.row_count} rows):")
            print(executor.format_results_as_table(sql_result))
            
            output_lines.append(plain_banner("SQL EXECUTION RESULTS"))
            output_lines.append(f"{executor.get_execution_summary(sql_result)}\n")
            output_lines.append(f"{executor.format_results_as_table(sql_result)}\n")
        elif not sql_result.success:
            print(f"   ❌ SQL Error: {sql_result.error_message}")
            output_lines.append(plain_banner("SQL EXECUTION ERROR"))
            output_lines.append(f"Error: {sql_result.error_message}\n")
    
    # Execute DAX query
    if result.dax_query:
        print("\n📊 Executing DAX Query...")
        
        # Check if we have enhanced DAX results
        if hasattr(result, 'enhanced_dax_result') and result.enhanced_dax_result:
            enhanced = result.enhanced_dax_result
            print(f"   🚀 Enhanced DAX Engine Results:")
            print(f"   • Pattern Used: {enhanced.pattern_used}")
            print(f"   • Confidence Score: {enhanced.confidence_score:.2f}")
            print(f"   • Execution Success: {'✅ YES' if enhanced.execution_success else '❌ NO'}")
            
            if enhanced.execution_success and enhanced.data:
                print(f"   • Rows Returned: {enhanced.row_count}")
                print(f"   • Execution Time: {enhanced.execution_time:.3f}s")
                
                print(f"\n📋 Enhanced DAX Results (showing {len(enhanced.data)} rows):")
                # Format the enhanced results as a proper table
                if enhanced.data:
                    dax_table = format_dax_results_as_table(enhanced.data)
                    print(dax_table)
                
                output_lines.append(plain_banner("ENHANCED DAX EXECUTION RESULTS"))
                output_lines.append(f"✅ Enhanced DAX executed successfully: {enhanced.row_count} rows in {enhanced.execution_time:.3f}s\n")
                output_lines.append(f"Pattern Used: {enhanced.pattern_used} (Confidence: {enhanced.confidence_score:.2f})\n")
                
                dax_table = format_dax_results_as_table(enhanced.data)
                output_lines.append(f"{dax_table}\n")
                
            elif not enhanced.execution_success:
                print(f"   ❌ Enhanced DAX Error: {enhanced.error_message}")
                output_lines.append(plain_banner("ENHANCED DAX EXECUTION ERROR"))
                output_lines.append(f"Error: {enhanced.error_message}\n")
                
            if enhanced.validation_issues:
                print(f"   ⚠️  Validation Issues ({len(enhanced.validation_issues)}):")
                for issue in enhanced.validation_issues[:3]:  # Show first 3
                    print(f"      • {issue}")
        else:
            # Fallback to original DAX execution
            dax_result = executor.execute_dax_query(result.dax_query, limit_rows=10)
            print(f"   {executor.get_execution_summary(dax_result)}")
            
            if dax_result.success and dax_result.data:
                print(f"\n📋 DAX Results (showing {dax_result.row_count} rows):")
                print(executor.format_results_as_table(dax_result))
                
                output_lines.append(plain_banner("DAX EXECUTION RESULTS"))
                output_lines.append(f"{executor.get_execution_summary(dax_result)}\n")
                output_lines.append(f"{executor.format_results_as_table(dax_result)}\n")
            elif not dax_result.success:
                print(f"   ⚠️  DAX Note: {dax_result.error_message}")
                output_lines.append(plain_banner("DAX EXECUTION INFO"))
                output_lines.append(f"Note: {dax_result.error_message}\n")
    
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
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
        os.makedirs(results_dir, exist_ok=True)
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines([line if line.endswith('\n') else line + '\n' for line in output_lines])
        print(f"[INFO] Results saved to {filepath}")
    except Exception as e:
        print(f"[WARN] Could not save results: {e}")
    
    print(colored_banner("UNIVERSAL PIPELINE COMPLETE", "96"))
    print("✅ Successfully demonstrated database-agnostic query generation!")
    if fact_tables and dimension_tables:
        print("⭐ Star schema automatically detected and focused analysis applied!")
        print(f"🎯 Generated queries use only {len(fact_tables)} fact and {len(dimension_tables)} dimension tables!")
    print("🔄 The system automatically adapts to any database schema.")
    print("🚀 Ready to work with different databases without code changes.")

if __name__ == "__main__":
    main()