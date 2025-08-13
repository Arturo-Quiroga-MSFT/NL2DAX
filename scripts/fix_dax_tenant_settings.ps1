# PowerShell script to enable "Dataset Execute Queries REST API" tenant setting
# This script requires Power BI Administrator privileges

Write-Host "🚀 Power BI Tenant Settings Fix for DAX 401 Error" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host ""

# Check if user has admin rights
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Warning "⚠️  This script should be run as Administrator for best results"
    Write-Host ""
}

# Install required modules
Write-Host "🔧 Checking required PowerShell modules..." -ForegroundColor Cyan

$requiredModules = @(
    @{Name = "MicrosoftPowerBIMgmt"; MinVersion = "1.2.1077"},
    @{Name = "Az.Accounts"; MinVersion = "2.0.0"}
)

foreach ($module in $requiredModules) {
    $installed = Get-Module -Name $module.Name -ListAvailable | Sort-Object Version -Descending | Select-Object -First 1
    
    if (-not $installed -or $installed.Version -lt [version]$module.MinVersion) {
        Write-Host "📦 Installing $($module.Name)..." -ForegroundColor Yellow
        try {
            Install-Module -Name $module.Name -MinimumVersion $module.MinVersion -Force -AllowClobber -Scope CurrentUser
            Write-Host "✅ $($module.Name) installed successfully" -ForegroundColor Green
        }
        catch {
            Write-Error "❌ Failed to install $($module.Name): $($_.Exception.Message)"
            exit 1
        }
    } else {
        Write-Host "✅ $($module.Name) is already installed (v$($installed.Version))" -ForegroundColor Green
    }
}

Write-Host ""

# Connect to Power BI
Write-Host "🔐 Connecting to Power BI..." -ForegroundColor Cyan

try {
    # Try to connect to Power BI
    Connect-PowerBIServiceAccount -WarningAction SilentlyContinue
    
    # Verify connection
    $context = Get-PowerBIAccessToken -AsString
    if ($context) {
        Write-Host "✅ Successfully connected to Power BI" -ForegroundColor Green
    } else {
        throw "Failed to get access token"
    }
}
catch {
    Write-Error "❌ Failed to connect to Power BI: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "💡 Please ensure you have Power BI Administrator privileges" -ForegroundColor Yellow
    Write-Host "   and try running: Connect-PowerBIServiceAccount" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Function to check and update tenant settings
function Set-PowerBITenantSetting {
    param(
        [string]$SettingName,
        [string]$DisplayName,
        [bool]$EnabledState = $true,
        [string]$TenantSettingGroup = "entire organization"
    )
    
    Write-Host "🔍 Checking '$DisplayName' setting..." -ForegroundColor Cyan
    
    try {
        # Get current tenant settings
        $tenantSettings = Invoke-PowerBIRestMethod -Url "admin/tenantsettings" -Method Get | ConvertFrom-Json
        
        # Find the specific setting
        $setting = $tenantSettings.tenantSettings | Where-Object { $_.settingName -eq $SettingName }
        
        if ($setting) {
            $currentState = $setting.enabled
            Write-Host "   Current state: $($currentState ? 'Enabled' : 'Disabled')" -ForegroundColor $(if ($currentState) { 'Green' } else { 'Red' })
            
            if ($currentState -eq $EnabledState) {
                Write-Host "✅ '$DisplayName' is already correctly configured" -ForegroundColor Green
                return $true
            } else {
                Write-Host "🔧 Updating '$DisplayName' setting..." -ForegroundColor Yellow
                
                # Prepare the update payload
                $updatePayload = @{
                    settingName = $SettingName
                    enabled = $EnabledState
                    tenantSettingGroup = $TenantSettingGroup
                } | ConvertTo-Json
                
                # Update the setting
                $response = Invoke-PowerBIRestMethod -Url "admin/tenantsettings" -Method Patch -Body $updatePayload
                
                Write-Host "✅ '$DisplayName' has been updated successfully" -ForegroundColor Green
                return $true
            }
        } else {
            Write-Warning "⚠️  Setting '$SettingName' not found in tenant settings"
            return $false
        }
    }
    catch {
        Write-Error "❌ Failed to update '$DisplayName': $($_.Exception.Message)"
        return $false
    }
}

# Main execution
Write-Host "🎯 Fixing Power BI tenant settings for DAX execution..." -ForegroundColor Green
Write-Host ""

# Critical settings for DAX execution
$settingsToFix = @(
    @{
        Name = "DatasetExecuteQueries"
        DisplayName = "Dataset Execute Queries REST API"
        Description = "Controls DAX query execution via REST API"
    },
    @{
        Name = "ServicePrincipalAccess"
        DisplayName = "Allow service principals to use Power BI APIs"
        Description = "Enables service principal authentication"
    },
    @{
        Name = "EmbedContent"
        DisplayName = "Embed content in apps"
        Description = "Allows embedding content (may be required)"
    }
)

$allSuccess = $true

foreach ($setting in $settingsToFix) {
    Write-Host "=" * 50 -ForegroundColor Gray
    Write-Host "$($setting.Description)" -ForegroundColor White
    
    $result = Set-PowerBITenantSetting -SettingName $setting.Name -DisplayName $setting.DisplayName
    $allSuccess = $allSuccess -and $result
    
    Write-Host ""
}

# Summary
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host "📊 CONFIGURATION SUMMARY" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Yellow

if ($allSuccess) {
    Write-Host "✅ All required tenant settings have been configured correctly!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "   1. ⏱️  Wait 15-20 minutes for changes to propagate across the service" -ForegroundColor White
    Write-Host "   2. 🧪 Test DAX execution: python CODE/xmla_status_check.py" -ForegroundColor White
    Write-Host "   3. 🚀 If still not working, run: python CODE/diagnose_permissions.py" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 If the issue persists after 20 minutes, the service principal may need" -ForegroundColor Yellow
    Write-Host "   to be added to a specific security group that has access to these settings." -ForegroundColor Yellow
} else {
    Write-Host "❌ Some settings could not be updated. Please check the errors above." -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 MANUAL STEPS:" -ForegroundColor Cyan
    Write-Host "   1. Go to Power BI Admin Portal (https://app.powerbi.com/admin-portal)" -ForegroundColor White
    Write-Host "   2. Navigate to Tenant Settings" -ForegroundColor White
    Write-Host "   3. Look for 'Export and sharing settings'" -ForegroundColor White
    Write-Host "   4. Enable 'Dataset Execute Queries REST API'" -ForegroundColor White
    Write-Host "   5. Set scope to 'Entire organization' or add your service principal's group" -ForegroundColor White
}

Write-Host ""
Write-Host "🔍 For verification, you can also check the settings manually at:" -ForegroundColor Cyan
Write-Host "   https://app.powerbi.com/admin-portal/tenantSettings" -ForegroundColor Blue

Write-Host ""
Write-Host "✨ Script completed!" -ForegroundColor Green
