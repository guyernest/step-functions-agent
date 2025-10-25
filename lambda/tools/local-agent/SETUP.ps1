# Local Agent - Windows Setup Script
# This script sets up the Python environment for the Local Agent on Windows

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Local Agent - Windows Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Determine app location
$AppPath = "$env:LOCALAPPDATA\Programs\Local Agent"
if (-not (Test-Path $AppPath)) {
    # Alternative: Program Files
    $AppPath = "${env:ProgramFiles}\Local Agent"
}

if (-not (Test-Path $AppPath)) {
    Write-Host "Error: Cannot find Local Agent installation" -ForegroundColor Red
    Write-Host "Expected locations:" -ForegroundColor Yellow
    Write-Host "  - $env:LOCALAPPDATA\Programs\Local Agent" -ForegroundColor Yellow
    Write-Host "  - ${env:ProgramFiles}\Local Agent" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found app at: $AppPath" -ForegroundColor Green
$VenvPath = Join-Path $AppPath ".venv"

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

# Find pyproject.toml
$PyProjectFile = Join-Path $AppPath "pyproject.toml"
if (-not (Test-Path $PyProjectFile)) {
    Write-Host "Error: pyproject.toml not found at $PyProjectFile" -ForegroundColor Red
    exit 1
}

# Install dependencies from pyproject.toml
try {
    Push-Location $AppPath
    & $uvPath pip install --python $VenvPath -e .
    Pop-Location
    Write-Host "✓ Python dependencies installed (PyAutoGUI, OpenCV, Pillow, NumPy)" -ForegroundColor Green
} catch {
    Write-Host "Error installing dependencies: $_" -ForegroundColor Red
    Pop-Location
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
Write-Host "  1. Launch 'Local Agent' from Start Menu" -ForegroundColor White
Write-Host "  2. Configure AWS credentials and activity ARN" -ForegroundColor White
Write-Host "  3. Start using GUI automation!" -ForegroundColor White
Write-Host ""
Write-Host "Note: This agent uses PyAutoGUI for GUI automation." -ForegroundColor Yellow
Write-Host "It can control mouse, keyboard, and capture screenshots." -ForegroundColor Yellow
Write-Host ""

pause
