# Add Service Principal to Power BI Workspace (with different permission levels)
$workspaceId = "e3fdee99-3aa4-4d71-a530-2964a062e326"
$clientId = "20c5495d-b98c-410b-aa7b-9ea13dd70f61"

# Check if already logged in
try {
    $null = Get-PowerBIAccessToken -ErrorAction Stop
    Write-Host "✅ Already logged in to Power BI"
} catch {
    Write-Host "🔐 Logging in to Power BI..."
    $null = Login-PowerBIServiceAccount
}

# Try different permission levels
$permissionLevels = @("Member", "Contributor", "Viewer", "Admin")

foreach ($permission in $permissionLevels) {
    Write-Host "Trying to add service principal with '$permission' access..."
    
    $body = @{
        identifier = $clientId
        groupUserAccessRight = $permission
        principalType = "App"
    } | ConvertTo-Json
    
    $url = "https://api.powerbi.com/v1.0/myorg/groups/$workspaceId/users"
    
    try {
        $response = Invoke-PowerBIRestMethod -Url $url -Method Post -Body $body
        Write-Host "✅ Successfully added service principal with '$permission' access!"
        Write-Host "Response: $response"
        break
    } catch {
        Write-Host "❌ Failed with '$permission' access: $($_.Exception.Message)"
        
        if ($_.Exception.Message -like "*already*") {
            Write-Host "🤔 Service principal might already exist. Let's check..."
            break
        }
    }
}

# Final check of workspace members
Write-Host "`nFinal workspace members check:"
$getUsersUrl = "https://api.powerbi.com/v1.0/myorg/groups/$workspaceId/users"

try {
    $users = Invoke-PowerBIRestMethod -Url $getUsersUrl -Method Get
    $usersObj = $users | ConvertFrom-Json
    
    $foundOurSP = $false
    foreach ($user in $usersObj.value) {
        if ($user.identifier -eq $clientId) {
            Write-Host "🎯 Found our service principal: $clientId with $($user.groupUserAccessRight) access!"
            $foundOurSP = $true
        }
    }
    
    if (-not $foundOurSP) {
        Write-Host "❌ Our service principal ($clientId) is still not in the workspace"
        Write-Host "Current service principals in workspace:"
        foreach ($user in $usersObj.value) {
            if ($user.principalType -eq "App") {
                Write-Host "  - $($user.identifier) ($($user.groupUserAccessRight))"
            }
        }
    }
} catch {
    Write-Host "❌ Error checking workspace members: $_"
}
