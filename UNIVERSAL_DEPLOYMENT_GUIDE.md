"""
UNIVERSAL NL2DAX DEPLOYMENT GUIDE
=================================

Quick Start Guide for Database-Agnostic Deployment
==================================================

OVERVIEW
--------
The Universal NL2DAX system can be deployed with ANY SQL database or Power BI semantic model
without code modifications. The system automatically discovers schema patterns and adapts
query generation to the specific database structure.

PREREQUISITES
------------
1. Python 3.8+ environment
2. Azure OpenAI API access
3. Target SQL database (any type)
4. Optional: Power BI/Fabric access for DAX queries

INSTALLATION STEPS
==================

1. Environment Setup
-------------------
```bash
# Clone or copy the NL2DAX_PIPELINE directory
cd /path/to/NL2DAX/CODE/NL2DAX_PIPELINE

# Install required packages
pip install -r requirements.txt

# Additional packages for universal system
pip install langchain-openai python-dotenv pandas plotly streamlit
```

2. Configuration
---------------
Create a .env file with your credentials:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Database Configuration (any SQL database)
DB_SERVER=your_server.database.windows.net
DB_DATABASE=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_DRIVER=ODBC Driver 17 for SQL Server

# Power BI Configuration (optional)
PBI_TENANT_ID=your_tenant_id
PBI_CLIENT_ID=your_client_id
PBI_CLIENT_SECRET=your_client_secret
PBI_WORKSPACE_NAME=your_workspace_name
PBI_DATASET_NAME=your_dataset_name
```

3. Database Validation
---------------------
Test database connectivity:

```bash
python -c "from schema_reader import get_schema_metadata; print('Schema tables:', len(get_schema_metadata()['tables']))"
```

4. System Testing
----------------
Run the universal demo:

```bash
python demo_universal_safe.py
```

Expected output:
```
✅ Interface initialized successfully!
📊 Schema Summary:
   • Total Tables: X
   • Fact Tables: Y
   • Dimension Tables: Z
   • Business Areas: [discovered areas]
   • Complexity: [Low/Medium/High]
```

DEPLOYMENT OPTIONS
==================

Option 1: Command Line Interface
--------------------------------
For batch processing and testing:

```bash
python main_universal.py
```

Features:
- Interactive query input
- Automatic schema analysis
- Both SQL and DAX generation
- Results saved to timestamped files

Option 2: Streamlit Web Interface
--------------------------------
For business user self-service:

```bash
streamlit run streamlit_universal_ui.py
```

Features:
- Interactive web interface
- Real-time query generation
- Automatic visualizations
- Schema exploration tools

Option 3: API Integration
------------------------
Import as Python modules:

```python
from universal_query_interface import UniversalQueryInterface, QueryType

# Initialize interface
interface = UniversalQueryInterface()

# Generate queries
result = interface.generate_query_from_intent(
    "Show me top customers by revenue", 
    QueryType.BOTH
)

print("SQL:", result.sql_query)
print("DAX:", result.dax_query)
```

ADAPTING TO NEW DATABASES
=========================

The beauty of the universal system is that it requires ZERO code changes for new databases.

For a New SQL Database:
----------------------
1. Update database connection in .env file
2. Run schema discovery: `python demo_universal_safe.py`
3. System automatically adapts to new schema
4. Generate queries for new database structure

Example - Switching from Banking to Retail:
```env
# OLD: Banking database
DB_DATABASE=banking_portfolio

# NEW: Retail database  
DB_DATABASE=retail_sales
```

The system will automatically:
- Discover product, customer, sales tables
- Identify fact/dimension relationships
- Generate appropriate business queries
- Adapt visualizations to retail concepts

For a New Power BI Model:
------------------------
1. Update Power BI workspace/dataset in .env
2. System discovers semantic model structure
3. Generates DAX queries adapted to model relationships
4. Works with any Power BI/Fabric semantic model

PRODUCTION CONSIDERATIONS
========================

Performance Optimization
-----------------------
- Schema metadata is cached automatically
- Query results cached for 5 minutes in Streamlit
- Consider implementing Redis for distributed caching
- Monitor AI API usage and implement rate limiting

Security Best Practices
----------------------
- Store credentials in secure environment variables
- Use Azure Key Vault for production secrets
- Implement proper authentication for web interface
- Audit query generation and execution logs

Monitoring and Maintenance
-------------------------
- Monitor schema discovery performance
- Track query generation success rates
- Set up alerts for database connection failures
- Regular testing with sample queries

Scaling Considerations
--------------------
- System handles databases with 100+ tables efficiently
- Consider query complexity limits for very large schemas
- Implement user access controls for sensitive data
- Plan for multiple concurrent users in web interface

TROUBLESHOOTING
==============

Common Issues and Solutions
--------------------------

1. "Schema analysis not available"
   - Check database connection string in .env
   - Verify database accessibility and credentials
   - Ensure ODBC driver is installed

2. "Query generation failed"
   - Verify Azure OpenAI credentials
   - Check API quota and rate limits
   - Ensure deployment name is correct

3. "DAX execution failed"
   - Verify Power BI workspace access
   - Check dataset permissions
   - Ensure proper Azure AD authentication

4. "No business suggestions"
   - Normal for databases without clear business patterns
   - System still generates queries on demand
   - Consider adding custom business concepts

Testing with Sample Data
-----------------------
```bash
# Test schema discovery
python -c "from universal_query_interface import UniversalQueryInterface; ui = UniversalQueryInterface(); print(ui.get_schema_summary())"

# Test query generation
python -c "from universal_query_interface import UniversalQueryInterface, QueryType; ui = UniversalQueryInterface(); result = ui.generate_query_from_intent('Show me all records', QueryType.SQL); print(result.sql_query)"
```

BUSINESS VALUE REALIZATION
==========================

Immediate Benefits
-----------------
- Deploy to new clients without custom development
- Support multiple databases with single codebase
- Enable business users to generate queries independently
- Reduce time-to-value from weeks to hours

Long-term Advantages
-------------------
- Scalable architecture grows with business needs
- Consistent query quality across all databases
- Easy maintenance and updates
- Future-proof design for new database technologies

Success Metrics
--------------
- Time to deploy to new database: < 1 hour
- Query generation success rate: > 95%
- Business user adoption: Self-service capable
- Development effort reduction: 80%+ for new databases

CONCLUSION
==========

The Universal NL2DAX system transforms database-specific query generation into a 
platform that adapts to any database automatically. This deployment guide provides
everything needed to get the system running in production with your specific database.

The key insight is that the system requires NO code changes for different databases -
simply update the connection string and the AI-powered schema discovery handles the rest.

For support or questions about deployment, refer to the comprehensive architecture
documentation and demo scripts provided with the system.

Contact: NL2DAX Development Team
Last Updated: August 17, 2025
Version: Universal 1.0
"""