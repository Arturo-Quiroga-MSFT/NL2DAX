"""
NL2DAX Streamlit Web Interface

This module provides a comprehensive web-based user interface for the NL2DAX pipeline,
allowing users to input natural language queries and view both SQL and DAX results
in a side-by-side comparison format with download capabilities.

Key Features:
- Natural language query input with examples
- Side-by-side SQL vs DAX results comparison  
- Interactive data tables with sorting and filtering
- Query performance metrics and timing
- Downloadable CSV exports of results
- Formatted code display for generated queries
- Error handling and validation feedback
- Session state management for query history

Author: NL2DAX Development Team
Date: August 2025
"""

import streamlit as st
import pandas as pd
import time
import io
import sys
import os
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import your existing pipeline modules
# Note: We'll import the core functions directly since main.py doesn't export them as modules
from dax_generator import generate_dax
from dax_formatter import format_and_validate_dax
from query_executor import execute_dax_query
from sql_executor import execute_sql_query
from schema_reader import get_schema_metadata

# We'll implement our own wrappers for the main.py functionality
import subprocess
import json
import re
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI LLM for intent parsing and SQL generation
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview",
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "o4-mini")
    # Note: o4-mini reasoning model only supports default temperature (1)
)

def parse_intent_entities(user_input):
    """Parse natural language into structured intent and entities"""
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert in translating natural language to database queries. 
        
        IMPORTANT DATA TYPE CONTEXT:
        - RISK_RATING_CODE is a text field with values like "A+", "A", "A-", "B+", "B", "B-", "C+", etc.
        - For numeric risk analysis, use PROBABILITY_OF_DEFAULT (decimal values)
        - LIMIT_AMOUNT and EXPOSURE_AT_DEFAULT are numeric currency fields
        
        Extract the intent and entities from the following user input, keeping in mind the data types above:
        {input}
        
        Return ONLY a valid JSON object with intent and entities. Example format:
        {{
            "intent": "show_top_customers",
            "entities": {{
                "limit": 5,
                "table": "customers",
                "sort_field": "total_exposure",
                "sort_order": "desc"
            }}
        }}
        
        Return only valid JSON - no explanatory text.
        """
    )
    chain = prompt | llm
    result = chain.invoke({"input": user_input})
    
    # Try to parse as JSON, fallback to raw text if parsing fails
    try:
        parsed_json = json.loads(result.content)
        return parsed_json
    except json.JSONDecodeError:
        # Return a structured fallback if JSON parsing fails
        return {
            "intent": "general_query",
            "entities": {
                "query_text": user_input,
                "raw_llm_response": result.content
            },
            "parse_error": "Failed to parse LLM response as JSON"
        }

def generate_sql_from_intent(intent_entities):
    """Generate SQL query from intent and entities"""
    from schema_reader import get_schema_metadata
    
    # Get database schema context
    schema_metadata = get_schema_metadata()
    
    sql_prompt = ChatPromptTemplate.from_template(
        """
        You are an expert SQL developer. Based on the intent and entities, generate a T-SQL query.
        
        IMPORTANT GUIDELINES:
        1. RISK_RATING_CODE is a text field (A+, A, A-, B+, B, etc.) - use COUNT(), GROUP BY, or string operations
        2. For numeric analysis, use PROBABILITY_OF_DEFAULT, LIMIT_AMOUNT, EXPOSURE_AT_DEFAULT
        3. Do not use AVG(), SUM(), or math functions on text fields like RISK_RATING_CODE
        4. Use appropriate data types for aggregations
        
        Database Schema:
        {schema}
        
        Intent and Entities:
        {intent_entities}
        
        Generate a valid T-SQL query that respects data types and fulfills the user's request.
        Return ONLY the SQL query without explanations or code blocks.
        """
    )
    
    chain = sql_prompt | llm
    result = chain.invoke({
        "schema": str(schema_metadata),
        "intent_entities": intent_entities
    })
    return result.content

def validate_dax_completeness(dax_query):
    """Validate that DAX query is complete and well-formed"""
    if not dax_query or len(dax_query.strip()) < 10:
        return "DAX query appears to be empty or too short"
    
    # Check for balanced parentheses
    open_count = dax_query.count('(')
    close_count = dax_query.count(')')
    
    if open_count != close_count:
        return f"Unbalanced parentheses: {open_count} open, {close_count} close - query may be incomplete"
    
    # Check for common DAX patterns
    if not any(keyword in dax_query.upper() for keyword in ['EVALUATE', 'RETURN', 'DEFINE']):
        return "DAX query doesn't start with required keywords (EVALUATE, RETURN, or DEFINE)"
    
    # Check for incomplete function calls
    incomplete_patterns = [
        r'CALCULATE\s*\(\s*$',
        r'SUMX\s*\(\s*$', 
        r'FILTER\s*\(\s*$',
        r'TOPN\s*\(\s*$'
    ]
    
    for pattern in incomplete_patterns:
        if re.search(pattern, dax_query, re.IGNORECASE):
            return f"DAX query appears incomplete - found unfinished function call"
    
    return "DAX query appears complete"

# Configure Streamlit page
st.set_page_config(
    page_title="NL2DAX Query Interface",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'sql_results' not in st.session_state:
    st.session_state.sql_results = None
if 'dax_results' not in st.session_state:
    st.session_state.dax_results = None

def format_execution_time(seconds):
    """Format execution time in a human-readable way"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"

def create_comparison_metrics(sql_results, dax_results, sql_time, dax_time):
    """Create comparison metrics between SQL and DAX results"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="SQL Rows",
            value=len(sql_results) if sql_results is not None else 0
        )
    
    with col2:
        st.metric(
            label="DAX Rows", 
            value=len(dax_results) if dax_results is not None else 0
        )
    
    with col3:
        st.metric(
            label="SQL Time",
            value=format_execution_time(sql_time)
        )
    
    with col4:
        st.metric(
            label="DAX Time",
            value=format_execution_time(dax_time)
        )

def execute_pipeline(user_query):
    """Execute the complete NL2DAX pipeline and return results"""
    
    # Initialize results
    results = {
        'sql_query': None,
        'dax_query': None,
        'sql_results': None,
        'dax_results': None,
        'sql_time': 0,
        'dax_time': 0,
        'intent_entities': None,
        'errors': []
    }
    
    try:
        # Step 1: Parse intent and entities
        with st.spinner("🧠 Analyzing your query..."):
            results['intent_entities'] = parse_intent_entities(user_query)
        
        # Step 2: Generate and execute SQL
        with st.spinner("🔍 Generating SQL query..."):
            sql_start = time.time()
            sql_raw = generate_sql_from_intent(results['intent_entities'])
            
            if sql_raw:
                # Extract SQL code from LLM output
                sql_code = sql_raw
                code_block = re.search(r"```sql\s*([\s\S]+?)```", sql_raw, re.IGNORECASE)
                if not code_block:
                    code_block = re.search(r"```([\s\S]+?)```", sql_raw)
                if code_block:
                    sql_code = code_block.group(1).strip()
                else:
                    select_match = re.search(r'(SELECT[\s\S]+)', sql_raw, re.IGNORECASE)
                    if select_match:
                        sql_code = select_match.group(1).strip()
                
                # Sanitize quotes
                sql_sanitized = sql_code.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
                results['sql_query'] = sql_sanitized
                
                # Execute SQL
                try:
                    results['sql_results'] = execute_sql_query(sql_sanitized)
                except Exception as e:
                    results['errors'].append(f"SQL Execution Error: {str(e)}")
            
            results['sql_time'] = time.time() - sql_start
        
        # Step 3: Generate and execute DAX
        with st.spinner("⚡ Generating DAX query..."):
            dax_start = time.time()
            dax_query = generate_dax(results['intent_entities'])
            
            if dax_query:
                # Extract DAX code from LLM output
                dax_code = dax_query
                code_block = re.search(r"```dax\s*([\s\S]+?)```", dax_query, re.IGNORECASE)
                if not code_block:
                    code_block = re.search(r"```([\s\S]+?)```", dax_query)
                if code_block:
                    dax_code = code_block.group(1).strip()
                else:
                    # Look for EVALUATE pattern
                    evaluate_match = re.search(r'(EVALUATE[\s\S]+)', dax_query, re.IGNORECASE)
                    if evaluate_match:
                        dax_code = evaluate_match.group(1).strip()
                
                # Sanitize quotes
                dax_sanitized = dax_code.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
                
                # Validate DAX completeness
                validation_result = validate_dax_completeness(dax_sanitized)
                if "appears complete" not in validation_result:
                    results['errors'].append(f"DAX Validation Warning: {validation_result}")
                
                # Format DAX
                try:
                    formatted_result = format_and_validate_dax(dax_sanitized)
                    if isinstance(formatted_result, tuple):
                        formatted_dax, format_errors = formatted_result
                        if format_errors:
                            results['errors'].extend([f"DAX Formatting Warning: {err}" for err in format_errors])
                    else:
                        formatted_dax = formatted_result
                    
                    results['dax_query'] = formatted_dax
                except Exception as format_error:
                    # If formatting fails, use the original DAX but log the error
                    results['errors'].append(f"DAX Formatting Warning: {str(format_error)}")
                    results['dax_query'] = dax_sanitized
                
                # Execute DAX
                try:
                    results['dax_results'] = execute_dax_query(results['dax_query'])
                except Exception as exec_error:
                    results['errors'].append(f"DAX Execution Error: {str(exec_error)}")
            
            results['dax_time'] = time.time() - dax_start
            
    except Exception as e:
        results['errors'].append(f"Pipeline Error: {str(e)}")
    
    return results

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("🔍 NL2DAX Query Interface")
    st.markdown("Transform natural language into SQL and DAX queries with side-by-side result comparison")
    
    # Sidebar with examples and history
    with st.sidebar:
        st.header("📝 Query Examples")
        
        example_queries = [
            "Show me the top 5 customers by total credit amount",
            "What is the average risk rating by customer type?",
            "List customers with the highest exposure at default",
            "Show me comprehensive customer analysis grouped by type",
            "Which customers are located in the United States?"
        ]
        
        for example in example_queries:
            if st.button(f"💡 {example}", key=f"example_{example}", use_container_width=True):
                st.session_state.last_query = example
                st.rerun()
        
        # Query History
        if st.session_state.query_history:
            st.header("📋 Recent Queries")
            for i, query in enumerate(reversed(st.session_state.query_history[-5:])):
                if st.button(f"🕒 {query[:50]}...", key=f"history_{i}", use_container_width=True):
                    st.session_state.last_query = query
                    st.rerun()
    
    # Main query interface
    user_query = st.text_area(
        "Enter your natural language query:",
        value=st.session_state.last_query,
        height=100,
        placeholder="e.g., Show me the top 10 customers by total credit amount and their risk ratings"
    )
    
    # Execute button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🧹 Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.last_query = ""
        st.session_state.sql_results = None
        st.session_state.dax_results = None
        st.rerun()
    
    # Execute pipeline
    if execute_button and user_query.strip():
        # Add to history
        if user_query not in st.session_state.query_history:
            st.session_state.query_history.append(user_query)
        
        # Execute pipeline
        with st.container():
            results = execute_pipeline(user_query)
            
            # Store results in session state
            st.session_state.sql_results = results['sql_results']
            st.session_state.dax_results = results['dax_results']
            
            # Display errors if any
            if results['errors']:
                for error in results['errors']:
                    st.error(error)
            
            # Success message and metrics
            if results['sql_results'] is not None or results['dax_results'] is not None:
                st.success("✅ Query executed successfully!")
                
                # Performance metrics
                create_comparison_metrics(
                    results['sql_results'], 
                    results['dax_results'],
                    results['sql_time'],
                    results['dax_time']
                )
                
                # Results tabs
                tab1, tab2, tab3 = st.tabs(["📊 Results Comparison", "🔍 Query Details", "📈 Analysis"])
                
                with tab1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🗄️ SQL Results")
                        if results['sql_results'] is not None and len(results['sql_results']) > 0:
                            df_sql = pd.DataFrame(results['sql_results'])
                            st.dataframe(df_sql, use_container_width=True)
                            
                            # Download button
                            csv_sql = df_sql.to_csv(index=False)
                            st.download_button(
                                label="📥 Download SQL Results (CSV)",
                                data=csv_sql,
                                file_name=f"sql_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("No SQL results to display")
                    
                    with col2:
                        st.subheader("⚡ DAX Results")
                        if results['dax_results'] is not None and len(results['dax_results']) > 0:
                            df_dax = pd.DataFrame(results['dax_results'])
                            st.dataframe(df_dax, use_container_width=True)
                            
                            # Download button
                            csv_dax = df_dax.to_csv(index=False)
                            st.download_button(
                                label="📥 Download DAX Results (CSV)",
                                data=csv_dax,
                                file_name=f"dax_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("No DAX results to display")
                
                with tab2:
                    # Intent and Entities
                    if results['intent_entities']:
                        st.subheader("🧠 Parsed Intent & Entities")
                        st.json(results['intent_entities'])
                    
                    # Generated queries
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🗄️ Generated SQL")
                        if results['sql_query']:
                            st.code(results['sql_query'], language="sql")
                        else:
                            st.info("No SQL query generated")
                    
                    with col2:
                        st.subheader("⚡ Generated DAX")
                        if results['dax_query']:
                            st.code(results['dax_query'], language="dax")
                        else:
                            st.info("No DAX query generated")
                
                with tab3:
                    # Basic analysis if we have data
                    if results['sql_results'] and len(results['sql_results']) > 0:
                        df_analysis = pd.DataFrame(results['sql_results'])
                        
                        st.subheader("📊 Data Overview")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Rows", len(df_analysis))
                        with col2:
                            st.metric("Columns", len(df_analysis.columns))
                        with col3:
                            numeric_cols = df_analysis.select_dtypes(include=['number']).columns
                            st.metric("Numeric Columns", len(numeric_cols))
                        
                        # Simple visualization if we have numeric data
                        if len(numeric_cols) > 0:
                            st.subheader("📈 Quick Visualization")
                            
                            if len(df_analysis) <= 20 and len(numeric_cols) >= 1:
                                # Create a simple chart
                                if len(df_analysis.columns) >= 2:
                                    x_col = df_analysis.columns[0]
                                    y_col = numeric_cols[0]
                                    
                                    fig = px.bar(
                                        df_analysis.head(10), 
                                        x=x_col, 
                                        y=y_col,
                                        title=f"{y_col} by {x_col}"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No data available for analysis")

if __name__ == "__main__":
    main()
