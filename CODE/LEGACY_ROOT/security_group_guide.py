#!/usr/bin/env python3
"""
Step-by-step guide for creating security groups and enabling XMLA endpoints
"""

print("""
🔐 POWER BI SECURITY GROUP SETUP GUIDE
=====================================

STEP 1: CREATE AZURE AD SECURITY GROUP
---------------------------------------
1. Go to: https://portal.azure.com
2. Sign in with your admin account
3. Navigate: Azure Active Directory → Groups → New group
4. Fill in details:
   ┌─────────────────────────────────────────────┐
   │ Group type: Security                        │
   │ Group name: PowerBI-XMLA-Users              │
   │ Group description: Power BI XMLA access    │
   │ Membership type: Assigned                   │
   │ Members: Add users/service principals       │
   └─────────────────────────────────────────────┘
5. Click "Create"

STEP 2: ADD SERVICE PRINCIPAL TO GROUP
--------------------------------------
1. In the newly created group, click "Members"
2. Click "Add members"
3. Search for your service principal:
   - App ID: 20c5495d-b98c-410b-aa7b-9ea13dd70f61
   - Or Object ID: 41c1b8cc-b650-4313-9543-3527e362694d
4. Select and add it

STEP 3: ENABLE XMLA IN POWER BI ADMIN PORTAL
--------------------------------------------
1. Go to: https://admin.powerbi.com
2. Sign in with admin account: admin@MngEnvMCAP094150.onmicrosoft.com
3. Navigate: Tenant settings (left menu)
4. Scroll to: "XMLA endpoint and Analyze in Excel with on-premises datasets"
5. Toggle: Enabled
6. Apply to: "Specific security groups"
7. Add group: "PowerBI-XMLA-Users" (or your group name)
8. Click "Apply"

STEP 4: WORKSPACE-LEVEL SETTINGS (OPTIONAL)
-------------------------------------------
1. Go to: https://app.powerbi.com
2. Navigate to: FIS workspace
3. Click: Settings (gear icon) → Workspace settings
4. Go to: Premium tab
5. Set: XMLA Endpoint to "Read" or "Read Write"
6. Click: Save

STEP 5: WAIT AND TEST
--------------------
1. Wait 5-10 minutes for settings to propagate
2. Test with: python CODE/smoke_test_xmla.py
3. Or run: python diagnose_permissions.py

ALTERNATIVE: POWERSHELL AUTOMATION
----------------------------------
Run the PowerShell script to automate group creation:
pwsh -File create_security_group.ps1

TROUBLESHOOTING
---------------
❌ If group creation fails:
   • Ensure you have Azure AD admin rights
   • Try using PowerShell with AzureAD module

❌ If XMLA still doesn't work:
   • Verify group membership includes service principal
   • Check tenant-level settings in admin portal
   • Ensure workspace is on Premium capacity (✅ already confirmed)

❌ If you can't access admin portal:
   • You need Power BI Service Administrator role
   • Or Global Administrator role

VERIFICATION CHECKLIST
----------------------
□ Azure AD security group created
□ Service principal added to group
□ XMLA endpoint enabled in admin portal
□ Group specified in tenant settings
□ Waited 5-10 minutes for propagation
□ Tested with diagnostic script

Your service principal credentials:
-----------------------------------
Tenant ID: a172a259-b1c7-4944-b2e1-6d551f954711
Client ID: 20c5495d-b98c-410b-aa7b-9ea13dd70f61
Object ID: 41c1b8cc-b650-4313-9543-3527e362694d
Workspace: FIS (e3fdee99-3aa4-4d71-a530-2964a062e326)
Dataset: FIS-SEMANTIC-MODEL (3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007)
""")
