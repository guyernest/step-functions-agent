<#
.SYNOPSIS
    Patches the Local Browser Agent Python executor with the latest version from GitHub.

.DESCRIPTION
    This script downloads the latest Python executor files from the public GitHub repository
    and updates the local installation. It creates backups of existing files before replacing them.

.PARAMETER InstallPath
    The installation path of Local Browser Agent. Defaults to standard Windows install location.

.PARAMETER Branch
    The GitHub branch to download from. Defaults to 'main'.

.PARAMETER DryRun
    If specified, shows what would be done without making changes.

.PARAMETER Force
    If specified, skips confirmation prompts.

.EXAMPLE
    .\patch-python-executor.ps1

.EXAMPLE
    .\patch-python-executor.ps1 -InstallPath "D:\CustomPath\Local Browser Agent" -Force

.EXAMPLE
    .\patch-python-executor.ps1 -DryRun

.NOTES
    Version: 1.0.0
    Author: Local Browser Agent Team
    Repository: https://github.com/guyernest/step-functions-agent
#>

param(
    [string]$InstallPath = "$env:LOCALAPPDATA\Local Browser Agent",
    [string]$Branch = "main",
    [switch]$DryRun,
    [switch]$Force
)

# Configuration
$GitHubRepo = "guyernest/step-functions-agent"
$GitHubBasePath = "lambda/tools/local-browser-agent/python"
$GitHubRawBaseUrl = "https://raw.githubusercontent.com/$GitHubRepo/$Branch/$GitHubBasePath"

# Files to update
$FilesToUpdate = @(
    "openai_playwright_executor.py",
    "browser_launch_config.py",
    "workflow_executor.py",
    "condition_evaluator.py",
    "profile_manager.py",
    "progressive_escalation_engine.py"
)

# Colors for output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }

function Show-Banner {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Local Browser Agent - Python Executor Patch" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Repository: https://github.com/$GitHubRepo"
    Write-Info "Branch: $Branch"
    Write-Info "Install Path: $InstallPath"
    Write-Host ""
}

function Test-Installation {
    param([string]$Path)

    $pythonDir = Join-Path $Path "python"
    $executorFile = Join-Path $pythonDir "openai_playwright_executor.py"

    if (-not (Test-Path $pythonDir)) {
        Write-Error "Python directory not found: $pythonDir"
        return $false
    }

    if (-not (Test-Path $executorFile)) {
        Write-Error "Executor file not found: $executorFile"
        return $false
    }

    return $true
}

function Get-FileVersion {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) {
        return "Not found"
    }

    # Try to extract version from file (look for version comments or patterns)
    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if ($content -match 'VERSION\s*=\s*["\']([^"\']+)["\']') {
        return $matches[1]
    }

    # Fallback to file hash (first 8 chars)
    $hash = (Get-FileHash $FilePath -Algorithm SHA256).Hash.Substring(0, 8)
    return "hash:$hash"
}

function Backup-File {
    param(
        [string]$FilePath,
        [string]$BackupDir
    )

    if (-not (Test-Path $FilePath)) {
        return $null
    }

    $fileName = Split-Path $FilePath -Leaf
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "${fileName}.backup_${timestamp}"
    $backupPath = Join-Path $BackupDir $backupName

    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }

    Copy-Item $FilePath $backupPath -Force
    return $backupPath
}

function Download-File {
    param(
        [string]$Url,
        [string]$DestinationPath
    )

    try {
        # Use TLS 1.2
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

        $webClient = New-Object System.Net.WebClient
        $webClient.Headers.Add("User-Agent", "LocalBrowserAgent-Patcher/1.0")
        $webClient.DownloadFile($Url, $DestinationPath)
        return $true
    }
    catch {
        Write-Error "Failed to download: $_"
        return $false
    }
}

function Update-File {
    param(
        [string]$FileName,
        [string]$PythonDir,
        [string]$BackupDir,
        [bool]$IsDryRun
    )

    $localPath = Join-Path $PythonDir $FileName
    $downloadUrl = "$GitHubRawBaseUrl/$FileName"
    $tempPath = Join-Path $env:TEMP "lba_patch_$FileName"

    Write-Host ""
    Write-Info "Processing: $FileName"
    Write-Host "  URL: $downloadUrl"

    # Get current version
    $currentVersion = Get-FileVersion $localPath
    Write-Host "  Current: $currentVersion"

    if ($IsDryRun) {
        Write-Warning "  [DRY RUN] Would download and replace file"
        return $true
    }

    # Download new file to temp location
    Write-Host "  Downloading..."
    if (-not (Download-File -Url $downloadUrl -DestinationPath $tempPath)) {
        Write-Error "  Failed to download $FileName"
        return $false
    }

    # Get new version
    $newVersion = Get-FileVersion $tempPath
    Write-Host "  New: $newVersion"

    # Check if file actually changed
    if ((Test-Path $localPath)) {
        $currentHash = (Get-FileHash $localPath -Algorithm SHA256).Hash
        $newHash = (Get-FileHash $tempPath -Algorithm SHA256).Hash

        if ($currentHash -eq $newHash) {
            Write-Success "  Already up to date"
            Remove-Item $tempPath -Force -ErrorAction SilentlyContinue
            return $true
        }
    }

    # Backup existing file
    if (Test-Path $localPath) {
        $backupPath = Backup-File -FilePath $localPath -BackupDir $BackupDir
        if ($backupPath) {
            Write-Host "  Backup: $backupPath"
        }
    }

    # Replace file
    try {
        Move-Item $tempPath $localPath -Force
        Write-Success "  Updated successfully"
        return $true
    }
    catch {
        Write-Error "  Failed to replace file: $_"
        return $false
    }
}

function Test-InternetConnection {
    try {
        $response = Invoke-WebRequest -Uri "https://github.com" -Method Head -TimeoutSec 5 -UseBasicParsing
        return $true
    }
    catch {
        return $false
    }
}

# Main execution
Show-Banner

# Check internet connection
Write-Info "Checking internet connection..."
if (-not (Test-InternetConnection)) {
    Write-Error "Cannot reach GitHub. Please check your internet connection."
    exit 1
}
Write-Success "Connected to GitHub"

# Verify installation
Write-Info "Verifying installation..."
if (-not (Test-Installation -Path $InstallPath)) {
    Write-Error "Local Browser Agent installation not found at: $InstallPath"
    Write-Host ""
    Write-Host "Please specify the correct installation path using -InstallPath parameter"
    Write-Host "Example: .\patch-python-executor.ps1 -InstallPath 'D:\MyPath\Local Browser Agent'"
    exit 1
}
Write-Success "Installation verified"

$pythonDir = Join-Path $InstallPath "python"
$backupDir = Join-Path $InstallPath "backups"

# Show what will be updated
Write-Host ""
Write-Host "Files to update:" -ForegroundColor White
foreach ($file in $FilesToUpdate) {
    $localPath = Join-Path $pythonDir $file
    $exists = if (Test-Path $localPath) { "exists" } else { "new" }
    Write-Host "  - $file ($exists)"
}

# Confirmation
if (-not $Force -and -not $DryRun) {
    Write-Host ""
    $confirmation = Read-Host "Do you want to proceed with the update? (Y/N)"
    if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
        Write-Warning "Update cancelled by user"
        exit 0
    }
}

if ($DryRun) {
    Write-Host ""
    Write-Warning "=== DRY RUN MODE - No changes will be made ==="
}

# Update files
Write-Host ""
Write-Host "Updating files..." -ForegroundColor White

$successCount = 0
$failCount = 0

foreach ($file in $FilesToUpdate) {
    $result = Update-File -FileName $file -PythonDir $pythonDir -BackupDir $backupDir -IsDryRun $DryRun
    if ($result) {
        $successCount++
    } else {
        $failCount++
    }
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Update Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Success "  Successful: $successCount"
if ($failCount -gt 0) {
    Write-Error "  Failed: $failCount"
}
Write-Host ""

if ($failCount -eq 0) {
    Write-Success "Patch completed successfully!"
    Write-Host ""
    Write-Info "Backups saved to: $backupDir"
    Write-Host ""
    Write-Host "To restore a backup, copy the .backup file back to the original name."
} else {
    Write-Warning "Some files failed to update. Check the errors above."
    Write-Host "You may need to run as Administrator or check file permissions."
}

Write-Host ""
