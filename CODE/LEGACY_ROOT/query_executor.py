import os

USE_XMLA_HTTP = os.getenv("USE_XMLA_HTTP", "false").lower() in ("1", "true", "yes")


def execute_dax_query(dax_query):
    """Execute a DAX query against a Tabular model via XMLA endpoint.

    If USE_XMLA_HTTP=true, use HTTP/XMLA via AAD (cross-platform). Otherwise attempt pyadomd.
    """
    if USE_XMLA_HTTP:
        try:
            from xmla_http_executor import execute_dax_via_http
            return execute_dax_via_http(dax_query)
        except Exception as e:
            raise RuntimeError(
                "DAX over HTTP/XMLA failed. Check PBI_* env vars, XMLA endpoint, dataset name, and permissions. "
                f"Root error: {e}"
            )

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
