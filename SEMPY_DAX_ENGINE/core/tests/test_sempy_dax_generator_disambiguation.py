import pytest

from SEMPY_DAX_ENGINE.core.semantic_analyzer import (
    SemanticModelSchema, TableInfo, ColumnInfo, DataTypeCategory
)
from SEMPY_DAX_ENGINE.core.sempy_dax_generator import SemPyDAXGenerator


def build_schema_with_ambiguous_column():
    t1 = TableInfo(
        name="Sales",
        type="Table",
        is_fact_table=True,
        columns=[
            ColumnInfo(name="Amount", table_name="Sales", data_type="decimal", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Name", table_name="Sales", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
    )
    t2 = TableInfo(
        name="Customers",
        type="Table",
        columns=[
            ColumnInfo(name="Name", table_name="Customers", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
    )
    schema = SemanticModelSchema(
        model_name="TestModel",
        workspace_name="TestWorkspace",
        tables=[t1, t2],
    )
    return schema


def test_to_bracketed_column_prefers_primary_table():
    schema = build_schema_with_ambiguous_column()
    gen = SemPyDAXGenerator(schema)
    # preferred table contains Name, so it should resolve to Sales[Name]
    out = gen._to_bracketed_column("Name", preferred_table="Sales")
    assert out == "Sales[Name]"


def test_to_bracketed_column_returns_original_if_ambiguous_without_preference():
    schema = build_schema_with_ambiguous_column()
    gen = SemPyDAXGenerator(schema)
    out = gen._to_bracketed_column("Name")
    assert out == "Name"  # ambiguous across tables, no preferred table provided
