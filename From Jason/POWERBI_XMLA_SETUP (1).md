# Power BI XMLA environment setup

Use this guide to obtain and set the values needed to run DAX over the Power BI XMLA endpoint from this project.

## Checklist
- PBI_TENANT_ID: Copy your Microsoft Entra ID (Azure AD) tenant ID.
- PBI_CLIENT_ID: Register an app; copy its Application (client) ID.
- PBI_CLIENT_SECRET: Create a client secret on that app; copy its Secret Value.
- PBI_XMLA_ENDPOINT: Copy the Workspace connection URL from your Power BI workspace (Premium/PPU).   
- PBI_DATASET_NAME: Use the dataset (semantic model) display name in that workspace. 

## How to get each value

### PBI_TENANT_ID
- Azure Portal: Microsoft Entra ID (Azure AD) → Overview → Tenant ID (GUID).
- Optional CLI:

```bash
# Optional
az login
az account show --query tenantId -o tsv
```

### PBI_CLIENT_ID and PBI_CLIENT_SECRET
1) Azure Portal → Microsoft Entra ID → App registrations → New registration.
   - Name: e.g., nl2dax-sp
   - Supported account types: Accounts in this organizational directory
   - Register → copy Application (client) ID → use as PBI_CLIENT_ID
2) Certificates & secrets → New client secret
   - Copy the Secret Value immediately → use as PBI_CLIENT_SECRET (store securely; not in Git)
3) Power BI Admin (Tenant settings): enable service principals and XMLA usage
   - Power BI Service → Admin portal (gear icon) → Tenant settings
   - Developer settings:
     - Allow service principals to use Power BI APIs: Enabled (entire org or a security group containing your app)
     - Users can work with semantic models using the XMLA endpoint: Enabled (entire org or allowed groups)  ***Don't have this setting so I used Service Principals can call Fabric public APIs
   ****- Integration Settings
     - Semantic Model Execute Queries REST API**** 


### PBI_XMLA_ENDPOINT
- Power BI Service → open the target workspace (must be Premium capacity or PPU)
  - Workspace settings → Premium → copy Workspace connection
  - It looks like: `powerbi://api.powerbi.com/v1.0/myorg/<workspace-name>`  See 
  *** I'm using this API which doesn't contain the workspace ID.  https://api.powerbi.com/v1.0/myorg/datasets/{datasetId}/executeQueries or this site for testing out the API.  https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries ****

### PBI_DATASET_NAME
- Power BI Service → the same workspace
  - Find the dataset (Semantic model) you will query; use its display name exactly.
  ******Display name hasn't worked for me and I use GUID********

## Required access
- Grant the service principal (the app registration) access to the workspace (Member/Contributor) or give it Build permission on the specific dataset. This is required for XMLA access.
- The workspace must be Premium capacity or PPU for XMLA endpoints to work.
-  - ******* Setup API permissions for service principal that is Power BI Services with Dataset.Read.all and Dataset.ReadWriteall****

## .env example
Create or update your `.env` (do not commit secrets):

```ini
PBI_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PBI_CLIENT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
PBI_CLIENT_SECRET=your-secret-value
PBI_XMLA_ENDPOINT=powerbi://api.powerbi.com/v1.0/myorg/Your-Workspace
PBI_DATASET_NAME=YourDatasetName   ***GUID****
```

## Notes
- The client secret Value is shown only once when you create it—store it securely (Key Vault, 1Password, etc.).
- If you later get 401/403 errors when running DAX:
  - Recheck the Tenant settings toggles for service principals and XMLA in the Power BI Admin portal.
  - Confirm the app is added to the workspace and has Build access to the dataset.
  - Verify the workspace is Premium or PPU and that you copied the correct Workspace connection URL.
