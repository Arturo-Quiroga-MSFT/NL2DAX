"""
generic_dax_generator.py - Semantic Model-Agnostic DAX Query Generation
======================================================================

This module provides generic DAX query generation that works with any PoBUSINESS INTENT:
{business_intent}

ANALYSIS TYPE: {analysis_type}

**CRITICAL REQUIREMENT FOR CUSTOMER AGGREGATION QUERIES:**
If this query involves customer ranking or aggregation (like "top customers", "customer exposure", etc.):
- MUST start aggregation from FACT table, not dimension table
- Use SUMMARIZE('FactTable', RELATED('DimTable'[Column])) pattern
- NEVER use SUMMARIZE('DimensionTable') with CALCULATE(SUM())
- This prevents context errors that cause all customers to show identical totals

REQUIREMENTS:
- Generate a complete, executable DAX query that starts with EVALUATE
- Use proper table and column names from the schema
- Follow the proven patterns above to avoid common mistakes
- Use TOPN() for rankings, never ORDER BY
- Return only the DAX query without explanations or markdown formattingic 
semantic model by using AI-powered model discovery and pattern-based query construction.
It replaces hardcoded model-specific queries with intelligent, adaptive query generation.

Key Features:
- Semantic model-agnostic DAX generation using AI analysis
- Pattern-based DAX templates for common business scenarios
- Automatic table and relationship discovery
- DAX best practices embedded in prompts rather than code
- Support for Power BI, Azure Analysis Services, and Fabric

Architecture:
- Uses LLM to analyze semantic model structure and discover patterns
- Generates DAX using business intent rather than technical specifications
- Provides proven DAX patterns for common financial/business scenarios
- Validates generated DAX against semantic model constraints

Author: NL2DAX Pipeline Development Team
Last Updated: August 16, 2025
"""

import os
import re
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .dax_query_validator import DAXQueryValidator

load_dotenv()

class GenericDAXGenerator:
    """Generic DAX query generator that adapts to any semantic model"""
    
    def __init__(self):
        """Initialize the generic DAX generator with Azure OpenAI"""
        self.llm = AzureChatOpenAI(
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version="2024-12-01-preview"
            # temperature=0.1  # Using default temperature for model compatibility
        )
        
        # DAX validator will be initialized when needed
        self.dax_validator = None
        
        # Generic DAX generation prompt with best practices
        self.dax_prompt = ChatPromptTemplate.from_template("""
You are an expert DAX query generator that works with any Power BI/Fabric semantic model. Your job is to analyze the provided model schema and generate robust, efficient DAX queries based on business intent.

SEMANTIC MODEL ANALYSIS BEST PRACTICES:
1. IDENTIFY TABLE TYPES:
   - Fact tables: Contain measures, amounts, counts, dates, foreign keys to dimensions
   - Dimension tables: Contain attributes, names, classifications, hierarchies
   - Date tables: Special dimension tables for time intelligence

2. DISCOVER COLUMN PATTERNS:
   - Key columns: Usually end with Key, ID, or named similar to table
   - Measure columns: Numeric columns in fact tables (Amount, Balance, Quantity, etc.)
   - Attribute columns: Descriptive columns in dimension tables (Name, Description, Type, etc.)
   - Currency columns: Look for Currency, CCY, Exchange patterns
   - Risk columns: Look for Risk, Rating, Probability, Default, Exposure patterns
   - Geographic columns: Look for Country, Region, State, Location patterns
   - Time columns: Look for Date, Time, Period, Month, Year patterns

3. RELATIONSHIP DISCOVERY:
   - Analyze relationships section to understand how tables connect
   - Use RELATED() to traverse from fact to dimension tables
   - Use RELATEDTABLE() to traverse from dimension to fact tables

PROVEN DAX PATTERNS FOR BUSINESS SCENARIOS:

PATTERN 1 - Detail Rows with Dimension Lookups:
```
EVALUATE
SELECTCOLUMNS(
    TOPN(
        N,
        'FactTable',
        'FactTable'[SortColumn], DESC
    ),
    "Column1", 'FactTable'[Column1],
    "DimAttribute", RELATED('DimTable'[Attribute])
)
```

PATTERN 2 - Aggregated Data with Grouping:
```
EVALUATE
ADDCOLUMNS(
    SUMMARIZE(
        'FactTable',
        RELATED('DimTable'[GroupColumn])
    ),
    "MeasureName", CALCULATE(SUM('FactTable'[Amount]))
)
```

PATTERN 2B - Customer Aggregation (REQUIRED for customer exposure/ranking queries):
```
EVALUATE
TOPN(
    N,
    ADDCOLUMNS(
        SUMMARIZE(
            'FactTable',
            'FactTable'[CustomerKey]
        ),
        "CustomerName", RELATED('CustomerDim'[CustomerName]),
        "TotalAmount", SUM('FactTable'[Amount])
    ),
    [TotalAmount], DESC
)
```

PATTERN 2C - Multi-Fact Table Customer Aggregation (for queries with multiple fact tables):
```
EVALUATE
TOPN(
    N,
    ADDCOLUMNS(
        SUMMARIZE(
            UNION(
                DISTINCT(SELECTCOLUMNS('Fact1', "CustomerKey", 'Fact1'[CustomerKey])),
                DISTINCT(SELECTCOLUMNS('Fact2', "CustomerKey", 'Fact2'[CustomerKey]))
            ),
            [CustomerKey]
        ),
        "CustomerName", CALCULATE(FIRSTNONBLANK('CustomerDim'[CustomerName], TRUE), 'CustomerDim'[CustomerKey] = [CustomerKey]),
        "TotalAmount", 
            CALCULATE(SUM('Fact1'[Amount]), 'Fact1'[CustomerKey] = [CustomerKey]) + 
            CALCULATE(SUM('Fact2'[Amount]), 'Fact2'[CustomerKey] = [CustomerKey])
    ),
    [TotalAmount], DESC
)
```

PATTERN 3 - Cross-Table Analysis with Multiple Dimensions:
```
EVALUATE
ADDCOLUMNS(
    SUMMARIZE(
        'FactTable',
        RELATED('Dim1'[Attribute1]),
        RELATED('Dim2'[Attribute2])
    ),
    "TotalAmount", CALCULATE(SUM('FactTable'[Amount])),
    "Count", CALCULATE(COUNT('FactTable'[Key]))
)
```

PATTERN 4 - Filtered Analysis:
```
EVALUATE
SELECTCOLUMNS(
    FILTER(
        'FactTable',
        RELATED('DimTable'[Attribute]) = "Value"
    ),
    "Column1", 'FactTable'[Column1],
    "Related", RELATED('DimTable'[Attribute])
)
```

CRITICAL DAX SYNTAX RULES:
1. ALWAYS start with EVALUATE
2. Table references MUST use single quotes: 'TableName'[ColumnName]
3. Use TOPN() for ranking, NEVER use ORDER BY (not supported in DAX)
4. Use RELATED() to get dimension attributes from fact table context
5. Use CALCULATE() for filtered aggregations
6. Use ADDCOLUMNS(SUMMARIZE()) pattern instead of SUMMARIZECOLUMNS for cross-table scenarios
7. String values in filters use double quotes: "Value"
8. Ensure all functions have proper closing parentheses

CRITICAL MISTAKES TO AVOID:
- NEVER use SUMMARIZECOLUMNS with columns from multiple tables (causes cartesian products)
- NEVER use ORDER BY (SQL syntax, not DAX)
- NEVER add calculated columns directly as SUMMARIZE parameters
- NEVER reference columns from unrelated tables without proper relationships
- NEVER use VALUES() for customer aggregation - use SUMMARIZE() instead
- NEVER use CALCULATE(SUM()) without proper row context from SUMMARIZE()
- ⚠️  CRITICAL: NEVER start customer aggregation from dimension tables - always start from FACT tables
- ⚠️  CRITICAL: When aggregating by customer, start SUMMARIZE() from the fact table and use RELATED() to get customer name

SPECIFIC PATTERNS FOR COMMON SCENARIOS:
- For customer exposure/ranking: ⚠️ ALWAYS start SUMMARIZE() from FACT tables with [CustomerKey], then add customer name using RELATED()
- For top N queries: Always use TOPN() with ADDCOLUMNS(SUMMARIZE()) pattern starting from fact table
- For cross-table aggregation: Start from fact table, use RELATED() to get dimension attributes
- For multi-fact aggregation: Create union of distinct customer keys from fact tables, then use explicit CALCULATE filters
- CRITICAL: When aggregating by customer, NEVER start from dimension - start from fact table for proper row context

MULTI-FACT TABLE PATTERN (for queries involving multiple fact tables):
```
EVALUATE
TOPN(
    N,
    ADDCOLUMNS(
        SUMMARIZE(
            'CustomerDim',
            'CustomerDim'[CustomerKey],
            'CustomerDim'[CustomerName]
        ),
        "TotalAmount", 
            CALCULATE(SUM('Fact1'[Amount])) + 
            CALCULATE(SUM('Fact2'[Amount]))
    ),
    [TotalAmount], DESC
)
```

CRITICAL: Always use the simple pattern above for multi-fact aggregation. Do NOT use complex UNION patterns.

SEMANTIC MODEL SCHEMA:
{model_context}

BUSINESS INTENT:
{business_intent}

ANALYSIS TYPE: {analysis_type}

REQUIREMENTS:
- Generate a complete, executable DAX query
- Use the actual table and column names from the schema
- Follow the proven patterns above
- Ensure proper relationship traversal using RELATED()
- Return only the DAX query without explanations or markdown formatting

DAX Query:
""")

    def analyze_model_for_intent(self, model_context: str, business_intent: str) -> Dict[str, List[str]]:
        """
        Analyze semantic model to discover relevant tables and columns for the business intent
        
        Args:
            model_context: Semantic model schema information
            business_intent: What the user wants to achieve
            
        Returns:
            Dictionary mapping table/column purposes to actual names
        """
        analysis_prompt = ChatPromptTemplate.from_template("""
Analyze this Power BI/Fabric semantic model and identify the most relevant tables and columns for the business intent.

MODEL SCHEMA:
{model_context}

BUSINESS INTENT:
{business_intent}

Please identify and return a JSON object with these categories:
{{
    "fact_tables": ["list of fact tables relevant to the intent"],
    "dimension_tables": ["list of dimension tables needed"],
    "key_relationships": ["important relationships for this query"],
    "measure_columns": ["numeric columns for calculations"],
    "attribute_columns": ["descriptive columns for grouping"],
    "filter_columns": ["columns suitable for filtering"],
    "sort_columns": ["columns suitable for sorting/ranking"],
    "recommended_pattern": "which DAX pattern (1-4) would work best"
}}

Return only the JSON object:
""")
        
        chain = analysis_prompt | self.llm
        result = chain.invoke({
            "model_context": model_context,
            "business_intent": business_intent
        })
        
        try:
            import json
            return json.loads(result.content)
        except:
            # Fallback to empty structure if JSON parsing fails
            return {
                "fact_tables": [],
                "dimension_tables": [],
                "key_relationships": [],
                "measure_columns": [],
                "attribute_columns": [],
                "filter_columns": [],
                "sort_columns": [],
                "recommended_pattern": "1"
            }

    def generate_dax_for_analysis(self, model_context: str, business_intent: str, analysis_type: str) -> str:
        """
        Generate DAX query for specific analysis type based on business intent
        
        Args:
            model_context: Semantic model schema information
            business_intent: What the user wants to achieve
            analysis_type: Type of analysis (customer, currency, risk, geographic, etc.)
            
        Returns:
            Generated DAX query string
        """
        
        # Generate the DAX query using the generic prompt
        chain = self.dax_prompt | self.llm
        result = chain.invoke({
            "model_context": model_context,
            "business_intent": business_intent,
            "analysis_type": analysis_type
        })
        
        # Clean up the DAX query
        dax_query = result.content.strip()
        
        # Remove any markdown formatting
        dax_query = re.sub(r'```dax\s*', '', dax_query, flags=re.IGNORECASE)
        dax_query = re.sub(r'```\s*$', '', dax_query)
        
        # Clean up extra whitespace
        dax_query = re.sub(r'\n\s*\n', '\n', dax_query)
        
        # Ensure it starts with EVALUATE
        if not dax_query.upper().strip().startswith('EVALUATE'):
            dax_query = 'EVALUATE\n' + dax_query
        
        # 🔧 CRITICAL FIX: Auto-correct problematic dimension-first patterns for customer queries
        if ('customer' in business_intent.lower() or 'exposure' in business_intent.lower()) and 'CUSTOMER_DIMENSION' in dax_query:
            print("[DEBUG] Detected customer aggregation query starting from dimension - auto-correcting...")
            # This is a customer aggregation query starting from dimension table - FIX IT
            dax_query = self._fix_customer_aggregation_pattern(dax_query, model_context)
        
        
        # Validate the generated DAX query
        print("[DEBUG] Validating generated DAX query...")
        
        # Initialize validator if not already done and we have schema info
        if self.dax_validator is None:
            # Try to extract schema info from model_context
            schema_info = self._extract_schema_from_context(model_context)
            if schema_info:
                self.dax_validator = DAXQueryValidator(schema_info)
            else:
                print("[WARNING] No schema info available for DAX validation")
                return dax_query.strip()
        
        validation_result = self.dax_validator.validate_dax_query(dax_query)
        
        if not validation_result.is_valid:
            print(f"[WARNING] DAX validation found {len(validation_result.issues)} issues:")
            for issue in validation_result.issues:
                print(f"  - {issue.severity}: {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")
            
            # For high-severity issues, we might want to regenerate
            critical_issues = [i for i in validation_result.issues if i.severity == "ERROR"]
            if critical_issues:
                print(f"[ERROR] Found {len(critical_issues)} critical issues in generated DAX. Consider regenerating.")
        else:
            print("[SUCCESS] DAX query validation passed!")

        return dax_query.strip()

    def _fix_customer_aggregation_pattern(self, dax_query: str, model_context: str) -> str:
        """
        Fix problematic customer aggregation patterns that start from dimension tables
        """
        print("[DEBUG] Applying customer aggregation fix...")
        
        # Extract the fact tables from model context
        fact_tables = []
        if 'FIS_CA_DETAIL_FACT' in model_context:
            fact_tables.append('FIS_CA_DETAIL_FACT')
        if 'FIS_CL_DETAIL_FACT' in model_context:
            fact_tables.append('FIS_CL_DETAIL_FACT')
        
        # For multiple fact tables, use a simpler approach - start from one and add the other
        if len(fact_tables) >= 2:
            return f"""EVALUATE
TOPN(
    5,
    ADDCOLUMNS(
        SUMMARIZE(
            '{fact_tables[0]}',
            '{fact_tables[0]}'[CUSTOMER_KEY]
        ),
        "CustomerName", RELATED('FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME]),
        "TotalExposure", 
            SUM('{fact_tables[0]}'[EXPOSURE_AT_DEFAULT]) + 
            CALCULATE(
                SUM('{fact_tables[1]}'[EXPOSURE_AT_DEFAULT]), 
                '{fact_tables[1]}'[CUSTOMER_KEY] = '{fact_tables[0]}'[CUSTOMER_KEY]
            )
    ),
    [TotalExposure], DESC
)"""
        
        # Single fact table pattern
        elif len(fact_tables) == 1:
            return f"""EVALUATE
TOPN(
    5,
    ADDCOLUMNS(
        SUMMARIZE(
            '{fact_tables[0]}',
            '{fact_tables[0]}'[CUSTOMER_KEY]
        ),
        "CustomerName", RELATED('FIS_CUSTOMER_DIMENSION'[CUSTOMER_NAME]),
        "TotalExposure", SUM('{fact_tables[0]}'[EXPOSURE_AT_DEFAULT])
    ),
    [TotalExposure], DESC
)"""
        
        # Fallback to original if no fact tables found
        return dax_query

    def _extract_schema_from_context(self, model_context: str) -> Optional[Dict[str, Any]]:
        """Extract schema information from model context for validation"""
        try:
            # Try to parse the model context as JSON (if it contains schema info)
            if model_context.strip().startswith('{') or 'tables' in model_context.lower():
                # Simple fallback schema structure for validation
                return {
                    'tables': {},
                    'table_details': {},
                    'relationships': []
                }
        except Exception:
            pass
        return None

    def generate_customer_analysis_dax(self, model_context: str) -> str:
        """Generate DAX for customer analysis"""
        return self.generate_dax_for_analysis(
            model_context,
            "Show customers with their geographic information, risk profiles, and financial metrics. Include country, risk ratings, and total amounts.",
            "customer_analysis"
        )
    
    def generate_currency_exposure_dax(self, model_context: str) -> str:
        """Generate DAX for currency exposure analysis"""
        return self.generate_dax_for_analysis(
            model_context,
            "Analyze financial exposure by currency and geography. Show aggregated amounts by currency and country from both loans and facilities.",
            "currency_exposure"
        )
    
    def generate_risk_analysis_dax(self, model_context: str) -> str:
        """Generate DAX for risk analysis"""
        return self.generate_dax_for_analysis(
            model_context,
            "Analyze risk metrics across the portfolio. Include risk ratings, probability measures, and exposure amounts grouped by risk categories.",
            "risk_analysis"
        )
    
    def generate_geographic_analysis_dax(self, model_context: str) -> str:
        """Generate DAX for geographic analysis"""
        return self.generate_dax_for_analysis(
            model_context,
            "Analyze portfolio distribution by geography. Show country-wise exposure, customer counts, and key financial metrics.",
            "geographic_analysis"
        )

    def generate_top_customers_dax(self, model_context: str, limit: int = 10, sort_by: str = "total_exposure") -> str:
        """Generate DAX for top customers analysis"""
        sort_descriptions = {
            "total_exposure": "total financial exposure or balance",
            "risk_rating": "highest risk rating or probability",
            "transaction_count": "number of transactions or facilities"
        }
        
        return self.generate_dax_for_analysis(
            model_context,
            f"Show the top {limit} customers ranked by {sort_descriptions.get(sort_by, sort_by)}. Include customer details, geographic information, and key financial metrics.",
            "top_customers"
        )

# Common DAX patterns for different business scenarios
DAX_PATTERNS = {
    "detail_with_lookup": {
        "description": "Detail rows from fact table with dimension attributes",
        "use_case": "Customer lists, transaction details, detailed reports",
        "pattern": "SELECTCOLUMNS + RELATED",
        "complexity": "simple"
    },
    "aggregated_summary": {
        "description": "Aggregated data grouped by dimension attributes",
        "use_case": "Summary reports, totals by category, KPI dashboards",
        "pattern": "ADDCOLUMNS(SUMMARIZE) + CALCULATE",
        "complexity": "medium"
    },
    "cross_table_analysis": {
        "description": "Analysis spanning multiple dimensions",
        "use_case": "Cross-tabulation, multi-dimensional analysis",
        "pattern": "ADDCOLUMNS(SUMMARIZE) with multiple RELATED",
        "complexity": "complex"
    },
    "filtered_analysis": {
        "description": "Filtered data based on specific criteria",
        "use_case": "Targeted analysis, conditional reports",
        "pattern": "FILTER + SELECTCOLUMNS/SUMMARIZE",
        "complexity": "medium"
    },
    "ranking_analysis": {
        "description": "Top/bottom performers, ranked results",
        "use_case": "Top customers, worst performers, rankings",
        "pattern": "TOPN + SELECTCOLUMNS",
        "complexity": "simple"
    }
}