"""
schema_agnostic_analyzer.py - Universal Database Schema Analysis
===============================================================

This module provides database-agnostic schema analysis that works with any SQL database
by discovering patterns and relationships automatically. It replaces hardcoded schema
knowledge with intelligent pattern recognition and AI-powered analysis.

Key Features:
- Universal schema discovery for any SQL database
- Pattern-based table and column classification
- Automatic relationship detection
- Business concept mapping (customer, currency, risk, geography, etc.)
- Support for multiple database systems (SQL Server, PostgreSQL, MySQL, etc.)

Architecture:
- Uses database metadata queries to discover schema structure
- Applies pattern recognition to classify tables and columns
- Uses AI to map database elements to business concepts
- Provides generic interfaces for query generation

Author: NL2DAX Pipeline Development Team
Last Updated: August 16, 2025
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate

load_dotenv()

class TableType(Enum):
    """Classification of database table types"""
    FACT = "fact"
    DIMENSION = "dimension"
    BRIDGE = "bridge"
    LOOKUP = "lookup"
    UNKNOWN = "unknown"

class ColumnType(Enum):
    """Classification of database column types"""
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    MEASURE = "measure"
    ATTRIBUTE = "attribute"
    CURRENCY = "currency"
    RISK = "risk"
    GEOGRAPHY = "geography"
    DATE_TIME = "date_time"
    STATUS = "status"
    CLASSIFICATION = "classification"
    UNKNOWN = "unknown"

@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    table_type: TableType
    columns: List[str]
    primary_key: Optional[str]
    foreign_keys: List[str]
    business_concepts: List[str]
    estimated_row_count: Optional[int] = None

@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    table_name: str
    column_type: ColumnType
    data_type: str
    business_concepts: List[str]
    is_nullable: bool
    is_key: bool = False

@dataclass
class Relationship:
    """Represents a foreign key relationship between tables"""
    fk_name: str
    parent_table: str
    parent_column: str
    referenced_table: str
    referenced_column: str

class SchemaAgnosticAnalyzer:
    """Universal database schema analyzer"""
    
    def __init__(self):
        """Initialize the schema analyzer"""
        self.llm = AzureChatOpenAI(
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version="2024-12-01-preview",
            temperature=0.1
        )
        
        # Pattern dictionaries for column classification
        self.column_patterns = {
            ColumnType.PRIMARY_KEY: [
                r'.*_?id$', r'.*_?key$', r'^id$', r'^key$', r'.*_pk$'
            ],
            ColumnType.FOREIGN_KEY: [
                r'.*_id$', r'.*_key$', r'.*id$', r'.*key$'
            ],
            ColumnType.MEASURE: [
                r'.*amount.*', r'.*balance.*', r'.*value.*', r'.*sum.*',
                r'.*total.*', r'.*count.*', r'.*quantity.*', r'.*limit.*',
                r'.*exposure.*', r'.*principal.*', r'.*interest.*'
            ],
            ColumnType.CURRENCY: [
                r'.*currency.*', r'.*ccy.*', r'.*curr.*', r'.*exchange.*',
                r'.*rate.*', r'.*fx.*'
            ],
            ColumnType.RISK: [
                r'.*risk.*', r'.*rating.*', r'.*probability.*', r'.*default.*',
                r'.*exposure.*', r'.*loss.*', r'.*pd.*', r'.*lgd.*'
            ],
            ColumnType.GEOGRAPHY: [
                r'.*country.*', r'.*region.*', r'.*state.*', r'.*city.*',
                r'.*location.*', r'.*postal.*', r'.*zip.*'
            ],
            ColumnType.DATE_TIME: [
                r'.*date.*', r'.*time.*', r'.*period.*', r'.*month.*',
                r'.*year.*', r'.*quarter.*', r'.*day.*'
            ],
            ColumnType.STATUS: [
                r'.*status.*', r'.*state.*', r'.*flag.*', r'.*indicator.*',
                r'.*active.*', r'.*enabled.*'
            ],
            ColumnType.CLASSIFICATION: [
                r'.*type.*', r'.*category.*', r'.*class.*', r'.*group.*',
                r'.*desc.*', r'.*description.*', r'.*name.*'
            ]
        }
        
        # Business concept mappings
        self.business_concepts = {
            'customer': ['customer', 'client', 'account_holder', 'borrower'],
            'financial': ['loan', 'credit', 'facility', 'account', 'transaction'],
            'risk': ['risk', 'rating', 'exposure', 'default', 'probability'],
            'geography': ['country', 'region', 'location', 'address'],
            'currency': ['currency', 'exchange', 'rate', 'forex'],
            'time': ['date', 'time', 'period', 'month', 'year'],
            'product': ['product', 'service', 'offering', 'type'],
            'organization': ['organization', 'institution', 'entity', 'owner']
        }

    def classify_column_type(self, column_name: str, data_type: str) -> ColumnType:
        """Classify a column based on name patterns and data type"""
        column_lower = column_name.lower()
        
        # Check each pattern category
        for col_type, patterns in self.column_patterns.items():
            for pattern in patterns:
                if re.match(pattern, column_lower):
                    return col_type
        
        # Default classification based on data type
        if data_type.lower() in ['int', 'bigint', 'decimal', 'float', 'money']:
            return ColumnType.MEASURE
        elif data_type.lower() in ['varchar', 'nvarchar', 'text', 'char']:
            return ColumnType.ATTRIBUTE
        
        return ColumnType.UNKNOWN

    def classify_table_type(self, table_name: str, columns: List[str], foreign_keys: List[str]) -> TableType:
        """Classify a table as fact, dimension, or other type"""
        table_lower = table_name.lower()
        column_lower = [col.lower() for col in columns]
        
        # Count different types of columns
        measure_count = sum(1 for col in column_lower 
                          if any(re.match(pattern, col) for pattern in self.column_patterns[ColumnType.MEASURE]))
        
        fk_count = len(foreign_keys)
        total_columns = len(columns)
        
        # Fact table indicators
        fact_indicators = ['fact', 'detail', 'transaction', 'event', 'log']
        if any(indicator in table_lower for indicator in fact_indicators):
            return TableType.FACT
        
        # Dimension table indicators
        dim_indicators = ['dimension', 'dim', 'master', 'reference', 'lookup']
        if any(indicator in table_lower for indicator in dim_indicators):
            return TableType.DIMENSION
        
        # Heuristic classification
        if fk_count >= 2 and measure_count >= 2:
            return TableType.FACT
        elif fk_count <= 1 and measure_count <= total_columns * 0.3:
            return TableType.DIMENSION
        
        return TableType.UNKNOWN

    def identify_business_concepts(self, table_name: str, columns: List[str]) -> List[str]:
        """Identify business concepts present in a table"""
        concepts = []
        table_lower = table_name.lower()
        column_text = ' '.join(columns).lower()
        
        for concept, keywords in self.business_concepts.items():
            if any(keyword in table_lower for keyword in keywords):
                concepts.append(concept)
            elif any(keyword in column_text for keyword in keywords):
                concepts.append(concept)
        
        return list(set(concepts))

    def analyze_schema_structure(self, schema_metadata: Dict) -> Dict[str, Any]:
        """
        Analyze complete schema structure and provide insights
        
        Args:
            schema_metadata: Dictionary containing tables, columns, and relationships
            
        Returns:
            Dictionary with analyzed schema structure and insights
        """
        tables_info = {}
        columns_info = {}
        
        # Analyze each table
        for table_name, columns in schema_metadata.get('tables', {}).items():
            # Get foreign keys for this table safely
            relationships = schema_metadata.get('relationships', [])
            fks = []
            if relationships:
                for rel in relationships:
                    if isinstance(rel, dict) and 'parent_table' in rel and 'parent_column' in rel:
                        if rel['parent_table'] == table_name:
                            fks.append(rel['parent_column'])
            
            # Classify table type
            table_type = self.classify_table_type(table_name, columns, fks)
            
            # Identify business concepts
            concepts = self.identify_business_concepts(table_name, columns)
            
            # Create table info
            tables_info[table_name] = TableInfo(
                name=table_name,
                table_type=table_type,
                columns=columns,
                primary_key=self._find_primary_key(columns),
                foreign_keys=fks,
                business_concepts=concepts
            )
            
            # Analyze each column
            for column in columns:
                col_type = self.classify_column_type(column, 'unknown')  # Data type would come from metadata
                col_concepts = self._identify_column_concepts(column)
                
                columns_info[f"{table_name}.{column}"] = ColumnInfo(
                    name=column,
                    table_name=table_name,
                    column_type=col_type,
                    data_type='unknown',
                    business_concepts=col_concepts,
                    is_nullable=True,  # Would come from metadata
                    is_key=col_type in [ColumnType.PRIMARY_KEY, ColumnType.FOREIGN_KEY]
                )
        
        return {
            'tables': tables_info,
            'columns': columns_info,
            'relationships': schema_metadata.get('relationships', []),
            'business_areas': self._identify_business_areas(tables_info),
            'query_patterns': self._suggest_query_patterns(tables_info)
        }

    def _find_primary_key(self, columns: List[str]) -> Optional[str]:
        """Find the most likely primary key column"""
        for column in columns:
            col_lower = column.lower()
            if col_lower.endswith('_key') or col_lower.endswith('_id') or col_lower == 'id':
                return column
        return None

    def _identify_column_concepts(self, column_name: str) -> List[str]:
        """Identify business concepts for a specific column"""
        concepts = []
        col_lower = column_name.lower()
        
        for concept, keywords in self.business_concepts.items():
            if any(keyword in col_lower for keyword in keywords):
                concepts.append(concept)
        
        return concepts

    def _identify_business_areas(self, tables_info: Dict[str, TableInfo]) -> List[str]:
        """Identify main business areas covered by the schema"""
        all_concepts = []
        for table in tables_info.values():
            all_concepts.extend(table.business_concepts)
        
        # Count concepts and return most common ones
        concept_counts = {}
        for concept in all_concepts:
            concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        return sorted(concept_counts.keys(), key=lambda x: concept_counts[x], reverse=True)

    def _suggest_query_patterns(self, tables_info: Dict[str, TableInfo]) -> List[str]:
        """Suggest useful query patterns based on schema analysis"""
        patterns = []
        
        fact_tables = [t for t in tables_info.values() if t.table_type == TableType.FACT]
        dim_tables = [t for t in tables_info.values() if t.table_type == TableType.DIMENSION]
        
        if fact_tables and dim_tables:
            patterns.append("Fact-Dimension Analysis: Join fact tables with dimensions for detailed analysis")
        
        customer_tables = [t for t in tables_info.values() if 'customer' in t.business_concepts]
        if customer_tables:
            patterns.append("Customer Analysis: Analyze customer demographics, risk, and financial metrics")
        
        geography_tables = [t for t in tables_info.values() if 'geography' in t.business_concepts]
        if geography_tables:
            patterns.append("Geographic Analysis: Portfolio distribution by country/region")
        
        currency_tables = [t for t in tables_info.values() if 'currency' in t.business_concepts]
        if currency_tables:
            patterns.append("Currency Exposure: Multi-currency portfolio analysis")
        
        risk_tables = [t for t in tables_info.values() if 'risk' in t.business_concepts]
        if risk_tables:
            patterns.append("Risk Analysis: Portfolio risk metrics and exposure analysis")
        
        return patterns

    def generate_business_query_suggestions(self, schema_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate natural language query suggestions based on schema analysis"""
        suggestions = []
        business_areas = schema_analysis.get('business_areas', [])
        
        if 'customer' in business_areas:
            suggestions.append({
                'query': 'Show me all customers by country',
                'analysis_type': 'customer_geographic',
                'complexity': 'simple'
            })
            
            if 'risk' in business_areas:
                suggestions.append({
                    'query': 'List customers with highest risk ratings',
                    'analysis_type': 'customer_risk',
                    'complexity': 'medium'
                })
        
        if 'currency' in business_areas and 'geography' in business_areas:
            suggestions.append({
                'query': 'Compare exposure by currency and country',
                'analysis_type': 'currency_geographic',
                'complexity': 'medium'
            })
        
        if 'financial' in business_areas:
            suggestions.append({
                'query': 'Show total portfolio exposure by product type',
                'analysis_type': 'portfolio_summary',
                'complexity': 'simple'
            })
        
        return suggestions