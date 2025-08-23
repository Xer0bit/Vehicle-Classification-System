@echo off
setlocal

set "SERVICE_NAME=ImageClassificationAPI"

echo Stopping and removing %SERVICE_NAME% service...

:: Check if NSSM exists
if not exist "%~dp0nssm.exe" (
    echo Error: nssm.exe not found in the current directory
    exit /b 1
)

:: Stop and remove the service
"%~dp0nssm.exe" stop %SERVICE_NAME% >nul 2>&1
"%~dp0nssm.exe" remove %SERVICE_NAME% confirm >nul 2>&1

echo Service removed successfully.
pause
