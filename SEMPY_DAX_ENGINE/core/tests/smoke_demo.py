from SEMPY_DAX_ENGINE.core.sempy_dax_generator import SemPyDAXGenerator
from SEMPY_DAX_ENGINE.core.semantic_analyzer import (
    SemanticModelSchema,
    TableInfo,
    ColumnInfo,
    MeasureInfo,
    DataTypeCategory,
)


def build_min_schema():
    sales = TableInfo(
        name="Sales",
        type="Table",
        columns=[
            ColumnInfo(name="SalesId", table_name="Sales", data_type="int", data_category=DataTypeCategory.NUMERIC, is_key=True),
            ColumnInfo(name="Amount", table_name="Sales", data_type="decimal", data_category=DataTypeCategory.NUMERIC),
            ColumnInfo(name="OrderDate", table_name="Sales", data_type="datetime", data_category=DataTypeCategory.DATE),
        ],
        is_fact_table=True,
    )
    date = TableInfo(
        name="Date",
        type="Table",
        columns=[
            ColumnInfo(name="Date", table_name="Date", data_type="datetime", data_category=DataTypeCategory.DATE),
            ColumnInfo(name="Month", table_name="Date", data_type="string", data_category=DataTypeCategory.TEXT),
            ColumnInfo(name="Year", table_name="Date", data_type="int", data_category=DataTypeCategory.NUMERIC),
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
    return SemanticModelSchema(
        model_name="TestModel",
        workspace_name="TestWorkspace",
        tables=[sales, date],
        measures=measures,
        relationships=[],
    )


if __name__ == "__main__":
    gen = SemPyDAXGenerator(build_min_schema())
    examples = [
        "total sales by month",
        "count by year",
        "list sales",
    ]
    for q in examples:
        plan = gen.generate_dax_query(q)
        print("\n=== NL:", q)
        print(plan.dax_expression)
