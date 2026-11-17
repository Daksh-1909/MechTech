# MechTech PowerShell Launch Script
# Run with: .\run.ps1

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "               MECHTECH PLATFORM LAUNCHER" -ForegroundColor White
Write-Host "     Intelligent Equipment Monitoring & Fault Diagnosis" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootPath

# 1. Check Python Venv
$PythonExe = Join-Path $RootPath ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[*] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    & "$RootPath\.venv\Scripts\pip.exe" install -e ".\backend[dev]"
}

# 2. Ensure data directories
$DbDir = Join-Path $RootPath "data\db"
if (-not (Test-Path $DbDir)) {
    New-Item -ItemType Directory -Force -Path $DbDir | Out-Null
}
$BackendDbDir = Join-Path $RootPath "backend\data\db"
if (-not (Test-Path $BackendDbDir)) {
    New-Item -ItemType Directory -Force -Path $BackendDbDir | Out-Null
}

# 3. Database migrations & demo seed
Write-Host "[1/3] Preparing Database & Migrations..." -ForegroundColor Yellow
Set-Location (Join-Path $RootPath "backend")
& "$RootPath\.venv\Scripts\alembic.exe" upgrade head

Write-Host "[2/3] Seeding Demo Fleet & User Accounts..." -ForegroundColor Yellow
& "$RootPath\.venv\Scripts\python.exe" "scripts\seed_demo_data.py"
Set-Location $RootPath

# 4. Start Backend in separate process
Write-Host "[3/3] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootPath\backend'; & '$RootPath\.venv\Scripts\Activate.ps1'; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

# 5. Start Frontend in separate process
Write-Host "Starting Vite React Frontend on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootPath\frontend'; npm run dev"

# 6. Open Browser
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "[SUCCESS] MechTech is now live!" -ForegroundColor White
Write-Host "  Frontend URL: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  API Docs URL: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Demo Logins:" -ForegroundColor White
Write-Host "  Admin:      demo.admin@example.com      / demo-password-123" -ForegroundColor Gray
Write-Host "  Maintainer: demo.maintainer@example.com / demo-password-123" -ForegroundColor Gray
Write-Host "  Viewer:     demo.viewer@example.com     / demo-password-123" -ForegroundColor Gray
Write-Host "=====================================================================" -ForegroundColor Green
