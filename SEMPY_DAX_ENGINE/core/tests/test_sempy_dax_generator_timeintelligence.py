import pytest

from SEMPY_DAX_ENGINE.core.semantic_analyzer import (
    SemanticModelSchema, TableInfo, ColumnInfo, MeasureInfo, DataTypeCategory
)
from SEMPY_DAX_ENGINE.core.sempy_dax_generator import SemPyDAXGenerator, QueryAnalysis, QueryIntent


def build_schema_with_date():
    sales_table = TableInfo(
        name="Sales",
        type="Table",
        is_fact_table=True,
        columns=[
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


def test_time_intelligence_generates_summarizecolumns():
    schema = build_schema_with_date()
    gen = SemPyDAXGenerator(schema)
    analysis = QueryAnalysis(
        original_query="Average sales by month",
        intent=QueryIntent.AGGREGATION,
        entities=["measure:Total Sales"],
        filters=[],
        aggregations=["avg"],
        grouping=["month"],
        ordering=None,
        limit=None,
        time_context="by month",
    )
    dax = gen._generate_time_intelligence_dax(analysis)
    assert "SUMMARIZECOLUMNS" in dax
    assert "Date[Month]" in dax or "[Month]" in dax
    assert "[Total Sales]" in dax
