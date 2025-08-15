# 🔄 NL2SQL&DAX Unified Pipeline

A comprehensive solution for executing both SQL and DAX queries from natural language input, connecting directly to Azure SQL Database to ensure data consistency and eliminate dependency on Power BI semantic models.

## 🎯 Overview

This unified pipeline addresses the fundamental challenge of data consistency between SQL and DAX queries by:

- **Direct Database Connection**: Both SQL and DAX queries execute against the same Azure SQL Database
- **Natural Language Processing**: Convert plain English questions into both SQL and DAX queries
- **Result Comparison**: Validate data consistency between query types
- **Performance Analysis**: Compare execution times and efficiency
- **Query Caching**: Improve performance with intelligent caching
- **Web Interface**: User-friendly Streamlit interface for testing and demonstration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│ Natural Language│───▶│ Unified Pipeline│───▶│   Azure SQL     │
│     Input       │    │   Orchestrator  │    │   Database      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼───┐  ┌────▼────┐  ┌───▼────┐
            │    SQL    │  │   DAX   │  │ Cache  │
            │ Generator │  │Generator│  │Manager │
            └───────────┘  └─────────┘  └────────┘
                    │           │           │
                    └───────────┼───────────┘
                                │
                    ┌───────────▼───────────┐
                    │                       │
                    │   Result Formatter    │
                    │   & Comparator        │
                    │                       │
                    └───────────────────────┘
```

## 📦 Components

### Core Pipeline Components

1. **`unified_pipeline.py`** - Main orchestrator that coordinates all components
2. **`azure_sql_executor.py`** - Executes both SQL and DAX queries against Azure SQL Database
3. **`schema_analyzer.py`** - Analyzes database schema and provides metadata
4. **`sql_generator.py`** - Converts natural language to SQL using Azure OpenAI
5. **`dax_generator.py`** - Converts natural language to DAX using Azure OpenAI
6. **`result_formatter.py`** - Formats and compares query results
7. **`query_cache.py`** - Provides caching capabilities for improved performance

### Web Interface

8. **`streamlit_app.py`** - Interactive web interface for testing and demonstration

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure SQL Database
- Azure OpenAI API access
- Required Python packages (see `requirements.txt`)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd NL2SQL_DAX_UNIFIED_PIPELINE
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create a `.env` file with the following variables:
   ```env
   # Azure SQL Database
   AZURE_SQL_SERVER=your-server.database.windows.net
   AZURE_SQL_DATABASE=your-database-name
   AZURE_SQL_USERNAME=your-username
   AZURE_SQL_PASSWORD=your-password
   
   # Azure OpenAI
   AZURE_OPENAI_API_KEY=your-openai-api-key
   AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   
   # Optional: Query caching
   CACHE_ENABLED=true
   CACHE_TTL=3600
   ```

### Running the Pipeline

#### Option 1: Web Interface (Recommended)
```bash
streamlit run streamlit_app.py
```

#### Option 2: Command Line
```python
from unified_pipeline import UnifiedPipeline

# Initialize pipeline
pipeline = UnifiedPipeline()

# Execute a query
results = pipeline.execute_pipeline(
    user_input="Show me the top 10 customers by total balance",
    execute_sql=True,
    execute_dax=True,
    compare_results=True
)

# Display results
print(results)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_SQL_SERVER` | Azure SQL Server hostname | ✅ |
| `AZURE_SQL_DATABASE` | Database name | ✅ |
| `AZURE_SQL_USERNAME` | Database username | ✅ |
| `AZURE_SQL_PASSWORD` | Database password | ✅ |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | ✅ |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | ✅ |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name | ✅ |
| `AZURE_OPENAI_API_VERSION` | API version | ✅ |
| `CACHE_ENABLED` | Enable query caching | ❌ |
| `CACHE_TTL` | Cache time-to-live (seconds) | ❌ |
| `MAX_RETRIES` | Maximum query retries | ❌ |
| `QUERY_TIMEOUT` | Query timeout (seconds) | ❌ |

### Pipeline Options

The pipeline can be configured with various options:

```python
pipeline = UnifiedPipeline(
    cache_enabled=True,
    cache_ttl=3600,
    max_retries=3,
    timeout=60
)
```

## 📊 Features

### Natural Language Processing
- Convert plain English questions to SQL and DAX
- Support for complex analytical queries
- Context-aware query generation based on database schema

### Query Execution
- Direct Azure SQL Database connectivity
- DAX-to-SQL translation for consistent results
- Comprehensive error handling and retries
- Query timeout management

### Result Comparison
- Row-by-row data comparison
- Column count and type validation
- Performance metrics comparison
- Detailed difference reporting

### Caching System
- Intelligent query result caching
- Configurable TTL (Time-To-Live)
- Cache invalidation strategies
- Performance statistics tracking

### Web Interface
- Interactive query input
- Real-time result display
- Performance visualization
- Query history tracking
- Schema exploration
- Export capabilities

## 🧪 Example Queries

The pipeline supports various types of natural language queries:

### Basic Queries
- "Show me all customers"
- "List all active loans"
- "What are the available product types?"

### Analytical Queries
- "Show me the top 10 customers by total balance"
- "What is the average loan amount by risk rating?"
- "List customers with balances over $100,000"

### Aggregation Queries
- "Count the number of customers by status"
- "Sum the total exposure by counterparty"
- "Average transaction amount by month"

### Complex Queries
- "Show me customers with high-risk loans and their total exposure"
- "List the monthly trend of new customer acquisitions"
- "Find customers with multiple products and their combined balances"

## 📈 Performance Optimization

### Query Caching
- Results are cached based on query hash and schema version
- Configurable TTL to balance freshness and performance
- Automatic cache invalidation on schema changes

### Connection Pooling
- Efficient database connection management
- Connection reuse across multiple queries
- Automatic connection recovery

### Parallel Execution
- SQL and DAX queries can execute in parallel
- Non-blocking result comparison
- Optimized resource utilization

## 🔍 Monitoring and Debugging

### Logging
The pipeline provides comprehensive logging:
- Query generation details
- Execution timings
- Error traces
- Cache hit/miss statistics

### Performance Metrics
Track key performance indicators:
- Query execution times
- Cache hit rates
- Error rates
- Resource utilization

### Debug Mode
Enable detailed debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

pipeline = UnifiedPipeline(debug=True)
```

## 🛠️ Development

### Adding New Query Types
To support additional query languages:

1. Create a new generator class (e.g., `mdx_generator.py`)
2. Implement the required interface methods
3. Add the generator to the unified pipeline
4. Update the web interface to support the new type

### Extending the Schema Analyzer
To support additional database types:

1. Extend the `SchemaAnalyzer` class
2. Implement database-specific metadata queries
3. Add connection logic for the new database type

### Custom Result Formatters
Create specialized formatters for different output types:

1. Inherit from `ResultFormatter`
2. Implement custom formatting methods
3. Register the formatter with the pipeline

## 📝 Testing

### Unit Tests
Run the test suite:
```bash
python -m pytest tests/
```

### Integration Tests
Test with real database:
```bash
python test_integration.py
```

### Web Interface Testing
Test the Streamlit app:
```bash
streamlit run streamlit_app.py
# Navigate to http://localhost:8501
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the example queries and configurations

## 🔄 Changelog

### v1.0.0 (Current)
- Initial release with unified SQL/DAX pipeline
- Streamlit web interface
- Query caching system
- Result comparison and validation
- Comprehensive error handling
- Performance monitoring

---

**Built with ❤️ for data consistency and analytical excellence**