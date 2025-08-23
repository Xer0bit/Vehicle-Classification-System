@echo off
echo Stopping Vehicle Classification Service...

:: Check for admin rights
NET SESSION >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run this script as an administrator.
    pause
    exit /b 1
)

:: Stop the service
net stop ImageClassificationAPI

if %errorlevel% equ 0 (
    echo Service stopped successfully.
) else (
    echo Failed to stop the service. Make sure it is running.
)

pause
