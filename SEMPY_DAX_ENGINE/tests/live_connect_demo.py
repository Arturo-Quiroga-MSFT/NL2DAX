"""
Live connect demo using real Fabric config from .env at repo root.
This will authenticate and attempt to connect to the configured workspace/model.
Run:
  source .venv/bin/activate && python SEMPY_DAX_ENGINE/tests/live_connect_demo.py
"""
import os
import sys

# Ensure repo root is on sys.path
_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from SEMPY_DAX_ENGINE.core.sempy_dax_engine import SemPyDAXEngine
from SEMPY_DAX_ENGINE.config.fabric_config import FabricConfig


def main():
    # Load config from repo root .env automatically via FabricConfig
    cfg = FabricConfig.from_env()

    # Pass config into engine so connector uses it
    engine = SemPyDAXEngine()
    engine.fabric_config = cfg
    workspace_name = cfg.get_workspace_name()
    model_name = cfg.dataset_name

    ok = engine.connect_and_analyze(workspace_name, model_name, auth_method="config")
    if not ok:
        print("❌ Failed to connect and analyze using provided .env")
        return

    # Quick NL query via live model
    nl = "total sales by month"
    result = engine.query(nl)
    print("\n=== Live NL ===")
    print(nl)
    if result.success:
        print(f"Rows: {result.row_count}, Exec ms: {result.execution_time_ms}")
        # Print a few rows if present
        if result.dataframe is not None:
            print(result.dataframe.head().to_string(index=False))
    else:
        print("❌ Query failed:", result.error_message)
        if result.metadata:
            print(result.metadata)


if __name__ == "__main__":
    main()
