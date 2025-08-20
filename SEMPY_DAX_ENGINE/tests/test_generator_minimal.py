"""
Minimal tests for SemPyDAXGenerator:
- Validator warnings when EVALUATE is missing but structure is valid
- Preferred-table disambiguation for bare column names
- Time-intelligence generation uses SUMMARIZECOLUMNS with date grouping
"""

from SEMPY_DAX_ENGINE.core.sempy_dax_generator import SemPyDAXGenerator
from SEMPY_DAX_ENGINE.core.semantic_analyzer import (
    SemanticModelSchema,
    TableInfo,
    ColumnInfo,
    MeasureInfo,
    DataTypeCategory,
)


def build_minimal_schema():
    # Date dimension
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

    # Customers dimension
    customers_table = TableInfo(
        name="Customers",
        type="Table",
        columns=[
            ColumnInfo(name="CustomerId", table_name="Customers", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Name", table_name="Customers", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
        is_dimension_table=True,
    )

    # Sales fact
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


def test_validator_missing_evaluate_warns_not_errors():
    schema = build_minimal_schema()
    gen = SemPyDAXGenerator(schema)

    dax = 'SUMMARIZE(\n    Sales,\n    Sales[Name],\n    "Total", COUNTROWS(Sales)\n)'
    res = gen.validate_generated_dax(dax)

    assert res["is_valid"] is True
    assert any("evaluate" in w.lower() for w in res["warnings"])  # warn on missing EVALUATE
    assert not res["errors"]


def test_preferred_table_disambiguation_on_bare_column():
    schema = build_minimal_schema()
    gen = SemPyDAXGenerator(schema)

    # Column Name exists in both Sales and Customers, prefer Customers
    col = gen._to_bracketed_column("Name", preferred_table="Customers")
    assert col == "Customers[Name]"

    # Prefer Sales if specified
    col2 = gen._to_bracketed_column("Name", preferred_table="Sales")
    assert col2 == "Sales[Name]"


def test_time_intelligence_generates_summarizecolumns():
    schema = build_minimal_schema()
    gen = SemPyDAXGenerator(schema)

    # NL query that should trigger aggregation + time context
    plan = gen.generate_dax_query("total sales by month")
    dax = plan.dax_expression

    assert dax.strip().startswith("EVALUATE")
    assert "SUMMARIZECOLUMNS" in dax
    # Expect a reference to Date table month column
    assert "Date[Month]" in dax or "Date[Year]" in dax
    # Measure label should appear
    assert "\"Total Sales\"" in dax
