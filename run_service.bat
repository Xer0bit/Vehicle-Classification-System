@echo off
REM This script is used by the Windows service to run the web server
cd /d "%~dp0"

REM Wait for network to be available
timeout /t 30

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating default .env file...
    echo API_KEY=default_api_key > .env
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Verify Python environment and key packages
echo Checking Python installation and packages...
python -c "import sys; print(f'Python {sys.version} at {sys.executable}')"
python -c "import flask, torch; print(f'Flask {flask.__version__}, PyTorch {torch.__version__}')" > logs\environment.log 2>&1
if %errorlevel% neq 0 (
    echo Error verifying Python packages. See logs\environment.log for details.
    echo Error: Required packages missing > logs\service_error.log
    exit /b 1
)

REM Run the web server
echo Starting Image Classification Web Server...
python web_server.py --host 0.0.0.0 --port 5000
