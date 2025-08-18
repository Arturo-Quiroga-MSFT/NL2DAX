"""
streamlit_universal_ui.py - Universal Database-Agnostic Streamlit Interface
==========================================================================

This is the new universal Streamlit interface that works with any database
schema using AI-powered query generation. It replaces hardcoded queries
with intelligent analysis that adapts to any database structure.

Key Features:
- Automatic schema discovery and visualization
- Database-agnostic query generation
- Real-time business intent analysis
- Interactive query suggestions
- Universal visualizations that adapt to any schema

Author: NL2DAX Pipeline Development Team
Last Updated: August 16, 2025
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import json

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import universal interface
from core import UniversalQueryInterface, QueryType, AnalysisType

# Configure page
st.set_page_config(
    page_title="Universal NL2DAX Analytics",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .query-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        color: #856404;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Cache the universal interface to avoid reinitialization
@st.cache_resource
def get_universal_interface():
    """Initialize and cache the universal query interface"""
    return UniversalQueryInterface()

# Cache query execution to improve performance
@st.cache_data(ttl=300)  # Cache for 5 minutes
def execute_cached_query(query, query_type):
    """Execute query with caching - note: requires external execution modules"""
    st.warning("Query execution requires external modules (sql_executor, query_executor)")
    return None

def main():
    # Main header
    st.markdown('<h1 class="main-header">🌐 Universal NL2DAX Analytics Platform</h1>', unsafe_allow_html=True)
    
    # Initialize universal interface
    try:
        interface = get_universal_interface()
    except Exception as e:
        st.error(f"Failed to initialize universal interface: {e}")
        st.stop()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Query type selection
        query_type = st.selectbox(
            "Query Generation Type",
            ["Both (SQL + DAX)", "SQL Only", "DAX Only"],
            help="Choose what type of queries to generate"
        )
        
        # Analysis options
        st.subheader("Analysis Options")
        auto_suggest = st.checkbox("Enable AI Query Suggestions", value=True)
        show_schema = st.checkbox("Show Schema Analysis", value=True)
        show_complexity = st.checkbox("Show Query Complexity", value=True)
        
        # Cache management
        st.subheader("Cache Management")
        if st.button("Clear Query Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Overview", "🔍 Query Generator", "📊 Results Analysis", "🗄️ Schema Explorer"])
    
    with tab1:
        st.header("Database-Agnostic Analytics Overview")
        
        # Get schema summary
        try:
            schema_summary = interface.get_schema_summary()
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    f'<div class="metric-container"><h3>{schema_summary["total_tables"]}</h3><p>Total Tables</p></div>',
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    f'<div class="metric-container"><h3>{schema_summary["fact_tables"]}</h3><p>Fact Tables</p></div>',
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    f'<div class="metric-container"><h3>{schema_summary["dimension_tables"]}</h3><p>Dimension Tables</p></div>',
                    unsafe_allow_html=True
                )
            
            with col4:
                complexity_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
                complexity_icon = complexity_color.get(schema_summary["complexity_assessment"], "⚪")
                st.markdown(
                    f'<div class="metric-container"><h3>{complexity_icon}</h3><p>{schema_summary["complexity_assessment"]} Complexity</p></div>',
                    unsafe_allow_html=True
                )
            
            # Business areas discovered
            st.subheader("📋 Discovered Business Areas")
            areas_cols = st.columns(min(len(schema_summary["business_areas"]), 4))
            for i, area in enumerate(schema_summary["business_areas"]):
                with areas_cols[i % 4]:
                    st.info(f"🏢 {area}")
            
            # AI-generated suggestions
            if auto_suggest:
                st.subheader("🤖 AI-Generated Query Suggestions")
                try:
                    suggestions = interface.get_business_suggestions()
                    for i, suggestion in enumerate(suggestions[:5]):  # Show top 5
                        with st.expander(f"💡 {suggestion['query'][:60]}..."):
                            st.write(f"**Full Query:** {suggestion['query']}")
                            st.write(f"**Complexity:** {suggestion['complexity']}")
                            if st.button(f"Use This Query", key=f"suggest_{i}"):
                                st.session_state.suggested_query = suggestion['query']
                                st.success("Query copied to generator tab!")
                except Exception as e:
                    st.warning(f"Could not generate suggestions: {e}")
                    
        except Exception as e:
            st.error(f"Failed to load schema summary: {e}")
    
    with tab2:
        st.header("🔍 Universal Query Generator")
        
        # Check for suggested query
        default_query = ""
        if hasattr(st.session_state, 'suggested_query'):
            default_query = st.session_state.suggested_query
            del st.session_state.suggested_query
        
        # Natural language input
        st.subheader("Natural Language Query Input")
        user_query = st.text_area(
            "Enter your business question in natural language:",
            value=default_query,
            height=100,
            help="Example: 'Show me customers with highest risk ratings and their geographic distribution'"
        )
        
        # Query generation options
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🚀 Generate Queries", type="primary", use_container_width=True):
                if user_query.strip():
                    st.session_state.user_query = user_query.strip()
                    st.session_state.generate_queries = True
                else:
                    st.warning("Please enter a query first!")
        
        with col2:
            if st.button("🧹 Clear", use_container_width=True):
                if 'user_query' in st.session_state:
                    del st.session_state.user_query
                if 'generate_queries' in st.session_state:
                    del st.session_state.generate_queries
                st.rerun()
        
        # Query generation and display
        if hasattr(st.session_state, 'generate_queries') and st.session_state.generate_queries:
            user_query = st.session_state.user_query
            
            # Map selection to QueryType
            query_type_map = {
                "Both (SQL + DAX)": QueryType.BOTH,
                "SQL Only": QueryType.SQL,
                "DAX Only": QueryType.DAX
            }
            selected_type = query_type_map[query_type]
            
            # Generate queries
            with st.spinner("🤖 Generating database-agnostic queries..."):
                try:
                    result = interface.generate_query_from_intent(user_query, selected_type)
                    st.session_state.query_result = result
                    
                    # Show generation info
                    if show_complexity:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Analysis Type", result.analysis_type.value)
                        with col2:
                            st.metric("Complexity", result.estimated_complexity)
                        with col3:
                            st.metric("Business Intent", "Detected" if result.business_intent else "Not Found")
                    
                    if result.execution_notes:
                        st.markdown(f'<div class="warning-box">ℹ️ <strong>Notes:</strong> {result.execution_notes}</div>', unsafe_allow_html=True)
                    
                    # Display generated queries
                    if result.sql_query:
                        st.subheader("📄 Generated SQL Query")
                        st.markdown(f'<div class="query-box">{result.sql_query}</div>', unsafe_allow_html=True)
                        
                        # Execute SQL
                        if st.button("▶️ Execute SQL Query", key="exec_sql"):
                            with st.spinner("Executing SQL query..."):
                                sql_results = execute_cached_query(result.sql_query, "SQL")
                                if sql_results:
                                    st.session_state.sql_results = sql_results
                                    st.success(f"SQL query executed successfully! {len(sql_results)} rows returned.")
                                else:
                                    st.warning("SQL query returned no results.")
                    
                    if result.dax_query:
                        st.subheader("📊 Generated DAX Query")
                        st.markdown(f'<div class="query-box">{result.dax_query}</div>', unsafe_allow_html=True)
                        
                        # Execute DAX
                        if st.button("▶️ Execute DAX Query", key="exec_dax"):
                            with st.spinner("Executing DAX query..."):
                                dax_results = execute_cached_query(result.dax_query, "DAX")
                                if dax_results:
                                    st.session_state.dax_results = dax_results
                                    st.success(f"DAX query executed successfully! {len(dax_results)} rows returned.")
                                else:
                                    st.warning("DAX query returned no results.")
                                    
                except Exception as e:
                    st.error(f"Query generation failed: {e}")
    
    with tab3:
        st.header("📊 Universal Results Analysis")
        
        # Check for results
        has_sql_results = hasattr(st.session_state, 'sql_results') and st.session_state.sql_results
        has_dax_results = hasattr(st.session_state, 'dax_results') and st.session_state.dax_results
        
        if not has_sql_results and not has_dax_results:
            st.info("📝 Execute queries in the Query Generator tab to see results here.")
            
            # Show demo visualization with sample data
            st.subheader("📊 Demo Visualization Capabilities")
            st.write("Here's what visualizations look like with real data:")
            
            # Create sample data for demo
            sample_data = {
                'Category': ['A', 'B', 'C', 'D', 'E'],
                'Value': [23, 45, 56, 78, 32],
                'Score': [0.8, 0.6, 0.9, 0.7, 0.5]
            }
            demo_df = pd.DataFrame(sample_data)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(demo_df, x='Category', y='Value', title="Sample Bar Chart")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(demo_df, x='Value', y='Score', title="Sample Scatter Plot")
                st.plotly_chart(fig, use_container_width=True)
        else:
            # Result selection
            result_options = []
            if has_sql_results:
                result_options.append("SQL Results")
            if has_dax_results:
                result_options.append("DAX Results")
            
            if len(result_options) > 1:
                selected_result = st.selectbox("Select results to analyze:", result_options)
            else:
                selected_result = result_options[0]
            
            # Get selected results
            if selected_result == "SQL Results":
                results_data = st.session_state.sql_results
            else:
                results_data = st.session_state.dax_results
            
            # Convert to DataFrame
            df = pd.DataFrame(results_data)
            
            # Display basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                numeric_cols = df.select_dtypes(include=['number']).columns
                st.metric("Numeric Columns", len(numeric_cols))
            
            # Data preview
            st.subheader("📋 Data Preview")
            st.dataframe(df, use_container_width=True)
            
            # Automatic visualizations based on data types
            st.subheader("📈 Automatic Visualizations")
            
            # Detect column types for smart visualizations
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            if len(numeric_cols) > 0:
                viz_col1, viz_col2 = st.columns(2)
                
                with viz_col1:
                    # Distribution of first numeric column
                    if len(numeric_cols) > 0:
                        col = numeric_cols[0]
                        fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                        st.plotly_chart(fig, use_container_width=True)
                
                with viz_col2:
                    # Correlation heatmap if multiple numeric columns
                    if len(numeric_cols) > 1:
                        corr_matrix = df[numeric_cols].corr()
                        fig = px.imshow(corr_matrix, text_auto=True, title="Correlation Matrix")
                        st.plotly_chart(fig, use_container_width=True)
                    elif len(categorical_cols) > 0:
                        # Bar chart of categorical vs numeric
                        cat_col = categorical_cols[0]
                        num_col = numeric_cols[0]
                        fig = px.bar(df.groupby(cat_col)[num_col].sum().reset_index(), 
                                   x=cat_col, y=num_col, title=f"{num_col} by {cat_col}")
                        st.plotly_chart(fig, use_container_width=True)
            
            # Custom visualization builder
            st.subheader("🎨 Custom Visualization Builder")
            with st.expander("Build Custom Charts"):
                chart_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot", "Box Plot"])
                
                col1, col2 = st.columns(2)
                with col1:
                    x_axis = st.selectbox("X-Axis", df.columns)
                with col2:
                    y_axis = st.selectbox("Y-Axis", df.columns)
                
                if st.button("Generate Custom Chart"):
                    try:
                        if chart_type == "Bar Chart":
                            fig = px.bar(df, x=x_axis, y=y_axis)
                        elif chart_type == "Line Chart":
                            fig = px.line(df, x=x_axis, y=y_axis)
                        elif chart_type == "Scatter Plot":
                            fig = px.scatter(df, x=x_axis, y=y_axis)
                        elif chart_type == "Box Plot":
                            fig = px.box(df, x=x_axis, y=y_axis)
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Could not create chart: {e}")
            
            # Data export
            st.subheader("💾 Export Data")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📄 Download as CSV",
                    data=csv_data,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_data = df.to_json(orient='records')
                st.download_button(
                    label="📋 Download as JSON",
                    data=json_data,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with tab4:
        st.header("🗄️ Universal Schema Explorer")
        
        if show_schema:
            try:
                # Get detailed schema information
                interface = get_universal_interface()
                
                # Schema overview
                st.subheader("📊 Schema Overview")
                schema_summary = interface.get_schema_summary()
                
                # Create schema visualization
                col1, col2 = st.columns(2)
                
                with col1:
                    # Table type distribution
                    table_types = {
                        "Fact Tables": schema_summary["fact_tables"],
                        "Dimension Tables": schema_summary["dimension_tables"],
                        "Other Tables": schema_summary["total_tables"] - schema_summary["fact_tables"] - schema_summary["dimension_tables"]
                    }
                    
                    fig = px.pie(
                        values=list(table_types.values()),
                        names=list(table_types.keys()),
                        title="Table Type Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Business areas
                    business_areas = schema_summary["business_areas"]
                    area_counts = {area: 1 for area in business_areas}  # Equal weight for visualization
                    
                    fig = px.bar(
                        x=list(area_counts.keys()),
                        y=list(area_counts.values()),
                        title="Identified Business Areas"
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Suggested query patterns
                st.subheader("🔍 Suggested Query Patterns")
                patterns = schema_summary.get("suggested_patterns", [])
                for i, pattern in enumerate(patterns):
                    st.markdown(f"**{i+1}.** {pattern}")
                
                # Schema complexity analysis
                st.subheader("⚡ Schema Complexity Analysis")
                complexity = schema_summary["complexity_assessment"]
                
                if complexity == "Low":
                    st.success("✅ **Low Complexity** - Simple schema with clear relationships")
                elif complexity == "Medium":
                    st.warning("⚠️ **Medium Complexity** - Moderate schema requiring some analysis")
                else:
                    st.error("🔥 **High Complexity** - Complex schema with many relationships")
                
                # Database adaptability info
                st.subheader("🌐 Universal Adaptability")
                st.markdown("""
                <div class="success-box">
                <h4>🚀 This interface automatically adapts to ANY database schema!</h4>
                <ul>
                <li><strong>SQL Databases:</strong> PostgreSQL, MySQL, SQL Server, Oracle, SQLite, etc.</li>
                <li><strong>Semantic Models:</strong> Power BI, Fabric, Analysis Services, etc.</li>
                <li><strong>AI-Powered:</strong> Intelligent schema discovery and pattern recognition</li>
                <li><strong>Business-Focused:</strong> Generates queries based on business intent</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Failed to load schema information: {e}")
        else:
            st.info("Enable 'Show Schema Analysis' in the sidebar to view schema details.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Universal NL2DAX Analytics Platform** - Powered by AI-driven schema discovery and database-agnostic query generation 🌐",
        help="This platform automatically adapts to any database schema without requiring code changes."
    )

if __name__ == "__main__":
    main()