"""
Smoke demo: generate DAX for a couple of NL queries using a minimal schema.
Run with the repo's .venv python:
    - .venv/bin/python -m SEMPY_DAX_ENGINE.tests.smoke_demo
    - or: python SEMPY_DAX_ENGINE/tests/smoke_demo.py
"""

import os
import sys

# Ensure repo root is on sys.path when running as a script
_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from SEMPY_DAX_ENGINE.core.sempy_dax_generator import SemPyDAXGenerator
from SEMPY_DAX_ENGINE.core.semantic_analyzer import (
    SemanticModelSchema,
    TableInfo,
    ColumnInfo,
    MeasureInfo,
    DataTypeCategory,
)


def build_minimal_schema():
    date_table = TableInfo(
        name="Date",
        type="Table",
        columns=[
            ColumnInfo(name="Date", table_name="Date", data_type="date", data_category=DataTypeCategory.DATE),
            ColumnInfo(name="Year", table_name="Date", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Month", table_name="Date", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
        is_dimension_table=True,
    )

    customers_table = TableInfo(
        name="Customers",
        type="Table",
        columns=[
            ColumnInfo(name="CustomerId", table_name="Customers", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Name", table_name="Customers", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
        is_dimension_table=True,
    )

    sales_table = TableInfo(
        name="Sales",
        type="Table",
        columns=[
            ColumnInfo(name="SaleId", table_name="Sales", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Amount", table_name="Sales", data_type="decimal", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Name", table_name="Sales", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
        is_fact_table=True,
    )

    measures = [
        MeasureInfo(
            name="Total Sales",
            table_name="Sales",
            expression="SUM(Sales[Amount])",
            data_type="decimal",
        )
    ]

    schema = SemanticModelSchema(
        model_name="TestModel",
        workspace_name="TestWorkspace",
        tables=[date_table, customers_table, sales_table],
        measures=measures,
        relationships=[],
    )
    return schema


if __name__ == "__main__":
    schema = build_minimal_schema()
    gen = SemPyDAXGenerator(schema)

    examples = [
        "list all customers",
        "total sales by month",
        "top 5 customers by total sales",
    ]

    for q in examples:
        plan = gen.generate_dax_query(q)
        print("\n=== NL ===")
        print(q)
        print("--- DAX ---")
        print(plan.dax_expression)
