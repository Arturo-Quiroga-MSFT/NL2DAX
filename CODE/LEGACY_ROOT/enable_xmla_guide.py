#!/usr/bin/env python3
"""
Script to create PowerShell commands for enabling XMLA endpoints
"""

print("""
🔧 ENABLE XMLA ENDPOINTS - STEP BY STEP INSTRUCTIONS
================================================================

OPTION 1: Power BI Admin Portal (Recommended)
----------------------------------------------
1. Go to https://admin.powerbi.com
2. Sign in with your admin account (admin@MngEnvMCAP094150.onmicrosoft.com)
3. Navigate to "Tenant settings" in the left menu
4. Scroll down to find "XMLA endpoint and Analyze in Excel with on-premises datasets"
5. Toggle it to "Enabled"
6. Choose scope: "The entire organization" or specific security groups
7. Click "Apply"

OPTION 2: Workspace-Level Settings
-----------------------------------
1. Go to https://app.powerbi.com
2. Navigate to your "FIS" workspace
3. Click the gear icon (⚙️) → "Workspace settings"
4. Go to the "Premium" tab
5. Set "XMLA Endpoint" to "Read" or "Read Write"
6. Click "Save"

OPTION 3: PowerShell Admin Commands
------------------------------------
""")

# Generate PowerShell commands
workspace_id = "e3fdee99-3aa4-4d71-a530-2964a062e326"
dataset_id = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"

print(f"""
# Check current tenant settings
Get-PowerBIAdminTenant | Select-Object -Property XmlaEndpointEnabled

# Enable XMLA endpoints for the entire tenant (requires tenant admin)
Set-PowerBIAdminTenant -XmlaEndpointEnabled $true

# Check workspace settings
Get-PowerBIWorkspace -Id "{workspace_id}" | Select-Object -Property Name, Id, IsOnDedicatedCapacity

# Alternative: Use REST API to check/set workspace settings
$headers = @{{
    "Authorization" = "Bearer $(Get-PowerBIAccessToken | Select-Object -ExpandProperty AccessToken)"
    "Content-Type" = "application/json"
}}

$workspaceUrl = "https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
Invoke-RestMethod -Uri $workspaceUrl -Headers $headers -Method Get
""")

print("""
TESTING AFTER ENABLING
-----------------------
After enabling XMLA endpoints, wait 5-10 minutes for settings to propagate, then run:

python diagnose_permissions.py

VERIFICATION CHECKLIST
----------------------
□ Tenant-level XMLA setting is enabled
□ Workspace is on Premium capacity (✅ already confirmed)
□ Service principal has workspace access (✅ already confirmed) 
□ Service principal has dataset permissions (✅ already confirmed)
□ XMLA endpoint is enabled for the workspace
□ Wait 5-10 minutes after making changes

If issues persist, the alternative is to use a different API approach
that doesn't require XMLA endpoints.
""")
