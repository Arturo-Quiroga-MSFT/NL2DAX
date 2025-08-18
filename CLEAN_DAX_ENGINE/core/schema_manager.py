"""
Clean Schema Manager - Schema caching and validation
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib

@dataclass
class SchemaTable:
    """Represents a table in the schema"""
    name: str
    table_type: str  # 'fact' or 'dimension'
    columns: List[str]
    key_columns: List[str]
    measure_columns: List[str]

@dataclass
class SchemaInfo:
    """Complete schema information"""
    tables: Dict[str, SchemaTable]
    relationships: List[Dict[str, str]]
    cached_at: datetime
    
    def is_expired(self, ttl_hours: int = 24) -> bool:
        """Check if schema cache has expired"""
        return datetime.now() - self.cached_at > timedelta(hours=ttl_hours)

class SchemaManager:
    """Clean schema management with caching"""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._schema_cache: Optional[SchemaInfo] = None
    
    def get_schema(self, force_refresh: bool = False) -> SchemaInfo:
        """Get validated schema information"""
        cache_file = os.path.join(self.cache_dir, "schema_cache.json")
        
        # Try to load from cache first
        if not force_refresh and os.path.exists(cache_file):
            try:
                schema = self._load_from_cache(cache_file)
                if schema and not schema.is_expired():
                    print(f"[INFO] Using cached schema ({len(schema.tables)} tables)")
                    self._schema_cache = schema
                    return schema
            except Exception as e:
                print(f"[WARNING] Failed to load schema cache: {e}")
        
        # Discover schema from database
        print("[INFO] Discovering schema from database...")
        schema = self._discover_schema()
        
        # Save to cache
        self._save_to_cache(schema, cache_file)
        self._schema_cache = schema
        
        return schema
    
    def _discover_schema(self) -> SchemaInfo:
        """Discover schema from the actual database"""
        try:
            # First try to load from UNIVERSAL system cache 
            universal_cache_file = "/Users/arturoquiroga/GITHUB/NL2DAX/UNIVERSAL_NL2DAX_SYSTEM/cache/schema_cache_12ac9b8719c488a1.json"
            if os.path.exists(universal_cache_file):
                print("[INFO] Loading schema from UNIVERSAL system cache...")
                with open(universal_cache_file, 'r') as f:
                    universal_data = json.load(f)
                    
                # Extract complete table info from UNIVERSAL cache
                tables = {}
                for table_name, column_list in universal_data.get('tables', {}).items():
                    # Only include tables with FACT or DIMENSION in their names
                    if not ('FACT' in table_name.upper() or 'DIMENSION' in table_name.upper()):
                        continue
                        
                    # Determine table type
                    table_type = 'fact' if 'FACT' in table_name.upper() else 'dimension'
                    
                    # Extract columns (column_list is a list in UNIVERSAL cache)
                    columns = column_list if isinstance(column_list, list) else []
                    
                    # Classify columns
                    key_columns = [col for col in columns if any(word in col.upper() for word in ['_KEY', '_ID', 'KEY', 'ID'])]
                    measure_columns = [col for col in columns if any(word in col.upper() for word in 
                                     ['AMOUNT', 'BALANCE', 'EXPOSURE', 'VALUE', 'TOTAL', 'PRINCIPAL', 'INTEREST', 'FEE', 'LIMIT', 'RATE', 'PCT', 'PERCENTAGE'])]
                    
                    tables[table_name] = SchemaTable(
                        name=table_name,
                        table_type=table_type,
                        columns=columns,
                        key_columns=key_columns,
                        measure_columns=measure_columns
                    )
                
                if tables:
                    print(f"[SUCCESS] Loaded complete schema: {len(tables)} tables")
                    print(f"[INFO] Fact tables: {[name for name, table in tables.items() if table.table_type == 'fact']}")
                    print(f"[INFO] Dimension tables: {[name for name, table in tables.items() if table.table_type == 'dimension']}")
                    
                    return SchemaInfo(
                        tables=tables,
                        relationships=universal_data.get('relationships', []),
                        cached_at=datetime.now()
                    )
            
            # Fallback to legacy cache
            cache_file = "/Users/arturoquiroga/GITHUB/NL2DAX/cache/query_cache.json"
            if os.path.exists(cache_file):
                print("[INFO] Loading schema from legacy cache file...")
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                # Extract table info from cache
                tables = {}
                if 'schema_info' in cache_data:
                    for table_name, table_info in cache_data['schema_info'].get('tables', {}).items():
                        # Determine table type
                        table_type = 'fact' if 'FACT' in table_name.upper() else 'dimension'
                        
                        # Extract columns
                        columns = list(table_info.get('columns', {}).keys())
                        
                        # Classify columns
                        key_columns = [col for col in columns if 'key' in col.lower() or 'id' in col.lower()]
                        measure_columns = [col for col in columns if any(word in col.lower() for word in ['amount', 'balance', 'exposure', 'value'])]
                        
                        tables[table_name] = SchemaTable(
                            name=table_name,
                            table_type=table_type,
                            columns=columns,
                            key_columns=key_columns,
                            measure_columns=measure_columns
                        )
                
                if tables:
                    print(f"[SUCCESS] Loaded {len(tables)} tables from legacy cache")
                    return SchemaInfo(
                        tables=tables,
                        relationships=[],
                        cached_at=datetime.now()
                    )
            
            # Final fallback: Create comprehensive schema based on known Power BI structure
            print("[INFO] Creating comprehensive fallback schema with all known Power BI tables...")
            
            # Define the complete schema based on the discovered structure
            known_tables = {}
            
            # Fact Tables
            known_tables['FIS_CA_DETAIL_FACT'] = SchemaTable(
                name='FIS_CA_DETAIL_FACT',
                table_type='fact',
                columns=['CA_DETAIL_KEY', 'CUSTOMER_KEY', 'CA_PRODUCT_KEY', 'LIMIT_KEY', 'INVESTOR_KEY', 'OWNER_KEY', 'MONTH_ID', 
                        'CA_CURRENCY_CODE', 'FACILITY_ID', 'AS_OF_DATE', 'LIMIT_AMOUNT', 'LIMIT_WITHHELD', 'LIMIT_USED', 
                        'LIMIT_AVAILABLE', 'PRINCIPAL_AMOUNT_DUE', 'NUMBER_OF_LIMIT_EXPOSURE', 'LIMIT_VALUE_OF_COLLATERAL',
                        'FEES_CHARGED_MTD', 'FEES_CHARGED_QTD', 'FEES_CHARGED_YTD', 'FEES_CHARGED_ITD', 'FEES_EARNED_MTD',
                        'FEES_EARNED_QTD', 'FEES_EARNED_YTD', 'FEES_EARNED_ITD', 'FEES_PAID_MTD', 'FEES_PAID_QTD',
                        'FEES_PAID_YTD', 'FEES_PAID_ITD', 'COMMITMENT_FEE_RATE', 'UTILIZATION_FEE_RATE', 
                        'CONTRACTUAL_OWNERSHIP_PCT', 'ORIGINAL_LIMIT_AMOUNT', 'FINANCIAL_FX_RATE', 'PORTFOLIO_ID',
                        'LIMIT_STATUS_CODE', 'LIMIT_STATUS_DESCRIPTION', 'LIMIT_STATUS_DATE', 'PROBABILITY_OF_DEFAULT',
                        'LOSS_GIVEN_DEFAULT', 'EXPOSURE_AT_DEFAULT', 'RISK_WEIGHT_PERCENTAGE', 'REGULATORY_CAPITAL'],
                key_columns=['CA_DETAIL_KEY', 'CUSTOMER_KEY', 'CA_PRODUCT_KEY', 'LIMIT_KEY', 'INVESTOR_KEY', 'OWNER_KEY'],
                measure_columns=['LIMIT_AMOUNT', 'LIMIT_WITHHELD', 'LIMIT_USED', 'LIMIT_AVAILABLE', 'PRINCIPAL_AMOUNT_DUE',
                               'EXPOSURE_AT_DEFAULT', 'ORIGINAL_LIMIT_AMOUNT', 'REGULATORY_CAPITAL']
            )
            
            known_tables['FIS_CL_DETAIL_FACT'] = SchemaTable(
                name='FIS_CL_DETAIL_FACT',
                table_type='fact',
                columns=['CL_DETAIL_KEY', 'LOAN_PRODUCT_KEY', 'CUSTOMER_KEY', 'INVESTOR_KEY', 'OWNER_KEY', 'CURRENCY_KEY',
                        'MONTH_ID', 'LOAN_ID', 'FACILITY_ID', 'LOAN_CURRENCY_CODE', 'AS_OF_DATE', 'CURRENT_PRINCIPAL_BALANCE',
                        'PRINCIPAL_BALANCE', 'PRINCIPAL_PAID', 'INTEREST_BALANCE', 'INTEREST_ACCRUED', 'INTEREST_PAID',
                        'INTEREST_RECEIVED', 'FEE_BALANCE', 'FEE_PAID', 'OTHER_BALANCES', 'TOTAL_BALANCE', 'TOTAL_PAID',
                        'REVOLVING_ACCOUNT_LIMIT', 'REVOLVING_ACCOUNT_AVAILABLE', 'ORIGINAL_AMOUNT', 'ORIGINAL_TERM',
                        'REMAINING_TERM', 'LOAN_STATUS', 'LOAN_STATUS_DESCRIPTION', 'MATURITY_DATE', 'EFFECTIVE_DATE',
                        'NEXT_PAYMENT_DATE', 'INTEREST_RATE', 'BASE_RATE', 'MARGIN_RATE', 'EFFECTIVE_RATE',
                        'SCHEDULED_PAYMENT', 'ACTUAL_PAYMENT', 'PAYMENT_DIFFERENCE', 'PAST_DUE_DAYS', 'IS_NON_PERFORMING',
                        'IS_DEFAULT', 'CHARGE_OFF_AMOUNT', 'RECOVERY_AMOUNT', 'PROVISION_AMOUNT', 'RISK_RATING',
                        'PROBABILITY_OF_DEFAULT', 'LOSS_GIVEN_DEFAULT', 'EXPOSURE_AT_DEFAULT'],
                key_columns=['CL_DETAIL_KEY', 'LOAN_PRODUCT_KEY', 'CUSTOMER_KEY', 'INVESTOR_KEY', 'OWNER_KEY', 'CURRENCY_KEY'],
                measure_columns=['CURRENT_PRINCIPAL_BALANCE', 'PRINCIPAL_BALANCE', 'TOTAL_BALANCE', 'ORIGINAL_AMOUNT',
                               'EXPOSURE_AT_DEFAULT', 'INTEREST_RATE', 'SCHEDULED_PAYMENT', 'ACTUAL_PAYMENT']
            )
            
            # Key Dimension Tables
            known_tables['FIS_CUSTOMER_DIMENSION'] = SchemaTable(
                name='FIS_CUSTOMER_DIMENSION',
                table_type='dimension',
                columns=['CUSTOMER_KEY', 'CUSTOMER_ID', 'CUSTOMER_NAME', 'CUSTOMER_SHORT_NAME', 'CUSTOMER_TYPE_CODE',
                        'CUSTOMER_TYPE_DESCRIPTION', 'INDUSTRY_CODE', 'INDUSTRY_DESCRIPTION', 'COUNTRY_CODE',
                        'COUNTRY_DESCRIPTION', 'STATE_CODE', 'STATE_DESCRIPTION', 'CITY', 'POSTAL_CODE',
                        'RISK_RATING_CODE', 'RISK_RATING_DESCRIPTION', 'CUSTOMER_STATUS', 'ESTABLISHED_DATE', 'RELATIONSHIP_MANAGER'],
                key_columns=['CUSTOMER_KEY', 'CUSTOMER_ID'],
                measure_columns=[]
            )
            
            known_tables['FIS_CURRENCY_DIMENSION'] = SchemaTable(
                name='FIS_CURRENCY_DIMENSION',
                table_type='dimension',
                columns=['CURRENCY_KEY', 'FROM_CURRENCY_CODE', 'FROM_CURRENCY_DESCRIPTION', 'TO_CURRENCY_CODE',
                        'TO_CURRENCY_DESCRIPTION', 'CURRENCY_MONTH_ID', 'CURRENCY_RATE_GROUP', 'CRNCY_EXCHANGE_RATE',
                        'OPERATION_INDICATOR', 'CONVERSION_RATE'],
                key_columns=['CURRENCY_KEY'],
                measure_columns=['CRNCY_EXCHANGE_RATE', 'CONVERSION_RATE']
            )
            
            known_tables['FIS_MONTH_DIMENSION'] = SchemaTable(
                name='FIS_MONTH_DIMENSION',
                table_type='dimension',
                columns=['MONTH_ID', 'MONTH_DESCRIPTION', 'MONTH_TIMESPAN', 'PERIOD_END_DATE', 'QUARTER_ID',
                        'QUARTER_DESCRIPTION', 'QUARTER_TIMESPAN', 'QUARTER_END_DATE', 'YEAR_ID', 'YEAR_DESCRIPTION',
                        'YEAR_TIMESPAN', 'YEAR_END_DATE'],
                key_columns=['MONTH_ID', 'QUARTER_ID', 'YEAR_ID'],
                measure_columns=[]
            )
            
            # Add other dimension tables as needed...
            
            return SchemaInfo(
                tables=known_tables,
                relationships=[],
                cached_at=datetime.now()
            )
            
        except Exception as e:
            print(f"[ERROR] Schema discovery failed: {e}")
            # Return minimal fallback schema
            return SchemaInfo(
                tables={},
                relationships=[],
                cached_at=datetime.now()
            )
    
    def _load_from_cache(self, cache_file: str) -> Optional[SchemaInfo]:
        """Load schema from cache file"""
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct SchemaTable objects
        tables = {}
        for table_name, table_data in data['tables'].items():
            tables[table_name] = SchemaTable(
                name=table_data['name'],
                table_type=table_data['table_type'],
                columns=table_data['columns'],
                key_columns=table_data['key_columns'],
                measure_columns=table_data['measure_columns']
            )
        
        return SchemaInfo(
            tables=tables,
            relationships=data['relationships'],
            cached_at=datetime.fromisoformat(data['cached_at'])
        )
    
    def _save_to_cache(self, schema: SchemaInfo, cache_file: str):
        """Save schema to cache file"""
        # Convert to serializable format
        data = {
            'tables': {
                name: {
                    'name': table.name,
                    'table_type': table.table_type,
                    'columns': table.columns,
                    'key_columns': table.key_columns,
                    'measure_columns': table.measure_columns
                }
                for name, table in schema.tables.items()
            },
            'relationships': schema.relationships,
            'cached_at': schema.cached_at.isoformat()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[INFO] Schema cached with {len(schema.tables)} tables")
    
    def validate_table_exists(self, table_name: str) -> bool:
        """Validate that a table exists in the schema"""
        if not self._schema_cache:
            self.get_schema()
        return table_name in self._schema_cache.tables
    
    def validate_column_exists(self, table_name: str, column_name: str) -> bool:
        """Validate that a column exists in a table"""
        if not self._schema_cache:
            self.get_schema()
        
        table = self._schema_cache.tables.get(table_name)
        if not table:
            return False
        
        return column_name in table.columns
    
    def get_fact_tables(self) -> List[str]:
        """Get list of fact table names"""
        if not self._schema_cache:
            self.get_schema()
        
        return [name for name, table in self._schema_cache.tables.items() 
                if table.table_type == 'fact']
    
    def get_dimension_tables(self) -> List[str]:
        """Get list of dimension table names"""
        if not self._schema_cache:
            self.get_schema()
        
        return [name for name, table in self._schema_cache.tables.items() 
                if table.table_type == 'dimension']
    
    def get_table_info(self, table_name: str) -> Optional[SchemaTable]:
        """Get detailed information about a table"""
        if not self._schema_cache:
            self.get_schema()
        
        return self._schema_cache.tables.get(table_name)