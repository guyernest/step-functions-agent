# Local Browser Agent - Windows Setup Script
# This script sets up the Python environment for the Local Browser Agent on Windows

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Local Browser Agent - Windows Setup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
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

Write-Host "✓ Found app at: $AppPath" -ForegroundColor Green
$PythonDir = Join-Path $AppPath "python"
$VenvPath = Join-Path $PythonDir ".venv"

Write-Host ""
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "Step 1: Checking for UV package manager" -ForegroundColor Cyan
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan

# Enhanced UV detection function
function Find-UV {
    Write-Host "  Searching for UV..." -ForegroundColor Gray

    # Check known installation locations
    $uvLocations = @(
        "$env:USERPROFILE\.local\bin\uv.exe",
        "$env:USERPROFILE\.cargo\bin\uv.exe"
    )

    foreach ($location in $uvLocations) {
        if (Test-Path $location) {
            Write-Host "  ✓ Found UV at: $location" -ForegroundColor Green
            return $location
        }
    }

    # Check PATH
    $uvInPath = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($uvInPath) {
        Write-Host "  ✓ Found UV in PATH: $($uvInPath.Source)" -ForegroundColor Green
        return $uvInPath.Source
    }

    Write-Host "  ✗ UV not found in known locations" -ForegroundColor Yellow
    return $null
}

$uvPath = Find-UV

if (-not $uvPath) {
    Write-Host ""
    Write-Host "  Installing UV package manager..." -ForegroundColor Yellow

    try {
        irm https://astral.sh/uv/install.ps1 | iex

        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path", "Machine")

        # Try to find UV again after installation
        Start-Sleep -Seconds 2
        $uvPath = Find-UV

        if (-not $uvPath) {
            Write-Host ""
            Write-Host "Error: Failed to install UV" -ForegroundColor Red
            Write-Host "Please install manually: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
            exit 1
        }

        Write-Host "  ✓ UV installed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "Error installing UV: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "Step 2: Creating Python virtual environment" -ForegroundColor Cyan
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan

# Create venv
try {
    Write-Host "  Creating Python 3.11 venv at: $VenvPath" -ForegroundColor Gray
    & $uvPath venv $VenvPath --python 3.11
    Write-Host "  ✓ Python 3.11 virtual environment created" -ForegroundColor Green
} catch {
    Write-Host "Error creating venv: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "Step 3: Installing Python dependencies" -ForegroundColor Cyan
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan

# Install dependencies
$RequirementsFile = Join-Path $PythonDir "requirements.txt"
if (-not (Test-Path $RequirementsFile)) {
    Write-Host "Error: requirements.txt not found at $RequirementsFile" -ForegroundColor Red
    exit 1
}

try {
    Write-Host "  Installing from: $RequirementsFile" -ForegroundColor Gray
    & $uvPath pip install --python $VenvPath -r $RequirementsFile
    Write-Host "  ✓ Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "Error installing dependencies: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "Step 4: Installing Playwright browsers" -ForegroundColor Cyan
Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Cyan

Write-Host "  Installing Chromium only (Microsoft Edge can be used via system)" -ForegroundColor Gray
Write-Host ""

try {
    $PlaywrightExe = Join-Path $VenvPath "Scripts\playwright.exe"
    & $PlaywrightExe install chromium --with-deps
    Write-Host "  ✓ Chromium browser installed" -ForegroundColor Green
} catch {
    Write-Host "Warning: Playwright browser installation had issues" -ForegroundColor Yellow
    Write-Host "  This is usually fine - continue with setup" -ForegroundColor Gray
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✓ Setup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Browser Configuration:" -ForegroundColor Yellow
Write-Host "  • Microsoft Edge (recommended for Windows)" -ForegroundColor White
Write-Host "    Already installed on Windows 10/11 - no additional setup needed!" -ForegroundColor Gray
Write-Host ""
Write-Host "  • Google Chrome" -ForegroundColor White
Write-Host "    Install separately if needed - see docs/CHROME_ENTERPRISE_INSTALL.md" -ForegroundColor Gray
Write-Host ""
Write-Host "  • Chromium (fallback)" -ForegroundColor White
Write-Host "    Installed by this script" -ForegroundColor Gray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Launch 'Local Browser Agent' from Start Menu" -ForegroundColor White
Write-Host "  2. Go to Configuration → Browser Channel" -ForegroundColor White
Write-Host "  3. Select 'Microsoft Edge' (recommended for Windows)" -ForegroundColor White
Write-Host "  4. Configure AWS credentials" -ForegroundColor White
Write-Host "  5. Test with an example script" -ForegroundColor White
Write-Host ""
Write-Host "Python environment: $VenvPath" -ForegroundColor Gray
Write-Host ""
