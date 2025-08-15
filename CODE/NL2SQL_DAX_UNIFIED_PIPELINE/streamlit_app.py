#!/usr/bin/env python3
"""
streamlit_app.py - Web Interface for Unified NL2SQL&DAX Pipeline
===============================================================

Streamlit web application for testing and demonstrating the
unified pipeline that executes both SQL and DAX queries.

Author: Unified Pipeline Team
Date: August 2025
"""

import streamlit as st
import sys
import os
from datetime import datetime
import json
import pandas as pd

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import our pipeline components
from unified_pipeline import UnifiedNL2SQLDAXPipeline
from result_formatter import ResultFormatter
from query_cache import QueryCache

# Page configuration
st.set_page_config(
    page_title="NL2SQL&DAX Unified Pipeline",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def save_results_to_markdown(user_query: str, results: dict) -> str:
    """Save execution results to a comprehensive markdown file with detailed analysis"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"nl2dax_run_{user_query.replace(' ', '_').replace('?', '').replace(',', '')[:50]}_{timestamp}.md"
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'RESULTS', 'UNIFIED_PIPELINE')
    
    # Create results directory if it doesn't exist
    os.makedirs(results_dir, exist_ok=True)
    
    filepath = os.path.join(results_dir, filename)
    
    # Extract information from results
    sql_query = results.get('generated_sql', results.get('sql_query', 'Not generated'))
    dax_query = results.get('generated_dax', results.get('dax_query', 'Not generated'))
    sql_results = results.get('sql_result', results.get('sql_results', {}))
    dax_results = results.get('dax_result', results.get('dax_results', {}))
    comparison = results.get('comparison', {})
    
    # Build comprehensive markdown content similar to the original format
    md_content = f"""
========== NATURAL LANGUAGE QUERY ==========
{user_query}

========== EXECUTION TIMESTAMP ==========
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

========== GENERATED SQL ==========
{sql_query}

========== GENERATED DAX ==========
{dax_query}

========== PIPELINE CONFIGURATION ==========
- OpenAI Model: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'o4-mini')}
- API Version: {os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')}
- Database: {results.get('schema_info', {}).get('database', 'Azure SQL Database')}
- Caching Enabled: {'Yes' if results.get('cache_enabled') else 'No'}

========== SQL EXECUTION RESULTS ==========
"""
    
    # Add SQL results details
    if sql_results.get('success'):
        md_content += f"""Status: ✅ SUCCESS
Execution Time: {sql_results.get('execution_time', 0):.3f} seconds
Rows Returned: {sql_results.get('row_count', 0)}
Columns: {len(sql_results.get('columns', []))}

========== SQL QUERY RESULTS (TABLE) ==========
"""
        
        # Add sample data if available
        if sql_results.get('data') and len(sql_results['data']) > 0:
            data = sql_results['data']
            columns = sql_results.get('columns', [])
            
            if columns and len(data) > 0:
                # Create header row
                header_row = ' | '.join(f"{col:<25}" for col in columns)
                separator_row = ' | '.join(['-' * 25 for _ in columns])
                
                md_content += header_row + "\n"
                md_content += separator_row + "\n"
                
                # Add data rows (first 10)
                for row in data[:10]:
                    if isinstance(row, dict):
                        row_values = [str(row.get(col, 'NULL'))[:25] for col in columns]
                    else:
                        row_values = [str(val)[:25] if val is not None else 'NULL' for val in row]
                    
                    row_line = ' | '.join(f"{val:<25}" for val in row_values)
                    md_content += row_line + "\n"
                
                if len(data) > 10:
                    md_content += f"\n... and {len(data) - 10} more rows\n"
        else:
            md_content += "No data returned\n"
    else:
        md_content += f"""Status: ❌ FAILED
Error: {sql_results.get('error', 'Unknown error')}
"""
    
    md_content += "\n========== DAX EXECUTION RESULTS ==========\n"
    
    # Add DAX results details
    if dax_results.get('success'):
        md_content += f"""Status: ✅ SUCCESS
Execution Time: {dax_results.get('execution_time', 0):.3f} seconds
Rows Returned: {dax_results.get('row_count', 0)}
Columns: {len(dax_results.get('columns', []))}

========== TRANSLATED DAX TO SQL ==========
{dax_results.get('translated_sql', 'Not available')}

========== DAX QUERY RESULTS (TABLE) ==========
"""
        
        # Add sample data if available
        if dax_results.get('data') and len(dax_results['data']) > 0:
            data = dax_results['data']
            columns = dax_results.get('columns', [])
            
            if columns and len(data) > 0:
                # Create header row
                header_row = ' | '.join(f"{col:<25}" for col in columns)
                separator_row = ' | '.join(['-' * 25 for _ in columns])
                
                md_content += header_row + "\n"
                md_content += separator_row + "\n"
                
                # Add data rows (first 10)
                for row in data[:10]:
                    if isinstance(row, dict):
                        row_values = [str(row.get(col, 'NULL'))[:25] for col in columns]
                    else:
                        row_values = [str(val)[:25] if val is not None else 'NULL' for val in row]
                    
                    row_line = ' | '.join(f"{val:<25}" for val in row_values)
                    md_content += row_line + "\n"
                
                if len(data) > 10:
                    md_content += f"\n... and {len(data) - 10} more rows\n"
        else:
            md_content += "No data returned\n"
    else:
        md_content += f"""Status: ❌ FAILED
Error: {dax_results.get('error', 'Unknown error')}
"""
    
    # Add comparison results
    md_content += f"""
========== RESULTS COMPARISON ==========
Results Match: {'✅ YES' if comparison.get('matches', comparison.get('match', False)) else '❌ NO'}
SQL Rows: {comparison.get('sql_rows', sql_results.get('row_count', 0))}
DAX Rows: {comparison.get('dax_rows', dax_results.get('row_count', 0))}
Summary: {comparison.get('summary', 'Comparison completed')}
"""
    
    if comparison.get('differences'):
        md_content += "\nDifferences Found:\n"
        for i, diff in enumerate(comparison['differences'], 1):
            md_content += f"{i}. {diff}\n"
    
    # Add performance analysis
    performance = results.get('performance', {})
    total_time = performance.get('total_execution_time', 0)
    sql_time = sql_results.get('execution_time', 0)
    dax_time = dax_results.get('execution_time', 0)
    
    md_content += f"""
========== PERFORMANCE ANALYSIS ==========
Total Pipeline Execution Time: {total_time:.3f} seconds
SQL Generation Time: {results.get('sql_generation_time', 0):.3f} seconds
DAX Generation Time: {results.get('dax_generation_time', 0):.3f} seconds
SQL Execution Time: {sql_time:.3f} seconds
DAX Execution Time: {dax_time:.3f} seconds
"""
    
    if sql_time > 0 and dax_time > 0:
        if sql_time < dax_time:
            ratio = dax_time / sql_time
            md_content += f"Performance Winner: 🏆 SQL (faster by {ratio:.2f}x)\n"
        elif dax_time < sql_time:
            ratio = sql_time / dax_time
            md_content += f"Performance Winner: 🏆 DAX (faster by {ratio:.2f}x)\n"
        else:
            md_content += "Performance: ⚖️ SQL and DAX had similar performance\n"

    md_content += f"""
========== SCHEMA INFORMATION ==========
Database: {results.get('schema_info', {}).get('database', 'Azure SQL Database')}
Tables Available: {len(results.get('schema_info', {}).get('tables', []))}
"""
    
    # Add table details
    if results.get('schema_info', {}).get('tables'):
        md_content += "\nTable Details:\n"
        for table in results.get('schema_info', {}).get('tables', []):
            table_name = table.get('name', 'Unknown')
            column_count = len(table.get('columns', []))
            md_content += f"- {table_name}: {column_count} columns\n"
    
    # Add environment details
    md_content += f"""
========== ENVIRONMENT DETAILS ==========
Execution Environment: Streamlit Web Interface
Pipeline Version: Unified NL2SQL & DAX Pipeline
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Working Directory: {os.getcwd()}

========== PIPELINE STATUS ==========
✅ Schema Reading: Complete
✅ SQL Generation: {'Complete' if sql_query != 'Not generated' else 'Failed'}
✅ DAX Generation: {'Complete' if dax_query != 'Not generated' else 'Failed'}
✅ SQL Execution: {'Complete' if sql_results.get('success') else 'Failed'}
✅ DAX Execution: {'Complete' if dax_results.get('success') else 'Failed'}
✅ Results Comparison: {'Complete' if comparison else 'Skipped'}
✅ Report Generation: Complete

---
Generated by NL2DAX Unified Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return filepath
    except Exception as e:
        st.error(f"❌ Failed to save results: {str(e)}")
        return None

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'pipeline_initialized' not in st.session_state:
        st.session_state.pipeline_initialized = False
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'cache_enabled' not in st.session_state:
        st.session_state.cache_enabled = True

def create_sidebar():
    """Create the sidebar with configuration options"""
    st.sidebar.title("⚙️ Configuration")
    
    # Environment file upload
    st.sidebar.subheader("📁 Environment Configuration")
    uploaded_file = st.sidebar.file_uploader(
        "Upload .env file",
        type=['env'],
        help="Upload your .env file with database and API configurations"
    )
    
    if uploaded_file is not None:
        # Save uploaded file
        env_content = uploaded_file.read().decode('utf-8')
        with open('.env', 'w') as f:
            f.write(env_content)
        st.sidebar.success("✅ Environment file uploaded successfully!")
    
    # Pipeline configuration
    st.sidebar.subheader("🔧 Pipeline Settings")
    
    cache_enabled = st.sidebar.checkbox(
        "Enable Query Caching",
        value=st.session_state.cache_enabled,
        help="Cache query results to improve performance"
    )
    st.session_state.cache_enabled = cache_enabled
    
    max_retries = st.sidebar.number_input(
        "Max Retries",
        min_value=0,
        max_value=5,
        value=3,
        help="Maximum number of retries for failed queries"
    )
    
    timeout = st.sidebar.number_input(
        "Query Timeout (seconds)",
        min_value=10,
        max_value=300,
        value=60,
        help="Maximum time to wait for query execution"
    )
    
    # Initialize pipeline button
    if st.sidebar.button("🚀 Initialize Pipeline", type="primary"):
        with st.spinner("Initializing pipeline..."):
            try:
                st.session_state.pipeline = UnifiedNL2SQLDAXPipeline()
                st.session_state.pipeline_initialized = True
                st.sidebar.success("✅ Pipeline initialized successfully!")
            except Exception as e:
                st.sidebar.error(f"❌ Failed to initialize pipeline: {str(e)}")
                st.session_state.pipeline_initialized = False
    
    # Pipeline status
    st.sidebar.subheader("📊 Pipeline Status")
    if st.session_state.pipeline_initialized:
        st.sidebar.success("🟢 Pipeline Ready")
        
        # Show cache stats if available
        if hasattr(st.session_state.pipeline, 'cache'):
            stats = st.session_state.pipeline.cache.get_stats()
            st.sidebar.metric("Cache Hit Rate", f"{stats.get('hit_rate', 0):.1%}")
            st.sidebar.metric("Cache Size", stats.get('cache_size', 0))
    else:
        st.sidebar.warning("🟡 Pipeline Not Initialized")
    
    return {
        'cache_enabled': cache_enabled,
        'max_retries': max_retries,
        'timeout': timeout
    }

def create_main_interface():
    """Create the main query interface"""
    st.title("🔄 NL2SQL&DAX Unified Pipeline")
    st.markdown("---")
    
    # Introduction
    with st.expander("ℹ️ About This Pipeline", expanded=False):
        st.markdown("""
        This unified pipeline allows you to:
        - 🗣️ **Enter natural language queries** and get both SQL and DAX results
        - 🔍 **Compare results** between SQL and DAX to ensure data consistency
        - ⚡ **Performance analysis** to see which query type is faster
        - 💾 **Query caching** to improve performance for repeated queries
        - 📊 **Schema exploration** to understand your database structure
        
        The pipeline connects directly to your Azure SQL Database, eliminating
        the need for Power BI semantic models and ensuring data consistency.
        """)
    
    # Query input section
    st.subheader("💬 Natural Language Query")
    
    col1, col2 = st.columns([3, 1])
    
    # Initialize session state for query if not exists
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    with col2:
        st.markdown("**📝 Example Queries:**")
        examples = [
            "Show me all active customers",
            "List top 10 customers by balance",
            "What is the average loan amount?",
            "Find customers with high risk rating",
            "Show monthly transaction trends"
        ]
        
        for i, example in enumerate(examples):
            if st.button(f"📋 {example}", key=f"example_{i}"):
                st.session_state.current_query = example
                st.rerun()
    
    with col1:
        user_query = st.text_area(
            "Enter your question about the data:",
            value=st.session_state.current_query,
            height=100,
            placeholder="e.g., Show me the top 10 customers by total balance",
            key="user_query_input"
        )
        
        # Update session state when user types
        st.session_state.current_query = user_query
    
    # Execution options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        execute_sql = st.checkbox("🗃️ Execute SQL", value=True)
    with col2:
        execute_dax = st.checkbox("📊 Execute DAX", value=True)
    with col3:
        compare_results = st.checkbox("🔍 Compare Results", value=True)
    
    # Execute button
    if st.button("🚀 Execute Query", type="primary", disabled=not st.session_state.pipeline_initialized):
        if not user_query.strip():
            st.error("❌ Please enter a query")
            return
        
        if not (execute_sql or execute_dax):
            st.error("❌ Please select at least one query type to execute")
            return
        
        execute_query(user_query, execute_sql, execute_dax, compare_results)

def execute_query(user_query: str, execute_sql: bool, execute_dax: bool, compare_results: bool):
    """Execute the query and display results"""
    
    with st.spinner("🔄 Processing your query..."):
        try:
            # Execute the pipeline
            results = st.session_state.pipeline.execute_query(user_query)
            
            # Add to query history
            st.session_state.query_history.append({
                'timestamp': datetime.now(),
                'query': user_query,
                'results': results
            })
            
            # Save results to markdown file
            saved_file = save_results_to_markdown(user_query, results)
            if saved_file:
                st.success(f"📁 Results saved to: `{saved_file}`")
            
            # Display results
            display_results(results, user_query)
            
        except Exception as e:
            st.error(f"❌ Error executing query: {str(e)}")
            st.exception(e)

def display_results(results: dict, user_query: str):
    """Display query results"""
    
    st.markdown("---")
    st.subheader("📊 Query Results")
    
    # Display Generated Queries Prominently
    st.subheader("🔍 Generated Queries")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗃️ SQL Query")
        if results.get('generated_sql'):
            st.code(results['generated_sql'], language="sql")
            
            # SQL execution status
            sql_result = results.get('sql_result', {})
            if sql_result.get('success'):
                st.success(f"✅ SQL executed successfully ({sql_result.get('execution_time', 0):.3f}s)")
            else:
                st.error(f"❌ SQL failed: {sql_result.get('error', 'Unknown error')}")
        else:
            st.info("No SQL query generated")
    
    with col2:
        st.markdown("### 📊 DAX Query")
        if results.get('generated_dax'):
            st.code(results['generated_dax'], language="text")
            
            # DAX execution status  
            dax_result = results.get('dax_result', {})
            if dax_result.get('success'):
                st.success(f"✅ DAX executed successfully ({dax_result.get('execution_time', 0):.3f}s)")
                
                # Show translated SQL if available
                if dax_result.get('translated_sql'):
                    with st.expander("🔄 DAX → SQL Translation"):
                        st.code(dax_result['translated_sql'], language="sql")
            else:
                st.error(f"❌ DAX failed: {dax_result.get('error', 'Unknown error')}")
        else:
            st.info("No DAX query generated")
    
    # Original query reminder
    with st.expander("💬 Original Natural Language Query"):
        st.markdown(f"**Query:** {user_query}")
        st.markdown(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Results tabs
    tab_names = []
    if results.get('sql_result'):
        tab_names.append("🗃️ SQL Results")
    if results.get('dax_result'):
        tab_names.append("📊 DAX Results")
    if results.get('comparison'):
        tab_names.append("🔍 Comparison")
    if results.get('performance'):
        tab_names.append("⏱️ Performance")
    
    if not tab_names:
        st.error("❌ No results to display")
        return
    
    tabs = st.tabs(tab_names)
    tab_index = 0
    
    # SQL Results Tab
    if results.get('sql_result'):
        with tabs[tab_index]:
            display_query_result(results['sql_result'], "SQL")
        tab_index += 1
    
    # DAX Results Tab
    if results.get('dax_result'):
        with tabs[tab_index]:
            display_query_result(results['dax_result'], "DAX")
        tab_index += 1
    
    # Comparison Tab
    if results.get('comparison'):
        with tabs[tab_index]:
            display_comparison(results['comparison'], results.get('sql_result'), results.get('dax_result'))
        tab_index += 1
    
    # Performance Tab
    if results.get('performance'):
        with tabs[tab_index]:
            display_performance(results['performance'])

def display_query_result(result: dict, query_type: str):
    """Display individual query result"""
    
    if not result.get('success', False):
        st.error(f"❌ {query_type} Query Failed")
        st.error(result.get('error', 'Unknown error'))
        return
    
    # Success metrics
    col1, col2, col3 = st.columns(3)
    
    data = result.get('data', [])
    with col1:
        st.metric("📊 Rows", len(data))
    
    columns = result.get('columns', [])
    with col2:
        st.metric("📋 Columns", len(columns))
    
    exec_time = result.get('execution_time', 0)
    with col3:
        st.metric("⏱️ Time", f"{exec_time:.3f}s")
    
    # Display data
    if data:
        # Convert to DataFrame for better display
        if isinstance(data[0], dict):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame(data, columns=columns if columns else None)
        
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {query_type} Results as CSV",
            data=csv,
            file_name=f"{query_type.lower()}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data returned")
    
    # Cache info
    if result.get('from_cache'):
        st.info(f"🎯 Result served from cache (cached at: {result.get('cache_timestamp', 'unknown')})")

def display_comparison(comparison: dict, sql_result: dict, dax_result: dict):
    """Display comparison results"""
    
    # Summary
    if comparison.get('matches'):
        st.success("✅ Results match perfectly!")
    else:
        st.error("❌ Results differ")
    
    st.markdown(f"**Summary:** {comparison.get('summary', 'No summary available')}")
    
    # Metrics comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🗃️ SQL Metrics:**")
        st.metric("Rows", comparison.get('sql_rows', 0))
        st.metric("Columns", comparison.get('sql_columns', 0))
        sql_time = sql_result.get('execution_time', 0) if sql_result else 0
        st.metric("Execution Time", f"{sql_time:.3f}s")
    
    with col2:
        st.markdown("**📊 DAX Metrics:**")
        st.metric("Rows", comparison.get('dax_rows', 0))
        st.metric("Columns", comparison.get('dax_columns', 0))
        dax_time = dax_result.get('execution_time', 0) if dax_result else 0
        st.metric("Execution Time", f"{dax_time:.3f}s")
    
    # Differences
    differences = comparison.get('differences', [])
    if differences:
        st.markdown("**❌ Differences Found:**")
        for i, diff in enumerate(differences[:10], 1):
            st.markdown(f"{i}. {diff}")
        
        if len(differences) > 10:
            st.markdown(f"... and {len(differences) - 10} more differences")
    
    # Detailed report
    if st.button("📋 Generate Detailed Report"):
        formatter = ResultFormatter()
        report = formatter.create_comparison_report(comparison, sql_result or {}, dax_result or {})
        st.code(report, language="text")

def display_performance(performance: dict):
    """Display performance metrics"""
    
    # Overall metrics
    col1, col2, col3 = st.columns(3)
    
    total_time = performance.get('total_execution_time', 0)
    with col1:
        st.metric("🕐 Total Time", f"{total_time:.3f}s")
    
    sql_time = performance.get('sql_execution_time', 0)
    with col2:
        st.metric("🗃️ SQL Time", f"{sql_time:.3f}s")
    
    dax_time = performance.get('dax_execution_time', 0)
    with col3:
        st.metric("📊 DAX Time", f"{dax_time:.3f}s")
    
    # Performance comparison
    if sql_time > 0 and dax_time > 0:
        if sql_time < dax_time:
            ratio = dax_time / sql_time
            st.success(f"🏆 SQL was faster by {ratio:.2f}x")
        elif dax_time < sql_time:
            ratio = sql_time / dax_time
            st.success(f"🏆 DAX was faster by {ratio:.2f}x")
        else:
            st.info("⚖️ SQL and DAX had similar performance")
    
    # Detailed breakdown
    with st.expander("📊 Detailed Performance Breakdown"):
        for key, value in performance.items():
            if isinstance(value, (int, float)):
                st.markdown(f"**{key}:** {value:.3f}s")
            else:
                st.markdown(f"**{key}:** {value}")

def create_history_tab():
    """Create the query history tab"""
    st.subheader("📚 Query History")
    
    if not st.session_state.query_history:
        st.info("No queries executed yet")
        return
    
    # Clear history button
    if st.button("🗑️ Clear History"):
        st.session_state.query_history = []
        st.rerun()
    
    # Display history
    for i, entry in enumerate(reversed(st.session_state.query_history), 1):
        with st.expander(f"Query {i}: {entry['query'][:50]}..." if len(entry['query']) > 50 else f"Query {i}: {entry['query']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Query:** {entry['query']}")
                st.markdown(f"**Executed:** {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                results = entry['results']
                sql_success = results.get('sql_result', {}).get('success', False)
                dax_success = results.get('dax_result', {}).get('success', False)
                
                st.markdown("**Status:**")
                if sql_success:
                    st.markdown("🗃️ SQL: ✅")
                if dax_success:
                    st.markdown("📊 DAX: ✅")
                
                if results.get('comparison', {}).get('matches'):
                    st.markdown("🔍 Match: ✅")

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Create sidebar
    config = create_sidebar()
    
    # Main content tabs
    main_tab, history_tab, schema_tab = st.tabs(["🔄 Query Pipeline", "📚 History", "🗂️ Schema"])
    
    with main_tab:
        create_main_interface()
    
    with history_tab:
        create_history_tab()
    
    with schema_tab:
        create_schema_tab()

def create_schema_tab():
    """Create the schema exploration tab"""
    st.subheader("🗂️ Database Schema")
    
    if not st.session_state.pipeline_initialized:
        st.warning("⚠️ Please initialize the pipeline first")
        return
    
    if st.button("🔍 Load Schema"):
        with st.spinner("Loading database schema..."):
            try:
                # Get schema information
                schema_analyzer = st.session_state.pipeline.schema_analyzer
                schema_info = schema_analyzer.get_full_schema()
                
                # Display tables
                st.markdown("### 📋 Tables")
                for table_name, table_info in schema_info.get('tables', {}).items():
                    with st.expander(f"📊 {table_name}"):
                        
                        # Table metadata
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Schema:** {table_info.get('schema', 'dbo')}")
                        with col2:
                            st.markdown(f"**Columns:** {len(table_info.get('columns', []))}")
                        
                        # Columns
                        columns = table_info.get('columns', [])
                        if columns:
                            df = pd.DataFrame(columns)
                            st.dataframe(df, use_container_width=True)
                
                # Display views if any
                views = schema_info.get('views', {})
                if views:
                    st.markdown("### 👁️ Views")
                    for view_name in views.keys():
                        st.markdown(f"- {view_name}")
                
            except Exception as e:
                st.error(f"❌ Error loading schema: {str(e)}")

if __name__ == "__main__":
    main()