@echo off
echo Starting Paper Data Converter V3.0...
echo.

python gui_app.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo  Startup Failed!
    echo ================================================
    echo.
    echo Possible reasons:
    echo 1. Python not installed or not in PATH
    echo 2. Missing dependencies
    echo.
    echo Solution:
    echo 1. Install Python 3.8+
    echo 2. Run: pip install -r requirements.txt
    echo.
    pause
)
