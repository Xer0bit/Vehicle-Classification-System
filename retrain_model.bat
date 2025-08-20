@echo off
echo =======================================
echo Model Retraining Tool
echo =======================================
echo.

if not exist "feedback_data\retraining_data_*.csv" (
    echo No retraining data found.
    echo Please use the interactive classifier to collect feedback first.
    echo Then export the feedback data for retraining.
    echo.
    pause
    exit /b 1
)

echo Found retraining data:
dir /b feedback_data\retraining_data_*.csv
echo.

set /p feedback_file=Enter the name of the feedback file to use (from the list above): 

if not exist "feedback_data\%feedback_file%" (
    echo Error: File not found.
    pause
    exit /b 1
)

echo.
echo Starting model retraining process...
echo This may take several minutes depending on your computer's performance.
echo.

python retrain.py --feedback "feedback_data\%feedback_file%" --output "pt/retrained"

if %errorlevel% neq 0 (
    echo.
    echo Error during retraining. Please check the error message above.
    echo.
    pause
    exit /b 1
)

echo.
echo Retraining complete!
echo.
echo The retrained model has been saved to:
echo - pt/retrained/retrained_model_weights.pth
echo - pt/retrained/retrained_label_encoder.pth
echo.
echo To use the retrained model, you can run the interactive classifier with:
echo python classifier_gui.py --model pt/retrained/retrained_model_weights.pth --encoder pt/retrained/retrained_label_encoder.pth
echo.

pause
