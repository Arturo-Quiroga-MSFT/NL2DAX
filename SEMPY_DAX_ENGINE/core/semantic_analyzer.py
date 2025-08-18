"""
semantic_analyzer.py - Semantic Model Metadata Discovery and Analysis
=====================================================================

This module provides comprehensive analysis of Power BI semantic models,
including table discovery, relationship mapping, measure analysis, and
business context extraction using SemPy.

Key Features:
- Table and column discovery with metadata
- Relationship mapping and cardinality analysis
- Measure and calculated column discovery
- Data type and formatting analysis
- Business context and naming pattern recognition

Author: NL2DAX Pipeline Development Team
Last Updated: August 18, 2025
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import re

try:
    import sempy.fabric as fabric
    from sempy.fabric import list_tables, list_columns, list_measures, list_relationships
    SEMPY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPy not available: {e}")
    SEMPY_AVAILABLE = False

class DataTypeCategory(Enum):
    """Categories of data types for DAX generation"""
    NUMERIC = "numeric"
    TEXT = "text"
    DATE = "date"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"

class RelationshipType(Enum):
    """Types of relationships between tables"""
    ONE_TO_MANY = "1:*"
    MANY_TO_ONE = "*:1"
    ONE_TO_ONE = "1:1"
    MANY_TO_MANY = "*:*"

@dataclass
class ColumnInfo:
    """Information about a column in a semantic model"""
    name: str
    table_name: str
    data_type: str
    data_category: DataTypeCategory
    is_key: bool = False
    is_nullable: bool = True
    description: Optional[str] = None
    format_string: Optional[str] = None
    sort_by_column: Optional[str] = None
    business_meaning: Optional[str] = None

@dataclass
class TableInfo:
    """Information about a table in a semantic model"""
    name: str
    type: str  # Table, CalculatedTable, etc.
    description: Optional[str] = None
    row_count: Optional[int] = None
    columns: List[ColumnInfo] = field(default_factory=list)
    is_fact_table: bool = False
    is_dimension_table: bool = False
    business_domain: Optional[str] = None

@dataclass
class RelationshipInfo:
    """Information about relationships between tables"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: RelationshipType
    is_active: bool = True
    cross_filter_direction: str = "Single"
    description: Optional[str] = None

@dataclass
class MeasureInfo:
    """Information about measures in a semantic model"""
    name: str
    table_name: str
    expression: str
    data_type: str
    format_string: Optional[str] = None
    description: Optional[str] = None
    folder: Optional[str] = None
    is_hidden: bool = False
    business_meaning: Optional[str] = None

@dataclass
class SemanticModelSchema:
    """Complete schema information for a semantic model"""
    model_name: str
    workspace_name: str
    tables: List[TableInfo] = field(default_factory=list)
    relationships: List[RelationshipInfo] = field(default_factory=list)
    measures: List[MeasureInfo] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)

class SemanticAnalyzer:
    """
    Semantic Model Analyzer
    
    Discovers and analyzes semantic model metadata to provide
    comprehensive information for DAX query generation.
    """
    
    def __init__(self):
        """Initialize the semantic analyzer"""
        self.logger = logging.getLogger(__name__)
        
        if not SEMPY_AVAILABLE:
            raise ImportError(
                "SemPy (semantic-link) is not available. "
                "Install with: pip install semantic-link"
            )
    
    def analyze_semantic_model(self, model_name: str, workspace_name: str) -> SemanticModelSchema:
        """
        Perform comprehensive analysis of a semantic model
        
        Args:
            model_name: Name of the semantic model
            workspace_name: Name of the workspace
            
        Returns:
            SemanticModelSchema with complete metadata
        """
        try:
            self.logger.info(f"Analyzing semantic model: {model_name}")
            
            schema = SemanticModelSchema(
                model_name=model_name,
                workspace_name=workspace_name
            )
            
            # Discover tables and columns
            schema.tables = self._discover_tables(model_name, workspace_name)
            
            # Discover relationships
            schema.relationships = self._discover_relationships(model_name, workspace_name)
            
            # Discover measures
            schema.measures = self._discover_measures(model_name, workspace_name)
            
            # Perform business analysis
            schema.analysis_metadata = self._analyze_business_context(schema)
            
            # Classify tables as fact/dimension
            self._classify_tables(schema)
            
            self.logger.info(f"Analysis complete: {len(schema.tables)} tables, "
                           f"{len(schema.relationships)} relationships, "
                           f"{len(schema.measures)} measures")
            
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to analyze semantic model: {e}")
            raise
    
    def _discover_tables(self, model_name: str, workspace_name: str) -> List[TableInfo]:
        """Discover tables and their columns"""
        try:
            tables = []
            
            # Get tables using SemPy
            tables_df = list_tables(dataset=model_name, workspace=workspace_name)
            
            for _, table_row in tables_df.iterrows():
                table_name = table_row.get('Name', '')
                
                table_info = TableInfo(
                    name=table_name,
                    type=table_row.get('Type', 'Table'),
                    description=table_row.get('Description'),
                    row_count=table_row.get('RowCount')
                )
                
                # Get columns for this table
                table_info.columns = self._discover_columns(model_name, workspace_name, table_name)
                
                tables.append(table_info)
            
            self.logger.info(f"Discovered {len(tables)} tables")
            return tables
            
        except Exception as e:
            self.logger.error(f"Failed to discover tables: {e}")
            return []
    
    def _discover_columns(self, model_name: str, workspace_name: str, table_name: str) -> List[ColumnInfo]:
        """Discover columns for a specific table"""
        try:
            columns = []
            
            # Get columns using SemPy
            columns_df = list_columns(dataset=model_name, workspace=workspace_name)
            
            # Filter for this table
            table_columns = columns_df[columns_df['Table Name'] == table_name]
            
            for _, col_row in table_columns.iterrows():
                column_info = ColumnInfo(
                    name=col_row.get('Column Name', ''),
                    table_name=table_name,
                    data_type=col_row.get('Data Type', ''),
                    data_category=self._categorize_data_type(col_row.get('Data Type', '')),
                    is_key=col_row.get('Key', False),
                    is_nullable=col_row.get('IsNullable', True),
                    description=col_row.get('Description'),
                    format_string=col_row.get('FormatString'),
                    sort_by_column=col_row.get('SortByColumn')
                )
                
                # Analyze business meaning
                column_info.business_meaning = self._analyze_column_business_meaning(column_info)
                
                columns.append(column_info)
            
            return columns
            
        except Exception as e:
            self.logger.error(f"Failed to discover columns for table {table_name}: {e}")
            return []
    
    def _discover_relationships(self, model_name: str, workspace_name: str) -> List[RelationshipInfo]:
        """Discover relationships between tables"""
        try:
            relationships = []
            
            # Get relationships using SemPy
            relationships_df = list_relationships(dataset=model_name, workspace=workspace_name)
            
            for _, rel_row in relationships_df.iterrows():
                relationship_info = RelationshipInfo(
                    from_table=rel_row.get('From Table', ''),
                    from_column=rel_row.get('From Column', ''),
                    to_table=rel_row.get('To Table', ''),
                    to_column=rel_row.get('To Column', ''),
                    relationship_type=self._parse_relationship_type(
                        rel_row.get('From Cardinality', ''),
                        rel_row.get('To Cardinality', '')
                    ),
                    is_active=rel_row.get('State', '') == 'Active',
                    cross_filter_direction=rel_row.get('CrossFilteringBehavior', 'Single')
                )
                
                relationships.append(relationship_info)
            
            self.logger.info(f"Discovered {len(relationships)} relationships")
            return relationships
            
        except Exception as e:
            self.logger.error(f"Failed to discover relationships: {e}")
            return []
    
    def _discover_measures(self, model_name: str, workspace_name: str) -> List[MeasureInfo]:
        """Discover measures in the semantic model"""
        try:
            measures = []
            
            # Get measures using SemPy
            measures_df = list_measures(dataset=model_name, workspace=workspace_name)
            
            for _, measure_row in measures_df.iterrows():
                measure_info = MeasureInfo(
                    name=measure_row.get('Measure Name', ''),
                    table_name=measure_row.get('Table Name', ''),
                    expression=measure_row.get('Expression', ''),
                    data_type=measure_row.get('Data Type', ''),
                    format_string=measure_row.get('FormatString'),
                    description=measure_row.get('Description'),
                    folder=measure_row.get('DisplayFolder'),
                    is_hidden=measure_row.get('IsHidden', False)
                )
                
                # Analyze business meaning
                measure_info.business_meaning = self._analyze_measure_business_meaning(measure_info)
                
                measures.append(measure_info)
            
            self.logger.info(f"Discovered {len(measures)} measures")
            return measures
            
        except Exception as e:
            self.logger.error(f"Failed to discover measures: {e}")
            return []
    
    def _categorize_data_type(self, data_type: str) -> DataTypeCategory:
        """Categorize data type for DAX generation"""
        data_type_lower = data_type.lower()
        
        if any(t in data_type_lower for t in ['int', 'decimal', 'double', 'currency', 'number']):
            return DataTypeCategory.NUMERIC
        elif any(t in data_type_lower for t in ['datetime', 'date', 'time']):
            return DataTypeCategory.DATE
        elif any(t in data_type_lower for t in ['string', 'text', 'varchar', 'char']):
            return DataTypeCategory.TEXT
        elif 'boolean' in data_type_lower:
            return DataTypeCategory.BOOLEAN
        else:
            return DataTypeCategory.UNKNOWN
    
    def _parse_relationship_type(self, from_cardinality: str, to_cardinality: str) -> RelationshipType:
        """Parse relationship type from cardinalities"""
        if from_cardinality == "One" and to_cardinality == "Many":
            return RelationshipType.ONE_TO_MANY
        elif from_cardinality == "Many" and to_cardinality == "One":
            return RelationshipType.MANY_TO_ONE
        elif from_cardinality == "One" and to_cardinality == "One":
            return RelationshipType.ONE_TO_ONE
        elif from_cardinality == "Many" and to_cardinality == "Many":
            return RelationshipType.MANY_TO_MANY
        else:
            return RelationshipType.ONE_TO_MANY  # Default assumption
    
    def _analyze_column_business_meaning(self, column: ColumnInfo) -> Optional[str]:
        """Analyze business meaning of a column based on name and type"""
        name_lower = column.name.lower()
        
        # Common business patterns
        if any(pattern in name_lower for pattern in ['id', 'key']):
            return "identifier"
        elif any(pattern in name_lower for pattern in ['name', 'title', 'description']):
            return "descriptor"
        elif any(pattern in name_lower for pattern in ['amount', 'value', 'price', 'cost']):
            return "monetary"
        elif any(pattern in name_lower for pattern in ['date', 'time', 'created', 'modified']):
            return "temporal"
        elif any(pattern in name_lower for pattern in ['count', 'quantity', 'number']):
            return "quantity"
        elif any(pattern in name_lower for pattern in ['status', 'state', 'flag']):
            return "status"
        elif any(pattern in name_lower for pattern in ['country', 'region', 'city', 'address']):
            return "geographic"
        else:
            return None
    
    def _analyze_measure_business_meaning(self, measure: MeasureInfo) -> Optional[str]:
        """Analyze business meaning of a measure"""
        name_lower = measure.name.lower()
        expression_lower = measure.expression.lower()
        
        # Analyze measure patterns
        if any(pattern in name_lower for pattern in ['total', 'sum']):
            return "aggregation"
        elif any(pattern in name_lower for pattern in ['avg', 'average', 'mean']):
            return "average"
        elif any(pattern in name_lower for pattern in ['count', 'number of']):
            return "count"
        elif any(pattern in name_lower for pattern in ['max', 'maximum', 'highest']):
            return "maximum"
        elif any(pattern in name_lower for pattern in ['min', 'minimum', 'lowest']):
            return "minimum"
        elif any(pattern in name_lower for pattern in ['ratio', 'rate', 'percentage', '%']):
            return "ratio"
        elif 'calculate' in expression_lower:
            return "calculation"
        else:
            return "metric"
    
    def _analyze_business_context(self, schema: SemanticModelSchema) -> Dict[str, Any]:
        """Analyze business context and patterns in the model"""
        context = {
            'domains': set(),
            'key_measures': [],
            'fact_tables': [],
            'dimension_tables': [],
            'common_patterns': [],
            'table_relationships': {}
        }
        
        # Analyze table names for business domains
        for table in schema.tables:
            if any(domain in table.name.lower() for domain in ['customer', 'client']):
                context['domains'].add('customer_management')
            elif any(domain in table.name.lower() for domain in ['product', 'item']):
                context['domains'].add('product_management')
            elif any(domain in table.name.lower() for domain in ['sales', 'order', 'transaction']):
                context['domains'].add('sales')
            elif any(domain in table.name.lower() for domain in ['finance', 'accounting', 'budget']):
                context['domains'].add('finance')
        
        # Identify key measures
        for measure in schema.measures:
            if any(key in measure.name.lower() for key in ['revenue', 'profit', 'total sales']):
                context['key_measures'].append(measure.name)
        
        return context
    
    def _classify_tables(self, schema: SemanticModelSchema) -> None:
        """Classify tables as fact or dimension tables"""
        for table in schema.tables:
            # Count numeric vs text columns
            numeric_cols = sum(1 for col in table.columns 
                             if col.data_category == DataTypeCategory.NUMERIC)
            text_cols = sum(1 for col in table.columns 
                           if col.data_category == DataTypeCategory.TEXT)
            
            # Count relationships
            outgoing_rels = sum(1 for rel in schema.relationships 
                              if rel.from_table == table.name)
            incoming_rels = sum(1 for rel in schema.relationships 
                              if rel.to_table == table.name)
            
            # Classification logic
            if numeric_cols > text_cols and incoming_rels > outgoing_rels:
                table.is_fact_table = True
                table.business_domain = "transactional"
            elif text_cols >= numeric_cols and outgoing_rels >= incoming_rels:
                table.is_dimension_table = True
                table.business_domain = "descriptive"
    
    def get_table_summary(self, schema: SemanticModelSchema) -> str:
        """Generate a summary of tables for user display"""
        summary = f"📊 Semantic Model: {schema.model_name}\n"
        summary += f"📂 Workspace: {schema.workspace_name}\n\n"
        
        fact_tables = [t for t in schema.tables if t.is_fact_table]
        dim_tables = [t for t in schema.tables if t.is_dimension_table]
        
        summary += f"🔢 Fact Tables ({len(fact_tables)}):\n"
        for table in fact_tables:
            summary += f"  • {table.name} ({len(table.columns)} columns)\n"
        
        summary += f"\n📋 Dimension Tables ({len(dim_tables)}):\n"
        for table in dim_tables:
            summary += f"  • {table.name} ({len(table.columns)} columns)\n"
        
        summary += f"\n📏 Measures: {len(schema.measures)}\n"
        summary += f"🔗 Relationships: {len(schema.relationships)}\n"
        
        return summary


def test_semantic_analyzer():
    """Test function for semantic analyzer"""
    print("🔍 Testing Semantic Analyzer...")
    
    analyzer = SemanticAnalyzer()
    print("✅ Semantic Analyzer initialized successfully")
    
    # Note: Actual testing requires a connected semantic model
    print("ℹ️  Full testing requires connection to a Power BI semantic model")
    
    return True


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run analyzer test
    test_semantic_analyzer()