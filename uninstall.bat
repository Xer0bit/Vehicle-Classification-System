@echo off
echo Uninstalling Image Classification Web Server
echo.

REM Check for admin rights
NET SESSION >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run this script as an administrator.
    pause
    exit /b 1
)

REM Stop and remove the service if it exists
sc query ImageClassificationAPI >nul 2>&1
if %errorlevel% equ 0 (
    echo Stopping service...
    net stop ImageClassificationAPI
    
    echo Removing service...
    where nssm >nul 2>&1
    if %errorlevel% equ 0 (
        nssm remove ImageClassificationAPI confirm
    ) else (
        if exist "%~dp0nssm.exe" (
            "%~dp0nssm.exe" remove ImageClassificationAPI confirm
        ) else (
            sc delete ImageClassificationAPI
        )
    )
)

REM Ask if the user wants to completely remove all files
echo.
echo Do you want to completely remove all files? (Y/N)
choice /c YN /m "Delete all program files"

if %errorlevel% equ 1 (
    echo.
    echo Removing all program files...
    
    REM Get parent directory
    for %%I in ("%~dp0..") do set "PARENT_DIR=%%~fI"
    
    REM Save current directory before deletion
    set "CURRENT_DIR=%CD%"
    
    REM Change to a safe directory to avoid "The process cannot access the file because it is being used by another process" error
    cd /d "%TEMP%"
    
    REM Recursively delete all files and directories except the batch file itself
    for /d %%D in ("%~dp0*") do if not "%%~fD"=="%~f0" rd /s /q "%%~fD"
    for %%F in ("%~dp0*") do if not "%%~fF"=="%~f0" del /q "%%~fF"
    
    echo.
    echo All files have been removed. This uninstall script will self-delete when you close this window.
    echo.
    
    REM Create a self-deletion script
    echo @echo off > "%TEMP%\cleanup.bat"
    echo timeout /t 1 >> "%TEMP%\cleanup.bat"
    echo del /q "%~f0" >> "%TEMP%\cleanup.bat"
    echo rd /q "%~dp0" >> "%TEMP%\cleanup.bat"
    
    REM Execute the cleanup script
    start "" "%TEMP%\cleanup.bat"
) else (
    echo.
    echo Uninstallation of service completed. Program files were preserved.
)

pause
