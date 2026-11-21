@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pip install -r tool\AutoVR-PC\requirements.txt && ".venv\Scripts\python.exe" verify.py
set "rc=%errorlevel%"
pause
exit /b %rc%
