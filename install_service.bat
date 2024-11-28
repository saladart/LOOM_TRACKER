@echo off
pip install pywin32 waitress
python windows_service.py install
sc start LoomTrackerService
pause