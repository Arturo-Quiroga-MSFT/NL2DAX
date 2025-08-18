"""
universal_query_interface.py - Unified Database-Agnostic Query Interface
=========================================================================

This module provides a unified interface for generating both SQL and DAX queries
that works with any database schema or semantic model. It combines schema analysis,
pattern recognition, and AI-powered query generation into a single, easy-to-use interface.

Key Features:
- Single interface for both SQL and DAX generation
- Automatic schema discovery and analysis
- Business intent-driven query generation
- Database-agnostic design patterns
- Built-in query validation and optimization

Architecture:
- Uses schema-agnostic analyzer for structure discovery
- Employs generic SQL and DAX generators for query creation
- Provides unified business intent interface
- Supports multiple database systems and semantic models

Author: NL2DAX Pipeline Development Team
Supervised and maintained by Arturo Quiroga
Last Updated: August 16, 2025
"""

import os
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from .schema_agnostic_analyzer import SchemaAgnosticAnalyzer, TableType, ColumnType
from .generic_sql_generator import GenericSQLGenerator
from .generic_dax_generator import GenericDAXGenerator
from .enhanced_dax_generator import EnhancedDAXGenerator, EnhancedDAXResult

class QueryType(Enum):
    """Type of query to generate"""
    SQL = "sql"
    DAX = "dax"
    BOTH = "both"

class AnalysisType(Enum):
    """Type of business analysis"""
    CUSTOMER_OVERVIEW = "customer_overview"
    CURRENCY_EXPOSURE = "currency_exposure" 
    RISK_ANALYSIS = "risk_analysis"
    GEOGRAPHIC_DISTRIBUTION = "geographic_distribution"
    PORTFOLIO_SUMMARY = "portfolio_summary"
    TOP_CUSTOMERS = "top_customers"
    CUSTOM = "custom"

@dataclass
class QueryResult:
    """Result of query generation"""
    query_type: QueryType
    analysis_type: AnalysisType
    sql_query: Optional[str] = None
    dax_query: Optional[str] = None
    business_intent: Optional[str] = None
    execution_notes: Optional[str] = None
    estimated_complexity: Optional[str] = None
    
    # Enhanced DAX results
    enhanced_dax_result: Optional[EnhancedDAXResult] = None
    dax_execution_success: bool = False
    dax_execution_data: List[Dict[str, Any]] = None
    dax_pattern_used: Optional[str] = None
    dax_confidence_score: float = 0.0

class UniversalQueryInterface:
    """Unified interface for database-agnostic query generation"""
    
    def __init__(self):
        """Initialize the universal query interface"""
        self.schema_analyzer = SchemaAgnosticAnalyzer()
        self.sql_generator = GenericSQLGenerator()
        self.dax_generator = GenericDAXGenerator()
        
        # Initialize Enhanced DAX Generator
        try:
            self.enhanced_dax_generator = EnhancedDAXGenerator()
            self.use_enhanced_dax = True
            print("[INFO] Universal Query Interface initialized with Enhanced DAX Generator")
        except Exception as e:
            print(f"[WARNING] Enhanced DAX Generator not available: {e}")
            self.enhanced_dax_generator = None
            self.use_enhanced_dax = False
        
        # Cache for schema analysis
        self._schema_cache = None
        self._schema_analysis_cache = None
    
    def analyze_current_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Analyze the current database schema and cache results
        
        Args:
            force_refresh: Force re-analysis even if cached
            
        Returns:
            Dictionary with schema analysis results
        """
        if self._schema_analysis_cache is None or force_refresh:
            # Discover actual database schema using real database connection
            if self._schema_cache is None or force_refresh:
                print("[DEBUG] Discovering database schema...")
                self._schema_cache = self.schema_analyzer.discover_database_schema()
            
            # Perform intelligent analysis on discovered schema
            print("[DEBUG] Analyzing discovered schema structure...")
            self._schema_analysis_cache = self.schema_analyzer.analyze_schema_structure(self._schema_cache)
        
        return self._schema_analysis_cache

    def get_business_suggestions(self) -> List[Dict[str, str]]:
        """Get business query suggestions based on current schema"""
        schema_analysis = self.analyze_current_schema()
        return self.schema_analyzer.generate_business_query_suggestions(schema_analysis)

    def generate_query_from_intent(
        self, 
        business_intent: str, 
        query_type: QueryType = QueryType.BOTH,
        analysis_type: AnalysisType = AnalysisType.CUSTOM
    ) -> QueryResult:
        """
        Generate queries based on business intent
        
        Args:
            business_intent: Natural language description of what user wants
            query_type: Whether to generate SQL, DAX, or both
            analysis_type: Type of business analysis being performed
            
        Returns:
            QueryResult with generated queries
        """
        # Get schema context
        schema_analysis = self.analyze_current_schema()
        schema_context = self._format_schema_for_prompts(schema_analysis)
        
        result = QueryResult(
            query_type=query_type,
            analysis_type=analysis_type,
            business_intent=business_intent
        )
        
        # Generate SQL if requested
        if query_type in [QueryType.SQL, QueryType.BOTH]:
            try:
                result.sql_query = self.sql_generator.generate_sql_for_analysis(
                    schema_context,
                    business_intent,
                    analysis_type.value
                )
            except Exception as e:
                result.execution_notes = f"SQL generation failed: {str(e)}"
        
        # Generate DAX if requested
        if query_type in [QueryType.DAX, QueryType.BOTH]:
            try:
                if self.use_enhanced_dax and self.enhanced_dax_generator:
                    # Use Enhanced DAX Generator with Clean DAX Engine capabilities
                    print("[INFO] Using Enhanced DAX Generator for improved results")
                    enhanced_result = self.enhanced_dax_generator.generate_dax(
                        business_intent=business_intent,
                        schema_info=schema_analysis,
                        analysis_type=analysis_type.value,
                        limit=10,
                        execute=True
                    )
                    
                    result.dax_query = enhanced_result.dax_query
                    result.enhanced_dax_result = enhanced_result
                    result.dax_execution_success = enhanced_result.execution_success
                    result.dax_execution_data = enhanced_result.data
                    result.dax_pattern_used = enhanced_result.pattern_used
                    result.dax_confidence_score = enhanced_result.confidence_score
                    
                    if not enhanced_result.success:
                        error_msg = f"Enhanced DAX generation failed: {enhanced_result.error_message}"
                        if result.execution_notes:
                            result.execution_notes += f"; {error_msg}"
                        else:
                            result.execution_notes = error_msg
                else:
                    # Fallback to original DAX generator
                    print("[INFO] Using original DAX generator (Enhanced DAX not available)")
                    model_context = self._format_schema_for_powerbi(schema_analysis)
                    result.dax_query = self.dax_generator.generate_dax_for_analysis(
                        model_context,
                        business_intent,
                        analysis_type.value
                    )
                    
            except Exception as e:
                dax_error = f"DAX generation failed: {str(e)}"
                if result.execution_notes:
                    result.execution_notes += f"; {dax_error}"
                else:
                    result.execution_notes = dax_error
        
        # Estimate complexity
        result.estimated_complexity = self._estimate_query_complexity(business_intent, schema_analysis)
        
        return result

    def generate_customer_overview(self, query_type: QueryType = QueryType.BOTH) -> QueryResult:
        """Generate queries for customer overview analysis"""
        return self.generate_query_from_intent(
            "Show me a comprehensive overview of customers including their geographic distribution, risk profiles, and financial exposure",
            query_type,
            AnalysisType.CUSTOMER_OVERVIEW
        )

    def generate_currency_exposure(self, query_type: QueryType = QueryType.BOTH) -> QueryResult:
        """Generate queries for currency exposure analysis"""
        return self.generate_query_from_intent(
            "Analyze our financial exposure by currency and geography, showing both loan and facility amounts",
            query_type,
            AnalysisType.CURRENCY_EXPOSURE
        )

    def generate_risk_analysis(self, query_type: QueryType = QueryType.BOTH) -> QueryResult:
        """Generate queries for risk analysis"""
        return self.generate_query_from_intent(
            "Provide a comprehensive risk analysis showing risk ratings, probability metrics, and exposure amounts",
            query_type,
            AnalysisType.RISK_ANALYSIS
        )

    def generate_geographic_analysis(self, query_type: QueryType = QueryType.BOTH) -> QueryResult:
        """Generate queries for geographic analysis"""
        return self.generate_query_from_intent(
            "Show portfolio distribution by geography with country-wise exposure and customer metrics",
            query_type,
            AnalysisType.GEOGRAPHIC_DISTRIBUTION
        )

    def generate_top_customers(self, limit: int = 10, sort_by: str = "exposure", query_type: QueryType = QueryType.BOTH) -> QueryResult:
        """Generate queries for top customers analysis"""
        return self.generate_query_from_intent(
            f"Show the top {limit} customers ranked by {sort_by} with their key details and metrics",
            query_type,
            AnalysisType.TOP_CUSTOMERS
        )

    def _format_schema_for_prompts(self, schema_analysis: Dict[str, Any]) -> str:
        """Format schema analysis for generic prompts"""
        context_parts = []
        
        # Check if we have star schema tables (FACT/DIMENSION pattern)
        tables_info = schema_analysis['tables']
        fact_tables = [name for name, info in tables_info.items() if 'FACT' in name.upper()]
        dimension_tables = [name for name, info in tables_info.items() if 'DIMENSION' in name.upper()]
        
        if fact_tables and dimension_tables:
            context_parts.append("STAR SCHEMA DATABASE - FACT AND DIMENSION TABLES:")
            context_parts.append(f"({len(fact_tables)} fact tables, {len(dimension_tables)} dimension tables)")
        else:
            context_parts.append("DATABASE TABLES:")
        
        # Add table information
        for table_name, table_info in tables_info.items():
            table_type = table_info.table_type.value.upper()
            concepts = ', '.join(table_info.business_concepts)
            context_parts.append(f"- {table_name} ({table_type}): {concepts}")
            context_parts.append(f"  Columns: {', '.join(table_info.columns)}")
            if table_info.primary_key:
                context_parts.append(f"  Primary Key: {table_info.primary_key}")
            if table_info.foreign_keys:
                context_parts.append(f"  Foreign Keys: {', '.join(table_info.foreign_keys)}")
        
        # Add relationships
        if schema_analysis.get('relationships'):
            context_parts.append("\nRELATIONSHIPS:")
            for rel in schema_analysis['relationships']:
                context_parts.append(f"- {rel['parent_table']}.{rel['parent_column']} -> {rel['referenced_table']}.{rel['referenced_column']}")
        
        # Add business areas
        if schema_analysis.get('business_areas'):
            context_parts.append(f"\nBUSINESS AREAS: {', '.join(schema_analysis['business_areas'])}")
        
        return '\n'.join(context_parts)

    def _format_schema_for_powerbi(self, schema_analysis: Dict[str, Any]) -> str:
        """Format schema analysis for Power BI/DAX context"""
        context_parts = []
        
        # Check if we have star schema tables (FACT/DIMENSION pattern)
        tables_info = schema_analysis['tables']
        fact_tables = []
        dim_tables = []
        
        for table_name, table_info in tables_info.items():
            if 'FACT' in table_name.upper():
                fact_tables.append((table_name, table_info))
            elif 'DIMENSION' in table_name.upper():
                dim_tables.append((table_name, table_info))
            elif table_info.table_type == TableType.FACT:
                fact_tables.append((table_name, table_info))
            else:
                dim_tables.append((table_name, table_info))
        
        if fact_tables and dim_tables:
            context_parts.append("POWER BI SEMANTIC MODEL - STAR SCHEMA:")
            context_parts.append(f"({len(fact_tables)} fact tables, {len(dim_tables)} dimension tables)")
        else:
            context_parts.append("SEMANTIC MODEL TABLES:")
        
        # Format fact tables
        if fact_tables:
            context_parts.append("\nFACT TABLES:")
            for table_name, table_info in fact_tables:
                concepts = ', '.join(table_info.business_concepts)
                context_parts.append(f"'{table_name}' ({concepts}):")
                
                # Categorize columns for DAX usage
                keys = [col for col in table_info.columns if col.lower().endswith(('_key', '_id'))]
                measures = [col for col in table_info.columns if any(pattern in col.lower() for pattern in ['amount', 'balance', 'value', 'count', 'sum', 'total', 'exposure'])]
                others = [col for col in table_info.columns if col not in keys and col not in measures]
                
                if keys:
                    context_parts.append(f"  Keys: {', '.join(keys)}")
                if measures:
                    context_parts.append(f"  Measures: {', '.join(measures)}")
                if others:
                    context_parts.append(f"  Other: {', '.join(others)}")
        
        # Format dimension tables
        if dim_tables:
            context_parts.append("\nDIMENSION TABLES:")
            for table_name, table_info in dim_tables:
                concepts = ', '.join(table_info.business_concepts)
                context_parts.append(f"'{table_name}' ({concepts}):")
                context_parts.append(f"  Columns: {', '.join(table_info.columns)}")
        
        # Add relationships for DAX
        if schema_analysis.get('relationships'):
            context_parts.append("\nRELATIONSHIPS:")
            for rel in schema_analysis['relationships']:
                context_parts.append(f"- '{rel['parent_table']}'[{rel['parent_column']}] -> '{rel['referenced_table']}'[{rel['referenced_column']}]")
        
        return '\n'.join(context_parts)

    def _estimate_query_complexity(self, business_intent: str, schema_analysis: Dict[str, Any]) -> str:
        """Estimate query complexity based on intent and schema"""
        intent_lower = business_intent.lower()
        
        # Count complexity indicators
        complexity_score = 0
        
        # Multiple table references
        table_count = len(schema_analysis['tables'])
        if table_count > 3:
            complexity_score += 1
        
        # Complex operations in intent
        complex_keywords = ['compare', 'analyze', 'comprehensive', 'across', 'correlation', 'trend']
        complexity_score += sum(1 for keyword in complex_keywords if keyword in intent_lower)
        
        # Multiple business areas
        if len(schema_analysis.get('business_areas', [])) > 2:
            complexity_score += 1
        
        # Aggregation indicators
        aggregation_keywords = ['total', 'average', 'sum', 'count', 'group', 'by']
        if any(keyword in intent_lower for keyword in aggregation_keywords):
            complexity_score += 1
        
        # Return complexity level
        if complexity_score <= 1:
            return "Simple"
        elif complexity_score <= 3:
            return "Medium"
        else:
            return "Complex"

    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the current schema analysis"""
        schema_analysis = self.analyze_current_schema()
        
        fact_count = sum(1 for t in schema_analysis['tables'].values() if t.table_type == TableType.FACT)
        dim_count = sum(1 for t in schema_analysis['tables'].values() if t.table_type == TableType.DIMENSION)
        
        return {
            'total_tables': len(schema_analysis['tables']),
            'fact_tables': fact_count,
            'dimension_tables': dim_count,
            'business_areas': schema_analysis.get('business_areas', []),
            'suggested_patterns': schema_analysis.get('query_patterns', []),
            'complexity_assessment': 'High' if len(schema_analysis['tables']) > 10 else 'Medium' if len(schema_analysis['tables']) > 5 else 'Low'
        }

# Example usage patterns
COMMON_BUSINESS_INTENTS = {
    "customer_analysis": [
        "Show me all customers by country",
        "List customers with highest risk ratings", 
        "Display customer portfolio overview",
        "Find customers with multiple currencies"
    ],
    "financial_analysis": [
        "What is our total exposure by currency?",
        "Show loan portfolio by geographic region",
        "Analyze facility utilization rates",
        "Compare loan vs facility amounts"
    ],
    "risk_analysis": [
        "Show portfolio risk distribution",
        "List high-risk customers with exposure",
        "Analyze probability of default trends",
        "Display risk by country exposure"
    ],
    "operational_analysis": [
        "Show transaction volume by month",
        "Analyze product performance metrics",
        "Display operational efficiency indicators",
        "Track key performance indicators"
    ]
}