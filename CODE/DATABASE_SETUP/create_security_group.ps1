# Create Azure AD Security Group for Power BI XMLA Access
# Requires AzureAD PowerShell module: Install-Module AzureAD

param(
    [Parameter(Mandatory=$false)]
    [string]$GroupName = "PowerBI-XMLA-Users",
    
    [Parameter(Mandatory=$false)]
    [string]$GroupDescription = "Security group for users with Power BI XMLA endpoint access",
    
    [Parameter(Mandatory=$false)]
    [string[]]$Members = @()
)

Write-Host "🔧 Creating Azure AD Security Group for Power BI..." -ForegroundColor Cyan

# Check if AzureAD module is installed
try {
    Import-Module AzureAD -ErrorAction Stop
    Write-Host "✅ AzureAD module loaded" -ForegroundColor Green
} catch {
    Write-Host "❌ AzureAD module not found. Installing..." -ForegroundColor Red
    try {
        Install-Module AzureAD -Force -Scope CurrentUser
        Import-Module AzureAD
        Write-Host "✅ AzureAD module installed and loaded" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install AzureAD module: $_" -ForegroundColor Red
        Write-Host "💡 Try running: Install-Module AzureAD -Force" -ForegroundColor Yellow
        exit 1
    }
}

# Connect to Azure AD
try {
    Write-Host "🔐 Connecting to Azure AD..." -ForegroundColor Yellow
    Connect-AzureAD
    Write-Host "✅ Connected to Azure AD" -ForegroundColor Green
    
    # Get current tenant info
    $tenant = Get-AzureADTenantDetail
    Write-Host "   Tenant: $($tenant.DisplayName)" -ForegroundColor White
    Write-Host "   Domain: $($tenant.VerifiedDomains[0].Name)" -ForegroundColor White
} catch {
    Write-Host "❌ Failed to connect to Azure AD: $_" -ForegroundColor Red
    exit 1
}

# Check if group already exists
Write-Host "`n🔍 Checking if group already exists..." -ForegroundColor Cyan
$existingGroup = Get-AzureADGroup -Filter "DisplayName eq '$GroupName'" -ErrorAction SilentlyContinue

if ($existingGroup) {
    Write-Host "⚠️  Group '$GroupName' already exists!" -ForegroundColor Yellow
    Write-Host "   Group ID: $($existingGroup.ObjectId)" -ForegroundColor White
    Write-Host "   Description: $($existingGroup.Description)" -ForegroundColor White
    
    $choice = Read-Host "Do you want to use the existing group? (y/n)"
    if ($choice -eq 'y' -or $choice -eq 'Y') {
        $group = $existingGroup
        Write-Host "✅ Using existing group" -ForegroundColor Green
    } else {
        Write-Host "❌ Exiting..." -ForegroundColor Red
        exit 0
    }
} else {
    # Create new security group
    Write-Host "`n🆕 Creating new security group..." -ForegroundColor Cyan
    try {
        $group = New-AzureADGroup -DisplayName $GroupName -Description $GroupDescription -SecurityEnabled $true -MailEnabled $false
        Write-Host "✅ Security group created successfully!" -ForegroundColor Green
        Write-Host "   Group Name: $($group.DisplayName)" -ForegroundColor White
        Write-Host "   Group ID: $($group.ObjectId)" -ForegroundColor White
        Write-Host "   Description: $($group.Description)" -ForegroundColor White
    } catch {
        Write-Host "❌ Failed to create security group: $_" -ForegroundColor Red
        exit 1
    }
}

# Add members if specified
if ($Members.Count -gt 0) {
    Write-Host "`n👥 Adding members to the group..." -ForegroundColor Cyan
    
    foreach ($member in $Members) {
        try {
            # Try to find user by UPN or display name
            $user = Get-AzureADUser -Filter "UserPrincipalName eq '$member' or DisplayName eq '$member'" -ErrorAction SilentlyContinue
            
            if (-not $user) {
                Write-Host "   ⚠️  User '$member' not found, skipping..." -ForegroundColor Yellow
                continue
            }
            
            # Check if already a member
            $isMember = Get-AzureADGroupMember -ObjectId $group.ObjectId | Where-Object { $_.ObjectId -eq $user.ObjectId }
            
            if ($isMember) {
                Write-Host "   ℹ️  '$($user.DisplayName)' is already a member" -ForegroundColor Blue
            } else {
                Add-AzureADGroupMember -ObjectId $group.ObjectId -RefObjectId $user.ObjectId
                Write-Host "   ✅ Added '$($user.DisplayName)' to the group" -ForegroundColor Green
            }
        } catch {
            Write-Host "   ❌ Failed to add '$member': $_" -ForegroundColor Red
        }
    }
}

# Add service principal if it exists
Write-Host "`n🤖 Checking for service principal..." -ForegroundColor Cyan
$clientId = "20c5495d-b98c-410b-aa7b-9ea13dd70f61"  # Your service principal
try {
    $servicePrincipal = Get-AzureADServicePrincipal -Filter "AppId eq '$clientId'" -ErrorAction SilentlyContinue
    
    if ($servicePrincipal) {
        # Check if already a member
        $isMember = Get-AzureADGroupMember -ObjectId $group.ObjectId | Where-Object { $_.ObjectId -eq $servicePrincipal.ObjectId }
        
        if ($isMember) {
            Write-Host "   ℹ️  Service principal is already a member" -ForegroundColor Blue
        } else {
            Add-AzureADGroupMember -ObjectId $group.ObjectId -RefObjectId $servicePrincipal.ObjectId
            Write-Host "   ✅ Added service principal to the group" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  Service principal not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Could not check/add service principal: $_" -ForegroundColor Yellow
}

# Display current group members
Write-Host "`n👥 Current group members:" -ForegroundColor Cyan
try {
    $members = Get-AzureADGroupMember -ObjectId $group.ObjectId
    if ($members.Count -eq 0) {
        Write-Host "   (No members)" -ForegroundColor Gray
    } else {
        foreach ($member in $members) {
            $type = if ($member.ObjectType -eq "User") { "👤" } elseif ($member.ObjectType -eq "ServicePrincipal") { "🤖" } else { "📋" }
            Write-Host "   $type $($member.DisplayName) ($($member.ObjectType))" -ForegroundColor White
        }
    }
} catch {
    Write-Host "   ⚠️  Could not retrieve group members: $_" -ForegroundColor Yellow
}

Write-Host "`n📋 NEXT STEPS TO ENABLE XMLA:" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray
Write-Host "1. Go to Power BI Admin Portal: https://admin.powerbi.com" -ForegroundColor White
Write-Host "2. Navigate to: Tenant settings" -ForegroundColor White
Write-Host "3. Find: 'XMLA endpoint and Analyze in Excel with on-premises datasets'" -ForegroundColor White
Write-Host "4. Enable it and set 'Apply to': Specific security groups" -ForegroundColor White
Write-Host "5. Add this group: $GroupName" -ForegroundColor Yellow
Write-Host "6. Click Apply and wait 5-10 minutes" -ForegroundColor White

Write-Host "`n✅ Security group setup complete!" -ForegroundColor Green
Write-Host "Group Object ID: $($group.ObjectId)" -ForegroundColor White
