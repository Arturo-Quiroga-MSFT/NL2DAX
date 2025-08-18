"""
sempy_dax_generator.py - Intelligent DAX Query Generator
========================================================

This module provides intelligent DAX query generation based on natural language
input and semantic model metadata discovered via SemPy. It uses pattern-based
generation with business context awareness.

Key Features:
- Natural language query analysis and intent detection
- Pattern-based DAX generation (filtering, aggregation, ranking, etc.)
- Semantic model-aware column and measure selection
- Business context integration for intelligent query generation
- Advanced DAX optimization and validation

Author: NL2DAX Pipeline Development Team
Last Updated: August 18, 2025
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .semantic_analyzer import (
    SemanticModelSchema, TableInfo, ColumnInfo, MeasureInfo,
    DataTypeCategory, RelationshipInfo
)

class QueryIntent(Enum):
    """Types of query intents"""
    FILTERING = "filtering"           # Show records matching criteria
    AGGREGATION = "aggregation"      # Sum, count, average, etc.
    RANKING = "ranking"              # Top N, bottom N
    COMPARISON = "comparison"        # Compare values across groups
    TREND_ANALYSIS = "trend"         # Time-based analysis
    CALCULATION = "calculation"      # Custom calculations
    UNKNOWN = "unknown"

class DAXPatternType(Enum):
    """Types of DAX patterns"""
    SIMPLE_FILTER = "simple_filter"
    MEASURE_AGGREGATION = "measure_aggregation"
    TOP_N = "top_n"
    CALCULATE_FILTER = "calculate_filter"
    TIME_INTELLIGENCE = "time_intelligence"
    CUSTOM_CALCULATION = "custom_calculation"

@dataclass
class QueryAnalysis:
    """Analysis of a natural language query"""
    original_query: str
    intent: QueryIntent
    entities: List[str]                # Identified tables, columns, measures
    filters: List[Dict[str, Any]]      # Filter conditions
    aggregations: List[str]            # Requested aggregations
    grouping: List[str]                # Group by fields
    ordering: Optional[str] = None     # Sort requirements
    limit: Optional[int] = None        # Top N requirements
    time_context: Optional[str] = None # Time-related context

@dataclass
class DAXQueryPlan:
    """Execution plan for DAX query generation"""
    analysis: QueryAnalysis
    pattern_type: DAXPatternType
    selected_tables: List[str]
    selected_columns: List[str]
    selected_measures: List[str]
    relationships_used: List[str]
    dax_expression: str
    confidence_score: float

class SemPyDAXGenerator:
    """
    SemPy-powered DAX Query Generator
    
    Generates intelligent DAX queries based on natural language input
    and semantic model metadata from SemPy analysis.
    """
    
    def __init__(self, schema: SemanticModelSchema):
        """
        Initialize the DAX generator with a semantic model schema
        
        Args:
            schema: SemanticModelSchema from semantic analysis
        """
        self.logger = logging.getLogger(__name__)
        self.schema = schema
        
        # Build lookup indexes for fast search
        self._build_indexes()
        
        # Initialize pattern templates
        self._initialize_patterns()
    
    def _build_indexes(self) -> None:
        """Build lookup indexes for tables, columns, and measures"""
        self.table_index = {table.name.lower(): table for table in self.schema.tables}
        
        self.column_index = {}
        self.measure_index = {}
        
        for table in self.schema.tables:
            for column in table.columns:
                key = f"{table.name.lower()}.{column.name.lower()}"
                self.column_index[key] = column
                # Also index by column name alone
                if column.name.lower() not in self.column_index:
                    self.column_index[column.name.lower()] = column
        
        for measure in self.schema.measures:
            self.measure_index[measure.name.lower()] = measure
    
    def _initialize_patterns(self) -> None:
        """Initialize DAX generation patterns"""
        self.dax_patterns = {
            DAXPatternType.SIMPLE_FILTER: {
                'template': "EVALUATE\nFILTER(\n    {table},\n    {filters}\n)",
                'description': "Simple table filtering"
            },
            DAXPatternType.MEASURE_AGGREGATION: {
                'template': "EVALUATE\nSUMMARIZE(\n    {table},\n    {groupby_columns},\n    {measure_expressions}\n)",
                'description': "Measure aggregation with grouping"
            },
            DAXPatternType.TOP_N: {
                'template': "EVALUATE\nTOPN(\n    {limit},\n    {source_expression},\n    {ranking_expression}\n)",
                'description': "Top N ranking"
            },
            DAXPatternType.CALCULATE_FILTER: {
                'template': "EVALUATE\nADDCOLUMNS(\n    {table},\n    {calculated_columns}\n)",
                'description': "Calculated columns with filters"
            },
            DAXPatternType.TIME_INTELLIGENCE: {
                'template': "EVALUATE\nSUMMARIZE(\n    {table},\n    {date_columns},\n    {time_measures}\n)",
                'description': "Time intelligence queries"
            }
        }
    
    def generate_dax_query(self, natural_language_query: str) -> DAXQueryPlan:
        """
        Generate DAX query from natural language input
        
        Args:
            natural_language_query: User's natural language query
            
        Returns:
            DAXQueryPlan with generated DAX and metadata
        """
        try:
            self.logger.info(f"Generating DAX for: {natural_language_query}")
            
            # Analyze the query
            analysis = self._analyze_query(natural_language_query)
            
            # Select appropriate pattern
            pattern_type = self._select_pattern(analysis)
            
            # Generate DAX expression
            dax_expression = self._generate_dax_expression(analysis, pattern_type)
            
            # Create query plan
            plan = DAXQueryPlan(
                analysis=analysis,
                pattern_type=pattern_type,
                selected_tables=self._get_selected_tables(analysis),
                selected_columns=self._get_selected_columns(analysis),
                selected_measures=self._get_selected_measures(analysis),
                relationships_used=self._get_relationships_used(analysis),
                dax_expression=dax_expression,
                confidence_score=self._calculate_confidence(analysis, pattern_type)
            )
            
            self.logger.info(f"DAX generation complete with confidence: {plan.confidence_score:.2f}")
            return plan
            
        except Exception as e:
            self.logger.error(f"Failed to generate DAX query: {e}")
            raise
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze natural language query to extract intent and entities"""
        query_lower = query.lower()
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Extract entities (tables, columns, measures)
        entities = self._extract_entities(query_lower)
        
        # Extract filters
        filters = self._extract_filters(query_lower, entities)
        
        # Extract aggregations
        aggregations = self._extract_aggregations(query_lower)
        
        # Extract grouping
        grouping = self._extract_grouping(query_lower, entities)
        
        # Extract ordering
        ordering = self._extract_ordering(query_lower)
        
        # Extract limit
        limit = self._extract_limit(query_lower)
        
        # Extract time context
        time_context = self._extract_time_context(query_lower)
        
        return QueryAnalysis(
            original_query=query,
            intent=intent,
            entities=entities,
            filters=filters,
            aggregations=aggregations,
            grouping=grouping,
            ordering=ordering,
            limit=limit,
            time_context=time_context
        )
    
    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the primary intent of the query"""
        
        # Ranking patterns
        ranking_patterns = [
            r'top\s+\d+', r'bottom\s+\d+', r'highest', r'lowest',
            r'best\s+\d+', r'worst\s+\d+', r'largest', r'smallest'
        ]
        
        if any(re.search(pattern, query) for pattern in ranking_patterns):
            return QueryIntent.RANKING
        
        # Aggregation patterns
        aggregation_patterns = [
            r'total', r'sum', r'average', r'count', r'maximum', r'minimum',
            r'avg', r'max', r'min', r'aggregate'
        ]
        
        if any(re.search(pattern, query) for pattern in aggregation_patterns):
            return QueryIntent.AGGREGATION
        
        # Filtering patterns (simple show/list/get)
        filtering_patterns = [
            r'show\s+(?:me\s+)?(?:all\s+)?', r'list\s+(?:all\s+)?',
            r'get\s+(?:all\s+)?', r'find\s+(?:all\s+)?',
            r'display\s+(?:all\s+)?'
        ]
        
        if any(re.search(pattern, query) for pattern in filtering_patterns):
            # Check if it's really filtering or aggregation
            if not any(re.search(pattern, query) for pattern in aggregation_patterns):
                return QueryIntent.FILTERING
        
        # Comparison patterns
        comparison_patterns = [
            r'compare', r'versus', r'vs', r'difference', r'between'
        ]
        
        if any(re.search(pattern, query) for pattern in comparison_patterns):
            return QueryIntent.COMPARISON
        
        # Trend analysis patterns
        trend_patterns = [
            r'trend', r'over\s+time', r'by\s+(?:month|year|quarter|week|day)',
            r'timeline', r'progression'
        ]
        
        if any(re.search(pattern, query) for pattern in trend_patterns):
            return QueryIntent.TREND_ANALYSIS
        
        return QueryIntent.UNKNOWN
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract table, column, and measure references from query"""
        entities = []
        
        # Check for table names
        for table_name, table in self.table_index.items():
            if table_name in query:
                entities.append(f"table:{table.name}")
        
        # Check for column names
        for col_key, column in self.column_index.items():
            if col_key in query:
                entities.append(f"column:{column.table_name}.{column.name}")
        
        # Check for measure names
        for measure_name, measure in self.measure_index.items():
            if measure_name in query:
                entities.append(f"measure:{measure.name}")
        
        # Look for business terms that might map to entities
        entities.extend(self._extract_business_terms(query))
        
        return list(set(entities))  # Remove duplicates
    
    def _extract_business_terms(self, query: str) -> List[str]:
        """Extract business terms and map to entities"""
        business_mappings = {
            'customer': ['customer', 'client', 'account'],
            'product': ['product', 'item', 'sku'],
            'sales': ['sales', 'revenue', 'transaction'],
            'country': ['country', 'nation', 'region'],
            'amount': ['amount', 'value', 'total', 'sum'],
            'date': ['date', 'time', 'when', 'period']
        }
        
        entities = []
        for business_term, keywords in business_mappings.items():
            if any(keyword in query for keyword in keywords):
                # Try to find matching entities in schema
                matching_entities = self._find_entities_by_business_term(business_term)
                entities.extend(matching_entities)
        
        return entities
    
    def _find_entities_by_business_term(self, business_term: str) -> List[str]:
        """Find schema entities that match a business term"""
        entities = []
        
        # Search tables
        for table in self.schema.tables:
            if business_term in table.name.lower():
                entities.append(f"table:{table.name}")
        
        # Search columns
        for table in self.schema.tables:
            for column in table.columns:
                if (business_term in column.name.lower() or 
                    business_term == column.business_meaning):
                    entities.append(f"column:{table.name}.{column.name}")
        
        # Search measures
        for measure in self.schema.measures:
            if (business_term in measure.name.lower() or 
                business_term == measure.business_meaning):
                entities.append(f"measure:{measure.name}")
        
        return entities
    
    def _extract_filters(self, query: str, entities: List[str]) -> List[Dict[str, Any]]:
        """Extract filter conditions from query"""
        filters = []
        
        # Common filter patterns
        filter_patterns = [
            r'from\s+(["\']?)([^"\']+)\1',      # from "value"
            r'in\s+(["\']?)([^"\']+)\1',        # in "value"
            r'where\s+([^=]+)=\s*(["\']?)([^"\']+)\2',  # where column = "value"
            r'with\s+([^=]+)=\s*(["\']?)([^"\']+)\2',   # with column = "value"
        ]
        
        for pattern in filter_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    value = match.group(-1)  # Last group is the value
                    filters.append({
                        'type': 'equals',
                        'value': value.strip(),
                        'raw_match': match.group(0)
                    })
        
        return filters
    
    def _extract_aggregations(self, query: str) -> List[str]:
        """Extract aggregation requirements from query"""
        aggregations = []
        
        agg_patterns = {
            'sum': [r'total', r'sum'],
            'count': [r'count', r'number\s+of'],
            'avg': [r'average', r'avg', r'mean'],
            'max': [r'maximum', r'max', r'highest'],
            'min': [r'minimum', r'min', r'lowest']
        }
        
        for agg_type, patterns in agg_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                aggregations.append(agg_type)
        
        return aggregations
    
    def _extract_grouping(self, query: str, entities: List[str]) -> List[str]:
        """Extract group by requirements from query"""
        grouping = []
        
        # Look for "by" patterns
        by_patterns = [
            r'by\s+([a-zA-Z_]+)',
            r'per\s+([a-zA-Z_]+)',
            r'for\s+each\s+([a-zA-Z_]+)'
        ]
        
        for pattern in by_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                group_field = match.group(1)
                grouping.append(group_field)
        
        return grouping
    
    def _extract_ordering(self, query: str) -> Optional[str]:
        """Extract ordering requirements from query"""
        if re.search(r'order\s+by|sort\s+by', query, re.IGNORECASE):
            if re.search(r'desc|descending|highest|largest', query, re.IGNORECASE):
                return 'DESC'
            else:
                return 'ASC'
        
        # Implicit ordering from top/bottom patterns
        if re.search(r'top|highest|largest|best', query, re.IGNORECASE):
            return 'DESC'
        elif re.search(r'bottom|lowest|smallest|worst', query, re.IGNORECASE):
            return 'ASC'
        
        return None
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract limit/top N requirements from query"""
        # Look for explicit numbers
        limit_patterns = [
            r'top\s+(\d+)',
            r'first\s+(\d+)',
            r'bottom\s+(\d+)',
            r'last\s+(\d+)',
            r'(\d+)\s+(?:highest|lowest|best|worst)'
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_time_context(self, query: str) -> Optional[str]:
        """Extract time-related context from query"""
        time_patterns = [
            r'this\s+year', r'current\s+year', r'2024', r'2025',
            r'last\s+month', r'this\s+month', r'current\s+month',
            r'by\s+month', r'by\s+year', r'by\s+quarter'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _select_pattern(self, analysis: QueryAnalysis) -> DAXPatternType:
        """Select appropriate DAX pattern based on query analysis"""
        
        if analysis.intent == QueryIntent.RANKING and analysis.limit:
            return DAXPatternType.TOP_N
        
        elif analysis.intent == QueryIntent.AGGREGATION:
            if analysis.time_context:
                return DAXPatternType.TIME_INTELLIGENCE
            else:
                return DAXPatternType.MEASURE_AGGREGATION
        
        elif analysis.intent == QueryIntent.FILTERING:
            if analysis.filters:
                return DAXPatternType.SIMPLE_FILTER
            else:
                return DAXPatternType.SIMPLE_FILTER  # Default to simple filter
        
        elif analysis.intent == QueryIntent.CALCULATION:
            return DAXPatternType.CALCULATE_FILTER
        
        else:
            # Default fallback
            if analysis.aggregations:
                return DAXPatternType.MEASURE_AGGREGATION
            else:
                return DAXPatternType.SIMPLE_FILTER
    
    def _generate_dax_expression(self, analysis: QueryAnalysis, pattern_type: DAXPatternType) -> str:
        """Generate the actual DAX expression"""
        
        if pattern_type == DAXPatternType.SIMPLE_FILTER:
            return self._generate_simple_filter_dax(analysis)
        
        elif pattern_type == DAXPatternType.MEASURE_AGGREGATION:
            return self._generate_measure_aggregation_dax(analysis)
        
        elif pattern_type == DAXPatternType.TOP_N:
            return self._generate_top_n_dax(analysis)
        
        elif pattern_type == DAXPatternType.CALCULATE_FILTER:
            return self._generate_calculate_filter_dax(analysis)
        
        elif pattern_type == DAXPatternType.TIME_INTELLIGENCE:
            return self._generate_time_intelligence_dax(analysis)
        
        else:
            return self._generate_simple_filter_dax(analysis)  # Fallback
    
    def _generate_simple_filter_dax(self, analysis: QueryAnalysis) -> str:
        """Generate simple filtering DAX"""
        
        # Find the primary table
        primary_table = self._get_primary_table(analysis)
        
        if not primary_table:
            raise ValueError("Could not identify primary table for query")
        
        # Build filter conditions
        filter_conditions = []
        for filter_item in analysis.filters:
            # Try to map filter value to a column
            column = self._find_column_for_filter(filter_item['value'], primary_table)
            if column:
                if column.data_category == DataTypeCategory.TEXT:
                    condition = f'{primary_table}[{column.name}] = "{filter_item["value"]}"'
                else:
                    condition = f'{primary_table}[{column.name}] = {filter_item["value"]}'
                filter_conditions.append(condition)
        
        if filter_conditions:
            filters_expr = ' && '.join(filter_conditions)
            return f"""EVALUATE
FILTER(
    {primary_table},
    {filters_expr}
)"""
        else:
            # No specific filters, return all records
            return f"""EVALUATE
{primary_table}"""
    
    def _generate_measure_aggregation_dax(self, analysis: QueryAnalysis) -> str:
        """Generate measure aggregation DAX"""
        
        primary_table = self._get_primary_table(analysis)
        if not primary_table:
            raise ValueError("Could not identify primary table for query")
        
        # Find grouping columns
        groupby_columns = []
        for entity in analysis.entities:
            if entity.startswith('column:'):
                col_ref = entity.replace('column:', '')
                groupby_columns.append(self._to_bracketed_column(col_ref, preferred_table=primary_table))
        
        # Find measures or create aggregations
        measure_expressions = []
        for entity in analysis.entities:
            if entity.startswith('measure:'):
                measure_name = entity.replace('measure:', '')
                measure_expressions.append(f'"{measure_name}", [{measure_name}]')
        
        # If no explicit measures, create based on aggregation intent
        if not measure_expressions and analysis.aggregations:
            for agg_type in analysis.aggregations:
                if agg_type == 'count':
                    measure_expressions.append(f'"Row Count", COUNTROWS({primary_table})')
        
        if groupby_columns and measure_expressions:
            groupby_expr = ',\n    '.join(groupby_columns)
            measures_expr = ',\n    '.join(measure_expressions)
            
            return f"""EVALUATE
SUMMARIZE(
    {primary_table},
    {groupby_expr},
    {measures_expr}
)"""
        else:
            # Fallback to simple aggregation
            return f"""EVALUATE
SUMMARIZE(
    {primary_table},
    "Total Rows", COUNTROWS({primary_table})
)"""
    
    def _generate_top_n_dax(self, analysis: QueryAnalysis) -> str:
        """Generate Top N ranking DAX"""
        
        primary_table = self._get_primary_table(analysis)
        if not primary_table:
            raise ValueError("Could not identify primary table for query")
        
        limit = analysis.limit or 10
        
        # Find ranking column/measure
        ranking_expr = self._get_ranking_expression(analysis, primary_table)
        
        # Create source expression (could be filtered table)
        source_expr = primary_table
        if analysis.filters:
            filter_conditions = []
            for filter_item in analysis.filters:
                column = self._find_column_for_filter(filter_item['value'], primary_table)
                if column:
                    condition = f'{primary_table}[{column.name}] = "{filter_item["value"]}"'
                    filter_conditions.append(condition)
            
            if filter_conditions:
                filters_expr = ' && '.join(filter_conditions)
                source_expr = f'FILTER({primary_table}, {filters_expr})'
        
        return f"""EVALUATE
TOPN(
    {limit},
    {source_expr},
    {ranking_expr}
)"""
    
    def _generate_calculate_filter_dax(self, analysis: QueryAnalysis) -> str:
        """Generate DAX with calculated columns"""
        return self._generate_simple_filter_dax(analysis)  # Simplified for now
    
    def _generate_time_intelligence_dax(self, analysis: QueryAnalysis) -> str:
        """Generate time intelligence DAX"""
        primary_table = self._get_primary_table(analysis)
        if not primary_table:
            raise ValueError("Could not identify primary table for time analysis")

        # Identify a date table/columns
        date_table = None
        date_columns = {
            'date': None,
            'year': None,
            'month': None,
            'quarter': None
        }

        for t in self.schema.tables:
            for c in t.columns:
                cname = c.name.lower()
                if c.data_category == DataTypeCategory.DATE or any(k in cname for k in ['date', 'year', 'month', 'quarter']):
                    date_table = date_table or t.name
                    if 'year' in cname and not date_columns['year']:
                        date_columns['year'] = f"{t.name}[{c.name}]"
                    if 'month' in cname and not date_columns['month']:
                        date_columns['month'] = f"{t.name}[{c.name}]"
                    if 'quarter' in cname and not date_columns['quarter']:
                        date_columns['quarter'] = f"{t.name}[{c.name}]"
                    if 'date' in cname and not date_columns['date']:
                        date_columns['date'] = f"{t.name}[{c.name}]"

        if not date_table:
            # Fallback to generic aggregation if no date context
            return self._generate_measure_aggregation_dax(analysis)

        # Choose grouping based on detected time context
        group_cols: List[str] = []
        q = (analysis.time_context or '').lower()
        if 'by year' in q and date_columns['year']:
            group_cols.append(date_columns['year'])
        if 'by quarter' in q and date_columns['quarter']:
            group_cols.append(date_columns['quarter'])
        if 'by month' in q and date_columns['month']:
            group_cols.append(date_columns['month'])

        # If no explicit "by" groupings found, prefer Year then Month then Date
        if not group_cols:
            for key in ['year', 'month', 'date']:
                if date_columns[key] and date_columns[key] not in group_cols:
                    group_cols.append(date_columns[key])
                    # keep it concise: year+month if both exist
                    if key == 'year' and date_columns['month']:
                        group_cols.append(date_columns['month'])
                    break

        # Measures: use explicit measures if present, else fallback to row count over primary table
        measure_expressions = []
        for entity in analysis.entities:
            if entity.startswith('measure:'):
                mname = entity.replace('measure:', '')
                measure_expressions.append(f'"{mname}", [{mname}]')
        if not measure_expressions:
            measure_expressions.append(f'"Total Rows", COUNTROWS({primary_table})')

        date_cols_expr = ',\n    '.join(group_cols)
        measures_expr = ',\n    '.join(measure_expressions)

        return f"""EVALUATE
SUMMARIZECOLUMNS(
    {date_cols_expr},
    {measures_expr}
)"""
    
    def _get_primary_table(self, analysis: QueryAnalysis) -> Optional[str]:
        """Identify the primary table for the query"""
        
        # Look for explicit table references
        for entity in analysis.entities:
            if entity.startswith('table:'):
                return entity.replace('table:', '')
        
        # Infer from column references
        table_counts = {}
        for entity in analysis.entities:
            if entity.startswith('column:'):
                col_ref = entity.replace('column:', '')
                if '.' in col_ref:
                    table_name = col_ref.split('.')[0]
                    table_counts[table_name] = table_counts.get(table_name, 0) + 1
        
        if table_counts:
            return max(table_counts.items(), key=lambda x: x[1])[0]
        
        # Default to first fact table if available
        fact_tables = [t for t in self.schema.tables if t.is_fact_table]
        if fact_tables:
            return fact_tables[0].name
        
        # Fallback to first table
        if self.schema.tables:
            return self.schema.tables[0].name
        
        return None
    
    def _find_column_for_filter(self, filter_value: str, table_name: str) -> Optional[ColumnInfo]:
        """Find the most likely column for a filter value"""
        
        table = self.table_index.get(table_name.lower())
        if not table:
            return None
        
        # Look for columns that might contain this value
        # Priority: string columns, then columns with business meaning
        candidates = []
        
        for column in table.columns:
            if column.data_category == DataTypeCategory.TEXT:
                candidates.append((column, 10))  # High priority for text columns
            elif column.business_meaning in ['descriptor', 'geographic', 'status']:
                candidates.append((column, 5))   # Medium priority for descriptive columns
        
        if candidates:
            # Return highest priority column
            return max(candidates, key=lambda x: x[1])[0]
        
        # Fallback to first text column
        text_columns = [col for col in table.columns 
                       if col.data_category == DataTypeCategory.TEXT]
        if text_columns:
            return text_columns[0]
        
        return None
    
    def _get_ranking_expression(self, analysis: QueryAnalysis, table_name: str) -> str:
        """Get expression for ranking in Top N queries"""
        
        # Look for measures first
        for entity in analysis.entities:
            if entity.startswith('measure:'):
                measure_name = entity.replace('measure:', '')
                return f'[{measure_name}]'
        
        # Look for numeric columns
        table = self.table_index.get(table_name.lower())
        if table:
            numeric_columns = [col for col in table.columns 
                             if col.data_category == DataTypeCategory.NUMERIC]
            if numeric_columns:
                return f'{table_name}[{numeric_columns[0].name}]'
        
        # Default fallback
        return f'COUNTROWS({table_name})'
    
    def _get_selected_tables(self, analysis: QueryAnalysis) -> List[str]:
        """Get list of tables used in the query"""
        tables = []
        for entity in analysis.entities:
            if entity.startswith('table:'):
                tables.append(entity.replace('table:', ''))
            elif entity.startswith('column:'):
                col_ref = entity.replace('column:', '')
                if '.' in col_ref:
                    tables.append(col_ref.split('.')[0])
        
        primary_table = self._get_primary_table(analysis)
        if primary_table and primary_table not in tables:
            tables.append(primary_table)
        
        return list(set(tables))
    
    def _get_selected_columns(self, analysis: QueryAnalysis) -> List[str]:
        """Get list of columns used in the query"""
        columns = []
        preferred_table = self._get_primary_table(analysis)
        for entity in analysis.entities:
            if entity.startswith('column:'):
                columns.append(self._to_bracketed_column(entity.replace('column:', ''), preferred_table=preferred_table))
        return columns
    
    def _get_selected_measures(self, analysis: QueryAnalysis) -> List[str]:
        """Get list of measures used in the query"""
        measures = []
        for entity in analysis.entities:
            if entity.startswith('measure:'):
                measures.append(entity.replace('measure:', ''))
        return measures
    
    def _get_relationships_used(self, analysis: QueryAnalysis) -> List[str]:
        """Get list of relationships that might be used"""
        # This would analyze which relationships are needed
        # Simplified for now
        return []
    
    def _calculate_confidence(self, analysis: QueryAnalysis, pattern_type: DAXPatternType) -> float:
        """Calculate confidence score for the generated query"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on entity recognition
        if analysis.entities:
            confidence += 0.2
        
        # Boost based on clear intent
        if analysis.intent != QueryIntent.UNKNOWN:
            confidence += 0.2
        
        # Boost based on pattern match
        if pattern_type != DAXPatternType.SIMPLE_FILTER:
            confidence += 0.1
        
        return min(confidence, 1.0)

    def _to_bracketed_column(self, col_ref: str, preferred_table: Optional[str] = None) -> str:
        """Convert 'Table.Column' or 'Table[Column]' or 'Column' into 'Table[Column]' when possible.
        Prefer the provided preferred_table when ambiguous.
        """
        # Already bracketed
        if '[' in col_ref and ']' in col_ref:
            return col_ref
        parts = col_ref.split('.')
        if len(parts) == 2:
            table, column = parts
            return f"{table}[{column}]"
        if len(parts) == 1:
            # Try to resolve unique column across schema
            target = parts[0].lower()
            # Prefer preferred_table if it contains the column
            if preferred_table:
                t = self.table_index.get(preferred_table.lower())
                if t:
                    for c in t.columns:
                        if c.name.lower() == target:
                            return f"{t.name}[{c.name}]"
            matches = []
            for t in self.schema.tables:
                for c in t.columns:
                    if c.name.lower() == target:
                        matches.append((t.name, c.name))
            if len(matches) == 1:
                tname, cname = matches[0]
                return f"{tname}[{cname}]"
            # If ambiguous or not found, return original to avoid incorrect DAX
            return col_ref
        return col_ref

    # -----------------------
    # DAX validation helpers
    # -----------------------
    def validate_generated_dax(self, dax_expression: str) -> Dict[str, Any]:
        """Lightweight validator for generated DAX.
        Checks: EVALUATE presence, balanced () and [], entity existence.
        Returns dict: { is_valid: bool, errors: [], warnings: [] }
        """
        errors: List[str] = []
        warnings: List[str] = []

        # EVALUATE presence (most query patterns require it)
        if 'evaluate' not in dax_expression.lower():
            warnings.append("DAX does not contain EVALUATE; ensure the expression returns a table.")

        # Balanced parentheses and brackets
        def _balanced(s: str, open_ch: str, close_ch: str) -> bool:
            cnt = 0
            for ch in s:
                if ch == open_ch:
                    cnt += 1
                elif ch == close_ch:
                    cnt -= 1
                    if cnt < 0:
                        return False
            return cnt == 0

        if not _balanced(dax_expression, '(', ')'):
            errors.append("Unbalanced parentheses () in DAX.")
        if not _balanced(dax_expression, '[', ']'):
            errors.append("Unbalanced brackets [] in DAX.")

        # Validate Table[Column] references and [Measure] tokens
        # Find Table[Column]
        table_col_refs = re.findall(r"([A-Za-z_][\w ]*)\[([^\[\]]+)\]", dax_expression)
        for tname, cname in table_col_refs:
            # Skip if this is actually a measure like [Measure] (no table name)
            if tname.strip().startswith('['):
                continue
            table = self.table_index.get(tname.strip().lower())
            if not table:
                warnings.append(f"Referenced table not found in schema: {tname}")
                continue
            if not any(c.name == cname for c in table.columns):
                warnings.append(f"Column {tname}[{cname}] not found in schema.")

        # Find [Measure] tokens (that aren't part of Table[Column])
        # First remove Table[Column] matches to avoid double counting
        tmp = re.sub(r"[A-Za-z_][\w ]*\[[^\[\]]+\]", "", dax_expression)
        measure_refs = re.findall(r"\[([^\[\]]+)\]", tmp)
        for mname in measure_refs:
            if mname.strip().lower() not in self.measure_index:
                warnings.append(f"Measure not found in schema: [{mname}]")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


def test_sempy_dax_generator():
    """Test function for SemPy DAX generator"""
    print("🎯 Testing SemPy DAX Generator...")
    
    # Note: This would need a real semantic model schema for full testing
    print("ℹ️  Full testing requires a semantic model schema from semantic analysis")
    
    return True


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run generator test
    test_sempy_dax_generator()