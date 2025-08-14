# NL2DAX Pipeline - Core Components

This directory contains the main Natural Language to DAX/SQL pipeline and all its core dependencies.

## Core Files

### Main Entry Point
- **`main.py`** - Main pipeline entrypoint demonstrating end-to-end NL2DAX/NL2SQL processing

### Query Generation Modules
- **`dax_generator.py`** - Handles DAX query generation from intent/entities using Azure OpenAI
- **`sql_executor.py`** - Azure SQL Database query execution module
- **`schema_reader.py`** - Database schema reading and caching functionality

### Query Execution Modules
- **`query_executor.py`** - Power BI semantic model query execution coordinator
- **`xmla_http_executor.py`** - Cross-platform XMLA execution using HTTP + Azure AD authentication

### Utilities
- **`dax_formatter.py`** - DAX syntax validation and formatting using daxformatter.com API

## Configuration Files

### Required Setup
- **`.env`** - Environment variables (create from `.env.example`)
- **`.env.example`** - Template showing required environment variables
- **`requirements.txt`** - Python package dependencies
- **`schema_cache.json`** - Cached database schema (auto-generated)

## Environment Variables Required

### Azure OpenAI Configuration
```bash
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
```

### Power BI/Analysis Services (for DAX execution)
```bash
USE_XMLA_HTTP=true
PBI_TENANT_ID=your-tenant-id
PBI_CLIENT_ID=your-app-client-id
PBI_CLIENT_SECRET=your-app-client-secret
PBI_XMLA_ENDPOINT=powerbi://api.powerbi.com/v1.0/myorg/your-workspace
PBI_DATASET_NAME=your-dataset-name
```

### Azure SQL Database (for SQL execution)
```bash
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DB=your-database-name
AZURE_SQL_USER=your-username
AZURE_SQL_PASSWORD=your-password
```

## Usage

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Run Pipeline**:
   ```bash
   python main.py
   ```

3. **Follow Prompts**:
   - Enter natural language query
   - Pipeline will generate both SQL and DAX
   - Execute against configured databases
   - Display formatted results

## Output

- Console: Formatted table results and debugging information
- File: Timestamped execution logs in `nl2dax_run_*_*.txt` format

## Dependencies

All Python dependencies are listed in `requirements.txt`. Key packages:
- `langchain` and `langchain-openai` for LLM integration
- `pyodbc` for SQL Server connectivity
- `msal` for Azure AD authentication
- `requests` for HTTP API calls
- `python-dotenv` for environment variable management

## Platform Notes

- **Windows**: Full native support
- **macOS/Linux**: Requires proper ODBC driver setup for SQL Server connectivity
- **Docker**: All dependencies can be containerized
