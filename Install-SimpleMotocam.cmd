@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto failed
call Install-OpenCV24.cmd --no-pause
if errorlevel 1 goto failed
echo Ready. Run Start-SimpleMotocam.cmd.
pause
exit /b 0
:failed
echo Installation failed. See README.md for Python and OpenCV 2.4 build prerequisites.
pause
exit /b 1
