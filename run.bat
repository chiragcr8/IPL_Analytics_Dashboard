@echo off
setlocal enabledelayedexpansion

:: Change to script directory
cd /d "%~dp0"

echo Setting up IPL Data Analysis Dashboard...

:: Check Python installation
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

:: Check required files
IF NOT EXIST "matches.csv" (
    echo Error: matches.csv file is missing!
    echo Please download the IPL dataset and place matches.csv in this folder.
    pause
    exit /b 1
)

IF NOT EXIST "deliveries.csv" (
    echo Error: deliveries.csv file is missing!
    echo Please download the IPL dataset and place deliveries.csv in this folder.
    pause
    exit /b 1
)

:: Create and activate virtual environment
IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Error creating virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error activating virtual environment
    pause
    exit /b 1
)

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing requirements
    pause
    exit /b 1
)

:: Install Streamlit
echo Installing Streamlit...
pip install streamlit
if %errorlevel% neq 0 (
    echo Error installing Streamlit
    pause
    exit /b 1
)

:: Run the application
echo Starting the application...
streamlit run "%~dp0app.py"

pause