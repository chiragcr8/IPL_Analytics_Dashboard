@echo off
setlocal enabledelayedexpansion

:: Change to script directory
cd /d "%~dp0"
echo Starting IPL Data Analysis Dashboard...

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install/Update required packages
echo Installing/Updating dependencies...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

:: Ensure Streamlit is installed
python -m pip install streamlit --quiet
if %errorlevel% neq 0 (
    echo Error: Failed to install Streamlit
    pause
    exit /b 1
)

:: Run the application
echo Starting Streamlit server...
python -m streamlit run "%~dp0app.py"

pause