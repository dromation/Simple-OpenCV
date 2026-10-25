@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto failed
".venv\Scripts\python.exe" -c "from simplemotocam.studio_backend import backend_catalog; raise SystemExit(0 if backend_catalog()['opencv24']['available'] else 1)"
if not errorlevel 1 goto ready
".venv\Scripts\python.exe" tools\fetch_references.py opencv-2.4.13.7
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --target work\build-tools cmake==3.31.10
if errorlevel 1 goto failed
".venv\Scripts\python.exe" tools\build_opencv24.py
if errorlevel 1 goto failed
:ready
echo OpenCV 2.4.13.7 is ready as the primary processing engine.
if not "%~1"=="--no-pause" pause
exit /b 0
:failed
echo OpenCV 2.4 installation failed. Install Visual Studio C++ tools, Windows SDK and CMake/Ninja.
echo See docs\OPENCV_BACKENDS.md. The application will not silently switch versions.
if not "%~1"=="--no-pause" pause
exit /b 1
