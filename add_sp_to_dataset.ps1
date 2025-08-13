# PowerShell script to add Service Principal to Power BI Dataset
# Run this script with appropriate permissions

# Install Power BI Management module if not already installed
Write-Host "Checking for Power BI Management module..." -ForegroundColor Yellow
if (!(Get-Module -ListAvailable -Name MicrosoftPowerBIMgmt)) {
    Write-Host "Installing MicrosoftPowerBIMgmt module..." -ForegroundColor Green
    Install-Module -Name MicrosoftPowerBIMgmt -Force -Scope CurrentUser
    Write-Host "Module installed successfully!" -ForegroundColor Green
} else {
    Write-Host "MicrosoftPowerBIMgmt module already installed." -ForegroundColor Green
}

# Import the module
Import-Module MicrosoftPowerBIMgmt

# Configuration - Update these values if needed
$DatasetId = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"
$ServicePrincipalClientId = "20c5495d-b98c-410b-aa7b-9ea13dd70f61"
$WorkspaceId = "e3fdee99-3aa4-4d71-a530-2964a062e326"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Dataset ID: $DatasetId" -ForegroundColor White
Write-Host "  Service Principal Client ID: $ServicePrincipalClientId" -ForegroundColor White
Write-Host "  Workspace ID: $WorkspaceId" -ForegroundColor White
Write-Host ""

# Connect to Power BI Service
Write-Host "Connecting to Power BI Service..." -ForegroundColor Yellow
Write-Host "You will be prompted to sign in with an account that has admin privileges." -ForegroundColor Yellow

try {
    Connect-PowerBIServiceAccount
    Write-Host "Successfully connected to Power BI Service!" -ForegroundColor Green
} catch {
    Write-Host "Failed to connect to Power BI Service: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Check current dataset users before adding
Write-Host "Checking current dataset users..." -ForegroundColor Yellow
try {
    $CurrentUsers = Get-PowerBIDatasetUser -DatasetId $DatasetId -Scope Organization
    Write-Host "Current dataset users:" -ForegroundColor Cyan
    foreach ($user in $CurrentUsers) {
        Write-Host "  - $($user.Identifier) ($($user.PrincipalType)) - $($user.DatasetUserAccessRight)" -ForegroundColor White
    }
    
    # Check if Service Principal already exists
    $ExistingSP = $CurrentUsers | Where-Object { $_.Identifier -eq $ServicePrincipalClientId }
    if ($ExistingSP) {
        Write-Host "Service Principal already exists in dataset users with permission: $($ExistingSP.DatasetUserAccessRight)" -ForegroundColor Yellow
        $continue = Read-Host "Do you want to continue anyway? (y/n)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Host "Operation cancelled." -ForegroundColor Yellow
            exit 0
        }
    }
} catch {
    Write-Host "Warning: Could not retrieve current dataset users: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Add Service Principal to dataset with ReadWrite permissions
Write-Host "Adding Service Principal to dataset users..." -ForegroundColor Yellow
try {
    # Method 1: Try Add-PowerBIDatasetUser (preferred)
    Add-PowerBIDatasetUser -DatasetId $DatasetId -UserEmailAddress $ServicePrincipalClientId -AccessRight "ReadWrite" -Scope Organization
    Write-Host "SUCCESS! Service Principal added to dataset users with ReadWrite permission." -ForegroundColor Green
} catch {
    Write-Host "Method 1 failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Method 2: Try alternative with different access right
    Write-Host "Trying alternative method..." -ForegroundColor Yellow
    try {
        Add-PowerBIDatasetUser -DatasetId $DatasetId -UserEmailAddress $ServicePrincipalClientId -AccessRight "Read" -Scope Organization
        Write-Host "SUCCESS! Service Principal added to dataset users with Read permission." -ForegroundColor Green
        Write-Host "Note: You may need to manually upgrade to ReadWrite permission in Power BI Service UI." -ForegroundColor Yellow
    } catch {
        Write-Host "Method 2 also failed: $($_.Exception.Message)" -ForegroundColor Red
        
        # Method 3: Try workspace-level approach
        Write-Host "Trying workspace-level approach..." -ForegroundColor Yellow
        try {
            Add-PowerBIWorkspaceUser -WorkspaceId $WorkspaceId -UserEmailAddress $ServicePrincipalClientId -AccessRight "Admin" -Scope Organization
            Write-Host "SUCCESS! Service Principal added to workspace users with Admin permission." -ForegroundColor Green
            Write-Host "This should provide dataset access as well." -ForegroundColor Green
        } catch {
            Write-Host "All methods failed: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "You may need to add the Service Principal manually through Power BI Service UI." -ForegroundColor Yellow
        }
    }
}

# Verify the addition
Write-Host "Verifying the addition..." -ForegroundColor Yellow
try {
    Start-Sleep -Seconds 2  # Wait a moment for changes to propagate
    $UpdatedUsers = Get-PowerBIDatasetUser -DatasetId $DatasetId -Scope Organization
    Write-Host "Updated dataset users:" -ForegroundColor Cyan
    foreach ($user in $UpdatedUsers) {
        if ($user.Identifier -eq $ServicePrincipalClientId) {
            Write-Host "  ✅ $($user.Identifier) ($($user.PrincipalType)) - $($user.DatasetUserAccessRight)" -ForegroundColor Green
        } else {
            Write-Host "  - $($user.Identifier) ($($user.PrincipalType)) - $($user.DatasetUserAccessRight)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "Could not verify the addition: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Script completed!" -ForegroundColor Green
Write-Host "You can now test DAX query execution with your Service Principal." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test your DAX queries using the Python scripts" -ForegroundColor White
Write-Host "2. If still getting 401 errors, check Power BI Admin Portal > Tenant Settings" -ForegroundColor White
Write-Host "3. Ensure 'Service principals can use Power BI APIs' is enabled" -ForegroundColor White

# Disconnect from Power BI Service
Disconnect-PowerBIServiceAccount
