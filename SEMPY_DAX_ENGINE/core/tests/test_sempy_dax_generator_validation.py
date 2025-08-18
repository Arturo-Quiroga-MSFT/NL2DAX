import pytest

from SEMPY_DAX_ENGINE.core.semantic_analyzer import (
    SemanticModelSchema, TableInfo, ColumnInfo, MeasureInfo, DataTypeCategory
)
from SEMPY_DAX_ENGINE.core.sempy_dax_generator import SemPyDAXGenerator


def build_min_schema():
    sales_table = TableInfo(
        name="Sales",
        type="Table",
        is_fact_table=True,
        columns=[
            ColumnInfo(name="Id", table_name="Sales", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Amount", table_name="Sales", data_type="decimal", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Customer", table_name="Sales", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
    )

    date_table = TableInfo(
        name="Date",
        type="Table",
        columns=[
            ColumnInfo(name="Date", table_name="Date", data_type="date", data_category=DataTypeCategory.DATE),
            ColumnInfo(name="Year", table_name="Date", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Month", table_name="Date", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
    )

    measures = [
        MeasureInfo(name="Total Sales", table_name="Sales", expression="SUM(Sales[Amount])", data_type="decimal"),
    ]

    schema = SemanticModelSchema(
        model_name="TestModel",
        workspace_name="TestWorkspace",
        tables=[sales_table, date_table],
        measures=measures,
    )
    return schema


def test_validator_catches_unbalanced_brackets():
    schema = build_min_schema()
    gen = SemPyDAXGenerator(schema)
    dax = "EVALUATE\nSUMMARIZE(Sales, Sales[Id)"  # Missing closing bracket for column
    result = gen.validate_generated_dax(dax)
    assert result["is_valid"] is False
    assert any("Unbalanced brackets" in e for e in result["errors"]) or any(
        "Unbalanced parentheses" in e for e in result["errors"]
    )


def test_validator_warns_on_unknown_table_or_measure():
    schema = build_min_schema()
    gen = SemPyDAXGenerator(schema)
    dax = "EVALUATE\nSUMMARIZE( UnknownTable, \"X\", [Unknown Measure] )"
    result = gen.validate_generated_dax(dax)
    assert result["is_valid"] is True  # Warnings should not make it invalid
    assert any("Referenced table not found" in w for w in result["warnings"]) or any(
        "Measure not found" in w for w in result["warnings"]
    )
