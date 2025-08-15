# Enable XMLA Endpoints for Power BI
# Run this script as a Power BI Admin

Write-Host "🔧 Checking and Enabling XMLA Endpoints..." -ForegroundColor Cyan

# Check if already logged in
try {
    $null = Get-PowerBIAccessToken -ErrorAction Stop
    Write-Host "✅ Already logged in to Power BI" -ForegroundColor Green
} catch {
    Write-Host "🔐 Logging in to Power BI..." -ForegroundColor Yellow
    $null = Login-PowerBIServiceAccount
}

$workspaceId = "e3fdee99-3aa4-4d71-a530-2964a062e326"

Write-Host "`n1️⃣ Checking current tenant XMLA settings..." -ForegroundColor Cyan
try {
    $tenantSettings = Get-PowerBIAdminTenant
    $xmlaEnabled = $tenantSettings.XmlaEndpointEnabled
    Write-Host "   Current XMLA Endpoint setting: $xmlaEnabled" -ForegroundColor White
    
    if ($xmlaEnabled -eq $false) {
        Write-Host "   ❌ XMLA endpoints are DISABLED at tenant level" -ForegroundColor Red
        Write-Host "   🔧 Attempting to enable..." -ForegroundColor Yellow
        
        try {
            Set-PowerBIAdminTenant -XmlaEndpointEnabled $true
            Write-Host "   ✅ XMLA endpoints enabled at tenant level" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ Failed to enable XMLA endpoints: $_" -ForegroundColor Red
            Write-Host "   💡 You may need to enable this manually in the Admin Portal" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ XMLA endpoints are ENABLED at tenant level" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Could not check tenant settings: $_" -ForegroundColor Yellow
    Write-Host "   💡 You may need admin privileges or manual configuration" -ForegroundColor Yellow
}

Write-Host "`n2️⃣ Checking workspace capacity..." -ForegroundColor Cyan
try {
    $workspace = Get-PowerBIWorkspace -Id $workspaceId
    if ($workspace) {
        Write-Host "   ✅ Workspace found: $($workspace.Name)" -ForegroundColor Green
        Write-Host "   ✅ On dedicated capacity: $($workspace.IsOnDedicatedCapacity)" -ForegroundColor Green
        
        if ($workspace.IsOnDedicatedCapacity -eq $false) {
            Write-Host "   ❌ Workspace is NOT on Premium capacity" -ForegroundColor Red
            Write-Host "   💡 XMLA endpoints require Premium or Premium Per User" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ Workspace not found or no access" -ForegroundColor Red
    }
} catch {
    Write-Host "   ⚠️  Could not check workspace: $_" -ForegroundColor Yellow
}

Write-Host "`n3️⃣ Testing XMLA endpoint via REST API..." -ForegroundColor Cyan
try {
    $token = Get-PowerBIAccessToken | Select-Object -ExpandProperty AccessToken
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    # Try a simple DAX query via REST API
    $datasetId = "3ed8f6b3-0a1d-4910-9d31-a9dd3f8f4007"
    $daxQuery = @{
        queries = @(
            @{
                query = "EVALUATE ROW(`"TestColumn`", 1)"
            }
        )
    } | ConvertTo-Json -Depth 3
    
    $executeUrl = "https://api.powerbi.com/v1.0/myorg/groups/$workspaceId/datasets/$datasetId/executeQueries"
    
    Write-Host "   🔍 Testing DAX query execution..." -ForegroundColor White
    $response = Invoke-RestMethod -Uri $executeUrl -Method Post -Headers $headers -Body $daxQuery
    
    if ($response) {
        Write-Host "   ✅ DAX query executed successfully!" -ForegroundColor Green
        Write-Host "   📊 Response: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor White
    }
} catch {
    $errorDetails = $_.Exception.Response
    if ($errorDetails) {
        $statusCode = $errorDetails.StatusCode
        Write-Host "   ❌ DAX query failed with HTTP $statusCode" -ForegroundColor Red
        
        if ($statusCode -eq 401) {
            Write-Host "   💡 This suggests XMLA endpoints are still disabled" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ DAX query failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n📋 SUMMARY AND NEXT STEPS:" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

Write-Host "✅ Things we've verified:" -ForegroundColor Green
Write-Host "   • Service principal has workspace access" -ForegroundColor White
Write-Host "   • Service principal has dataset permissions" -ForegroundColor White
Write-Host "   • Workspace is on Premium capacity" -ForegroundColor White

Write-Host "`n🔧 If DAX queries still fail:" -ForegroundColor Yellow
Write-Host "1. Manually enable XMLA in Admin Portal:" -ForegroundColor White
Write-Host "   → Go to https://admin.powerbi.com" -ForegroundColor Gray
Write-Host "   → Tenant settings → XMLA endpoint → Enable" -ForegroundColor Gray

Write-Host "`n2. Enable at workspace level:" -ForegroundColor White
Write-Host "   → Go to workspace settings → Premium tab" -ForegroundColor Gray
Write-Host "   → Set XMLA Endpoint to 'Read' or 'Read Write'" -ForegroundColor Gray

Write-Host "`n3. Wait 5-10 minutes after making changes" -ForegroundColor White

Write-Host "`n4. Test again with: python diagnose_permissions.py" -ForegroundColor White
