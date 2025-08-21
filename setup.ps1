# Image Classification System - Development Setup
Write-Host "============================================"
Write-Host "Image Classification System - Development Setup"
Write-Host "============================================"
Write-Host ""

# Check if Python is available
try {
    python --version | Out-Null
} catch {
    Write-Host "Error: Python is not installed or not in PATH"
    Write-Host "Please install Python and try again"
    pause
    exit 1
}

Write-Host "Checking for virtual environment..."
if (Test-Path "vision") {
    Write-Host "Vision environment already exists..."
} else {
    Write-Host "Creating new vision environment..."
    python -m venv vision
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create vision environment with venv, trying virtualenv..."
        python -m pip install --user virtualenv
        python -m virtualenv vision
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to create vision environment."
            Write-Host "Please check your Python installation."
            pause
            exit 1
        }
    }
}

# Activate virtual environment
if (Test-Path "vision\Scripts\Activate.ps1") {
    Write-Host "Activating vision environment..."
    & "vision\Scripts\Activate.ps1"
    
    # Create activation script for future use
    @"
if (Test-Path "vision\Scripts\Activate.ps1") {
    & "vision\Scripts\Activate.ps1"
    Write-Host "Vision environment activated. Use 'deactivate' to exit."
} else {
    Write-Host "No activation script found."
}
"@ | Out-File -FilePath "activate_env.ps1" -Encoding UTF8
} else {
    Write-Host "Vision environment exists but activation script not found."
    Write-Host "Please check your Python installation."
    pause
    exit 1
}

# Install required packages
Write-Host "`nInstalling required packages..."
python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Standard installation failed. Trying with --user flag..."
    python -m pip install --user -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "All installation methods failed."
        Write-Host "`nPossible solutions:"
        Write-Host "1. Run this script as administrator"
        Write-Host "2. Use a different Python environment"
        Write-Host "3. Install packages manually with: pip install --user -r requirements.txt`n"
        
        $response = Read-Host "Continue anyway? (Y/N)"
        if ($response -ne "Y") {
            Write-Host "Setup aborted by user."
            pause
            exit 1
        }
    }
}

# Verify key packages
Write-Host "`nVerifying package installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torchvision; print(f'TorchVision version: {torchvision.__version__}')"
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
python -c "import PIL; print(f'Pillow version: {PIL.__version__}')"
python -c "import flask; print(f'Flask version: {flask.__version__}')" 2>$null

Write-Host "`nSetup completed successfully!`n"

# Create usage instructions
Write-Host "Creating usage instructions file..."
@"
# Image Classification System - Usage Instructions

## Development Usage

1. Activate vision environment:
   ```powershell
   .\activate_env.ps1
   ```

2. Run GUI classifier:
   ```powershell
   python classifier_gui.py
   ```

3. Run Web server:
   ```powershell
   .\run_web_server.bat
   ```
"@ | Out-File -FilePath "USAGE.md" -Encoding UTF8

Write-Host "`nFor development usage:"
Write-Host "  - Activate vision environment: .\activate_env.ps1"
Write-Host "  - Run GUI classifier: python classifier_gui.py"
Write-Host "  - Run Web server: .\run_web_server.bat"
Write-Host "`nSee USAGE.md for detailed instructions.`n"

pause
