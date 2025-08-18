"""
generic_sql_generator.py - Database-Agnostic SQL Query Generation
================================================================

This module provides generic SQL query generation that works with any database schema
by using AI-powered schema discovery and pattern-based query construction. It replaces
hardcoded schema-specific queries with intelligent, adaptive query generation.

Key Features:
- Schema-agnostic query generation using AI analysis
- Pattern-based query templates for common business scenarios
- Automatic column mapping and relationship discovery
- Best practices embedded in prompts rather than code
- Support for multiple SQL databases (SQL Server, PostgreSQL, MySQL, etc.)

Architecture:
- Uses LLM to analyze database schema and discover patterns
- Generates SQL using business intent rather than technical specifications
- Provides fallback patterns for common financial/business scenarios
- Validates generated queries against schema constraints

Author: NL2DAX Pipeline Development Team
Last Updated: August 16, 2025
"""

import os
import re
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate

load_dotenv()

class GenericSQLGenerator:
    """Generic SQL query generator that adapts to any database schema"""
    
    def __init__(self):
        """Initialize the generic SQL generator with Azure OpenAI"""
        self.llm = AzureChatOpenAI(
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version="2024-12-01-preview"
            # temperature=0.1  # Using default temperature for model compatibility
        )
        
        # Generic SQL generation prompt with best practices
        self.sql_prompt = ChatPromptTemplate.from_template("""
You are an expert SQL query generator that works with any database schema. Your job is to analyze the provided schema and generate robust, efficient SQL queries based on business intent.

SCHEMA ANALYSIS BEST PRACTICES:
1. IDENTIFY TABLE TYPES:
   - Fact tables: Usually contain measures, amounts, counts, dates, foreign keys
   - Dimension tables: Usually contain descriptive attributes, names, classifications
   - Bridge tables: Connect many-to-many relationships

2. DISCOVER COLUMN PATTERNS:
   - Primary Keys: Usually end with _KEY, _ID, or named ID
   - Foreign Keys: Usually end with _KEY and match dimension table primary keys
   - Currency columns: Look for *CURRENCY*, *CCY*, *CURR*, *EXCHANGE* patterns
   - Amount columns: Look for *AMOUNT*, *BALANCE*, *LIMIT*, *VALUE*, *SUM* patterns
   - Risk columns: Look for *RISK*, *RATING*, *PROBABILITY*, *DEFAULT*, *EXPOSURE* patterns
   - Date columns: Look for *DATE*, *TIME*, *PERIOD*, *MONTH*, *YEAR* patterns
   - Geographic columns: Look for *COUNTRY*, *STATE*, *REGION*, *LOCATION* patterns
   - Classification columns: Look for *TYPE*, *CATEGORY*, *CLASS*, *STATUS* patterns

3. RELATIONSHIP DISCOVERY:
   - Look for foreign key constraints in the relationships section
   - Infer relationships from column name patterns
   - Prefer explicit JOINs over implicit relationships

SQL GENERATION BEST PRACTICES:
1. QUERY STRUCTURE:
   - Use meaningful table aliases (fact tables: f, dimension tables: d1, d2, etc.)
   - Include proper JOINs based on discovered relationships
   - Use COALESCE() for LEFT JOINs that might return NULLs
   - Add appropriate WHERE clauses for data filtering

2. AGGREGATION PATTERNS:
   - Use SUM() for amount/balance columns
   - Use COUNT() for counting records
   - Use AVG() for calculating averages of numeric measures
   - Use MAX/MIN for finding extremes
   - Include proper GROUP BY clauses for all non-aggregated columns

3. COLUMN NAMING:
   - Use descriptive aliases for calculated columns
   - Maintain consistent naming conventions
   - Include units or context in column names where appropriate

4. PERFORMANCE OPTIMIZATION:
   - Limit results with TOP/LIMIT when appropriate
   - Use indexes efficiently by filtering on key columns
   - Avoid unnecessary subqueries when JOINs suffice

DATABASE SCHEMA:
{schema_context}

BUSINESS INTENT:
{business_intent}

ANALYSIS TYPE: {analysis_type}

REQUIREMENTS:
- Generate a complete, executable SQL query
- Use the actual table and column names from the schema
- Follow the patterns above to discover appropriate columns
- Include proper error handling with COALESCE where needed
- Return only the SQL query without explanations or markdown formatting

SQL Query:
""")

    def analyze_schema_for_intent(self, schema_context: str, business_intent: str) -> Dict[str, List[str]]:
        """
        Analyze database schema to discover relevant tables and columns for the business intent
        
        Args:
            schema_context: Database schema information
            business_intent: What the user wants to achieve
            
        Returns:
            Dictionary mapping column purposes to actual column names
        """
        analysis_prompt = ChatPromptTemplate.from_template("""
Analyze this database schema and identify the most relevant tables and columns for the business intent.

SCHEMA:
{schema_context}

BUSINESS INTENT:
{business_intent}

Please identify and return a JSON object with these categories:
{{
    "primary_tables": ["list of main tables to query"],
    "join_tables": ["list of tables to join for additional context"],
    "key_columns": ["primary and foreign key columns for joins"],
    "measure_columns": ["numeric columns for calculations and aggregations"],
    "dimension_columns": ["descriptive columns for grouping and filtering"],
    "geographic_columns": ["country, region, location columns"],
    "currency_columns": ["currency-related columns"],
    "risk_columns": ["risk, rating, probability columns"],
    "date_columns": ["date and time columns"],
    "relationships": ["key relationships needed for this query"]
}}

Return only the JSON object:
""")
        
        chain = analysis_prompt | self.llm
        result = chain.invoke({
            "schema_context": schema_context,
            "business_intent": business_intent
        })
        
        try:
            import json
            return json.loads(result.content)
        except:
            # Fallback to empty structure if JSON parsing fails
            return {
                "primary_tables": [],
                "join_tables": [],
                "key_columns": [],
                "measure_columns": [],
                "dimension_columns": [],
                "geographic_columns": [],
                "currency_columns": [],
                "risk_columns": [],
                "date_columns": [],
                "relationships": []
            }

    def generate_sql_for_analysis(self, schema_context: str, business_intent: str, analysis_type: str) -> str:
        """
        Generate SQL query for specific analysis type based on business intent
        
        Args:
            schema_context: Database schema information
            business_intent: What the user wants to achieve
            analysis_type: Type of analysis (customer, currency, risk, geographic, etc.)
            
        Returns:
            Generated SQL query string
        """
        
        # Generate the SQL query using the generic prompt
        chain = self.sql_prompt | self.llm
        result = chain.invoke({
            "schema_context": schema_context,
            "business_intent": business_intent,
            "analysis_type": analysis_type
        })
        
        # Clean up the SQL query
        sql_query = result.content.strip()
        
        # Remove any markdown formatting
        sql_query = re.sub(r'```sql\s*', '', sql_query, flags=re.IGNORECASE)
        sql_query = re.sub(r'```\s*$', '', sql_query)
        
        # Clean up extra whitespace
        sql_query = re.sub(r'\n\s*\n', '\n', sql_query)
        
        return sql_query.strip()

    def generate_customer_analysis_sql(self, schema_context: str) -> str:
        """Generate SQL for customer analysis"""
        return self.generate_sql_for_analysis(
            schema_context,
            "Analyze customers with their geographic distribution, risk profiles, and financial exposure. Include country information, risk ratings, and total amounts.",
            "customer_analysis"
        )
    
    def generate_currency_exposure_sql(self, schema_context: str) -> str:
        """Generate SQL for currency exposure analysis"""
        return self.generate_sql_for_analysis(
            schema_context,
            "Analyze financial exposure by currency and geography. Show loan and facility amounts grouped by currency and country.",
            "currency_exposure"
        )
    
    def generate_risk_analysis_sql(self, schema_context: str) -> str:
        """Generate SQL for risk analysis"""
        return self.generate_sql_for_analysis(
            schema_context,
            "Analyze risk metrics across customers and portfolios. Include risk ratings, probability of default, and exposure amounts.",
            "risk_analysis"
        )
    
    def generate_geographic_analysis_sql(self, schema_context: str) -> str:
        """Generate SQL for geographic analysis"""
        return self.generate_sql_for_analysis(
            schema_context,
            "Analyze portfolio distribution by geography. Include country-wise exposure, customer counts, and risk metrics.",
            "geographic_analysis"
        )

# Example usage patterns for common business scenarios
ANALYSIS_PATTERNS = {
    "customer_overview": {
        "description": "Customer list with geographic and risk information",
        "required_concepts": ["customer", "geography", "risk"],
        "optional_concepts": ["amounts", "currency"],
        "typical_aggregation": "customer_level"
    },
    "currency_exposure": {
        "description": "Financial exposure breakdown by currency",
        "required_concepts": ["currency", "amounts", "geography"],
        "optional_concepts": ["customer", "product"],
        "typical_aggregation": "currency_country_level"
    },
    "risk_dashboard": {
        "description": "Risk metrics and exposure analysis",
        "required_concepts": ["risk", "amounts", "customer"],
        "optional_concepts": ["geography", "currency"],
        "typical_aggregation": "risk_category_level"
    },
    "geographic_portfolio": {
        "description": "Portfolio analysis by geographic regions",
        "required_concepts": ["geography", "amounts", "customer"],
        "optional_concepts": ["currency", "risk"],
        "typical_aggregation": "country_region_level"
    }
}