@echo off
REM Build Ascent Inventory for Windows
cd /d "%~dp0\.."
python -m pip install -r requirements.txt -r requirements-build.txt
python scripts\build_desktop.py --zip
pause
