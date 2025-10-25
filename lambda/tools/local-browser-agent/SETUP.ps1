# Local Browser Agent - Windows Setup Script
# This script sets up the Python environment for the Local Browser Agent on Windows

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Local Browser Agent - Windows Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Determine app location
$AppPath = "$env:LOCALAPPDATA\Programs\Local Browser Agent"
if (-not (Test-Path $AppPath)) {
    # Alternative: Program Files
    $AppPath = "${env:ProgramFiles}\Local Browser Agent"
}

if (-not (Test-Path $AppPath)) {
    Write-Host "Error: Cannot find Local Browser Agent installation" -ForegroundColor Red
    Write-Host "Expected locations:" -ForegroundColor Yellow
    Write-Host "  - $env:LOCALAPPDATA\Programs\Local Browser Agent" -ForegroundColor Yellow
    Write-Host "  - ${env:ProgramFiles}\Local Browser Agent" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found app at: $AppPath" -ForegroundColor Green
$PythonDir = Join-Path $AppPath "python"
$VenvPath = Join-Path $PythonDir ".venv"

Write-Host ""
Write-Host "Step 1: Checking for uv package manager..." -ForegroundColor Cyan

# Check if uv is installed
$uvPath = "$env:USERPROFILE\.cargo\bin\uv.exe"
if (-not (Test-Path $uvPath)) {
    Write-Host "Installing uv package manager..." -ForegroundColor Yellow
    try {
        irm https://astral.sh/uv/install.ps1 | iex
        $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
    } catch {
        Write-Host "Error installing uv: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ uv package manager found" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Creating Python virtual environment..." -ForegroundColor Cyan

# Create venv
try {
    & $uvPath venv $VenvPath --python 3.11
    Write-Host "✓ Python 3.11 virtual environment created" -ForegroundColor Green
} catch {
    Write-Host "Error creating venv: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Installing Python dependencies..." -ForegroundColor Cyan

# Install dependencies
$RequirementsFile = Join-Path $PythonDir "requirements.txt"
if (-not (Test-Path $RequirementsFile)) {
    Write-Host "Error: requirements.txt not found at $RequirementsFile" -ForegroundColor Red
    exit 1
}

try {
    & $uvPath pip install --python $VenvPath -r $RequirementsFile
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "Error installing dependencies: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 4: Installing Playwright browsers..." -ForegroundColor Cyan

try {
    $PlaywrightExe = Join-Path $VenvPath "Scripts\playwright.exe"
    & $PlaywrightExe install chromium
    Write-Host "✓ Chromium browser installed" -ForegroundColor Green
} catch {
    Write-Host "Error installing Playwright browsers: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python environment location:" -ForegroundColor Cyan
Write-Host "  $VenvPath" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Launch 'Local Browser Agent' from Start Menu" -ForegroundColor White
Write-Host "  2. Configure AWS credentials and API key" -ForegroundColor White
Write-Host "  3. Start using browser automation!" -ForegroundColor White
Write-Host ""
Write-Host "Configuration file location:" -ForegroundColor Cyan
Write-Host "  $env:USERPROFILE\.local-browser-agent\config.yaml" -ForegroundColor White
Write-Host ""

pause
