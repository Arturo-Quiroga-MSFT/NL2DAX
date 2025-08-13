# 🛠️ scripts Directory

This directory contains PowerShell scripts and shell utilities for setting up, configuring, and troubleshooting the NL2DAX Power BI integration.

## 📋 Overview

The scripts automate complex setup procedures, particularly for Power BI service principal configuration and XMLA endpoint management. These tools are essential for initial deployment and ongoing maintenance.

## 📁 Script Inventory

### PowerShell Scripts (.ps1)

| Script | Purpose | Requirements |
|--------|---------|--------------|
| `create_service_principal.ps1` | Create and configure service principal | Azure admin rights |
| `enable_xmla_endpoints.ps1` | Enable XMLA in Power BI admin portal | Power BI admin rights |
| `add_security_group.ps1` | Create Azure AD security group | Azure AD admin rights |
| `setup_permissions.ps1` | Configure all required permissions | Combined admin rights |

### Shell Scripts (.sh)

| Script | Purpose | Platform |
|--------|---------|----------|
| `pbi_xmla_troubleshoot.sh` | XMLA connectivity troubleshooting | macOS/Linux |
| `setup_environment.sh` | Complete environment setup | macOS/Linux |

### Documentation

| File | Purpose |
|------|---------|
| `POWERBI_XMLA_SETUP.md` | Comprehensive setup guide |
| `setup_checklist.md` | Step-by-step checklist |

## 🚀 Quick Setup

### Automated Setup (Recommended)

```powershell
# Run complete setup (requires admin rights)
.\scripts\setup_permissions.ps1 -TenantId "your-tenant-id" -WorkspaceName "Your Workspace"
```

### Manual Setup (Step by Step)

1. **Create Service Principal**
   ```powershell
   .\scripts\create_service_principal.ps1 -AppName "NL2DAX-ServicePrincipal"
   ```

2. **Create Security Group**
   ```powershell
   .\scripts\add_security_group.ps1 -GroupName "PowerBI-XMLA-Access"
   ```

3. **Enable XMLA Endpoints**
   ```powershell
   .\scripts\enable_xmla_endpoints.ps1
   ```

## 📜 Script Details

### create_service_principal.ps1

**Purpose:** Creates a new Azure AD application and service principal for Power BI access.

**Parameters:**
- `-AppName` (required): Name for the Azure AD application
- `-TenantId` (optional): Azure tenant ID (auto-detected if not provided)
- `-OutputFile` (optional): Path to save credentials (default: `.env`)

**Output:**
- Azure AD application
- Service principal with appropriate permissions
- Client ID and secret saved to specified file

**Usage:**
```powershell
.\create_service_principal.ps1 -AppName "NL2DAX-App" -OutputFile "../CODE/.env"
```

**What it does:**
1. Creates Azure AD application registration
2. Generates client secret with 2-year expiration
3. Assigns necessary API permissions
4. Creates service principal
5. Outputs credentials in .env format

### enable_xmla_endpoints.ps1

**Purpose:** Enables XMLA read-write endpoints in Power BI tenant settings.

**Requirements:**
- Power BI administrator privileges
- Power BI PowerShell module

**Parameters:**
- `-SecurityGroupId` (optional): Limit XMLA access to specific security group
- `-ReadOnly` (switch): Enable only read access (default: read-write)

**Usage:**
```powershell
# Enable for entire organization
.\enable_xmla_endpoints.ps1

# Enable for specific security group
.\enable_xmla_endpoints.ps1 -SecurityGroupId "group-object-id"

# Enable read-only access
.\enable_xmla_endpoints.ps1 -ReadOnly
```

**What it does:**
1. Connects to Power BI Admin APIs
2. Updates tenant settings for XMLA endpoints
3. Configures security group restrictions (if specified)
4. Verifies settings were applied correctly

### add_security_group.ps1

**Purpose:** Creates Azure AD security group for Power BI XMLA access management.

**Parameters:**
- `-GroupName` (required): Name for the security group
- `-Description` (optional): Group description
- `-Members` (optional): Array of user UPNs to add as members

**Usage:**
```powershell
.\add_security_group.ps1 -GroupName "PowerBI-XMLA-Users" -Members @("user1@domain.com", "user2@domain.com")
```

**What it does:**
1. Creates new Azure AD security group
2. Adds specified members
3. Configures group for Power BI service access
4. Returns group object ID for use in other scripts

### pbi_xmla_troubleshoot.sh

**Purpose:** Comprehensive XMLA connectivity troubleshooting for macOS/Linux.

**Features:**
- Network connectivity tests
- DNS resolution verification
- SSL certificate validation
- Authentication testing
- XMLA endpoint discovery

**Usage:**
```bash
chmod +x pbi_xmla_troubleshoot.sh
./pbi_xmla_troubleshoot.sh
```

**Interactive prompts:**
- Workspace name or ID
- Service principal credentials
- Test query to execute

## 🔧 Configuration Management

### Environment Variable Setup

Several scripts can automatically configure environment variables:

```powershell
# Generate complete .env file
.\create_service_principal.ps1 -AppName "NL2DAX" -OutputFile "../CODE/.env"

# The script outputs:
# POWER_BI_CLIENT_ID=generated-client-id
# POWER_BI_CLIENT_SECRET=generated-secret
# POWER_BI_TENANT_ID=your-tenant-id
```

### Credential Management

**Best practices:**
- Store secrets in Azure Key Vault for production
- Use managed identities when possible
- Rotate secrets regularly (scripts support this)

**Secret rotation:**
```powershell
# Create new secret for existing app
.\create_service_principal.ps1 -AppName "existing-app" -RotateSecret
```

## 🔍 Troubleshooting Scripts

### Common Issues and Solutions

1. **XMLA Endpoints Not Working**
   ```bash
   # Run comprehensive diagnostics
   ./pbi_xmla_troubleshoot.sh
   
   # Check specific connectivity
   python ../CODE/xmla_status_check.py
   ```

2. **Service Principal Authentication Failures**
   ```powershell
   # Verify service principal setup
   .\verify_service_principal.ps1 -ClientId "your-client-id"
   ```

3. **Permission Issues**
   ```powershell
   # Re-apply all permissions
   .\setup_permissions.ps1 -Fix
   ```

### Diagnostic Output

Scripts generate detailed logs for troubleshooting:

```
📊 Power BI XMLA Troubleshoot Results
=====================================
✅ DNS Resolution: powerbi.com resolves correctly
✅ Network Connectivity: Can reach powerbi.com:443
✅ SSL Certificate: Valid and trusted
❌ Authentication: 401 Unauthorized
⚠️  Recommendation: Check service principal permissions

Detailed logs saved to: troubleshoot_2025-01-14_10-30-45.log
```

## 📋 Setup Checklist

Use this checklist when setting up a new environment:

### Prerequisites
- [ ] Azure subscription with admin rights
- [ ] Power BI Premium license
- [ ] PowerShell 5.1 or newer
- [ ] Azure PowerShell module installed
- [ ] Power BI PowerShell module installed

### Service Principal Setup
- [ ] Run `create_service_principal.ps1`
- [ ] Save credentials to `.env` file
- [ ] Verify service principal creation in Azure portal

### Power BI Configuration
- [ ] Run `enable_xmla_endpoints.ps1`
- [ ] Create security group (optional)
- [ ] Add service principal to workspace
- [ ] Grant dataset permissions

### Verification
- [ ] Test with `../CODE/diagnose_permissions.py`
- [ ] Verify XMLA with `../CODE/xmla_status_check.py`
- [ ] Run end-to-end test with `../CODE/main.py`

## 🔐 Security Considerations

### Service Principal Permissions

The scripts configure minimal required permissions:
- **Power BI Service**: Dataset.Read.All, Dashboard.Read.All
- **Azure AD**: User.Read (for token validation)
- **Microsoft Graph**: Directory.Read.All (for group membership)

### Security Group Strategy

```powershell
# Create production group with limited membership
.\add_security_group.ps1 -GroupName "PowerBI-XMLA-Production" -Members @("service-account@domain.com")

# Create development group with broader access
.\add_security_group.ps1 -GroupName "PowerBI-XMLA-Development" -Members @("dev-team@domain.com")
```

### Credential Storage

**Development:**
- Use `.env` files (excluded from Git)
- Rotate secrets monthly

**Production:**
- Use Azure Key Vault
- Implement managed identities where possible
- Automate secret rotation

## 🔄 Maintenance Scripts

### Regular Maintenance Tasks

1. **Monthly Secret Rotation**
   ```powershell
   .\rotate_secrets.ps1 -AppName "NL2DAX" -NotifyEmail "admin@domain.com"
   ```

2. **Permission Audit**
   ```powershell
   .\audit_permissions.ps1 -GenerateReport
   ```

3. **Health Check**
   ```bash
   # Run weekly health check
   ./health_check.sh --email-report admin@domain.com
   ```

### Backup and Recovery

```powershell
# Backup current configuration
.\backup_config.ps1 -OutputPath "./backups/"

# Restore from backup
.\restore_config.ps1 -BackupPath "./backups/config-2025-01-14.json"
```

---

💡 **Tip**: Always test scripts in a development environment before running in production. Most scripts include a `-WhatIf` parameter for dry-run testing.
