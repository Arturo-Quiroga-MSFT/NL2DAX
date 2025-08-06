def print_schema_summary(schema):
    print("\n" + "="*60)
    print(" STAR SCHEMA SUMMARY ".center(60, '='))
    print("="*60)

    print("\nTABLES AND COLUMNS:")
    for table, columns in schema.get('tables', {}).items():
        print(f"  {table}:")
        for col in columns:
            print(f"    - {col}")

    # Print primary keys if available
    if 'primary_keys' in schema:
        print("\n" + "-"*60)
        print(" PRIMARY KEYS ".center(60, '-'))
        print("-"*60)
        for table, pk in schema['primary_keys'].items():
            print(f"  {table}: {', '.join(pk)}")

    print("\n" + "-"*60)
    print(" FOREIGN KEYS & RELATIONSHIPS ".center(60, '-'))
    print("-"*60)
    for rel in schema.get('relationships', []):
        # Try both naming conventions for compatibility
        from_table = rel.get('from_table') or rel.get('parent_table')
        from_col = rel.get('from_column') or rel.get('parent_column')
        to_table = rel.get('to_table') or rel.get('referenced_table')
        to_col = rel.get('to_column') or rel.get('referenced_column')
        print(f"  {from_table}.{from_col} -> {to_table}.{to_col}  (FK)")
        if 'relationship_type' in rel:
            print(f"    Type: {rel['relationship_type']}")
        if 'cardinality' in rel:
            print(f"    Cardinality: {rel['cardinality']}")

    print("\n" + "="*60)
    print(" END OF SCHEMA SUMMARY ".center(60, '='))
    print("="*60)
import os
import pyodbc
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
AZURE_SQL_DB = os.getenv("AZURE_SQL_DB")
AZURE_SQL_USER = os.getenv("AZURE_SQL_USER")
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

CONN_STR = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={AZURE_SQL_SERVER};"
    f"DATABASE={AZURE_SQL_DB};"
    f"UID={AZURE_SQL_USER};PWD={AZURE_SQL_PASSWORD};"
    "Encrypt=yes;TrustServerCertificate=yes;"
)

def get_schema_metadata():
    """Fetch tables, columns, and foreign key relationships from Azure SQL DB using SQL authentication."""
    with pyodbc.connect(CONN_STR) as conn:
        cursor = conn.cursor()
        # Get tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
        tables = [row.TABLE_NAME for row in cursor.fetchall()]
        # Get columns for each table
        schema = {}
        for table in tables:
            cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}'")
            columns = [row.COLUMN_NAME for row in cursor.fetchall()]
            schema[table] = columns
        # Get foreign key relationships
        cursor.execute("""
            SELECT 
                fk.name AS FK_Name,
                tp.name AS ParentTable,
                cp.name AS ParentColumn,
                tr.name AS ReferencedTable,
                cr.name AS ReferencedColumn
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        """)
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                "fk_name": row.FK_Name,
                "parent_table": row.ParentTable,
                "parent_column": row.ParentColumn,
                "referenced_table": row.ReferencedTable,
                "referenced_column": row.ReferencedColumn
            })
        return {"tables": schema, "relationships": relationships}

def cache_schema():
    """Fetch schema from DB and write to cache file."""
    data = get_schema_metadata()
    cache_file = Path(__file__).parent / 'schema_cache.json'
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Schema metadata cached to {cache_file}")

if __name__ == '__main__':
    import sys
    if '--cache' in sys.argv:
        cache_schema()
    else:
        metadata = get_schema_metadata()
        print_schema_summary(metadata)
import json
from pathlib import Path

def get_schema_metadata():
    """Load schema metadata from local cache file."""
    cache_file = Path(__file__).parent / 'schema_cache.json'
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load schema cache: {e}")
    print("[WARN] schema_cache.json not found or invalid; returning empty metadata")
    return {"tables": {}, "relationships": []}
