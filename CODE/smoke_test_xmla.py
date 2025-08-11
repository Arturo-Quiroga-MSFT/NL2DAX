"""
smoke_test_xmla.py

Run a simple DAX ping against the configured Power BI XMLA endpoint to verify connectivity.
Usage: python CODE/smoke_test_xmla.py
"""
from dotenv import load_dotenv
from xmla_http_executor import health_check, execute_dax_via_http


def main():
    load_dotenv()
    print("[SMOKE] Checking XMLA connectivity with EVALUATE ROW(\"ping\", 1)...")
    ok = False
    try:
        ok = health_check()
    except Exception as e:
        print(f"[SMOKE] Health check failed: {e}")
    if ok:
        print("[SMOKE] Health check passed.")
        # Run a sample optional query to show rows (safe if model exists)
        try:
            res = execute_dax_via_http('EVALUATE TOPN(5, VALUES(\"Customer\"[Customer Name]))')
            print(f"[SMOKE] Sample rows: {res}")
        except Exception as e:
            print(f"[SMOKE] Sample query failed (this can be normal if model schema differs): {e}")
    else:
        print("[SMOKE] Health check did not pass.")


if __name__ == "__main__":
    main()
