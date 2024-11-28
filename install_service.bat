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

REM Clean up any existing service
echo Cleaning up existing service...
sc stop LoomTrackerService >nul 2>&1
sc delete LoomTrackerService >nul 2>&1

echo Installing required packages...
"%PYTHON_PATH%" -m pip install pywin32 waitress > logs\pip_install.log 2>&1
if %errorLevel% neq 0 (
    echo Failed to install packages. Check logs\pip_install.log
    type logs\pip_install.log
    pause
    exit /b 1
)

echo Installing service...
"%PYTHON_PATH%" "%SERVICE_PATH%" install > logs\service_install.log 2>&1
if %errorLevel% neq 0 (
    echo Failed to install service. Check logs\service_install.log
    type logs\service_install.log
    pause
    exit /b 1
)

echo Starting service...
net start LoomTrackerService > logs\service_start.log 2>&1
if %errorLevel% neq 0 (
    echo Failed to start service. Check logs\service_start.log
    type logs\service_start.log
    pause
    exit /b 1
)

echo Service installation complete
sc query LoomTrackerService
pause