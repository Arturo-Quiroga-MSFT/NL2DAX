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
import os

try:
    import yaml  # type: ignore
    YAML_AVAILABLE = True
except Exception:
    YAML_AVAILABLE = False

try:
    import sempy.fabric as fabric
    from sempy.fabric import list_tables, list_columns, list_measures, list_relationships
    SEMPY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SemPy not available: {e}")
    SEMPY_AVAILABLE = False

# REST fallback imports
try:
    from ..config.fabric_config import FabricConfig
    from .fabric_auth_provider import FabricApiClient, create_fabric_token_provider
    FABRIC_REST_AVAILABLE = True
except Exception as e:
    logging.warning(f"Fabric REST fallback not fully available: {e}")
    FABRIC_REST_AVAILABLE = False

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
        # Allow initialization even if SemPy is unavailable; we'll use REST fallback.
        if not SEMPY_AVAILABLE:
            self.logger.warning("SemPy not available; will attempt REST DMV fallback for metadata.")
    
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
            
            # Discover via SemPy first
            schema.tables = self._discover_tables(model_name, workspace_name)
            schema.relationships = self._discover_relationships(model_name, workspace_name)
            schema.measures = self._discover_measures(model_name, workspace_name)

            # If SemPy discovery failed (empty), try REST DMV fallback
            if (not schema.tables or not schema.measures) and FABRIC_REST_AVAILABLE:
                self.logger.info("SemPy metadata discovery incomplete; attempting REST DMV fallback...")
                rest_meta = self._discover_metadata_via_rest(model_name, workspace_name)
                if rest_meta:
                    schema.tables = rest_meta.get('tables', schema.tables)
                    schema.relationships = rest_meta.get('relationships', schema.relationships)
                    schema.measures = rest_meta.get('measures', schema.measures)

            # If still empty, try offline schema overrides (YAML/JSON) to allow progress without live metadata
            if not schema.tables or not schema.measures:
                overrides = self._load_schema_overrides()
                if overrides:
                    self.logger.info("Loaded schema overrides from configuration file.")
                    schema.tables = overrides.get('tables', schema.tables)
                    schema.relationships = overrides.get('relationships', schema.relationships)
                    schema.measures = overrides.get('measures', schema.measures)
            
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

    def _load_schema_overrides(self) -> Optional[Dict[str, List[Any]]]:
        """
        Load schema overrides from configuration files to enable offline operation when
        SemPy and REST DMV discovery are unavailable (e.g., missing XMLA permissions).

        Looks for files in prioritized order:
        - SEMPY_DAX_ENGINE/config/schema_overrides.yaml
        - SEMPY_DAX_ENGINE/config/schema_overrides.json
        - config/schema_overrides.yaml (repo root)
        - config/schema_overrides.json (repo root)

        Expected structure:
        tables: [{ name, type, columns: [{ name, data_type }] }]
        measures: [{ table_name, name, expression, data_type }]
        relationships: [{ from_table, from_column, to_table, to_column, relationship_type, is_active, cross_filter_direction }]
        """
        try:
            candidates = [
                os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_overrides.yaml'),
                os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_overrides.json'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'schema_overrides.yaml'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'schema_overrides.json'),
            ]
            candidates = [os.path.abspath(p) for p in candidates]

            path = next((p for p in candidates if os.path.exists(p)), None)
            if not path:
                self.logger.info("No schema overrides file found.")
                return None

            self.logger.info(f"Loading schema overrides from: {path}")
            data: Dict[str, Any] = {}
            if path.endswith('.yaml') or path.endswith('.yml'):
                if not YAML_AVAILABLE:
                    self.logger.warning("PyYAML not installed; cannot read YAML overrides.")
                    return None
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
            else:
                import json
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}

            # Convert dicts into dataclass instances
            tables: List[TableInfo] = []
            for t in data.get('tables', []) or []:
                cols = []
                for c in t.get('columns', []) or []:
                    dtype = str(c.get('data_type', ''))
                    cols.append(ColumnInfo(
                        name=str(c.get('name', '')),
                        table_name=str(t.get('name', '')),
                        data_type=dtype,
                        data_category=self._categorize_data_type(dtype)
                    ))
                tables.append(TableInfo(
                    name=str(t.get('name', '')),
                    type=str(t.get('type', 'Table')),
                    description=t.get('description'),
                    row_count=t.get('row_count'),
                    columns=cols
                ))

            measures: List[MeasureInfo] = []
            for m in data.get('measures', []) or []:
                measures.append(MeasureInfo(
                    name=str(m.get('name', '')),
                    table_name=str(m.get('table_name', '')),
                    expression=str(m.get('expression', '')),
                    data_type=str(m.get('data_type', '')),
                    format_string=m.get('format_string'),
                    description=m.get('description'),
                    folder=m.get('folder'),
                    is_hidden=bool(m.get('is_hidden', False))
                ))

            relationships: List[RelationshipInfo] = []
            for r in data.get('relationships', []) or []:
                rel_type = r.get('relationship_type', '1:*')
                # Normalize relationship type
                try:
                    if rel_type in (RelationshipType.ONE_TO_MANY.value, RelationshipType.MANY_TO_ONE.value,
                                    RelationshipType.ONE_TO_ONE.value, RelationshipType.MANY_TO_MANY.value):
                        rt_enum = RelationshipType(rel_type)
                    else:
                        rt_enum = RelationshipType.ONE_TO_MANY
                except Exception:
                    rt_enum = RelationshipType.ONE_TO_MANY
                relationships.append(RelationshipInfo(
                    from_table=str(r.get('from_table', '')),
                    from_column=str(r.get('from_column', '')),
                    to_table=str(r.get('to_table', '')),
                    to_column=str(r.get('to_column', '')),
                    relationship_type=rt_enum,
                    is_active=bool(r.get('is_active', True)),
                    cross_filter_direction=str(r.get('cross_filter_direction', 'Single'))
                ))

            return {
                'tables': tables,
                'measures': measures,
                'relationships': relationships,
            }
        except Exception as e:
            self.logger.error(f"Failed to load schema overrides: {e}")
            return None
    
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

    # ------------------------------
    # REST DMV FALLBACK IMPLEMENTATION
    # ------------------------------
    def _discover_metadata_via_rest(self, model_name: str, workspace_name: str) -> Optional[Dict[str, Any]]:
        """Discover tables, columns, measures, and relationships using Power BI Execute Queries (DMVs).
        Returns dict with keys: tables, columns, measures, relationships (lists of dataclass instances).
        """
        try:
            client, group_id, dataset_id = self._get_rest_client_and_ids(model_name, workspace_name)
            if not client or not group_id or not dataset_id:
                self.logger.warning("REST fallback: could not resolve client/group/dataset IDs.")
                return None

            # Query DMVs
            tables_rows = self._dmv_query(client, dataset_id, group_id, "TMSCHEMA_TABLES")
            columns_rows = self._dmv_query(client, dataset_id, group_id, "TMSCHEMA_COLUMNS")
            measures_rows = self._dmv_query(client, dataset_id, group_id, "TMSCHEMA_MEASURES")
            rel_rows = self._dmv_query(client, dataset_id, group_id, "TMSCHEMA_RELATIONSHIPS")

            # Build lookup maps
            table_by_id: Dict[int, Dict[str, Any]] = {}
            for r in tables_rows:
                # Expect keys like 'ID', 'Name', 'IsHidden', 'Type'
                tid = r.get('ID') or r.get('Id') or r.get('TableID')
                if tid is not None:
                    table_by_id[int(tid)] = r

            col_by_id: Dict[int, Dict[str, Any]] = {}
            cols_by_table_id: Dict[int, List[Dict[str, Any]]] = {}
            for r in columns_rows:
                cid = r.get('ID') or r.get('Id') or r.get('ColumnID')
                tid = r.get('TableID')
                if cid is not None:
                    col_by_id[int(cid)] = r
                if tid is not None:
                    cols_by_table_id.setdefault(int(tid), []).append(r)

            # Tables
            tables: List[TableInfo] = []
            for tid, trow in table_by_id.items():
                tname = trow.get('Name') or trow.get('Table') or f"Table_{tid}"
                ttype = trow.get('Type', 'Table')
                table = TableInfo(name=tname, type=str(ttype), columns=[])
                # Attach columns if present
                for crow in cols_by_table_id.get(tid, []):
                    cname = crow.get('Name') or crow.get('Column') or f"Column_{crow.get('ID', '')}"
                    dtype = crow.get('DataType') or crow.get('Type') or ''
                    table.columns.append(ColumnInfo(
                        name=str(cname),
                        table_name=tname,
                        data_type=str(dtype),
                        data_category=self._categorize_data_type(str(dtype))
                    ))
                tables.append(table)

            # Measures
            measures: List[MeasureInfo] = []
            for mrow in measures_rows:
                mname = mrow.get('Name') or 'Measure'
                mtable_id = mrow.get('TableID')
                mexpr = mrow.get('Expression') or mrow.get('Definition') or ''
                mdatatype = mrow.get('DataType') or ''
                mtable_name = table_by_id.get(int(mtable_id), {}).get('Name') if mtable_id is not None else ''
                measures.append(MeasureInfo(
                    name=str(mname),
                    table_name=str(mtable_name or ''),
                    expression=str(mexpr),
                    data_type=str(mdatatype)
                ))

            # Relationships (best-effort)
            relationships: List[RelationshipInfo] = []
            for r in rel_rows:
                ftid = r.get('FromTableID')
                fcid = r.get('FromColumnID')
                ttid = r.get('ToTableID')
                tcid = r.get('ToColumnID')
                from_table = table_by_id.get(int(ftid), {}).get('Name') if ftid is not None else ''
                to_table = table_by_id.get(int(ttid), {}).get('Name') if ttid is not None else ''
                from_column = col_by_id.get(int(fcid), {}).get('Name') if fcid is not None else ''
                to_column = col_by_id.get(int(tcid), {}).get('Name') if tcid is not None else ''
                relationships.append(RelationshipInfo(
                    from_table=str(from_table),
                    from_column=str(from_column),
                    to_table=str(to_table),
                    to_column=str(to_column),
                    relationship_type=self._parse_relationship_type(r.get('FromCardinality', ''), r.get('ToCardinality', '')),
                    is_active=bool(r.get('IsActive', True)),
                    cross_filter_direction=str(r.get('CrossFilterDirection', 'Single'))
                ))

            return {
                'tables': tables,
                'relationships': relationships,
                'measures': measures,
            }

        except Exception as e:
            self.logger.error(f"REST DMV fallback failed: {e}")
            return None

    def _get_rest_client_and_ids(self, model_name: str, workspace_name: str):
        """Resolve REST client, group (workspace) ID, and dataset ID by names."""
        try:
            cfg = FabricConfig.from_env()
            token_provider = create_fabric_token_provider(cfg)
            client = FabricApiClient(token_provider)
            # Find group id by workspace name
            groups = client.list_groups()
            group_id = None
            for g in groups:
                if str(g.get('name', '')).lower() == workspace_name.lower():
                    group_id = g.get('id')
                    break
            if not group_id:
                # Try configured workspace id
                group_id = cfg.workspace_id

            # Find dataset id by name within group
            ds = client.list_datasets(group_id)
            dataset_id = None
            for d in ds:
                if str(d.get('name', '')).lower() == model_name.lower():
                    dataset_id = d.get('id')
                    break
            if not dataset_id:
                # Fallback to configured dataset id
                dataset_id = cfg.dataset_id

            return client, group_id, dataset_id
        except Exception as e:
            self.logger.error(f"Failed to resolve REST client/IDs: {e}")
            return None, None, None

    def _dmv_query(self, client: 'FabricApiClient', dataset_id: str, group_id: str, dmv_name: str) -> List[Dict[str, Any]]:
        """Execute a DMV query via executeQueries and return list of row dicts."""
        dax = f"EVALUATE {dmv_name}"
        resp = client.execute_dax(dataset_id, dax, group_id)
        if not resp or 'error' in resp:
            self.logger.warning(f"DMV query failed for {dmv_name}: {resp.get('error') if isinstance(resp, dict) else resp}")
            return []
        try:
            results = resp.get('results', [])
            if not results:
                return []
            tables = results[0].get('tables', [])
            if not tables:
                return []
            rows = tables[0].get('rows', [])
            # Expect list of dicts
            if rows and isinstance(rows[0], dict):
                return rows
            # If rows are arrays, map using columns metadata
            cols_meta = tables[0].get('columns', [])
            col_names = [c.get('name') for c in cols_meta]
            mapped = []
            for arr in rows:
                mapped.append({col_names[i]: arr[i] for i in range(min(len(arr), len(col_names)))})
            return mapped
        except Exception as e:
            self.logger.error(f"Failed to parse DMV response for {dmv_name}: {e}")
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