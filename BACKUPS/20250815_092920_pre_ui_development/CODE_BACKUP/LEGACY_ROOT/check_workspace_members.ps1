# Check Workspace Members
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

Write-Host "Checking workspace members..."
$getUsersUrl = "https://api.powerbi.com/v1.0/myorg/groups/$workspaceId/users"

try {
    $users = Invoke-PowerBIRestMethod -Url $getUsersUrl -Method Get
    $usersObj = $users | ConvertFrom-Json
    
    Write-Host "Current workspace members:"
    Write-Host "=========================="
    
    foreach ($user in $usersObj.value) {
        Write-Host "Type: $($user.principalType)"
        Write-Host "Identifier: $($user.identifier)"
        Write-Host "Access: $($user.groupUserAccessRight)"
        Write-Host "---"
        
        if ($user.identifier -eq $clientId) {
            Write-Host "🎯 Found our service principal with $($user.groupUserAccessRight) access!"
        }
    }
} catch {
    Write-Host "❌ Error retrieving workspace users: $_"
    Write-Host "Full error: $($_.Exception.Message)"
}
