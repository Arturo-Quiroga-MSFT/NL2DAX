# Database Setup and Configuration Scripts

This directory contains scripts for setting up databases, configuring service principals, and preparing the environment for NL2DAX pipeline operations.

## Database Setup Scripts

### Data Export and Connection
- **`export_all_tables.py`** - Export all database tables for analysis and backup
- **`db_connection_check.py`** - Test and validate database connectivity

### Service Principal Management
- **`add_sp_to_dataset.py`** - Python script to add service principal to Power BI datasets
- **`add_service_principal.ps1`** - PowerShell script for basic service principal setup
- **`add_service_principal_with_login.ps1`** - Enhanced service principal with login configuration
- **`add_sp_comprehensive.ps1`** - Comprehensive service principal setup with full permissions
- **`add_sp_to_dataset.ps1`** - PowerShell version of dataset service principal assignment

### Security and Access Management
- **`create_security_group.ps1`** - Create Azure AD security groups for organized access
- **`check_workspace_members.ps1`** - Audit workspace membership and permissions

### Power BI Configuration
- **`enable_xmla_endpoints.ps1`** - Enable XMLA read/write endpoints for Power BI Premium

## Typical Setup Workflow

1. **Database Connection Setup**:
   ```bash
   python db_connection_check.py
   ```

2. **Export Database Schema**:
   ```bash
   python export_all_tables.py
   ```

3. **Service Principal Configuration**:
   ```powershell
   .\add_sp_comprehensive.ps1
   ```

4. **Power BI Workspace Setup**:
   ```powershell
   .\enable_xmla_endpoints.ps1
   .\check_workspace_members.ps1
   ```

5. **Security Group Management**:
   ```powershell
   .\create_security_group.ps1
   ```

## Prerequisites

### For Python Scripts
- Python 3.8+ with required packages
- Valid Azure SQL Database connection
- Appropriate Azure AD permissions

### For PowerShell Scripts
- PowerShell 5.1+ or PowerShell Core 7+
- Azure PowerShell module (`Install-Module Az`)
- Power BI PowerShell module (`Install-Module MicrosoftPowerBIMgmt`)
- Global Administrator or Power BI Administrator permissions

## Environment Variables

Many scripts rely on environment variables. Ensure these are set:

```bash
# Azure SQL Database
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DB=your-database-name
AZURE_SQL_USER=your-username
AZURE_SQL_PASSWORD=your-password

# Azure AD Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-client-id
AZURE_CLIENT_SECRET=your-app-client-secret

# Power BI Configuration
PBI_WORKSPACE_ID=your-workspace-id
PBI_DATASET_ID=your-dataset-id
```

## Security Considerations

- **Service Principal Permissions**: Grant minimum required permissions
- **Secret Management**: Store secrets securely, never commit to version control
- **Access Reviews**: Regularly audit service principal and workspace access
- **Principle of Least Privilege**: Apply minimal permissions for functionality

## Troubleshooting

Common issues and solutions:

1. **Authentication Failures**: Verify service principal has correct permissions
2. **XMLA Endpoint Issues**: Ensure Power BI Premium capacity and proper workspace configuration
3. **Database Connection**: Check firewall rules and authentication methods
4. **PowerShell Execution**: May need to set execution policy: `Set-ExecutionPolicy RemoteSigned`
