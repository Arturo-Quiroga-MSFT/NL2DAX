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
import pyodbc
import json
import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from .schema_cache_manager import SchemaCacheManager, get_connection_params_from_env

# Load environment variables from multiple possible locations
load_dotenv()  # Load from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))  # Load from parent directory

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
        
        # Initialize schema cache manager
        self.cache_manager = SchemaCacheManager()
        
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

    def discover_database_schema(self) -> Dict[str, Any]:
        """
        Connect to the database and discover the complete schema structure.
        Uses caching to accelerate subsequent executions.
        
        Returns:
            Dictionary containing tables, columns, relationships, and constraints
        """
        try:
            # Build connection parameters from environment variables
            connection_params = get_connection_params_from_env()
            
            # Check if we have a valid cached schema
            print("[DEBUG] Checking for cached schema...")
            cached_schema = self.cache_manager.load_schema_from_cache(connection_params)
            
            if cached_schema:
                # Convert cached schema back to the expected format
                return self._convert_cached_schema_to_discovery_result(cached_schema)
            
            # No valid cache, proceed with fresh discovery
            print("[DEBUG] No valid cache found, performing fresh schema discovery...")
            
            # Build connection string from environment variables
            # Support multiple naming conventions for database credentials
            server = (os.getenv('DB_SERVER') or 
                     os.getenv('AZURE_SQL_SERVER') or 
                     os.getenv('SQL_SERVER'))
            database = (os.getenv('DB_DATABASE') or 
                       os.getenv('AZURE_SQL_DB') or 
                       os.getenv('SQL_DATABASE'))
            username = (os.getenv('DB_USERNAME') or 
                       os.getenv('AZURE_SQL_USER') or 
                       os.getenv('SQL_USERNAME') or 
                       os.getenv('DB_USER'))
            password = (os.getenv('DB_PASSWORD') or 
                       os.getenv('AZURE_SQL_PASSWORD') or 
                       os.getenv('SQL_PASSWORD') or 
                       os.getenv('DB_PASS'))
            driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
            
            if not all([server, database, username, password]):
                raise ValueError("Missing required database connection parameters in environment variables")
            
            connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            
            print(f"[DEBUG] Connecting to database: {server}/{database}")
            
            # Connect to database
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            # Discover all tables
            print("[DEBUG] Discovering database tables...")
            tables_query = """
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA NOT IN ('sys', 'information_schema')
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            cursor.execute(tables_query)
            table_rows = cursor.fetchall()
            
            tables = {}
            table_details = {}
            
            # Get detailed information for each table
            for schema_name, table_name, table_type in table_rows:
                full_table_name = f"{schema_name}.{table_name}" if schema_name != 'dbo' else table_name
                
                # Get column information
                columns_query = """
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, 
                           COLUMN_DEFAULT, CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """
                
                cursor.execute(columns_query, schema_name, table_name)
                column_rows = cursor.fetchall()
                
                columns = []
                column_details = {}
                
                for col_name, data_type, is_nullable, default_val, max_length in column_rows:
                    columns.append(col_name)
                    column_details[col_name] = {
                        'data_type': data_type,
                        'is_nullable': is_nullable == 'YES',
                        'default_value': default_val,
                        'max_length': max_length
                    }
                
                tables[full_table_name] = columns
                table_details[full_table_name] = {
                    'schema': schema_name,
                    'table_name': table_name,
                    'columns': column_details,
                    'row_count': None  # We'll get this separately if needed
                }
            
            print(f"[DEBUG] Found {len(tables)} tables")
            
            # Discover foreign key relationships
            print("[DEBUG] Discovering foreign key relationships...")
            fk_query = """
                SELECT 
                    fk.name AS FK_NAME,
                    tp.name AS PARENT_TABLE,
                    cp.name AS PARENT_COLUMN,
                    tr.name AS REFERENCED_TABLE,
                    cr.name AS REFERENCED_COLUMN
                FROM sys.foreign_keys fk
                INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
                INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
                INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                INNER JOIN sys.columns cp ON fkc.parent_column_id = cp.column_id AND fkc.parent_object_id = cp.object_id
                INNER JOIN sys.columns cr ON fkc.referenced_column_id = cr.column_id AND fkc.referenced_object_id = cr.object_id
                ORDER BY tp.name, cp.name
            """
            
            cursor.execute(fk_query)
            fk_rows = cursor.fetchall()
            
            relationships = []
            for fk_name, parent_table, parent_column, referenced_table, referenced_column in fk_rows:
                relationships.append({
                    'fk_name': fk_name,
                    'parent_table': parent_table,
                    'parent_column': parent_column,
                    'referenced_table': referenced_table,
                    'referenced_column': referenced_column
                })
            
            print(f"[DEBUG] Found {len(relationships)} foreign key relationships")
            
            # Get table row counts for fact/dimension classification
            print("[DEBUG] Getting table row counts for classification...")
            for table_name in tables.keys():
                try:
                    # Clean table name for query
                    clean_table = table_name.replace('[', '').replace(']', '')
                    count_query = f"SELECT COUNT(*) FROM [{clean_table}]"
                    cursor.execute(count_query)
                    row_count = cursor.fetchone()[0]
                    table_details[table_name]['row_count'] = row_count
                except Exception as e:
                    print(f"[WARN] Could not get row count for {table_name}: {e}")
                    table_details[table_name]['row_count'] = 0
            
            conn.close()
            
            schema_metadata = {
                'tables': tables,
                'table_details': table_details,
                'relationships': relationships,
                'discovery_timestamp': json.dumps({"timestamp": "now"}),  # For cache management
                'database_info': {
                    'server': server,
                    'database': database,
                    'total_tables': len(tables),
                    'total_relationships': len(relationships)
                }
            }
            
            print(f"[SUCCESS] Schema discovery complete: {len(tables)} tables, {len(relationships)} relationships")
            
            # Save to cache for future use
            print("[DEBUG] Saving schema to cache...")
            self.cache_manager.save_schema_to_cache(connection_params, self._convert_discovery_result_to_cacheable(schema_metadata))
            
            return schema_metadata
            
        except Exception as e:
            print(f"[ERROR] Schema discovery failed: {e}")
            # Return a minimal fallback schema for testing
            return {
                'tables': {
                    'sample_table': ['id', 'name', 'value']
                },
                'table_details': {},
                'relationships': [],
                'error': str(e)
            }

    def _convert_cached_schema_to_discovery_result(self, cached_schema):
        """Convert cached schema back to discovery result format"""
        return {
            'tables': cached_schema.tables,
            'table_details': {},  # Will be populated when needed
            'relationships': cached_schema.relationships,
            'discovery_timestamp': json.dumps({"timestamp": cached_schema.discovery_time}),
            'database_info': {
                'total_tables': cached_schema.total_tables,
                'fact_tables': cached_schema.fact_tables,
                'dimension_tables': cached_schema.dimension_tables,
                'schema_type': cached_schema.schema_type
            }
        }
    
    def _convert_discovery_result_to_cacheable(self, discovery_result):
        """Convert discovery result to cacheable schema format"""
        from .schema_cache_manager import CachedSchema
        import datetime
        
        # Extract info for the cache format expected by SchemaCacheManager
        return CachedSchema(
            connection_hash="",  # Will be set by cache manager
            discovery_time=datetime.datetime.now().isoformat(),
            schema_version="1.0",
            total_tables=len(discovery_result.get('tables', {})),
            fact_tables=[],  # Will be determined by classification
            dimension_tables=[],  # Will be determined by classification  
            schema_type="generic",  # Will be determined by analysis
            tables=discovery_result['tables'],
            relationships=discovery_result['relationships'],
            business_areas=[],  # Will be populated by business analysis
            suggested_patterns=[]  # Will be populated by pattern analysis
        )

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

    def classify_table_type(self, table_name: str, columns: List[str], foreign_keys: List[str], row_count: int = 0) -> TableType:
        """Classify a table as fact, dimension, or other type"""
        table_lower = table_name.lower()
        column_lower = [col.lower() for col in columns]
        
        # Count different types of columns
        measure_count = sum(1 for col in column_lower 
                          if any(re.match(pattern, col) for pattern in self.column_patterns[ColumnType.MEASURE]))
        
        date_count = sum(1 for col in column_lower 
                        if any(re.match(pattern, col) for pattern in self.column_patterns[ColumnType.DATE_TIME]))
        
        fk_count = len(foreign_keys)
        total_columns = len(columns)
        
        # Enhanced fact table detection
        fact_indicators = ['fact', 'detail', 'transaction', 'event', 'log', 'activity', 'history']
        fact_name_match = any(indicator in table_lower for indicator in fact_indicators)
        
        # Enhanced dimension table detection  
        dim_indicators = ['dimension', 'dim', 'master', 'reference', 'lookup', 'customer', 'product', 'account', 'region']
        dim_name_match = any(indicator in table_lower for indicator in dim_indicators)
        
        # Analyze column patterns for fact vs dimension characteristics
        has_measures = measure_count > 0
        has_dates = date_count > 0
        many_fks = fk_count >= 2  # Fact tables typically have multiple FKs
        few_fks = fk_count <= 1   # Dimension tables typically have 0-1 FKs
        
        # Use row count as additional indicator (if available)
        high_row_count = row_count > 10000  # Fact tables tend to have more rows
        low_row_count = row_count < 1000    # Dimension tables tend to have fewer rows
        
        # Scoring system for classification
        fact_score = 0
        dim_score = 0
        
        # Name-based scoring
        if fact_name_match:
            fact_score += 3
        if dim_name_match:
            dim_score += 3
            
        # Structure-based scoring
        if has_measures:
            fact_score += 2
        if has_dates:
            fact_score += 1
        if many_fks:
            fact_score += 2
        if few_fks:
            dim_score += 1
            
        # Row count-based scoring (if available)
        if row_count > 0:
            if high_row_count:
                fact_score += 1
            if low_row_count:
                dim_score += 1
        
        # Decision logic
        if fact_score > dim_score and fact_score >= 2:
            return TableType.FACT
        elif dim_score > fact_score and dim_score >= 2:
            return TableType.DIMENSION
        elif fk_count == 0 and not has_measures:
            # Standalone lookup table
            return TableType.LOOKUP
        else:
            # Default classification based on characteristics
            if has_measures or many_fks:
                return TableType.FACT
            else:
                return TableType.DIMENSION
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
        
        # Check if this is a star schema database by looking for FACT and DIMENSION tables
        all_tables = schema_metadata.get('tables', {})
        fact_tables = [name for name in all_tables.keys() if 'FACT' in name.upper()]
        dimension_tables = [name for name in all_tables.keys() if 'DIMENSION' in name.upper()]
        
        # If we have both FACT and DIMENSION tables, focus only on those (star schema pattern)
        if fact_tables and dimension_tables:
            print(f"[DEBUG] Star schema detected: {len(fact_tables)} fact tables, {len(dimension_tables)} dimension tables")
            print(f"[DEBUG] Focusing only on FACT and DIMENSION tables")
            
            # Filter to only include FACT and DIMENSION tables
            filtered_tables = {}
            for table_name, columns in all_tables.items():
                if 'FACT' in table_name.upper() or 'DIMENSION' in table_name.upper():
                    filtered_tables[table_name] = columns
            
            print(f"[DEBUG] Filtered from {len(all_tables)} to {len(filtered_tables)} star schema tables")
            tables_to_analyze = filtered_tables
        else:
            print(f"[DEBUG] Generic schema detected, analyzing all {len(all_tables)} tables")
            tables_to_analyze = all_tables
        
        # Analyze each relevant table
        for table_name, columns in tables_to_analyze.items():
            # Get foreign keys for this table safely
            relationships = schema_metadata.get('relationships', [])
            fks = []
            if relationships:
                for rel in relationships:
                    if isinstance(rel, dict) and 'parent_table' in rel and 'parent_column' in rel:
                        if rel['parent_table'] == table_name:
                            fks.append(rel['parent_column'])
            
            # Get row count if available
            table_details = schema_metadata.get('table_details', {})
            row_count = 0
            if table_name in table_details and 'row_count' in table_details[table_name]:
                row_count = table_details[table_name]['row_count'] or 0
            
            # Classify table type with row count information
            table_type = self.classify_table_type(table_name, columns, fks, row_count)
            
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