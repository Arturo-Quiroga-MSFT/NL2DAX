"""
export_all_tables.py

Exports all user tables in the configured Azure SQL DB to CSV files.
- Reuses existing pyodbc connection pattern
- Streams results in chunks to avoid high memory usage
- Creates a timestamped subdirectory under ./EXPORTS

Usage:
  python CODE/export_all_tables.py
"""
import os
import csv
import socket
import pyodbc
from datetime import datetime
from dotenv import load_dotenv

# Load env vars
load_dotenv()

AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER")
AZURE_SQL_DB = os.getenv("AZURE_SQL_DB")
AZURE_SQL_USER = os.getenv("AZURE_SQL_USER")
AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")

# Build explicit tcp endpoint and add timeouts to avoid silent hangs
SERVER_ADDR = f"tcp:{AZURE_SQL_SERVER},1433"
CONN_STR = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER_ADDR};"
    f"DATABASE={AZURE_SQL_DB};"
    f"UID={AZURE_SQL_USER};PWD={AZURE_SQL_PASSWORD};"
    "Authentication=SqlPassword;"
    "Encrypt=yes;TrustServerCertificate=yes;"
    "Connection Timeout=30;Login Timeout=30;"
)

CHUNK_SIZE = int(os.getenv("EXPORT_CHUNK_SIZE", "50000"))
OUTPUT_ROOT = os.path.join(os.path.dirname(__file__), "EXPORTS")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(OUTPUT_ROOT, f"export_{TIMESTAMP}")

LIST_TABLES_SQL = """
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
ORDER BY TABLE_SCHEMA, TABLE_NAME;
"""

def safe_filename(name: str) -> str:
    return name.replace('/', '_').replace('\\', '_').replace(' ', '_')


def stream_table_to_csv(cursor, schema: str, table: str, out_path: str):
    quoted = f"[{schema}].[{table}]"
    cursor.execute(f"SELECT * FROM {quoted}")
    columns = [desc[0] for desc in cursor.description]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(columns)
        rows_written = 0
        while True:
            rows = cursor.fetchmany(CHUNK_SIZE)
            if not rows:
                break
            for row in rows:
                # Convert pyodbc row to list; handle Decimal and datetime gracefully via str()
                writer.writerow(["" if (v is None) else str(v) for v in row])
                rows_written += 1
    return rows_written


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[EXPORT] Writing CSVs to: {OUTPUT_DIR}")
    # Diagnostics
    try:
        print(f"[EXPORT][DIAG] ODBC drivers: {pyodbc.drivers()}")
        print(f"[EXPORT][DIAG] Resolving host {AZURE_SQL_SERVER}...")
        infos = socket.getaddrinfo(AZURE_SQL_SERVER, 1433, proto=socket.IPPROTO_TCP)
        addrs = sorted({ai[4][0] for ai in infos})
        print(f"[EXPORT][DIAG] Resolved addresses: {addrs}")
    except Exception as diag_e:
        print(f"[EXPORT][DIAG] DNS/Driver check warning: {diag_e}")

    with pyodbc.connect(CONN_STR, timeout=30) as conn:
        conn.timeout = int(os.getenv("EXPORT_SQL_TIMEOUT", "0"))  # 0 = driver default
        cur = conn.cursor()
        cur.execute(LIST_TABLES_SQL)
        tables = cur.fetchall()
        total_tables = len(tables)
        print(f"[EXPORT] Found {total_tables} tables to export.")
        for idx, (schema, table) in enumerate(tables, start=1):
            filename = safe_filename(f"{schema}.{table}.csv")
            out_path = os.path.join(OUTPUT_DIR, filename)
            print(f"[EXPORT] ({idx}/{total_tables}) Exporting {schema}.{table} -> {filename}")
            try:
                rows = stream_table_to_csv(cur, schema, table, out_path)
                print(f"[EXPORT] Wrote {rows} rows.")
            except Exception as e:
                print(f"[EXPORT] Failed {schema}.{table}: {e}")

    print("[EXPORT] Done.")


if __name__ == "__main__":
    main()
