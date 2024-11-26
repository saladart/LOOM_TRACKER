@echo off
REM Run this batch file as administrator
@REM Activate env
cd /d %~dp0
.venv\Scripts\activate && python run.py
pause