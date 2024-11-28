@echo off
sc stop LoomTrackerService
python windows_service.py remove
pause