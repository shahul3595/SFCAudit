@echo off
REM ULB Audit Framework - Auto-setup and Run Script (CORRECTED VERSION)
REM This script will:
REM 1. Check if virtual environment exists, create if needed
REM 2. Activate virtual environment
REM 3. Install/upgrade dependencies
REM 4. Run the audit engine

echo ========================================================================
echo ULB AUDIT FRAMEWORK - Tamil Nadu State Finance Commission
echo ========================================================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Current Directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [2/4] Virtual environment not found. Creating venv...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo [2/4] Virtual environment found.
)
echo.

REM Activate virtual environment
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

REM Install/upgrade dependencies
echo [4/4] Installing/upgrading dependencies...
echo This may take a few moments...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo WARNING: Some packages may not have installed correctly
    echo Attempting to continue...
)
echo Dependencies installed.
echo.

echo ========================================================================
echo STARTING AUDIT ENGINE
echo ========================================================================
echo.

REM Run the audit engine
python scripts\run_audit.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ========================================================================
    echo ERROR: AUDIT ENGINE ENCOUNTERED ERRORS
    echo ========================================================================
    echo.
    echo Please check the logs folder for detailed error messages.
    echo.
) else (
    echo.
    echo ========================================================================
    echo AUDIT ENGINE COMPLETED SUCCESSFULLY
    echo ========================================================================
    echo.
    echo Check the 'reports' folder for output files:
    echo   - Individual ULB audit reports (PDF)
    echo   - Master dashboard (Excel)
    echo   - Detailed findings report (Excel)
    echo.
    echo Check the 'logs' folder for execution logs.
    echo.
)

pause