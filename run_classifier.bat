@echo off
echo =======================================
echo Image Classification System
echo =======================================
echo.

:menu
echo Choose an option:
echo 1. Run Demo (Test with sample images)
echo 2. Run Demo with Class Mapping (Truck, Minitruck, Car)
echo 3. Classify a single image
echo 4. Classify a single image with Class Mapping
echo 5. Classify all images in a folder
echo 6. Classify all images in a folder with Class Mapping
echo 7. Exit
echo.

set /p choice=Enter your choice (1-7): 

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto demo_mapped
if "%choice%"=="3" goto single
if "%choice%"=="4" goto single_mapped
if "%choice%"=="5" goto folder
if "%choice%"=="6" goto folder_mapped
if "%choice%"=="7" goto end

echo Invalid choice, please try again.
echo.
goto menu

:demo
echo.
echo Running demo...
python demo.py
echo.
goto menu

:demo_mapped
echo.
echo Running demo with class mapping (Truck, Minitruck, Car)...
python demo.py --map
echo.
goto menu

:single
echo.
set /p img_path=Enter path to image file: 
if exist "%img_path%" (
    echo Classifying image...
    python classify.py --image "%img_path%" --show
) else (
    echo Error: Image file not found.
)
echo.
goto menu

:single_mapped
echo.
set /p img_path=Enter path to image file: 
if exist "%img_path%" (
    echo Classifying image with class mapping (Truck, Minitruck, Car)...
    python classify.py --image "%img_path%" --show --map
) else (
    echo Error: Image file not found.
)
echo.
goto menu

:folder
echo.
set /p folder_path=Enter path to folder containing images: 
if exist "%folder_path%" (
    echo Classifying all images in the folder...
    python classify.py --dir "%folder_path%" --show
) else (
    echo Error: Folder not found.
)
echo.
goto menu

:folder_mapped
echo.
set /p folder_path=Enter path to folder containing images: 
if exist "%folder_path%" (
    echo Classifying all images in the folder with class mapping (Truck, Minitruck, Car)...
    python classify.py --dir "%folder_path%" --show --map
) else (
    echo Error: Folder not found.
)
echo.
goto menu

:end
echo.
echo Thank you for using the Image Classification System.
echo Goodbye!
pause
