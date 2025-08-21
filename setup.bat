@echo off
REM Install required Python packages

echo Installing required packages...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo Error installing packages. Please check your Python installation and try again.
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo You can now run the classifier using:
echo   python classifier_gui.py
echo.
pause
