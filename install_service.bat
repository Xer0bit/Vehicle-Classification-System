@echo off
echo Installing Image Classification Web Server as a Windows Service
echo.

REM Check for admin rights
NET SESSION >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run this script as an administrator.
    pause
    exit /b 1
)

REM Get the absolute path of the installation directory
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

REM Check for NSSM (Non-Sucking Service Manager)
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo NSSM not found. Downloading NSSM...
    
    REM Create temp directory
    mkdir "%TEMP%\nssm_install" 2>nul
    
    REM Download NSSM
    powershell -Command "& {(New-Object Net.WebClient).DownloadFile('https://nssm.cc/release/nssm-2.24.zip', '%TEMP%\nssm.zip')}"
    
    REM Extract NSSM
    powershell -Command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%TEMP%\nssm.zip', '%TEMP%\nssm_install')}"
    
    REM Find the correct architecture
    if exist "%TEMP%\nssm_install\nssm-2.24\win64\nssm.exe" (
        copy "%TEMP%\nssm_install\nssm-2.24\win64\nssm.exe" "%INSTALL_DIR%\nssm.exe"
    ) else (
        copy "%TEMP%\nssm_install\nssm-2.24\win32\nssm.exe" "%INSTALL_DIR%\nssm.exe"
    )
    
    REM Clean up
    rmdir /S /Q "%TEMP%\nssm_install"
    del /Q "%TEMP%\nssm.zip"
    
    set "NSSM_CMD=%INSTALL_DIR%\nssm.exe"
) else (
    set "NSSM_CMD=nssm"
)

REM Install the service
echo Installing service 'ImageClassificationAPI'...
%NSSM_CMD% install ImageClassificationAPI "%INSTALL_DIR%\run_service.bat"
%NSSM_CMD% set ImageClassificationAPI DisplayName "Image Classification API"
%NSSM_CMD% set ImageClassificationAPI Description "Vehicle Image Classification API Web Server"
%NSSM_CMD% set ImageClassificationAPI AppDirectory "%INSTALL_DIR%"
%NSSM_CMD% set ImageClassificationAPI AppStdout "%INSTALL_DIR%\logs\service.log"
%NSSM_CMD% set ImageClassificationAPI AppStderr "%INSTALL_DIR%\logs\service_error.log"
%NSSM_CMD% set ImageClassificationAPI Start SERVICE_AUTO_START
%NSSM_CMD% set ImageClassificationAPI ObjectName LocalSystem

REM Create logs directory if it doesn't exist
mkdir "%INSTALL_DIR%\logs" 2>nul

REM Start the service
echo Starting service 'ImageClassificationAPI'...
net start ImageClassificationAPI

echo.
echo Service installation complete! The Image Classification API will now start automatically on system boot.
echo Logs are saved to %INSTALL_DIR%\logs
echo.
echo You can manage the service from Windows Services or use the following commands:
echo   net stop ImageClassificationAPI   - to stop the service
echo   net start ImageClassificationAPI  - to start the service
echo.

pause
