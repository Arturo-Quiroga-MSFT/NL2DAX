import os
import pyodbc
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

def execute_sql_query(sql_query):
    """Execute a SQL query against Azure SQL DB and return results as list of dicts."""
    with pyodbc.connect(CONN_STR) as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
    return results

if __name__ == '__main__':
    import json
    sql = input("Enter SQL query for execution: ")
    try:
        res = execute_sql_query(sql)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error executing SQL: {e}")
