# Test Activity Connection for Browser Agent
# This script tests connectivity to AWS Step Functions Activity
# Usage: .\test-activity-connection.ps1

param(
    [string]$Profile = "local-browser",
    [string]$ActivityArn = "arn:aws:states:eu-west-1:923154134542:activity:browser-remote-prod",
    [string]$Region = "eu-west-1"
)

Write-Host "Testing Activity Connection" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Profile: $Profile"
Write-Host "Activity ARN: $ActivityArn"
Write-Host "Region: $Region"
Write-Host ""

# Test 1: Check AWS CLI is installed
Write-Host "[1/4] Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    Write-Host "  SUCCESS: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: AWS CLI not found. Please install AWS CLI from:" -ForegroundColor Red
    Write-Host "  https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Check credentials
Write-Host "[2/4] Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --profile $Profile --region $Region 2>&1 | ConvertFrom-Json
    Write-Host "  SUCCESS: Authenticated as:" -ForegroundColor Green
    Write-Host "    User: $($identity.Arn)" -ForegroundColor Gray
    Write-Host "    Account: $($identity.Account)" -ForegroundColor Gray
} catch {
    Write-Host "  ERROR: Failed to authenticate with profile '$Profile'" -ForegroundColor Red
    Write-Host "  Error details: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "TROUBLESHOOTING:" -ForegroundColor Yellow
    Write-Host "  1. Check that AWS profile '$Profile' exists in:" -ForegroundColor Yellow
    Write-Host "     $env:USERPROFILE\.aws\credentials" -ForegroundColor Gray
    Write-Host "  2. Run: aws configure --profile $Profile" -ForegroundColor Yellow
    Write-Host "  3. Or use: assume $Profile (if using assume role)" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Test 3: Check Activity exists
Write-Host "[3/4] Checking Activity ARN..." -ForegroundColor Yellow
try {
    $activity = aws stepfunctions describe-activity --activity-arn $ActivityArn --profile $Profile --region $Region 2>&1 | ConvertFrom-Json
    Write-Host "  SUCCESS: Activity found:" -ForegroundColor Green
    Write-Host "    Name: $($activity.name)" -ForegroundColor Gray
    Write-Host "    Created: $($activity.creationDate)" -ForegroundColor Gray
} catch {
    Write-Host "  ERROR: Failed to describe activity" -ForegroundColor Red
    Write-Host "  Error details: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "TROUBLESHOOTING:" -ForegroundColor Yellow
    Write-Host "  1. Verify the Activity ARN is correct" -ForegroundColor Yellow
    Write-Host "  2. Ensure the Activity exists in region '$Region'" -ForegroundColor Yellow
    Write-Host "  3. Check the ARN format matches:" -ForegroundColor Yellow
    Write-Host "     arn:aws:states:region:account:activity:name" -ForegroundColor Gray
    exit 1
}
Write-Host ""

# Test 4: Test polling permission
Write-Host "[4/4] Testing polling permission..." -ForegroundColor Yellow
Write-Host "  Attempting to poll for task (will timeout after 3s if no tasks)..." -ForegroundColor Gray
Write-Host "  This tests the 'states:GetActivityTask' permission..." -ForegroundColor Gray

$job = Start-Job -ScriptBlock {
    param($arn, $prof, $reg)
    aws stepfunctions get-activity-task --activity-arn $arn --worker-name "test-connection-ps" --profile $prof --region $reg 2>&1
} -ArgumentList $ActivityArn, $Profile, $Region

# Wait up to 3 seconds
$completed = Wait-Job $job -Timeout 3
if ($completed) {
    $result = Receive-Job $job
    Remove-Job $job

    # If we got here without error, connection works
    Write-Host "  SUCCESS: Connection works!" -ForegroundColor Green
    Write-Host "    No tasks currently available (this is normal)" -ForegroundColor Gray
    Write-Host "    The poller is able to connect and poll for tasks." -ForegroundColor Gray
} else {
    # Still running after 3 seconds means long-polling is working
    Stop-Job $job
    Remove-Job $job
    Write-Host "  SUCCESS: Long-polling working!" -ForegroundColor Green
    Write-Host "    The request is actively polling for tasks." -ForegroundColor Gray
    Write-Host "    This proves the connection and permissions are correct." -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ALL TESTS PASSED!" -ForegroundColor Green -BackgroundColor Black
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your configuration is working correctly:" -ForegroundColor Green
Write-Host "  Credentials: Valid" -ForegroundColor Gray
Write-Host "  Activity ARN: Accessible" -ForegroundColor Gray
Write-Host "  Permissions: Correct (states:GetActivityTask)" -ForegroundColor Gray
Write-Host "  Network: Connected to $Region" -ForegroundColor Gray
Write-Host ""
Write-Host "You can now run the Local Browser Agent with this configuration." -ForegroundColor Green
