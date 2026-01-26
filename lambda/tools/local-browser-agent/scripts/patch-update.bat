@echo off
REM Local Browser Agent - Python Executor Patch
REM Double-click this file to update the Python executor to the latest version

echo.
echo ============================================================
echo   Local Browser Agent - Patch Updater
echo ============================================================
echo.

REM Check if running as administrator (recommended but not required)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges
) else (
    echo Note: Running without administrator privileges
    echo If you encounter permission errors, right-click and "Run as administrator"
)

echo.
echo This will download and install the latest Python executor updates.
echo Your existing files will be backed up before updating.
echo.

pause

REM Run the PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0patch-python-executor.ps1"

echo.
echo Press any key to close...
pause >nul
