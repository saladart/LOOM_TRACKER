@echo off
REM Ensure running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrator privileges
    echo Please run as administrator
    pause
    exit /b 1
)

REM Set paths
set "PYTHON_PATH=%~dp0.venv\Scripts\python.exe"
set "SERVICE_PATH=%~dp0windows_service.py"

REM Create logs directory
if not exist "%~dp0logs" mkdir "%~dp0logs"

echo Installing required packages...
"%PYTHON_PATH%" -m pip install pywin32 waitress > logs\pip_install.log 2>&1
if %errorLevel% neq 0 (
    echo Failed to install packages. Check logs\pip_install.log
    pause
    exit /b 1
)

echo Activating virtual environment...
call "%~dp0.venv\Scripts\activate"

echo Installing service...
"%PYTHON_PATH%" "%SERVICE_PATH%" --startup auto install > logs\service_install.log 2>&1
if %errorLevel% neq 0 (
    echo Failed to install service. Check logs\service_install.log
    pause
    exit /b 1
)

echo Starting service...
sc start LoomTrackerService > logs\service_start.log 2>&1
if %errorLevel% neq 0 (
    echo Failed to start service. Check logs\service_start.log
    pause
    exit /b 1
)

echo Service installation complete
pause