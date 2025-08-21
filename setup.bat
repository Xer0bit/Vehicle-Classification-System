@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo Image Classification System - Development Setup
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Checking for virtual environment...
if not exist "vision\" (
    echo Creating new vision environment...
    python -m venv vision
    if %errorlevel% neq 0 (
        echo Failed to create vision environment
        pause
        exit /b 1
    )
) else (
    echo Vision environment already exists.
)

REM Activate virtual environment
if exist "vision\Scripts\activate.bat" (
    echo Activating vision environment...
    call vision\Scripts\activate.bat
    
    REM Create activation batch file for future use
    echo @echo off > activate_env.bat
    echo call vision\Scripts\activate.bat >> activate_env.bat
    echo echo Vision environment activated. Use 'deactivate' to exit. >> activate_env.bat
)

REM Install required packages
echo.
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo Package installation failed.
    echo Please try: python -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM Verify key packages are installed correctly
echo.
echo Verifying package installation...
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torchvision; print(f'TorchVision version: {torchvision.__version__}')"
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
python -c "import PIL; print(f'Pillow version: {PIL.__version__}')"
python -c "import flask; print(f'Flask version: {flask.__version__}')" 2>nul

echo.
echo Setup completed successfully!
echo.
echo To activate the environment in the future, run: activate_env.bat
echo.
pause
