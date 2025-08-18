"""
Clean DAX Generator - Best practices DAX generation
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schema_manager import SchemaManager, SchemaTable

@dataclass
class DAXGenerationRequest:
    """Request for DAX generation"""
    business_intent: str
    limit: int = 10
    analysis_type: str = "customer_analysis"

@dataclass 
class DAXGenerationResult:
    """Result of DAX generation"""
    dax_query: str
    confidence_score: float
    pattern_used: str
    tables_referenced: List[str]
    validation_warnings: List[str]

class CleanDAXGenerator:
    """Clean DAX generator with embedded best practices"""
    
    def __init__(self, schema_manager: SchemaManager):
        self.schema_manager = schema_manager
        self.patterns = self._initialize_patterns()
    
    def generate_dax(self, request: DAXGenerationRequest) -> DAXGenerationResult:
        """Generate DAX query following best practices"""
        schema = self.schema_manager.get_schema()
        
        # Analyze the business intent
        analysis = self._analyze_intent(request.business_intent, schema)
        
        # Select appropriate pattern
        pattern = self._select_pattern(analysis, schema)
        
        # Generate the DAX query
        dax_query = self._generate_from_pattern(pattern, analysis, request.limit)
        
        # Validate against schema
        warnings = self._validate_schema_references(dax_query, schema)
        
        return DAXGenerationResult(
            dax_query=dax_query,
            confidence_score=analysis['confidence'],
            pattern_used=pattern['name'],
            tables_referenced=analysis['tables'],
            validation_warnings=warnings
        )
    
    def _analyze_intent(self, intent: str, schema) -> Dict[str, Any]:
        """Analyze business intent to determine query structure"""
        intent_lower = intent.lower()
        
        analysis = {
            'intent_type': 'ranking',  # ranking, filtering, aggregation, detail
            'target_entity': 'customer',  # customer, product, transaction, etc.
            'measures': [],
            'dimensions': [],
            'tables': [],
            'confidence': 0.8
        }
        
        # Detect ranking queries
        if any(word in intent_lower for word in ['top', 'highest', 'largest', 'best', 'worst', 'lowest']):
            analysis['intent_type'] = 'ranking'
        
        # Detect customer focus
        if 'customer' in intent_lower:
            analysis['target_entity'] = 'customer'
            # Find customer-related tables
            customer_tables = [name for name in schema.tables.keys() 
                             if 'customer' in name.lower()]
            analysis['tables'].extend(customer_tables)
        
        # Detect exposure/financial measures
        if any(word in intent_lower for word in ['exposure', 'balance', 'amount', 'total', 'sum']):
            # Find fact tables with exposure columns - be selective for primary exposure measures
            for table_name, table_info in schema.tables.items():
                if table_info.table_type == 'fact':
                    # Prioritize key exposure measures
                    if 'exposure' in intent_lower:
                        # For exposure queries, focus on EXPOSURE_AT_DEFAULT
                        exposure_cols = [col for col in table_info.columns 
                                       if col.upper() == 'EXPOSURE_AT_DEFAULT']
                    else:
                        # For general financial queries, use primary balance/amount columns
                        exposure_cols = [col for col in table_info.columns 
                                       if col.upper() in ['TOTAL_BALANCE', 'PRINCIPAL_BALANCE', 'CURRENT_PRINCIPAL_BALANCE', 'ORIGINAL_AMOUNT']]
                    
                    if exposure_cols:
                        analysis['measures'].extend([(table_name, col) for col in exposure_cols])
                        if table_name not in analysis['tables']:
                            analysis['tables'].append(table_name)
        
        return analysis
    
    def _select_pattern(self, analysis: Dict[str, Any], schema) -> Dict[str, Any]:
        """Select the best DAX pattern for the analysis"""
        
        if analysis['intent_type'] == 'ranking' and analysis['target_entity'] == 'customer':
            if len([t for t in analysis['tables'] if schema.tables[t].table_type == 'fact']) > 1:
                return self.patterns['multi_fact_customer_ranking']
            else:
                return self.patterns['single_fact_customer_ranking']
        
        # Default pattern
        return self.patterns['basic_aggregation']
    
    def _generate_from_pattern(self, pattern: Dict[str, Any], analysis: Dict[str, Any], limit: int) -> str:
        """Generate DAX query from selected pattern"""
        template = pattern['template']
        
        # Get schema info
        schema = self.schema_manager.get_schema()
        
        # Find the primary fact table
        fact_tables = [t for t in analysis['tables'] if schema.tables[t].table_type == 'fact']
        primary_fact = fact_tables[0] if fact_tables else None
        
        # Find customer dimension
        customer_dim = None
        for table_name in schema.tables.keys():
            if 'customer' in table_name.lower() and 'dimension' in table_name.lower():
                customer_dim = table_name
                break
        
        # Find measure columns
        measure_expressions = []
        if analysis['measures']:
            for table, column in analysis['measures']:
                measure_expressions.append(f"CALCULATE(SUM('{table}'[{column}]))")
        
        # Apply template substitutions
        substitutions = {
            'LIMIT': str(limit),
            'FACT_TABLE': primary_fact or 'Unknown',
            'CUSTOMER_DIM': customer_dim or 'Unknown',
            'MEASURE_EXPRESSION': ' + '.join(measure_expressions) if measure_expressions else 'CALCULATE(SUM(Unknown[Amount]))',
            'CUSTOMER_KEY_COL': self._find_customer_key_column(customer_dim, schema) if customer_dim else 'CUSTOMER_KEY',
            'CUSTOMER_NAME_COL': 'CUSTOMER_NAME'
        }
        
        dax_query = template
        for placeholder, value in substitutions.items():
            dax_query = dax_query.replace(f'{{{placeholder}}}', value)
        
        return dax_query
    
    def _find_customer_key_column(self, table_name: str, schema) -> str:
        """Find the customer key column in a table"""
        table = schema.tables.get(table_name)
        if not table:
            return 'CUSTOMER_KEY'
        
        # Look for customer key patterns
        for col in table.columns:
            if 'customer' in col.lower() and 'key' in col.lower():
                return col
            if 'customer' in col.lower() and 'id' in col.lower():
                return col
        
        return 'CUSTOMER_KEY'  # fallback
    
    def _validate_schema_references(self, dax_query: str, schema) -> List[str]:
        """Validate that all referenced tables and columns exist"""
        warnings = []
        
        # Extract table references (looking for 'TableName' patterns)
        import re
        table_refs = re.findall(r"'([^']+)'", dax_query)
        
        for table_ref in table_refs:
            if not self.schema_manager.validate_table_exists(table_ref):
                warnings.append(f"Table '{table_ref}' not found in schema")
        
        return warnings
    
    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize proven DAX patterns"""
        return {
            'single_fact_customer_ranking': {
                'name': 'Single Fact Customer Ranking',
                'description': 'Customer ranking from a single fact table',
                'template': '''EVALUATE
TOPN(
    {LIMIT},
    ADDCOLUMNS(
        SUMMARIZE(
            '{CUSTOMER_DIM}',
            '{CUSTOMER_DIM}'[{CUSTOMER_KEY_COL}]
        ),
        "CustomerName", CALCULATE(VALUES('{CUSTOMER_DIM}'[{CUSTOMER_NAME_COL}])),
        "TotalAmount", {MEASURE_EXPRESSION}
    ),
    [TotalAmount], DESC
)'''
            },
            
            'multi_fact_customer_ranking': {
                'name': 'Multi Fact Customer Ranking',
                'description': 'Customer ranking aggregating multiple fact tables',
                'template': '''EVALUATE
TOPN(
    {LIMIT},
    ADDCOLUMNS(
        SUMMARIZE(
            '{CUSTOMER_DIM}',
            '{CUSTOMER_DIM}'[{CUSTOMER_KEY_COL}]
        ),
        "CustomerName", CALCULATE(VALUES('{CUSTOMER_DIM}'[{CUSTOMER_NAME_COL}])),
        "TotalAmount", {MEASURE_EXPRESSION}
    ),
    [TotalAmount], DESC
)'''
            },
            
            'basic_aggregation': {
                'name': 'Basic Aggregation',
                'description': 'Simple aggregation pattern',
                'template': '''EVALUATE
ADDCOLUMNS(
    SUMMARIZE(
        '{FACT_TABLE}',
        '{FACT_TABLE}'[{CUSTOMER_KEY_COL}]
    ),
    "TotalAmount", {MEASURE_EXPRESSION}
)'''
            }
        }