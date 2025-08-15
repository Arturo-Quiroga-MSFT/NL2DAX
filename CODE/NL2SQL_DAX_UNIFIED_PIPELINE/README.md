# NL2SQL & DAX Unified Pipeline

## Overview

This unified pipeline enables natural language queries to be converted to both SQL and DAX queries that execute directly against the **same Azure SQL Database**, ensuring complete data consistency between both query types.

## Architecture

```
Natural Language Query
         ↓
   Intent Extraction
         ↓
    Schema Analysis
         ↓
    ┌─────────────────┐
    │                 │
    ▼                 ▼
SQL Generator    DAX Generator
    │                 │
    ▼                 ▼
    ┌─────────────────┐
    │   Azure SQL DB  │
    │  (Single Source)│
    └─────────────────┘
```

## Key Benefits

1. **Data Consistency**: Both SQL and DAX queries execute against the same live Azure SQL database
2. **No Semantic Model Dependency**: Eliminates Power BI semantic model configuration issues
3. **Real-time Data**: All queries return live data directly from the source
4. **Simplified Architecture**: Single data source, dual query types
5. **Cost Effective**: No need for Power BI Premium or Fabric capacity

## Components

- `unified_pipeline.py` - Main pipeline orchestrator
- `sql_generator.py` - Natural language to SQL query generation
- `dax_generator.py` - Natural language to DAX query generation  
- `azure_sql_executor.py` - Azure SQL Database executor for both query types
- `schema_analyzer.py` - Database schema analysis and metadata extraction
- `result_formatter.py` - Unified result formatting and comparison
- `streamlit_app.py` - Web UI for the unified pipeline

## Configuration

Set these environment variables in your `.env` file:

```env
# Azure SQL Database (Primary Data Source)
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DB=your-database
AZURE_SQL_USER=your-username
AZURE_SQL_PASSWORD=your-password

# Azure OpenAI for NL processing
AZURE_OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
```

## Usage

```python
from unified_pipeline import UnifiedNL2SQLDAXPipeline

pipeline = UnifiedNL2SQLDAXPipeline()
result = pipeline.execute_query("Show me all customers with high risk ratings")
```

## Features

- ✅ Direct Azure SQL DB connectivity for both SQL and DAX
- ✅ Schema-aware query generation
- ✅ Result comparison and validation
- ✅ Error handling and debugging
- ✅ Performance metrics
- ✅ Streamlit web interface
- ✅ Query caching and optimization