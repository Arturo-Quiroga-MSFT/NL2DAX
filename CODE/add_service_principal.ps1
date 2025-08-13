# Add Service Principal to Power BI Workspace
# Note: Service principals must be added at workspace level, not dataset level
$datasetId = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"
$workspaceId = "e3fdee99-3aa4-4d71-a530-2964a062e326"
$clientId = "20c5495d-b98c-410b-aa7b-9ea13dd70f61"

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
}

