@echo off
pip install pywin32 waitress

cd /d %~dp0
call .venv\Scripts\activate

python windows_service.py install
sc start LoomTrackerService
pause