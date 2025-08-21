@echo off
echo Starting Image Classification Web Server...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import flask, torch, torchvision, PIL, sklearn" >nul 2>&1
if %errorlevel% neq 0 (
    echo Some required packages are missing. Installing...
    pip install flask torch torchvision pillow scikit-learn python-dotenv
    if %errorlevel% neq 0 (
        echo Failed to install required packages
        pause
        exit /b 1
    )
)

REM Check if model files exist
if not exist "pt\model_weights.pth" (
    echo Error: Model weights file not found at pt\model_weights.pth
    echo Please ensure the model is trained and saved
    pause
    exit /b 1
)

if not exist "pt\label_encoder.pth" (
    echo Error: Label encoder file not found at pt\label_encoder.pth
    echo Please ensure the label encoder is saved
    pause
    exit /b 1
)

REM Check if .env file exists, create if not
if not exist ".env" (
    echo Creating default .env file...
    echo API_KEY=your_api_key_here > .env
    echo API_SECRET_KEY=your_secret_key_here >> .env
    echo.
    echo Default .env file created. Please update with your actual credentials.
    echo.
)

echo.
echo ====================================
echo Image Classification Web Server
echo ====================================
echo.
echo Web UI will be available at: http://127.0.0.1:5000
echo API Test Interface: http://127.0.0.1:5000/api-test
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the web server
python web_server.py --host 127.0.0.1 --port 5000

echo.
echo Server stopped.
pause
