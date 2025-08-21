@echo off
echo ============================================
echo Image Classification System - Production Setup
echo ============================================
echo.

REM Check for admin rights
NET SESSION >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run this script as an administrator.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Create logs directory
echo Creating log directories...
mkdir logs 2>nul

REM Check if running in virtual environment or if one exists
echo Checking Python environment...
python -c "import sys; print('Virtual environment: ' + ('Yes' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'No'))"

if exist "vision\Scripts\activate.bat" (
    echo Virtual environment found. Activating...
    call vision\Scripts\activate.bat
    echo Environment activated. Using Python from:
    where python
)

REM Install required packages
echo.
echo Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing packages. Please check your Python installation.
    pause
    exit /b 1
)

REM Verify installation of critical packages
echo.
echo Verifying package installation...
python -c "import torch, torchvision, flask, PIL, sklearn, numpy; print('All critical packages verified!')"
if %errorlevel% neq 0 (
    echo Error: Some critical packages are not installed properly.
    echo Please check the error message above and fix the installation.
    pause
    exit /b 1
)

REM Check for model files
echo.
echo Checking model files...
if not exist "pt\model_weights.pth" (
    echo Error: Model weights file not found at pt\model_weights.pth
    echo Please ensure the model is trained and saved before setting up production.
    pause
    exit /b 1
)

if not exist "pt\label_encoder.pth" (
    echo Error: Label encoder file not found at pt\label_encoder.pth
    echo Please ensure the label encoder is saved before setting up production.
    pause
    exit /b 1
)

REM Create .env file with secure random API key
echo Generating secure API key...
set "API_KEY="
for /L %%i in (1,1,32) do call :append_random

echo Creating .env file...
echo API_KEY=%API_KEY% > .env

REM Create directories for uploads and feedback
echo Creating required directories...
mkdir temp_uploads 2>nul
mkdir feedback_data\corrected_images 2>nul

REM Run test to verify setup
echo Running server test...
start /b "" python web_server.py --port 5000
timeout /t 5
curl -s http://localhost:5000/api/health > nul
if %errorlevel% neq 0 (
    echo Warning: Could not connect to the web server. There might be an issue with the setup.
    echo Please check the logs for more details.
) else (
    echo Server test successful!
    taskkill /f /im python.exe > nul 2>&1
)

echo.
echo ============================================
echo Production setup complete!
echo.
echo To install as a Windows service, run:
echo   install_service.bat
echo.
echo To start the web server manually, run:
echo   run_web_server.bat
echo.
echo To uninstall the application, run:
echo   uninstall.bat
echo ============================================
echo.

pause
exit /b 0

:append_random
set /a r=%random% %% 36
set "chars=0123456789abcdefghijklmnopqrstuvwxyz"
set "API_KEY=%API_KEY%%%chars:~%r%,1%%"
exit /b
