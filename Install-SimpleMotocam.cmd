@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto failed
echo Ready. Run Start-SimpleMotocam.cmd.
pause
exit /b 0
:failed
echo Installation failed. Install Python 3.10 or newer and see README.md.
pause
exit /b 1
