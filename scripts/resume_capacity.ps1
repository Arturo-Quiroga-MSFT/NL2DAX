# Resume Paused Power BI Capacities
# Requires Power BI Administrator or Capacity Administrator privileges

param(
    [string]$SpecificCapacityId = "",
    [switch]$AutoConfirm = $false,
    [switch]$WaitForComplete = $true
)

Write-Host "🚀 Power BI Capacity Resume Utility" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray
Write-Host "🕐 Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  WARNING: This requires Power BI Administrator privileges" -ForegroundColor Yellow
Write-Host "   Resuming capacities may incur costs!" -ForegroundColor Yellow
Write-Host ""

# Install and import required modules
Write-Host "🔧 Checking PowerShell modules..." -ForegroundColor Cyan

$requiredModules = @(
    "MicrosoftPowerBIMgmt",
    "Az.Accounts"
)

foreach ($module in $requiredModules) {
    if (!(Get-Module -ListAvailable -Name $module)) {
        Write-Host "📥 Installing $module..." -ForegroundColor Yellow
        Install-Module -Name $module -Force -AllowClobber -Scope CurrentUser
    }
    Import-Module $module -Force
}

# Connect to Power BI
Write-Host "🔐 Connecting to Power BI..." -ForegroundColor Cyan
try {
    $null = Get-PowerBIAccessToken -ErrorAction Stop
    Write-Host "✅ Already connected to Power BI" -ForegroundColor Green
} catch {
    Write-Host "🔑 Logging in to Power BI..." -ForegroundColor Yellow
    Connect-PowerBIServiceAccount
}

# Get all capacities
Write-Host "`n🔍 Scanning all capacities..." -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Gray

try {
    # Try admin API first
    $allCapacities = Invoke-PowerBIRestMethod -Url "admin/capacities" -Method Get | ConvertFrom-Json
    Write-Host "✅ Found $($allCapacities.value.Count) total capacities (admin view)" -ForegroundColor Green
    $capacities = $allCapacities.value
} catch {
    Write-Host "⚠️  Admin API not accessible, trying user view..." -ForegroundColor Yellow
    try {
        $userCapacities = Invoke-PowerBIRestMethod -Url "capacities" -Method Get | ConvertFrom-Json
        Write-Host "✅ Found $($userCapacities.value.Count) accessible capacities (limited view)" -ForegroundColor Green
        $capacities = $userCapacities.value
    } catch {
        Write-Host "❌ Cannot access capacity information: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Analyze capacity status
Write-Host "`n📊 CAPACITY STATUS ANALYSIS:" -ForegroundColor Cyan
Write-Host "-" * 40 -ForegroundColor Gray

$pausedCapacities = @()
$targetCapacityId = "1ABA0BFF-BDBA-41CE-83D6-D93AE8E8003A"  # From your workspace

foreach ($capacity in $capacities) {
    $name = $capacity.displayName
    $id = $capacity.id
    $state = $capacity.state
    $sku = $capacity.sku
    $region = $capacity.region
    
    Write-Host "📋 $name" -ForegroundColor White
    Write-Host "   ID: $id" -ForegroundColor Gray
    Write-Host "   SKU: $sku" -ForegroundColor Gray
    Write-Host "   Region: $region" -ForegroundColor Gray
    
    $isTarget = $id -eq $targetCapacityId
    $targetMarker = if ($isTarget) { " ← YOUR WORKSPACE CAPACITY" } else { "" }
    
    if ($state -in @("Paused", "Suspended")) {
        Write-Host "   🔴 STATUS: $state$targetMarker" -ForegroundColor Red
        $pausedCapacities += $capacity
    } elseif ($state -in @("Active", "Running")) {
        Write-Host "   🟢 STATUS: $state$targetMarker" -ForegroundColor Green
    } else {
        Write-Host "   🟡 STATUS: $state$targetMarker" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Check if target capacity is paused
$targetCapacity = $capacities | Where-Object { $_.id -eq $targetCapacityId }

if (-not $targetCapacity) {
    Write-Host "❌ Target workspace capacity not found in accessible list!" -ForegroundColor Red
    Write-Host "   This confirms the capacity is likely paused/suspended" -ForegroundColor Yellow
    Write-Host "   Capacity ID: $targetCapacityId" -ForegroundColor Gray
    
    # Try to resume the specific capacity even if not in list
    if ($SpecificCapacityId -or $targetCapacityId) {
        $capacityToResume = if ($SpecificCapacityId) { $SpecificCapacityId } else { $targetCapacityId }
        Write-Host "`n🎯 Attempting to resume target capacity: $capacityToResume" -ForegroundColor Cyan
        
        if ($AutoConfirm -or (Read-Host "❓ Attempt to resume capacity $capacityToResume? (y/N)") -match "^[Yy]") {
            try {
                Write-Host "🔄 Sending resume command..." -ForegroundColor Yellow
                $resumeResult = Invoke-PowerBIRestMethod -Url "admin/capacities/$capacityToResume/resume" -Method Post
                Write-Host "✅ Resume command sent successfully!" -ForegroundColor Green
                
                if ($WaitForComplete) {
                    Write-Host "`n⏳ Waiting for capacity to become available..." -ForegroundColor Cyan
                    $maxWaitMinutes = 5
                    $startTime = Get-Date
                    $resumed = $false
                    
                    do {
                        Start-Sleep -Seconds 15
                        try {
                            $checkCapacity = Invoke-PowerBIRestMethod -Url "admin/capacities/$capacityToResume" -Method Get | ConvertFrom-Json
                            $currentState = $checkCapacity.state
                            $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
                            
                            Write-Host "🔄 Current state: $currentState (${elapsed}s elapsed)" -ForegroundColor White
                            
                            if ($currentState -in @("Active", "Running")) {
                                Write-Host "✅ Capacity is now RUNNING! (took ${elapsed} seconds)" -ForegroundColor Green
                                $resumed = $true
                                break
                            }
                        } catch {
                            Write-Host "🔄 Still checking capacity status..." -ForegroundColor White
                        }
                        
                    } while (((Get-Date) - $startTime).TotalMinutes -lt $maxWaitMinutes)
                    
                    if (-not $resumed) {
                        Write-Host "⏰ Timeout after $maxWaitMinutes minutes - capacity may still be resuming" -ForegroundColor Yellow
                    }
                }
                
            } catch {
                Write-Host "❌ Failed to resume capacity: $($_.Exception.Message)" -ForegroundColor Red
                
                if ($_.Exception.Message -match "403") {
                    Write-Host "💡 You need Power BI Administrator or Capacity Administrator privileges" -ForegroundColor Yellow
                } elseif ($_.Exception.Message -match "404") {
                    Write-Host "💡 Capacity not found or already running" -ForegroundColor Yellow
                }
            }
        }
    }
} else {
    Write-Host "✅ Target workspace capacity found in accessible list" -ForegroundColor Green
    if ($targetCapacity.state -in @("Paused", "Suspended")) {
        Write-Host "🔴 But it is currently: $($targetCapacity.state)" -ForegroundColor Red
        $pausedCapacities += $targetCapacity
    } else {
        Write-Host "🟢 And it is currently: $($targetCapacity.state)" -ForegroundColor Green
    }
}

# Process other paused capacities
if ($pausedCapacities.Count -eq 0) {
    Write-Host "✅ No additional paused capacities found" -ForegroundColor Green
} else {
    Write-Host "`n🔴 FOUND $($pausedCapacities.Count) PAUSED CAPACITY(IES)" -ForegroundColor Red
    Write-Host "=" * 50 -ForegroundColor Gray
    
    $resumedCount = 0
    
    foreach ($capacity in $pausedCapacities) {
        $name = $capacity.displayName
        $id = $capacity.id
        $sku = $capacity.sku
        
        Write-Host "`n🎯 PROCESSING: $name" -ForegroundColor Cyan
        Write-Host "   ID: $id" -ForegroundColor Gray
        Write-Host "   SKU: $sku" -ForegroundColor Gray
        Write-Host "   State: $($capacity.state)" -ForegroundColor Gray
        
        $shouldResume = $AutoConfirm
        if (-not $shouldResume) {
            $response = Read-Host "❓ Resume capacity '$name'? (y/N)"
            $shouldResume = $response -match "^[Yy]"
        }
        
        if ($shouldResume) {
            try {
                Write-Host "🔄 Resuming $name..." -ForegroundColor Yellow
                $resumeResult = Invoke-PowerBIRestMethod -Url "admin/capacities/$id/resume" -Method Post
                Write-Host "✅ Resume command sent for $name" -ForegroundColor Green
                $resumedCount++
                
                if ($WaitForComplete) {
                    Write-Host "⏳ Waiting for $name to resume..." -ForegroundColor Cyan
                    Start-Sleep -Seconds 30  # Give it a moment to start
                    
                    try {
                        $checkCapacity = Invoke-PowerBIRestMethod -Url "admin/capacities/$id" -Method Get | ConvertFrom-Json
                        if ($checkCapacity.state -in @("Active", "Running")) {
                            Write-Host "✅ $name is now running!" -ForegroundColor Green
                        } else {
                            Write-Host "⏳ $name is still resuming (state: $($checkCapacity.state))" -ForegroundColor Yellow
                        }
                    } catch {
                        Write-Host "⏳ $name resume in progress..." -ForegroundColor Yellow
                    }
                }
                
            } catch {
                Write-Host "❌ Failed to resume $name`: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "⏭️  Skipped $name" -ForegroundColor Gray
        }
    }
}

# Final summary and verification
Write-Host "`n📋 RESUME OPERATION SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Gray
Write-Host "✅ Capacities processed: $($pausedCapacities.Count)" -ForegroundColor Green
Write-Host "🔄 Resume commands sent: $resumedCount" -ForegroundColor Green

if ($resumedCount -gt 0) {
    Write-Host "`n🧪 VERIFICATION STEPS:" -ForegroundColor Cyan
    Write-Host "1. Wait 2-3 minutes for full startup" -ForegroundColor White
    Write-Host "2. Run: python3 fabric_capacity_status.py" -ForegroundColor White
    Write-Host "3. Run: python3 check_xmla_capacity.py" -ForegroundColor White
    Write-Host "4. Test DAX execution: python3 main.py" -ForegroundColor White
    
    Write-Host "`n🚀 Quick verification..." -ForegroundColor Cyan
    try {
        # Check if our target capacity is now accessible
        $updatedCapacities = Invoke-PowerBIRestMethod -Url "capacities" -Method Get | ConvertFrom-Json
        $targetFound = $updatedCapacities.value | Where-Object { $_.id -eq $targetCapacityId }
        
        if ($targetFound) {
            Write-Host "✅ Target workspace capacity is now accessible!" -ForegroundColor Green
            Write-Host "   State: $($targetFound.state)" -ForegroundColor White
        } else {
            Write-Host "⏳ Target capacity not yet visible (still resuming...)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⏳ Verification pending - capacities may still be starting up" -ForegroundColor Yellow
    }
}

Write-Host "`n⏰ Completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White

# Usage examples as comments
<#
USAGE EXAMPLES:

# Resume all paused capacities with prompts
./resume_capacity.ps1

# Resume specific capacity automatically
./resume_capacity.ps1 -SpecificCapacityId "1ABA0BFF-BDBA-41CE-83D6-D93AE8E8003A" -AutoConfirm

# Resume all paused capacities without prompts
./resume_capacity.ps1 -AutoConfirm

# Resume without waiting for completion
./resume_capacity.ps1 -AutoConfirm -WaitForComplete:$false

# Target the specific workspace capacity
./resume_capacity.ps1 -SpecificCapacityId "1ABA0BFF-BDBA-41CE-83D6-D93AE8E8003A" -AutoConfirm -WaitForComplete
#>
