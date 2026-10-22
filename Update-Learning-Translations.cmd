@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-translation\Scripts\python.exe" (
  echo First prepare the translation environment. See tools\doc_translate\README.md
  exit /b 1
)
node tools\doc_translate\export_catalog.cjs
if errorlevel 1 exit /b 1
".venv-translation\Scripts\python.exe" tools\doc_translate\translate.py %*
if errorlevel 1 exit /b 1
echo Learning translations updated.
