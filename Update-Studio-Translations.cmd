@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-translation\Scripts\python.exe" (
  echo Prepare the translation environment first. See tools\doc_translate\README.md
  exit /b 1
)
".venv-translation\Scripts\python.exe" tools\doc_translate\translate.py --input src/simplemotocam/studio_ui/i18n/en.json --output src/simplemotocam/studio_ui/i18n --glossary tools/doc_translate/studio-protected.json --no-bundle %*
if errorlevel 1 exit /b 1
".venv-translation\Scripts\python.exe" tools\doc_translate\build_studio_bundle.py
