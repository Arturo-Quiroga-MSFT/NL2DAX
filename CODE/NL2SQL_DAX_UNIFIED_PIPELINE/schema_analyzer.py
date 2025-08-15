#!/usr/bin/env python3
"""
schema_analyzer.py - Database Schema Analysis
============================================

This module analyzes Azure SQL Database schema to provide metadata
for SQL and DAX query generation. It extracts table structures,
relationships, and data types to inform the query generators.

Author: Unified Pipeline Team
Date: August 2025
"""

import os
import pyodbc
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SchemaAnalyzer:
    """Analyze Azure SQL Database schema for query generation"""
    
    def __init__(self):
        """Initialize the schema analyzer"""
        self.server = os.getenv("AZURE_SQL_SERVER")
        self.database = os.getenv("AZURE_SQL_DB")
        self.username = os.getenv("AZURE_SQL_USER")
        self.password = os.getenv("AZURE_SQL_PASSWORD")
        self.driver = "{ODBC Driver 18 for SQL Server}"
        
        # Cache for schema information
        self._schema_cache = None
        
    def get_connection_string(self) -> str:
        """Generate connection string"""
        return (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information"""
        if self._schema_cache is None:
            self._schema_cache = self._analyze_schema()
        return self._schema_cache
    
    def get_basic_schema(self) -> Dict[str, Any]:
        """Get basic schema information for validation"""
        try:
            with pyodbc.connect(self.get_connection_string()) as conn:
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("""
                    SELECT TABLE_NAME, TABLE_TYPE 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """)
                
                tables = []
                for row in cursor.fetchall():
                    tables.append({
                        "name": row.TABLE_NAME,
                        "type": row.TABLE_TYPE
                    })
                
                return {"tables": tables}
                
        except Exception as e:
            print(f"❌ Basic schema analysis failed: {str(e)}")
            return {"tables": []}
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the database schema"""
        schema_info = self.get_schema_info()
        
        summary = {
            "database": self.database,
            "table_count": len(schema_info.get("tables", [])),
            "total_columns": sum(len(table.get("columns", [])) for table in schema_info.get("tables", [])),
            "relationship_count": len(schema_info.get("relationships", [])),
            "tables": [
                {
                    "name": table["name"],
                    "column_count": len(table.get("columns", [])),
                    "primary_key": table.get("primary_key"),
                    "description": table.get("description", "")
                }
                for table in schema_info.get("tables", [])
            ]
        }
        
        return summary
    
    def _analyze_schema(self) -> Dict[str, Any]:
        """Perform comprehensive schema analysis"""
        try:
            with pyodbc.connect(self.get_connection_string()) as conn:
                cursor = conn.cursor()
                
                schema_info = {
                    "database": self.database,
                    "tables": self._get_tables_info(cursor),
                    "relationships": self._get_relationships_info(cursor),
                    "indexes": self._get_indexes_info(cursor)
                }
                
                return schema_info
                
        except Exception as e:
            print(f"❌ Schema analysis failed: {str(e)}")
            return {"tables": [], "relationships": [], "indexes": []}
    
    def _get_tables_info(self, cursor) -> List[Dict[str, Any]]:
        """Get detailed table information"""
        tables = []
        
        # Get all tables
        cursor.execute("""
            SELECT 
                t.TABLE_SCHEMA,
                t.TABLE_NAME,
                t.TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
        """)
        
        for table_row in cursor.fetchall():
            schema_name = table_row.TABLE_SCHEMA
            table_name = table_row.TABLE_NAME
            
            # Get columns for this table
            columns = self._get_table_columns(cursor, schema_name, table_name)
            
            # Get primary key
            primary_key = self._get_primary_key(cursor, schema_name, table_name)
            
            # Get sample data for context
            sample_data = self._get_sample_data(cursor, schema_name, table_name)
            
            table_info = {
                "schema": schema_name,
                "name": table_name,
                "full_name": f"{schema_name}.{table_name}",
                "columns": columns,
                "primary_key": primary_key,
                "sample_data": sample_data,
                "description": f"Table containing {len(columns)} columns"
            }
            
            tables.append(table_info)
        
        return tables
    
    def _get_table_columns(self, cursor, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """Get detailed column information for a table"""
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, schema_name, table_name)
        
        columns = []
        for col_row in cursor.fetchall():
            column_info = {
                "name": col_row.COLUMN_NAME,
                "data_type": col_row.DATA_TYPE,
                "is_nullable": col_row.IS_NULLABLE == 'YES',
                "default_value": col_row.COLUMN_DEFAULT,
                "max_length": col_row.CHARACTER_MAXIMUM_LENGTH,
                "precision": col_row.NUMERIC_PRECISION,
                "scale": col_row.NUMERIC_SCALE,
                "position": col_row.ORDINAL_POSITION
            }
            columns.append(column_info)
        
        return columns
    
    def _get_primary_key(self, cursor, schema_name: str, table_name: str) -> List[str]:
        """Get primary key columns for a table"""
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = ? 
            AND TABLE_NAME = ?
            AND CONSTRAINT_NAME IN (
                SELECT CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = ?
                AND TABLE_NAME = ?
                AND CONSTRAINT_TYPE = 'PRIMARY KEY'
            )
            ORDER BY ORDINAL_POSITION
        """, schema_name, table_name, schema_name, table_name)
        
        return [row.COLUMN_NAME for row in cursor.fetchall()]
    
    def _get_sample_data(self, cursor, schema_name: str, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get sample data from a table for context"""
        try:
            full_table_name = f"[{schema_name}].[{table_name}]"
            cursor.execute(f"SELECT TOP {limit} * FROM {full_table_name}")
            
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                sample_data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Convert values to JSON-serializable types
                        if value is None:
                            row_dict[columns[i]] = None
                        elif isinstance(value, (int, float, str, bool)):
                            row_dict[columns[i]] = value
                        else:
                            row_dict[columns[i]] = str(value)
                    sample_data.append(row_dict)
                
                return sample_data
            
        except Exception as e:
            print(f"⚠️  Could not get sample data for {schema_name}.{table_name}: {str(e)}")
        
        return []
    
    def _get_relationships_info(self, cursor) -> List[Dict[str, Any]]:
        """Get foreign key relationships"""
        cursor.execute("""
            SELECT 
                fk.CONSTRAINT_NAME,
                fk.TABLE_SCHEMA AS FK_SCHEMA,
                fk.TABLE_NAME AS FK_TABLE,
                fk.COLUMN_NAME AS FK_COLUMN,
                pk.TABLE_SCHEMA AS PK_SCHEMA,
                pk.TABLE_NAME AS PK_TABLE,
                pk.COLUMN_NAME AS PK_COLUMN
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk 
                ON fk.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                AND fk.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk 
                ON pk.CONSTRAINT_NAME = rc.UNIQUE_CONSTRAINT_NAME
                AND pk.TABLE_SCHEMA = rc.UNIQUE_CONSTRAINT_SCHEMA
                AND pk.ORDINAL_POSITION = fk.ORDINAL_POSITION
            ORDER BY fk.CONSTRAINT_NAME, fk.ORDINAL_POSITION
        """)
        
        relationships = []
        for row in cursor.fetchall():
            relationship = {
                "name": row.CONSTRAINT_NAME,
                "from_schema": row.FK_SCHEMA,
                "from_table": row.FK_TABLE,
                "from_column": row.FK_COLUMN,
                "to_schema": row.PK_SCHEMA,
                "to_table": row.PK_TABLE,
                "to_column": row.PK_COLUMN
            }
            relationships.append(relationship)
        
        return relationships
    
    def _get_indexes_info(self, cursor) -> List[Dict[str, Any]]:
        """Get index information"""
        cursor.execute("""
            SELECT 
                i.name AS INDEX_NAME,
                t.name AS TABLE_NAME,
                i.type_desc AS INDEX_TYPE,
                i.is_unique,
                i.is_primary_key
            FROM sys.indexes i
            JOIN sys.tables t ON i.object_id = t.object_id
            WHERE i.type > 0  -- Exclude heaps
            ORDER BY t.name, i.name
        """)
        
        indexes = []
        for row in cursor.fetchall():
            index_info = {
                "name": row.INDEX_NAME,
                "table": row.TABLE_NAME,
                "type": row.INDEX_TYPE,
                "is_unique": row.is_unique,
                "is_primary_key": row.is_primary_key
            }
            indexes.append(index_info)
        
        return indexes
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information for a specific table"""
        schema_info = self.get_schema_info()
        
        for table in schema_info.get("tables", []):
            if table["name"].lower() == table_name.lower():
                return table
        
        return {}
    
    def get_column_info(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get information for a specific column"""
        table_info = self.get_table_info(table_name)
        
        for column in table_info.get("columns", []):
            if column["name"].lower() == column_name.lower():
                return column
        
        return {}

def main():
    """Test the schema analyzer"""
    print("🧪 Testing Schema Analyzer")
    print("=" * 40)
    
    analyzer = SchemaAnalyzer()
    
    # Test basic schema
    print("📊 Getting basic schema...")
    basic_schema = analyzer.get_basic_schema()
    print(f"Found {len(basic_schema['tables'])} tables")
    
    # Test full schema analysis
    print("\\n🔍 Performing full schema analysis...")
    schema_info = analyzer.get_schema_info()
    
    # Display summary
    summary = analyzer.get_schema_summary()
    print(f"\\n📋 Schema Summary:")
    print(f"   Database: {summary['database']}")
    print(f"   Tables: {summary['table_count']}")
    print(f"   Total Columns: {summary['total_columns']}")
    print(f"   Relationships: {summary['relationship_count']}")
    
    # Show table details
    print(f"\\n📊 Table Details:")
    for table in summary['tables'][:5]:  # Show first 5 tables
        print(f"   - {table['name']}: {table['column_count']} columns")
    
    print("\\n🏁 Schema analysis completed!")
    return 0

if __name__ == "__main__":
    exit(main())