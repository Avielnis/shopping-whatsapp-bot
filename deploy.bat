@echo off
cd /d "%~dp0"
venv\Scripts\python.exe deploy\deploy.py
echo.
pause
