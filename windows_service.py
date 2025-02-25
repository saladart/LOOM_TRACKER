import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
from pathlib import Path

# Add local paths for DLLs
os.environ['PYTHONPATH'] = str(Path(__file__).parent / '.venv' / 'Lib' / 'site-packages')
os.environ['PATH'] = str(Path(__file__).parent / '.venv' / 'Scripts') + os.pathsep + os.environ['PATH']

class LoomTrackerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "LoomTrackerService"
    _svc_display_name_ = "Loom Time Tracker"
    _svc_description_ = "Loom Time Tracker Web Application"
    _exe_name_ = str(Path(__file__).parent / '.venv' / 'Scripts' / 'python.exe')  # Use venv Python
    _exe_args_ = f'"{__file__}"'  # Quote the path

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False
        
        # Set working directory
        os.chdir(Path(__file__).parent)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.stop_requested = True

    def SvcDoRun(self):
        try:
            from app import create_app
            from waitress import serve
            app = create_app()
            serve(app, host='192.168.3.100', port=80)
        except Exception as e:
            servicemanager.LogErrorMsg(str(e))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(LoomTrackerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(LoomTrackerService)