# Setup script for Python environment
# This script helps set up either conda or venv environment

param(
    [switch]$UseVenv,
    [string]$EnvName = "m2_env"
)

if ($UseVenv) {
    Write-Host "Setting up Python venv environment..." -ForegroundColor Green
    
    # Check if Python is available
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-Host "Python not found. Please install Python first." -ForegroundColor Red
        exit 1
    }
    
    # Create venv
    Write-Host "Creating virtual environment: $EnvName" -ForegroundColor Yellow
    python -m venv $EnvName
    
    # Activate venv
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\$EnvName\Scripts\Activate.ps1"
    
    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    
    # Install dependencies
    if (Test-Path "requirements.txt") {
        Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
    
    Write-Host "Environment setup complete!" -ForegroundColor Green
    Write-Host "To activate in the future, run: .\${EnvName}\Scripts\Activate.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Setting up conda environment..." -ForegroundColor Green
    
    # Try to find conda
    $condaPaths = @(
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "$env:USERPROFILE\AppData\Local\Continuum\anaconda3\Scripts\conda.exe",
        "$env:USERPROFILE\AppData\Local\Continuum\miniconda3\Scripts\conda.exe"
    )
    
    $condaExe = $null
    foreach ($path in $condaPaths) {
        if (Test-Path $path) {
            $condaExe = $path
            break
        }
    }
    
    if (-not $condaExe) {
        Write-Host "Conda not found. Use -UseVenv flag to use Python venv instead." -ForegroundColor Red
        Write-Host "Example: .\setup-env.ps1 -UseVenv" -ForegroundColor Yellow
        exit 1
    }
    
    # Create conda environment
    Write-Host "Creating conda environment: $EnvName" -ForegroundColor Yellow
    & $condaExe create -n $EnvName python=3.10 -y
    
    # Activate conda (requires conda to be initialized)
    Write-Host "To activate conda environment, run:" -ForegroundColor Yellow
    Write-Host "  conda activate $EnvName" -ForegroundColor Cyan
    Write-Host "Or if conda is not initialized, use:" -ForegroundColor Yellow
    Write-Host "  & $condaExe activate $EnvName" -ForegroundColor Cyan
}
