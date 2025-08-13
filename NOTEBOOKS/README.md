# 📓 NOTEBOOKS Directory

This directory contains Jupyter notebooks demonstrating Power BI REST API integration and DAX query execution through HTTP endpoints.

## 📋 Overview

The notebooks provide interactive examples of how to connect to Power BI using REST APIs, execute DAX queries, and handle authentication using service principals. These are particularly useful for understanding the underlying API calls that the main application makes.

## 📚 Notebook Contents

### PowerBI_RESTAPI_DAX_Query_Example.ipynb
**Primary REST API demonstration notebook**

**What it covers:**
- Service principal authentication with Azure AD
- Power BI REST API endpoint discovery
- DAX query execution via HTTP requests
- Response parsing and data visualization
- Error handling for common authentication issues

**Key sections:**
1. **Authentication Setup** - Service principal configuration
2. **API Discovery** - Finding workspace and dataset IDs
3. **DAX Execution** - Sending queries via REST API
4. **Result Processing** - Parsing JSON responses into dataframes
5. **Visualization** - Basic charts and tables from query results

**Prerequisites:**
- Service principal with Power BI permissions
- Jupyter notebook environment
- Required Python packages (see notebook requirements)

### PowerBI_RESTAPI_DAX_Query_Example2.ipynb
**Advanced scenarios and troubleshooting**

**What it covers:**
- Advanced authentication patterns
- Batch query execution
- Performance optimization techniques
- Comprehensive error handling
- Integration with pandas and visualization libraries

**Key sections:**
1. **Advanced Auth** - Token refresh and session management
2. **Batch Operations** - Multiple queries in sequence
3. **Performance Tips** - Optimizing API calls
4. **Error Recovery** - Handling timeouts and failures
5. **Data Export** - Saving results to various formats

## 🚀 Getting Started

### Prerequisites

1. **Jupyter Environment**
   ```bash
   pip install jupyter notebook
   # or
   pip install jupyterlab
   ```

2. **Required Packages**
   ```bash
   pip install requests pandas matplotlib seaborn azure-identity python-dotenv
   ```

3. **Power BI Setup**
   - Service principal with appropriate permissions
   - Power BI Premium workspace
   - Dataset with DAX query support

### Running the Notebooks

1. **Start Jupyter**
   ```bash
   # From the NOTEBOOKS directory
   jupyter notebook
   # or
   jupyter lab
   ```

2. **Open a notebook**
   - Click on `PowerBI_RESTAPI_DAX_Query_Example.ipynb`
   - Follow the cell-by-cell instructions

3. **Configure credentials**
   - Either use environment variables
   - Or update the credential cells directly (not recommended for production)

## 🔐 Authentication Configuration

### Service Principal Setup

The notebooks use service principal authentication. You'll need:

```python
# Configuration variables (use environment variables in production)
CLIENT_ID = "your-service-principal-client-id"
CLIENT_SECRET = "your-service-principal-client-secret"
TENANT_ID = "your-azure-tenant-id"
WORKSPACE_ID = "your-powerbi-workspace-id"
DATASET_ID = "your-powerbi-dataset-id"
```

### Environment Variables

Create a `.env` file in the NOTEBOOKS directory:

```bash
# Power BI Service Principal
POWER_BI_CLIENT_ID=your-service-principal-client-id
POWER_BI_CLIENT_SECRET=your-service-principal-secret
POWER_BI_TENANT_ID=your-azure-tenant-id
POWER_BI_WORKSPACE_ID=your-powerbi-workspace-id
POWER_BI_DATASET_ID=your-powerbi-dataset-id

# Optional: API endpoints (use defaults if not specified)
POWER_BI_API_BASE=https://api.powerbi.com/v1.0/myorg
AZURE_AD_AUTHORITY=https://login.microsoftonline.com
```

## 📊 Example Queries

The notebooks include several sample DAX queries:

### Basic Table Query
```dax
EVALUATE
TOPN(
    10,
    FIS_CUSTOMER_DIMENSION,
    FIS_CUSTOMER_DIMENSION[CUSTOMER_NAME],
    ASC
)
```

### Aggregation Query
```dax
EVALUATE
SUMMARIZE(
    FIS_CL_DETAIL_FACT,
    FIS_CUSTOMER_DIMENSION[COUNTRY_DESCRIPTION],
    "TotalBalance", SUM(FIS_CL_DETAIL_FACT[TOTAL_BALANCE]),
    "CustomerCount", DISTINCTCOUNT(FIS_CL_DETAIL_FACT[CUSTOMER_KEY])
)
```

### Complex Analysis
```dax
EVALUATE
ADDCOLUMNS(
    SUMMARIZE(
        FIS_CL_DETAIL_FACT,
        FIS_CUSTOMER_DIMENSION[RISK_RATING_DESCRIPTION],
        "TotalExposure", SUM(FIS_CL_DETAIL_FACT[TOTAL_BALANCE])
    ),
    "NPLRatio", 
    DIVIDE(
        CALCULATE(
            SUM(FIS_CL_DETAIL_FACT[TOTAL_BALANCE]),
            FIS_CL_DETAIL_FACT[IS_NON_PERFORMING] = TRUE
        ),
        [TotalExposure],
        0
    )
)
```

## 🔍 Troubleshooting Guide

### Common Issues

1. **Authentication Failures**
   ```python
   # Check service principal permissions
   # Verify tenant ID is correct
   # Ensure client secret hasn't expired
   ```

2. **DAX Query Errors**
   ```python
   # Verify table and column names match your dataset
   # Check for syntax errors in DAX
   # Ensure proper data types in calculations
   ```

3. **API Rate Limiting**
   ```python
   import time
   # Add delays between requests
   time.sleep(1)  # Wait 1 second between API calls
   ```

### Debug Techniques

1. **Enable Verbose Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Inspect API Responses**
   ```python
   print(f"Status Code: {response.status_code}")
   print(f"Response Headers: {response.headers}")
   print(f"Response Content: {response.text}")
   ```

3. **Validate Token**
   ```python
   # Check token expiration
   import jwt
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(f"Token expires: {decoded.get('exp')}")
   ```

## 📈 Data Visualization Examples

The notebooks include several visualization patterns:

### Bar Charts
```python
import matplotlib.pyplot as plt

# Simple bar chart from DAX results
df.plot(kind='bar', x='Country', y='TotalBalance', 
        title='Total Balance by Country')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### Heat Maps
```python
import seaborn as sns

# Create pivot table for heatmap
pivot_table = df.pivot_table(
    values='TotalBalance', 
    index='RiskRating', 
    columns='Country', 
    aggfunc='sum'
)

sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd')
plt.title('Total Balance by Risk Rating and Country')
plt.show()
```

### Time Series
```python
# Convert date columns and plot trends
df['Date'] = pd.to_datetime(df['PeriodEndDate'])
df.plot(x='Date', y='TotalBalance', kind='line', 
        title='Balance Trend Over Time')
plt.show()
```

## 🔄 Integration with Main Application

The notebooks demonstrate the same API calls that the main application (`../CODE/`) uses internally. This makes them valuable for:

- **Debugging API issues** - Step through calls manually
- **Testing new queries** - Rapid prototyping in interactive environment
- **Understanding responses** - See raw API responses
- **Performance analysis** - Measure query execution times

### Code Reuse

Many functions from the notebooks can be extracted and used in the main application:

```python
# Example: Extract authentication function
def get_power_bi_token(client_id, client_secret, tenant_id):
    """Get Power BI access token using service principal"""
    # Implementation from notebook
    pass

# Use in main application
from notebook_utils import get_power_bi_token
token = get_power_bi_token(CLIENT_ID, CLIENT_SECRET, TENANT_ID)
```

## 📦 Dependencies

The notebooks require these additional packages beyond the main application:

```bash
# Jupyter environment
pip install jupyter notebook jupyterlab

# Data analysis and visualization
pip install pandas matplotlib seaborn plotly

# API interaction
pip install requests azure-identity

# Utility libraries
pip install python-dotenv python-dateutil
```

## 🎯 Best Practices

1. **Security**
   - Never commit credentials to version control
   - Use environment variables for sensitive data
   - Regularly rotate service principal secrets

2. **Performance**
   - Cache authentication tokens
   - Batch multiple queries when possible
   - Use appropriate timeouts for API calls

3. **Error Handling**
   - Always check response status codes
   - Implement retry logic for transient failures
   - Log errors for debugging

4. **Data Management**
   - Validate DAX query results
   - Handle empty result sets gracefully
   - Export important results to persistent storage

---

💡 **Tip**: Start with `PowerBI_RESTAPI_DAX_Query_Example.ipynb` for basic concepts, then move to the second notebook for advanced scenarios.
