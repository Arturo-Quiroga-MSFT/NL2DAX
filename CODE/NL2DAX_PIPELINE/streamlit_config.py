"""
Streamlit Configuration and Utilities

This module provides configuration management and utility functions
for the NL2DAX Streamlit interface, including theme settings,
environment validation, and common UI components.
"""

import streamlit as st
import os
from pathlib import Path

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "NL2DAX Query Interface",
    "page_icon": "🔍", 
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        'Get Help': 'https://github.com/Arturo-Quiroga-MSFT/NL2DAX',
        'Report a bug': 'https://github.com/Arturo-Quiroga-MSFT/NL2DAX/issues',
        'About': "# NL2DAX Query Interface\nTransform natural language into SQL and DAX queries!"
    }
}

# CSS styling for the interface
CUSTOM_CSS = """
<style>
    .main-header {
        background: linear-gradient(90deg, #0066cc 0%, #004499 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .metric-container {
        background: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
    }
    
    .query-box {
        border: 2px solid #e1e5e9;
        border-radius: 0.5rem;
        padding: 1rem;
        background: #fafbfc;
    }
    
    .results-container {
        border: 1px solid #d1d5db;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 0.75rem;
        color: #155724;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 0.75rem;
        color: #721c24;
    }
</style>
"""

# Example queries for the sidebar
EXAMPLE_QUERIES = [
    {
        "title": "Top Customers by Credit",
        "query": "Show me the top 5 customers by total credit amount",
        "description": "Returns customers ranked by their total credit exposure"
    },
    {
        "title": "Risk Analysis",
        "query": "What is the average risk rating by customer type?",
        "description": "Analyzes risk distribution across customer segments"
    },
    {
        "title": "Exposure Analysis",
        "query": "List customers with the highest exposure at default",
        "description": "Identifies customers with maximum potential loss exposure"
    },
    {
        "title": "Comprehensive Analysis",
        "query": "Show me comprehensive customer analysis grouped by type",
        "description": "Complete customer breakdown with multiple metrics"
    },
    {
        "title": "Geographic Analysis",
        "query": "Which customers are located in the United States?",
        "description": "Filters customers by geographic location"
    },
    {
        "title": "Portfolio Overview",
        "query": "Show me the total portfolio balance and count by customer type",
        "description": "High-level portfolio metrics and distribution"
    }
]

def apply_custom_styling():
    """Apply custom CSS styling to the Streamlit interface"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def create_header():
    """Create the main application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 NL2DAX Query Interface</h1>
        <p>Transform natural language into SQL and DAX queries with side-by-side result comparison</p>
    </div>
    """, unsafe_allow_html=True)

def validate_environment():
    """Validate that required environment variables are set"""
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'SQL_SERVER_CONNECTION_STRING'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        st.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        st.info("💡 Please ensure your .env file contains all required variables")
        return False
    
    return True

def create_sidebar():
    """Create the sidebar with examples and history"""
    with st.sidebar:
        st.header("📝 Query Examples")
        
        for example in EXAMPLE_QUERIES:
            with st.expander(f"💡 {example['title']}"):
                st.write(example['description'])
                if st.button(f"Use: {example['title']}", key=f"example_{example['title']}", use_container_width=True):
                    return example['query']
        
        return None

def format_dataframe_for_display(df, title="Results"):
    """Format a pandas DataFrame for better display in Streamlit"""
    if df is None or len(df) == 0:
        return None
    
    # Convert numeric columns to appropriate display format
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    
    for col in numeric_columns:
        if df[col].dtype == 'float64':
            # Format float columns to 2 decimal places
            df[col] = df[col].round(2)
    
    return df

def create_download_button(data, filename_prefix, label_prefix="Download"):
    """Create a standardized download button for data"""
    if data is not None and len(data) > 0:
        import pandas as pd
        from datetime import datetime
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
            
        csv = df.to_csv(index=False)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.csv"
        
        return st.download_button(
            label=f"📥 {label_prefix} ({len(df)} rows)",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    
    return False

def show_query_info(query_type, query_text, execution_time, row_count):
    """Display formatted query information"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.code(query_text, language="sql" if query_type == "SQL" else "dax")
    
    with col2:
        st.metric("⏱️ Execution Time", f"{execution_time:.1f}s")
        st.metric("📊 Rows Returned", row_count)

def create_error_display(errors):
    """Create a standardized error display"""
    if errors:
        for error in errors:
            st.markdown(f"""
            <div class="error-box">
                ❌ <strong>Error:</strong> {error}
            </div>
            """, unsafe_allow_html=True)

def create_success_display(message):
    """Create a standardized success display"""
    st.markdown(f"""
    <div class="success-box">
        ✅ <strong>Success:</strong> {message}
    </div>
    """, unsafe_allow_html=True)

def get_app_version():
    """Get application version information"""
    return {
        "version": "1.0.0",
        "build_date": "2025-08-15",
        "author": "NL2DAX Development Team"
    }

# Configuration validation
def validate_streamlit_config():
    """Validate Streamlit configuration and dependencies"""
    try:
        import streamlit as st
        import pandas as pd
        import plotly.express as px
        return True
    except ImportError as e:
        st.error(f"❌ Missing dependency: {e}")
        return False
