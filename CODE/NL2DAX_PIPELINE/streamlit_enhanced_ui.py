"""
Enhanced NL2DAX Streamlit Interface with Advanced Visualizations

This enhanced version includes a sophisticated Analysis tab with international data visualizations
based on the comprehensive test question suite. It supports geographic maps, financial dashboards,
risk analytics, and interactive exploration of the multi-country, multi-currency dataset.

Key Features:
- Advanced Analysis tab with geographic visualizations
- Multi-currency financial dashboards
- Risk analytics and concentration monitoring
- Interactive filters and drill-down capabilities
- International customer and portfolio analysis
- Comprehensive chart library (maps, treemaps, dashboards, time series)

Author: NL2DAX Development Team
Date: August 16, 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import io
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff

# Additional imports for advanced visualizations
import json

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import your existing pipeline modules
from dax_generator import generate_dax
from dax_formatter import format_and_validate_dax
from query_executor import execute_dax_query
from sql_executor import execute_sql_query
from schema_reader import get_schema_metadata, get_sql_database_schema_context
from query_cache import get_cache
from report_generator import PipelineReportGenerator

# Import core pipeline functions directly (avoiding streamlit_ui.py to prevent set_page_config conflicts)
from main import generate_sql
import re
import json
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Azure OpenAI LLM for intent parsing and SQL generation
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2025-04-01-preview",
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "o4-mini")
)

# Initialize schema cache - load once and reuse throughout the session
@st.cache_data
def get_cached_schema_metadata():
    """Get comprehensive schema metadata with Streamlit caching"""
    return get_schema_metadata()

@st.cache_data  
def get_cached_sql_schema_context():
    """Get SQL database schema context with Streamlit caching"""
    return get_sql_database_schema_context()

def parse_intent_entities(user_input):
    """Parse natural language into structured intent and entities"""
    
    # Get cached schema for context
    schema_context = get_cached_sql_schema_context()
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert in translating natural language to database queries for a Financial Risk Management system.
        
        EXACT DATABASE SCHEMA CONTEXT:
        {schema}
        
        IMPORTANT GUIDELINES:
        - Use ONLY the exact table and column names from the schema above
        - Main customer table: FIS_CUSTOMER_DIMENSION (NOT "customers")
        - Credit arrangements: FIS_CA_DETAIL_FACT 
        - Commercial loans: FIS_CL_DETAIL_FACT
        - Key customer fields: CUSTOMER_KEY, CUSTOMER_NAME, CUSTOMER_TYPE_DESCRIPTION, RISK_RATING_CODE
        - Credit amount fields: LIMIT_AMOUNT, EXPOSURE_AT_DEFAULT, PRINCIPAL_BALANCE
        - RISK_RATING_CODE is a text field with values like "A+", "A", "A-", "B+", "B", "B-", "C+", etc.
        - For numeric risk analysis, use PROBABILITY_OF_DEFAULT (decimal values)
        - LIMIT_AMOUNT and EXPOSURE_AT_DEFAULT are numeric currency fields
        
        Extract the intent and entities from the following user input, using the correct table names from the schema:
        {input}
        
        Return ONLY a valid JSON object with intent and entities. Example format:
        {{
            "intent": "show_top_customers",
            "entities": {{
                "limit": 5,
                "table": "FIS_CUSTOMER_DIMENSION",
                "sort_field": "LIMIT_AMOUNT",
                "sort_order": "desc"
            }}
        }}
        
        Return only valid JSON - no explanatory text.
        """
    )
    chain = prompt | llm
    result = chain.invoke({"input": user_input, "schema": schema_context})
    
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

def validate_sql_syntax(sql_query):
    """Basic SQL syntax validation"""
    if not sql_query or len(sql_query.strip()) < 10:
        return "SQL query appears to be empty or too short"
    
    # Check for balanced parentheses
    open_count = sql_query.count('(')
    close_count = sql_query.count(')')
    
    if open_count != close_count:
        return f"Unbalanced parentheses: {open_count} open, {close_count} close"
    
    # Check for CTE syntax
    if 'WITH' not in sql_query.upper() and any(cte_pattern in sql_query for cte_pattern in ['AS (', 'AS(']):
        return "Query appears to use CTEs but missing WITH keyword"
    
    # Check for incomplete statements
    sql_upper = sql_query.upper().strip()
    if sql_upper.endswith(',') or sql_upper.endswith('('):
        return "SQL query appears incomplete - ends with comma or open parenthesis"
    
    return "SQL query appears valid"

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
            sql_raw = generate_sql(results['intent_entities'])  # Use existing function from main.py
            
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
                
                # Validate SQL syntax
                sql_validation = validate_sql_syntax(sql_sanitized)
                if "appears valid" not in sql_validation:
                    results['errors'].append(f"SQL Validation Warning: {sql_validation}")
                
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
        
        # Step 4: Generate comprehensive report (optional, can be disabled to avoid errors)
        try:
            cache = get_cache()
            cache_stats = cache.get_stats_for_report()
            
            report_generator = PipelineReportGenerator()
            
            # Prepare execution data for report
            execution_data = {
                'user_query': user_query,
                'intent_entities': results['intent_entities'],
                'sql_query': results['sql_query'],
                'dax_query': results['dax_query'],
                'sql_results': results['sql_results'],
                'dax_results': results['dax_results'],
                'sql_execution_time': results['sql_time'],
                'dax_execution_time': results['dax_time'],
                'total_execution_time': time.time() - sql_start,
                'errors': results['errors'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Generate and save report
            report_path = report_generator.generate_report(
                user_query=user_query,
                execution_results=execution_data,
                cache_stats=cache_stats
            )
            
            results['report_path'] = report_path
            
        except Exception as report_error:
            results['errors'].append(f"Report Generation Warning: {str(report_error)}")
            
    except Exception as e:
        results['errors'].append(f"Pipeline Error: {str(e)}")
    
    return results

# Country code mapping for enhanced geographic visualizations
COUNTRY_CODE_MAPPING = {
    'US': 'United States',
    'CA': 'Canada', 
    'MX': 'Mexico',
    'BR': 'Brazil',
    'AR': 'Argentina',
    'CO': 'Colombia',
    'DE': 'Germany',
    'SG': 'Singapore',
    'ZA': 'South Africa'
}

# Currency display mapping
CURRENCY_MAPPING = {
    'USD': '🇺🇸 US Dollar',
    'CAD': '🇨🇦 Canadian Dollar',
    'MXN': '🇲🇽 Mexican Peso',
    'BRL': '🇧🇷 Brazilian Real',
    'ARS': '🇦🇷 Argentine Peso',
    'COP': '🇨🇴 Colombian Peso',
    'EUR': '🇪🇺 Euro'
}

# Risk rating colors
RISK_COLORS = {
    'A+': '#00ff00', 'A': '#40ff00', 'A-': '#80ff00',
    'B+': '#c0ff00', 'B': '#ffff00', 'B-': '#ffc000',
    'C+': '#ff8000', 'C': '#ff4000', 'C-': '#ff0000'
}

@st.cache_data
def get_international_customer_data():
    """Get comprehensive international customer data for analysis"""
    try:
        query = """
        SELECT 
            cd.CUSTOMER_KEY,
            cd.CUSTOMER_NAME,
            cd.COUNTRY_CODE,
            cd.COUNTRY_DESCRIPTION,
            cd.CUSTOMER_TYPE_DESCRIPTION,
            cd.RISK_RATING_CODE,
            COALESCE(fact_summary.AVG_PROBABILITY_OF_DEFAULT, 0) as PROBABILITY_OF_DEFAULT,
            COALESCE(loan_summary.TOTAL_LOAN_AMOUNT, 0) as TOTAL_LOAN_AMOUNT,
            COALESCE(loan_summary.LOAN_COUNT, 0) as LOAN_COUNT,
            COALESCE(facility_summary.TOTAL_FACILITY_AMOUNT, 0) as TOTAL_FACILITY_AMOUNT,
            COALESCE(facility_summary.FACILITY_COUNT, 0) as FACILITY_COUNT
        FROM FIS_CUSTOMER_DIMENSION cd
        LEFT JOIN (
            SELECT 
                CUSTOMER_KEY,
                AVG(PROBABILITY_OF_DEFAULT) as AVG_PROBABILITY_OF_DEFAULT
            FROM FIS_CA_DETAIL_FACT
            GROUP BY CUSTOMER_KEY
        ) fact_summary ON cd.CUSTOMER_KEY = fact_summary.CUSTOMER_KEY
        LEFT JOIN (
            SELECT 
                CUSTOMER_KEY,
                SUM(PRINCIPAL_BALANCE) as TOTAL_LOAN_AMOUNT,
                COUNT(*) as LOAN_COUNT
            FROM FIS_CL_DETAIL_FACT
            GROUP BY CUSTOMER_KEY
        ) loan_summary ON cd.CUSTOMER_KEY = loan_summary.CUSTOMER_KEY
        LEFT JOIN (
            SELECT 
                CUSTOMER_KEY,
                SUM(LIMIT_AMOUNT) as TOTAL_FACILITY_AMOUNT,
                COUNT(*) as FACILITY_COUNT
            FROM FIS_CA_DETAIL_FACT
            GROUP BY CUSTOMER_KEY
        ) facility_summary ON cd.CUSTOMER_KEY = facility_summary.CUSTOMER_KEY
        WHERE cd.CUSTOMER_KEY IS NOT NULL
        ORDER BY cd.COUNTRY_CODE, cd.CUSTOMER_NAME
        """
        
        results = execute_sql_query(query)
        if results:
            df = pd.DataFrame(results)
            # Add enhanced country and currency mappings
            df['COUNTRY_DISPLAY'] = df['COUNTRY_CODE'].map(COUNTRY_CODE_MAPPING)
            df['TOTAL_EXPOSURE'] = df['TOTAL_LOAN_AMOUNT'] + df['TOTAL_FACILITY_AMOUNT']
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading international customer data: {e}")
        return pd.DataFrame()

@st.cache_data
def get_currency_exposure_data():
    """Get multi-currency exposure data for analysis"""
    try:
        # Loan exposure by currency
        loan_query = """
        SELECT 
            lp.LOAN_CURRENCY_CODE as CURRENCY_CODE,
            cd.COUNTRY_CODE,
            cd.COUNTRY_DESCRIPTION,
            SUM(cl.PRINCIPAL_BALANCE) as LOAN_EXPOSURE,
            COUNT(cl.CL_DETAIL_KEY) as LOAN_COUNT
        FROM FIS_CL_DETAIL_FACT cl
        JOIN FIS_LOAN_PRODUCT_DIMENSION lp ON cl.LOAN_PRODUCT_KEY = lp.LOAN_PRODUCT_KEY
        JOIN FIS_CUSTOMER_DIMENSION cd ON cl.CUSTOMER_KEY = cd.CUSTOMER_KEY
        WHERE cd.CUSTOMER_KEY IS NOT NULL
        GROUP BY lp.LOAN_CURRENCY_CODE, cd.COUNTRY_CODE, cd.COUNTRY_DESCRIPTION
        """
        
        # Credit facility exposure by currency
        facility_query = """
        SELECT 
            cap.CA_CURRENCY_CODE as CURRENCY_CODE,
            cd.COUNTRY_CODE,
            cd.COUNTRY_DESCRIPTION,
            SUM(ca.LIMIT_AMOUNT) as FACILITY_EXPOSURE,
            COUNT(ca.CA_DETAIL_KEY) as FACILITY_COUNT
        FROM FIS_CA_DETAIL_FACT ca
        JOIN FIS_CA_PRODUCT_DIMENSION cap ON ca.CA_PRODUCT_KEY = cap.CA_PRODUCT_KEY
        JOIN FIS_CUSTOMER_DIMENSION cd ON ca.CUSTOMER_KEY = cd.CUSTOMER_KEY
        WHERE cd.CUSTOMER_KEY IS NOT NULL
        GROUP BY cap.CA_CURRENCY_CODE, cd.COUNTRY_CODE, cd.COUNTRY_DESCRIPTION
        """
        
        loan_results = execute_sql_query(loan_query)
        facility_results = execute_sql_query(facility_query)
        
        # Combine results
        combined_data = []
        
        if loan_results:
            for row in loan_results:
                combined_data.append({
                    'CURRENCY_CODE': row['CURRENCY_CODE'],
                    'COUNTRY_CODE': row['COUNTRY_CODE'],
                    'COUNTRY_DESCRIPTION': row['COUNTRY_DESCRIPTION'],
                    'LOAN_EXPOSURE': row['LOAN_EXPOSURE'],
                    'FACILITY_EXPOSURE': 0,
                    'TOTAL_EXPOSURE': row['LOAN_EXPOSURE'],
                    'PRODUCT_TYPE': 'Loans'
                })
        
        if facility_results:
            for row in facility_results:
                combined_data.append({
                    'CURRENCY_CODE': row['CURRENCY_CODE'],
                    'COUNTRY_CODE': row['COUNTRY_CODE'],
                    'COUNTRY_DESCRIPTION': row['COUNTRY_DESCRIPTION'],
                    'LOAN_EXPOSURE': 0,
                    'FACILITY_EXPOSURE': row['FACILITY_EXPOSURE'],
                    'TOTAL_EXPOSURE': row['FACILITY_EXPOSURE'],
                    'PRODUCT_TYPE': 'Credit Facilities'
                })
        
        if combined_data:
            df = pd.DataFrame(combined_data)
            df['CURRENCY_DISPLAY'] = df['CURRENCY_CODE'].map(CURRENCY_MAPPING)
            df['COUNTRY_DISPLAY'] = df['COUNTRY_CODE'].map(COUNTRY_CODE_MAPPING)
            return df
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading currency exposure data: {e}")
        return pd.DataFrame()

def create_world_map_visualization(df, value_column, title):
    """Create an interactive world map visualization"""
    if df.empty:
        st.warning("No data available for world map visualization")
        return None
    
    # Aggregate data by country
    country_data = df.groupby(['COUNTRY_CODE', 'COUNTRY_DISPLAY'])[value_column].sum().reset_index()
    
    # Create the map
    fig = px.choropleth(
        country_data,
        locations='COUNTRY_CODE',
        color=value_column,
        hover_name='COUNTRY_DISPLAY',
        hover_data={value_column: ':,.0f'},
        color_continuous_scale='Blues',
        title=title
    )
    
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        title_x=0.5,
        height=500
    )
    
    return fig

def create_currency_treemap(df):
    """Create a currency treemap visualization"""
    if df.empty:
        st.warning("No data available for currency treemap")
        return None
    
    # Aggregate by currency
    currency_data = df.groupby(['CURRENCY_CODE', 'CURRENCY_DISPLAY']).agg({
        'TOTAL_EXPOSURE': 'sum',
        'COUNTRY_CODE': 'count'
    }).reset_index()
    currency_data.rename(columns={'COUNTRY_CODE': 'COUNTRY_COUNT'}, inplace=True)
    
    fig = px.treemap(
        currency_data,
        path=['CURRENCY_DISPLAY'],
        values='TOTAL_EXPOSURE',
        title='Portfolio Exposure by Currency',
        color='TOTAL_EXPOSURE',
        color_continuous_scale='RdYlBu_r'
    )
    
    fig.update_layout(
        title_x=0.5,
        height=500
    )
    
    return fig

def create_risk_dashboard(customer_df):
    """Create a comprehensive risk analytics dashboard"""
    if customer_df.empty:
        st.warning("No customer data available for risk dashboard")
        return None
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Risk Distribution by Country',
            'Exposure vs Risk Rating',
            'Geographic Risk Concentration',
            'Risk Profile Summary'
        ),
        specs=[
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "sunburst"}, {"type": "indicator"}]
        ]
    )
    
    # 1. Risk distribution by country
    risk_by_country = customer_df.groupby(['COUNTRY_CODE', 'RISK_RATING_CODE']).size().reset_index(name='COUNT')
    for country in risk_by_country['COUNTRY_CODE'].unique():
        country_data = risk_by_country[risk_by_country['COUNTRY_CODE'] == country]
        fig.add_trace(
            go.Bar(
                x=country_data['RISK_RATING_CODE'],
                y=country_data['COUNT'],
                name=country,
                showlegend=True
            ),
            row=1, col=1
        )
    
    # 2. Exposure vs Risk (Bubble chart)
    risk_exposure = customer_df.groupby('RISK_RATING_CODE').agg({
        'TOTAL_EXPOSURE': 'sum',
        'PROBABILITY_OF_DEFAULT': 'mean',
        'CUSTOMER_KEY': 'count'
    }).reset_index()
    
    fig.add_trace(
        go.Scatter(
            x=risk_exposure['PROBABILITY_OF_DEFAULT'],
            y=risk_exposure['TOTAL_EXPOSURE'],
            mode='markers',
            marker=dict(
                size=risk_exposure['CUSTOMER_KEY'] * 10,
                color=risk_exposure['TOTAL_EXPOSURE'],
                colorscale='Reds',
                showscale=True
            ),
            text=risk_exposure['RISK_RATING_CODE'],
            name='Risk vs Exposure',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. Geographic risk concentration (Sunburst)
    sunburst_data = customer_df.groupby(['COUNTRY_DISPLAY', 'RISK_RATING_CODE']).agg({
        'TOTAL_EXPOSURE': 'sum'
    }).reset_index()
    
    fig.add_trace(
        go.Sunburst(
            labels=sunburst_data['COUNTRY_DISPLAY'].tolist() + sunburst_data['RISK_RATING_CODE'].tolist(),
            parents=[''] * len(sunburst_data['COUNTRY_DISPLAY'].unique()) + sunburst_data['COUNTRY_DISPLAY'].tolist(),
            values=[0] * len(sunburst_data['COUNTRY_DISPLAY'].unique()) + sunburst_data['TOTAL_EXPOSURE'].tolist(),
            name='Geographic Risk'
        ),
        row=2, col=1
    )
    
    # 4. Risk indicators
    avg_risk = customer_df['PROBABILITY_OF_DEFAULT'].mean()
    high_risk_count = len(customer_df[customer_df['RISK_RATING_CODE'].isin(['C+', 'C', 'C-'])])
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=avg_risk * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Avg PD %"},
            delta={'reference': 5},
            gauge={
                'axis': {'range': [None, 20]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 5], 'color': "lightgray"},
                    {'range': [5, 10], 'color': "yellow"},
                    {'range': [10, 20], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 10
                }
            }
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title_text="International Portfolio Risk Dashboard",
        title_x=0.5,
        height=800,
        showlegend=True
    )
    
    return fig

def create_financial_trends_chart(currency_df):
    """Create financial trends visualization"""
    if currency_df.empty:
        st.warning("No data available for financial trends")
        return None
    
    # Aggregate by currency and product type
    trends_data = currency_df.groupby(['CURRENCY_CODE', 'PRODUCT_TYPE']).agg({
        'TOTAL_EXPOSURE': 'sum'
    }).reset_index()
    
    fig = px.sunburst(
        trends_data,
        path=['CURRENCY_CODE', 'PRODUCT_TYPE'],
        values='TOTAL_EXPOSURE',
        title='Portfolio Composition: Currency → Product Type',
        color='TOTAL_EXPOSURE',
        color_continuous_scale='RdYlBu'
    )
    
    fig.update_layout(
        title_x=0.5,
        height=600
    )
    
    return fig

def enhanced_analysis_tab():
    """Enhanced Analysis tab with comprehensive visualizations"""
    st.header("📈 Advanced Portfolio Analysis")
    st.markdown("Interactive visualizations of international portfolio data")
    
    # Load data
    with st.spinner("Loading international portfolio data..."):
        customer_df = get_international_customer_data()
        currency_df = get_currency_exposure_data()
    
    if customer_df.empty and currency_df.empty:
        st.error("No data available for analysis. Please ensure the database contains international customer data.")
        return
    
    # Create analysis tabs
    viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
        "🗺️ Geographic Analysis", 
        "💰 Currency & Financial", 
        "⚠️ Risk Analytics", 
        "📊 Portfolio Overview"
    ])
    
    with viz_tab1:
        st.subheader("🌍 Geographic Portfolio Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # World map of customer distribution
            if not customer_df.empty:
                world_map = create_world_map_visualization(
                    customer_df, 
                    'TOTAL_EXPOSURE', 
                    'Portfolio Exposure by Country'
                )
                if world_map:
                    st.plotly_chart(world_map, use_container_width=True)
            
        with col2:
            # Country comparison bar chart
            if not customer_df.empty:
                country_summary = customer_df.groupby('COUNTRY_DISPLAY').agg({
                    'TOTAL_EXPOSURE': 'sum',
                    'CUSTOMER_KEY': 'count'
                }).reset_index()
                
                fig_bar = px.bar(
                    country_summary,
                    x='COUNTRY_DISPLAY',
                    y='TOTAL_EXPOSURE',
                    title='Total Exposure by Country',
                    color='CUSTOMER_KEY',
                    color_continuous_scale='Blues'
                )
                fig_bar.update_xaxes(tickangle=45)
                fig_bar.update_layout(title_x=0.5, height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Geographic data table
        if not customer_df.empty:
            st.subheader("📋 Geographic Summary")
            geo_summary = customer_df.groupby(['COUNTRY_CODE', 'COUNTRY_DISPLAY']).agg({
                'CUSTOMER_KEY': 'count',
                'TOTAL_EXPOSURE': 'sum',
                'TOTAL_LOAN_AMOUNT': 'sum',
                'TOTAL_FACILITY_AMOUNT': 'sum'
            }).reset_index()
            geo_summary.columns = ['Code', 'Country', 'Customers', 'Total Exposure', 'Loans', 'Facilities']
            st.dataframe(geo_summary, use_container_width=True)
    
    with viz_tab2:
        st.subheader("💱 Multi-Currency Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Currency treemap
            if not currency_df.empty:
                treemap = create_currency_treemap(currency_df)
                if treemap:
                    st.plotly_chart(treemap, use_container_width=True)
        
        with col2:
            # Currency distribution pie chart
            if not currency_df.empty:
                currency_summary = currency_df.groupby('CURRENCY_DISPLAY')['TOTAL_EXPOSURE'].sum().reset_index()
                
                fig_pie = px.pie(
                    currency_summary,
                    values='TOTAL_EXPOSURE',
                    names='CURRENCY_DISPLAY',
                    title='Portfolio Distribution by Currency'
                )
                fig_pie.update_layout(title_x=0.5, height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        # Financial trends
        if not currency_df.empty:
            st.subheader("📈 Portfolio Composition Analysis")
            trends_chart = create_financial_trends_chart(currency_df)
            if trends_chart:
                st.plotly_chart(trends_chart, use_container_width=True)
        
        # Currency exposure table
        if not currency_df.empty:
            st.subheader("💰 Currency Exposure Summary")
            currency_table = currency_df.groupby(['CURRENCY_CODE', 'CURRENCY_DISPLAY']).agg({
                'TOTAL_EXPOSURE': 'sum',
                'LOAN_EXPOSURE': 'sum',
                'FACILITY_EXPOSURE': 'sum'
            }).reset_index()
            currency_table.columns = ['Code', 'Currency', 'Total Exposure', 'Loan Exposure', 'Facility Exposure']
            st.dataframe(currency_table, use_container_width=True)
    
    with viz_tab3:
        st.subheader("⚠️ Risk Analytics Dashboard")
        
        if not customer_df.empty:
            # Comprehensive risk dashboard
            risk_dashboard = create_risk_dashboard(customer_df)
            if risk_dashboard:
                st.plotly_chart(risk_dashboard, use_container_width=True)
            
            # Risk metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_pd = customer_df['PROBABILITY_OF_DEFAULT'].mean() * 100
                st.metric("Avg Probability of Default", f"{avg_pd:.2f}%")
            
            with col2:
                high_risk = len(customer_df[customer_df['RISK_RATING_CODE'].isin(['C+', 'C', 'C-'])])
                st.metric("High Risk Customers", high_risk)
            
            with col3:
                countries_count = customer_df['COUNTRY_CODE'].nunique()
                st.metric("Countries", countries_count)
            
            with col4:
                total_exposure = customer_df['TOTAL_EXPOSURE'].sum()
                st.metric("Total Exposure", f"${total_exposure:,.0f}")
        
        # Risk concentration table
        if not customer_df.empty:
            st.subheader("🎯 Risk Concentration Analysis")
            risk_concentration = customer_df.groupby(['COUNTRY_DISPLAY', 'RISK_RATING_CODE']).agg({
                'CUSTOMER_KEY': 'count',
                'TOTAL_EXPOSURE': 'sum'
            }).reset_index()
            risk_concentration.columns = ['Country', 'Risk Rating', 'Customers', 'Total Exposure']
            st.dataframe(risk_concentration, use_container_width=True)
    
    with viz_tab4:
        st.subheader("📊 Portfolio Overview Dashboard")
        
        # Key metrics row
        if not customer_df.empty:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                total_customers = len(customer_df)
                st.metric("Total Customers", total_customers)
            
            with col2:
                total_exposure = customer_df['TOTAL_EXPOSURE'].sum()
                st.metric("Total Exposure", f"${total_exposure:,.0f}")
            
            with col3:
                avg_exposure = customer_df['TOTAL_EXPOSURE'].mean()
                st.metric("Avg Exposure per Customer", f"${avg_exposure:,.0f}")
            
            with col4:
                countries = customer_df['COUNTRY_CODE'].nunique()
                st.metric("Countries", countries)
            
            with col5:
                currencies = customer_df['COUNTRY_CODE'].nunique()  # Approximation
                st.metric("Currencies", currencies)
        
        # Portfolio composition analysis
        col1, col2 = st.columns(2)
        
        with col1:
            if not customer_df.empty:
                # Customer type distribution
                customer_type_dist = customer_df.groupby('CUSTOMER_TYPE_DESCRIPTION')['TOTAL_EXPOSURE'].sum().reset_index()
                
                fig_type = px.bar(
                    customer_type_dist,
                    x='CUSTOMER_TYPE_DESCRIPTION',
                    y='TOTAL_EXPOSURE',
                    title='Exposure by Customer Type',
                    color='TOTAL_EXPOSURE',
                    color_continuous_scale='Viridis'
                )
                fig_type.update_xaxis(tickangle=45)
                fig_type.update_layout(title_x=0.5, height=400)
                st.plotly_chart(fig_type, use_container_width=True)
        
        with col2:
            if not customer_df.empty:
                # Risk rating distribution
                risk_dist = customer_df.groupby('RISK_RATING_CODE')['TOTAL_EXPOSURE'].sum().reset_index()
                
                fig_risk = px.bar(
                    risk_dist,
                    x='RISK_RATING_CODE',
                    y='TOTAL_EXPOSURE',
                    title='Exposure by Risk Rating',
                    color='RISK_RATING_CODE',
                    color_discrete_map=RISK_COLORS
                )
                fig_risk.update_layout(title_x=0.5, height=400, showlegend=False)
                st.plotly_chart(fig_risk, use_container_width=True)
        
        # Detailed portfolio table
        if not customer_df.empty:
            st.subheader("🏦 Detailed Customer Portfolio")
            
            # Add filters
            col1, col2, col3 = st.columns(3)
            with col1:
                country_filter = st.selectbox(
                    "Filter by Country",
                    options=['All'] + list(customer_df['COUNTRY_DISPLAY'].unique()),
                    key="country_filter"
                )
            with col2:
                risk_filter = st.selectbox(
                    "Filter by Risk Rating",
                    options=['All'] + list(customer_df['RISK_RATING_CODE'].unique()),
                    key="risk_filter"
                )
            with col3:
                min_exposure = st.number_input(
                    "Minimum Exposure",
                    min_value=0,
                    value=0,
                    key="min_exposure"
                )
            
            # Apply filters
            filtered_df = customer_df.copy()
            if country_filter != 'All':
                filtered_df = filtered_df[filtered_df['COUNTRY_DISPLAY'] == country_filter]
            if risk_filter != 'All':
                filtered_df = filtered_df[filtered_df['RISK_RATING_CODE'] == risk_filter]
            if min_exposure > 0:
                filtered_df = filtered_df[filtered_df['TOTAL_EXPOSURE'] >= min_exposure]
            
            # Display filtered data
            display_cols = [
                'CUSTOMER_NAME', 'COUNTRY_DISPLAY', 'RISK_RATING_CODE', 
                'TOTAL_EXPOSURE', 'TOTAL_LOAN_AMOUNT', 'TOTAL_FACILITY_AMOUNT'
            ]
            st.dataframe(
                filtered_df[display_cols].round(2), 
                use_container_width=True,
                column_config={
                    'TOTAL_EXPOSURE': st.column_config.NumberColumn(
                        'Total Exposure',
                        format='$%.2f'
                    ),
                    'TOTAL_LOAN_AMOUNT': st.column_config.NumberColumn(
                        'Loan Amount',
                        format='$%.2f'
                    ),
                    'TOTAL_FACILITY_AMOUNT': st.column_config.NumberColumn(
                        'Facility Amount',
                        format='$%.2f'
                    )
                }
            )

def main():
    """Enhanced main Streamlit application with advanced Analysis tab"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="NL2DAX International Portfolio Analysis",
        page_icon="🌍",
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
    
    # Header
    st.title("🌍 NL2DAX International Portfolio Analysis")
    st.markdown("Advanced analytics for multi-country, multi-currency financial portfolios")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Query Interface", "📈 Advanced Analysis", "📊 Quick Insights"])
    
    with tab1:
        # Original query interface with enhanced examples
        st.header("🔍 Natural Language Query Interface")
        
        # Sidebar with international examples
        with st.sidebar:
            st.header("🌍 International Query Examples")
            
            international_examples = [
                "Show me all customers by country",
                "What is our exposure by currency?",
                "List customers with highest risk ratings",
                "Display loan portfolio by geographic region",
                "Show currency concentration analysis",
                "Compare North American vs South American exposure",
                "What are our German and Singapore operations?",
                "Show me Brazilian and Argentine customer analysis"
            ]
            
            for example in international_examples:
                if st.button(f"🌐 {example}", key=f"intl_example_{example}", use_container_width=True):
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
            placeholder="e.g., Show me the geographic distribution of our international portfolio by country and currency"
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
        
        # Execute pipeline (using existing logic from streamlit_ui.py)
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
                
                # Success message and results
                if results['sql_results'] is not None or results['dax_results'] is not None:
                    st.success("✅ Query executed successfully!")
                    
                    # Performance metrics
                    create_comparison_metrics(
                        results['sql_results'], 
                        results['dax_results'],
                        results['sql_time'],
                        results['dax_time']
                    )
                    
                    # Display results in tabs
                    result_tab1, result_tab2 = st.tabs(["📊 Results", "🔍 Query Details"])
                    
                    with result_tab1:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("🗄️ SQL Results")
                            if results['sql_results'] is not None and len(results['sql_results']) > 0:
                                df_sql = pd.DataFrame(results['sql_results'])
                                st.dataframe(df_sql, use_container_width=True)
                            else:
                                st.info("No SQL results to display")
                        
                        with col2:
                            st.subheader("⚡ DAX Results")
                            if results['dax_results'] is not None and len(results['dax_results']) > 0:
                                df_dax = pd.DataFrame(results['dax_results'])
                                st.dataframe(df_dax, use_container_width=True)
                            else:
                                st.info("No DAX results to display")
                    
                    with result_tab2:
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
    
    with tab2:
        # Enhanced Analysis tab with advanced visualizations
        enhanced_analysis_tab()
    
    with tab3:
        # Quick insights tab
        st.header("📊 Quick Portfolio Insights")
        st.markdown("Pre-built analysis of international portfolio data")
        
        # Load and display quick insights
        with st.spinner("Loading quick insights..."):
            customer_df = get_international_customer_data()
            currency_df = get_currency_exposure_data()
        
        if not customer_df.empty:
            # Quick metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total International Customers", len(customer_df))
                st.metric("Countries Covered", customer_df['COUNTRY_CODE'].nunique())
            
            with col2:
                total_exposure = customer_df['TOTAL_EXPOSURE'].sum()
                st.metric("Total Portfolio Exposure", f"${total_exposure:,.0f}")
                avg_risk = customer_df['PROBABILITY_OF_DEFAULT'].mean() * 100
                st.metric("Average PD", f"{avg_risk:.2f}%")
            
            with col3:
                top_country = customer_df.groupby('COUNTRY_DISPLAY')['TOTAL_EXPOSURE'].sum().idxmax()
                st.metric("Top Country by Exposure", top_country)
                high_risk_count = len(customer_df[customer_df['RISK_RATING_CODE'].isin(['C+', 'C', 'C-'])])
                st.metric("High Risk Customers", high_risk_count)
            
            # Quick charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Top countries chart
                top_countries = customer_df.groupby('COUNTRY_DISPLAY')['TOTAL_EXPOSURE'].sum().reset_index().sort_values('TOTAL_EXPOSURE', ascending=False).head(5)
                
                fig_countries = px.bar(
                    top_countries,
                    x='COUNTRY_DISPLAY',
                    y='TOTAL_EXPOSURE',
                    title='Top 5 Countries by Exposure'
                )
                fig_countries.update_layout(title_x=0.5, height=400)
                st.plotly_chart(fig_countries, use_container_width=True)
            
            with col2:
                # Risk distribution
                risk_dist = customer_df['RISK_RATING_CODE'].value_counts().reset_index()
                risk_dist.columns = ['Risk_Rating', 'Count']
                
                fig_risk = px.pie(
                    risk_dist,
                    values='Count',
                    names='Risk_Rating',
                    title='Risk Rating Distribution'
                )
                fig_risk.update_layout(title_x=0.5, height=400)
                st.plotly_chart(fig_risk, use_container_width=True)

if __name__ == "__main__":
    main()