@echo off
echo =======================================
echo Interactive Classifier
echo =======================================
echo.

python classifier_gui.py

if %errorlevel% neq 0 (
    echo.
    echo Error running the interactive classifier.
    echo Please make sure all dependencies are installed by running setup.bat first.
    echo.
    pause
    exit /b 1
)

pause
