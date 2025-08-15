# Diagnostics and Troubleshooting Scripts

This directory contains comprehensive diagnostic tools, troubleshooting scripts, and system health checks for Power BI, Azure Fabric, and the NL2DAX pipeline.

## Main Diagnostic Scripts

### Comprehensive Diagnostics
- **`fabric_api_with_scopes.py`** - Complete Fabric mirrored database diagnostics with proper API scopes
- **`comprehensive_mirrored_db_diagnostic.py`** - Full mirrored database troubleshooting suite
- **`powerbi_admin_inspector.py`** - Admin API dataset inspection with detailed properties
- **`mirrored_db_source_checker.py`** - Source Azure SQL connection verification for mirrored databases

### System Health Checks
- **`status_report_aug14.py`** - Comprehensive system status report and health check
- **`smoke_test_xmla.py`** - Quick XMLA endpoint connectivity and functionality test

## Categorized Diagnostic Tools

### Connection and Authentication
- **`check_dataset_content.py`** - Verify dataset content and structure
- **`check_mirrored_db_connection.py`** - Test mirrored database connectivity
- **`check_mirrored_db_status.py`** - Check mirrored database refresh status
- **`check_premium_capacity.py`** - Verify Premium capacity configuration
- **`check_xmla_capacity.py`** - XMLA endpoint capacity verification
- **`check_xmla_config.py`** - XMLA configuration validation

### Permission and Access Diagnostics
- **`diagnose_permissions.py`** - Comprehensive permission diagnostics
- **`test_permissions.py`** - Basic permission testing
- **`test_permissions_detailed.py`** - Detailed permission validation
- **`test_prerequisites.py`** - System prerequisite verification
- **`troubleshoot_permissions.py`** - Permission troubleshooting workflows

### Fabric-Specific Tools
- **`fabric_capacity_status.py`** - Fabric capacity monitoring and status
- **`fabric_mirrored_database_handler.py`** - Mirrored database management operations
- **`fabric_sync_and_refresh.py`** - Fabric synchronization and refresh operations

### Performance and Analysis
- **`api_compliance_analysis.py`** - API usage compliance and analysis
- **`test_endpoint_comparison.py`** - Compare different API endpoint performance
- **`test_rest_api_dax.py`** - REST API DAX execution testing
- **`alternative_table_discovery.py`** - Alternative methods for table discovery

### Issue Resolution
- **`fix_capacity_permissions.py`** - Automated capacity permission fixes
- **`fix_dax_401.py`** - Resolve DAX 401 authentication errors
- **`fix_semantic_model_refresh.py`** - Fix semantic model refresh issues
- **`fix_workspace_capacity.py`** - Workspace capacity assignment fixes
- **`resume_capacity.py`** - Resume paused Premium capacity

### Validation and Testing
- **`test_capacity_status.py`** - Test capacity status and availability
- **`test_sql_queries.py`** - SQL query execution testing
- **`test_xmla_simple.py`** - Simple XMLA connectivity test
- **`verify_xmla_setup.py`** - Comprehensive XMLA setup verification

### Utilities and Helpers
- **`investigate_error_details.py`** - Deep dive error investigation
- **`list_datasets.py`** - List and analyze available datasets
- **`security_group_guide.py`** - Security group configuration guidance
- **`xmla_status_check.py`** - XMLA endpoint status monitoring

## Usage Patterns

### Quick Health Check
```bash
python status_report_aug14.py
python smoke_test_xmla.py
```

### Comprehensive Diagnostics
```bash
python fabric_api_with_scopes.py
python comprehensive_mirrored_db_diagnostic.py
python powerbi_admin_inspector.py
```

### Permission Troubleshooting
```bash
python diagnose_permissions.py
python test_permissions_detailed.py
python troubleshoot_permissions.py
```

### Fabric Mirrored Database Issues
```bash
python mirrored_db_source_checker.py
python check_mirrored_db_status.py
python fabric_sync_and_refresh.py
```

### 401 Error Resolution
```bash
python fix_dax_401.py
python fix_capacity_permissions.py
python verify_xmla_setup.py
```

## Common Diagnostic Workflows

### 1. New Environment Setup Validation
1. Run `test_prerequisites.py`
2. Execute `verify_xmla_setup.py`
3. Test with `smoke_test_xmla.py`

### 2. Mirrored Database Troubleshooting
1. Check status with `check_mirrored_db_status.py`
2. Verify source with `mirrored_db_source_checker.py`
3. Run comprehensive diagnostic with `comprehensive_mirrored_db_diagnostic.py`

### 3. Permission Issues
1. Diagnose with `diagnose_permissions.py`
2. Get detailed analysis with `test_permissions_detailed.py`
3. Apply fixes with `fix_capacity_permissions.py`

### 4. Performance Issues
1. Check capacity with `check_premium_capacity.py`
2. Compare endpoints with `test_endpoint_comparison.py`
3. Analyze API usage with `api_compliance_analysis.py`

## Environment Requirements

Most scripts require these environment variables:
```bash
# Azure AD Authentication
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Power BI Configuration
PBI_WORKSPACE_ID=your-workspace-id
PBI_DATASET_ID=your-dataset-id
PBI_XMLA_ENDPOINT=powerbi://api.powerbi.com/v1.0/myorg/workspace-name

# Azure SQL (for mirrored database diagnostics)
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DB=your-database-name
AZURE_SQL_USER=your-username
AZURE_SQL_PASSWORD=your-password
```

## Output and Logging

- Most scripts provide detailed console output
- Many generate timestamped log files
- Error details are captured for further analysis
- Status reports include actionable recommendations

## Best Practices

1. **Start with comprehensive diagnostics** before targeted fixes
2. **Run status reports regularly** to monitor system health
3. **Keep diagnostic logs** for trend analysis
4. **Test fixes in development** before applying to production
5. **Document custom configurations** discovered through diagnostics
