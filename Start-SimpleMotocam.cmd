@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Python environment missing. See SIMPLEMOTOCAM.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m simplemotocam.studio %*
if errorlevel 1 pause
