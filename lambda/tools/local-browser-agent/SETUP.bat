@echo off
REM Local Browser Agent - Windows Setup (Batch Wrapper)
REM This calls the PowerShell setup script

echo ========================================
echo Local Browser Agent - Windows Setup
echo ========================================
echo.
echo Running PowerShell setup script...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0SETUP.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Setup failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0
