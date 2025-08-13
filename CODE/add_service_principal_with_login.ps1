# Add Service Principal to Power BI Workspace with Login
$datasetId = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"
$workspaceId = "e3fdee99-3aa4-4d71-a530-2964a062e326"
$clientId = "20c5495d-b98c-410b-aa7b-9ea13dd70f61"

# Check if already logged in
try {
    $token = Get-PowerBIAccessToken -ErrorAction Stop
    Write-Host "✅ Already logged in to Power BI"
} catch {
    Write-Host "🔐 Logging in to Power BI..."
    $loginResult = Login-PowerBIServiceAccount
    if ($loginResult) {
        Write-Host "✅ Successfully logged in to Power BI"
    } else {
        Write-Host "❌ Failed to login to Power BI"
        exit 1
    }
}

# For service principals, use the workspace users endpoint
$body = @{
    identifier = $clientId
    groupUserAccessRight = "Admin"  # Can be "Admin", "Member", "Contributor", or "Viewer"
    principalType = "App"
} | ConvertTo-Json

$url = "https://api.powerbi.com/v1.0/myorg/groups/$workspaceId/users"

Write-Host "Adding service principal to workspace..."
Write-Host "URL: $url"
Write-Host "Body: $body"

try {
    $response = Invoke-PowerBIRestMethod -Url $url -Method Post -Body $body
    Write-Host "✅ Successfully added service principal to workspace!"
    Write-Host "Service principal will now have access to all datasets in this workspace."
    Write-Host "Response: $response"
} catch {
    Write-Host "❌ Error adding service principal: $_"
    Write-Host "Full error: $($_.Exception.Message)"
    
    # Check if it's because the service principal is already added
    if ($_.Exception.Message -like "*already exists*" -or $_.Exception.Message -like "*already a member*") {
        Write-Host "ℹ️  Service principal may already be a member of this workspace."
        
        # Try to get workspace users to verify
        try {
            $getUsersUrl = "https://api.powerbi.com/v1.0/myorg/groups/$workspaceId/users"
            $users = Invoke-PowerBIRestMethod -Url $getUsersUrl -Method Get
            Write-Host "Current workspace users:"
            $users | ConvertFrom-Json | ConvertTo-Json -Depth 3
        } catch {
            Write-Host "Could not retrieve workspace users: $_"
        }
    }
}
