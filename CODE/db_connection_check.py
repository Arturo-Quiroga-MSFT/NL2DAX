import os
import pyodbc
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
AZURE_SQL_DB = os.getenv("AZURE_SQL_DB")
AZURE_SQL_USER = os.getenv("AZURE_SQL_USER")
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

## Use ODBC Driver 18 for SQL Server
BASE_CONN = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={AZURE_SQL_SERVER};"
    f"DATABASE={AZURE_SQL_DB};"
    "Encrypt=yes;TrustServerCertificate=yes;"
)

# SQL Server access token attribute
SQL_COPT_SS_ACCESS_TOKEN = 1256

def check_connection():
    """Quick check to verify Azure SQL DB connectivity using Azure AD token."""
    # First, try SQL authentication if credentials provided
    if AZURE_SQL_USER and AZURE_SQL_PASSWORD:
        conn_str_sql = BASE_CONN + f"UID={AZURE_SQL_USER};PWD={AZURE_SQL_PASSWORD};"
        try:
            conn = pyodbc.connect(conn_str_sql, timeout=5)
            conn.close()
            print("[OK] Connected via SQL authentication.")
            return
        except Exception as e:
            print(f"[WARN] SQL auth failed: {e}")
    # Next, try Azure AD token auth
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        access_token = token.token.encode('utf-16-le')
        conn = pyodbc.connect(
            BASE_CONN,
            attrs_before={SQL_COPT_SS_ACCESS_TOKEN: access_token},
            timeout=5
        )
        conn.close()
        print("[OK] Connected via Azure AD authentication.")
    except Exception as e:
        print(f"[ERROR] Failed to connect via Azure AD: {e}")

if __name__ == "__main__":
    check_connection()
