# Query Results Directory

This directory contains output files from the Universal NL2DAX System.

## File Naming Convention

Generated files follow this pattern:
```
universal_nl2dax_run_{query_description}_{timestamp}.txt
```

## Content Structure

Each result file contains:
1. **Schema Analysis** - Discovered database structure
2. **Business Suggestions** - AI-generated query recommendations  
3. **Natural Language Query** - User input
4. **Generated Queries** - SQL and/or DAX queries produced
5. **Execution Results** - Query output and data
6. **Performance Metrics** - Timing and system information

## Sample Files

After running the system, you'll see files like:
- `universal_nl2dax_run_top_customers_by_revenue_20250817_143022.txt`
- `universal_nl2dax_run_monthly_sales_trends_20250817_143155.txt`
- `universal_nl2dax_run_risk_analysis_by_region_20250817_143287.txt`

## Data Export Formats

The Streamlit interface also supports exporting results in:
- **CSV** - For spreadsheet analysis
- **JSON** - For API integration  
- **Excel** - For business reporting

## Cleanup

Result files can be safely deleted as they are regenerated with each query execution.