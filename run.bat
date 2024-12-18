@echo off
REM Run this batch file as administrator
@REM Activate env
cd /d %~dp0
.venv\Scripts\activate
REM Check for mode argument
SET MODE=local
IF NOT "%1"=="" SET MODE=%1
python run.py --mode %MODE%
pause