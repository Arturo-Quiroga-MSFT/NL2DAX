import os

def execute_dax_query(dax_query):
    """Execute a DAX query against a Tabular model via XMLA endpoint."""
    # Delay import to avoid crashing on module load if Mono/pythonnet missing
    try:
        from pyadomd import Pyadomd
    except Exception as e:
        raise RuntimeError(
            "Cannot execute DAX: pyadomd import failed. "
            "Install Mono (`brew install mono`) and pythonnet (`pip install pyadomd pythonnet`)."
        )
    xmla_conn_str = os.getenv("XMLA_CONNECTION_STRING")
    if not xmla_conn_str:
        raise ValueError("XMLA_CONNECTION_STRING is not set in environment")
    with Pyadomd(xmla_conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute(dax_query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
    return results

if __name__ == '__main__':
    import json
    dax = input("Enter DAX query for execution: ")
    try:
        res = execute_dax_query(dax)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error executing DAX: {e}")
