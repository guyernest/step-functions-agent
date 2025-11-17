# Test Profile Tag Matching
# This script tests if the profile manager can find profiles by tags

Write-Host "Testing Profile Tag Matching" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# Find the profile_manager.py script
$pythonDir = "C:\Program Files\Local Browser Agent\resources\python"
$profileManager = Join-Path $pythonDir "profile_manager.py"

if (-not (Test-Path $profileManager)) {
    # Try alternative location
    $profileManager = ".\python\profile_manager.py"
    if (-not (Test-Path $profileManager)) {
        Write-Host "ERROR: profile_manager.py not found" -ForegroundColor Red
        Write-Host "Tried:" -ForegroundColor Yellow
        Write-Host "  - C:\Program Files\Local Browser Agent\resources\python\profile_manager.py"
        Write-Host "  - .\python\profile_manager.py"
        exit 1
    }
}

Write-Host "Found profile_manager.py at: $profileManager" -ForegroundColor Green
Write-Host ""

# Test 1: List all profiles
Write-Host "[1/3] Listing all profiles..." -ForegroundColor Yellow
$output = python $profileManager list 2>&1
Write-Host $output
Write-Host ""

# Test 2: Show bt_wholesale profile details
Write-Host "[2/3] Showing bt_wholesale profile details..." -ForegroundColor Yellow
$output = python $profileManager get --profile bt_wholesale 2>&1
Write-Host $output
Write-Host ""

# Test 3: Test tag-based search
Write-Host "[3/3] Testing tag-based profile search..." -ForegroundColor Yellow
Write-Host "  Searching for tags: btwholesale.com, authenticated" -ForegroundColor Gray

# Create a test session config JSON
$testConfig = @"
{
  "required_tags": ["btwholesale.com", "authenticated"],
  "allow_temp_profile": false
}
"@

Write-Host ""
Write-Host "Test session config:" -ForegroundColor Gray
Write-Host $testConfig -ForegroundColor DarkGray
Write-Host ""

# This would be done internally by the script executor, but we can check manually
Write-Host "Checking if profile has these tags..." -ForegroundColor Yellow
$profileJson = python $profileManager get --profile bt_wholesale --json 2>&1
if ($profileJson -match '"tags"') {
    $profile = $profileJson | ConvertFrom-Json
    $profileTags = $profile.tags

    Write-Host "  Profile tags: $($profileTags -join ', ')" -ForegroundColor Gray

    $requiredTags = @("btwholesale.com", "authenticated")
    $hasAllTags = $true

    foreach ($tag in $requiredTags) {
        if ($profileTags -contains $tag) {
            Write-Host "  SUCCESS: Has required tag '$tag'" -ForegroundColor Green
        } else {
            Write-Host "  ERROR: Missing required tag '$tag'" -ForegroundColor Red
            $hasAllTags = $false
        }
    }

    Write-Host ""
    if ($hasAllTags) {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "TAGS ARE CORRECT!" -ForegroundColor Green -BackgroundColor Black
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "The profile should be matched by tags." -ForegroundColor Green
        Write-Host ""
        Write-Host "NEXT STEP: Update the template to use tag-based matching" -ForegroundColor Yellow
        Write-Host "The template should have:" -ForegroundColor Yellow
        Write-Host '  "session": {' -ForegroundColor Gray
        Write-Host '    "required_tags": ["btwholesale.com", "authenticated"],' -ForegroundColor Gray
        Write-Host '    "allow_temp_profile": false' -ForegroundColor Gray
        Write-Host '  }' -ForegroundColor Gray
    } else {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "TAG MISMATCH!" -ForegroundColor Red -BackgroundColor Black
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Add the missing tags to the profile." -ForegroundColor Yellow
    }
} else {
    Write-Host "  ERROR: Could not parse profile JSON" -ForegroundColor Red
    Write-Host "  Output: $profileJson" -ForegroundColor Gray
}
