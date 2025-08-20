import re
from SEMPY_DAX_ENGINE.core.sempy_dax_generator import SemPyDAXGenerator
from SEMPY_DAX_ENGINE.core.semantic_analyzer import (
    SemanticModelSchema,
    TableInfo,
    ColumnInfo,
    MeasureInfo,
    DataTypeCategory,
)


def build_min_schema():
    # Tables
    sales = TableInfo(
        name="Sales",
        type="Table",
        columns=[
            ColumnInfo(name="SalesId", table_name="Sales", data_type="int", data_category=DataTypeCategory.NUMERIC, is_key=True),
            ColumnInfo(name="Amount", table_name="Sales", data_type="decimal", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="CustomerId", table_name="Sales", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="OrderDate", table_name="Sales", data_type="datetime", data_category=DataTypeCategory.DATE),
            ColumnInfo(name="Name", table_name="Sales", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
        is_fact_table=True,
    )

    customer = TableInfo(
        name="Customer",
        type="Table",
        columns=[
            ColumnInfo(name="CustomerId", table_name="Customer", data_type="int", data_category=DataTypeCategory.NUMERIC, is_key=True),
            ColumnInfo(name="Name", table_name="Customer", data_type="string", data_category=DataTypeCategory.TEXT),
            ColumnInfo(name="Country", table_name="Customer", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
        is_dimension_table=True,
    )

    date = TableInfo(
        name="Date",
        type="Table",
        columns=[
            ColumnInfo(name="Date", table_name="Date", data_type="datetime", data_category=DataTypeCategory.DATE),
            ColumnInfo(name="Year", table_name="Date", data_type="int", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="Month", table_name="Date", data_type="string", data_category=DataTypeCategory.TEXT),
            ColumnInfo(name="Quarter", table_name="Date", data_type="string", data_category=DataTypeCategory.TEXT),
        ],
        is_dimension_table=True,
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
        tables=[sales, customer, date],
        measures=measures,
        relationships=[],
    )
    return schema


def test_validator_unbalanced_brackets():
    gen = SemPyDAXGenerator(build_min_schema())
    bad_dax = "EVALUATE\nSUMMARIZE( Sales, Sales[Amount )"  # missing closing bracket
    v = gen.validate_generated_dax(bad_dax)
    assert v["is_valid"] is False
    assert any("Unbalanced" in e for e in v["errors"])  # has structural error


def test_validator_ok_with_evaluate():
    gen = SemPyDAXGenerator(build_min_schema())
    good_dax = "EVALUATE\nSUMMARIZE( Sales, Sales[Name], \"Total Rows\", COUNTROWS(Sales) )"
    v = gen.validate_generated_dax(good_dax)
    assert v["is_valid"] is True
    # EVALUATE present so no warning about missing evaluate
    assert not any("does not contain EVALUATE" in w for w in v["warnings"]) 


def test_preferred_table_bracketing():
    gen = SemPyDAXGenerator(build_min_schema())
    # Ambiguous column Name exists in both Sales and Customer; prefer Customer
    assert gen._to_bracketed_column("Name", preferred_table="Customer") == "Customer[Name]"
    # Explicit table.column should bracket
    assert gen._to_bracketed_column("Sales.Amount", preferred_table=None) == "Sales[Amount]"


def test_time_intelligence_uses_summarizecolumns():
    gen = SemPyDAXGenerator(build_min_schema())
    plan = gen.generate_dax_query("total sales by month")
    dax = plan.dax_expression
    assert "SUMMARIZECOLUMNS" in dax
    assert re.search(r"Date\[[^\]]*Month\]", dax)  # includes a Date[Month] grouping
    # should include the explicit measure if detected
    assert '"Total Sales"' in dax or "[Total Sales]" in dax


def test_groupby_columns_are_bracketed():
    gen = SemPyDAXGenerator(build_min_schema())
    plan = gen.generate_dax_query("count by country")
    dax = plan.dax_expression
    # either SUMMARIZE (fallback) or SUMMARIZECOLUMNS, but the column should be bracketed
    assert "Customer[Country]" in dax
