@echo off
setlocal enabledelayedexpansion
title MechTech Platform Launcher

echo =====================================================================
echo                MECHTECH PLATFORM LAUNCHER
echo      Intelligent Equipment Monitoring ^& Fault Diagnosis
echo =====================================================================
echo.

:: 1. Navigate to project root
cd /d "%~dp0"

:: 2. Check Python Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing backend dependencies...
    pip install -e ".\backend[dev]"
) else (
    echo [OK] Virtual environment detected.
    call .venv\Scripts\activate.bat
)

:: 3. Ensure database directory exists
if not exist "data\db" (
    mkdir "data\db"
)
if not exist "backend\data\db" (
    mkdir "backend\data\db"
)

:: 4. Run Alembic Database Migrations
echo [1/3] Running database migrations...
cd backend
alembic upgrade head
if errorlevel 1 (
    echo [WARNING] Alembic upgrade encountered an issue. Ensuring tables via Python...
)

:: 5. Seed Demonstration Data (Organization, Users, Induction Motor, Rules, Models)
echo [2/3] Seeding demo users and induction motor equipment...
python scripts\seed_demo_data.py
cd ..

:: 6. Launch Backend Server in a new window
echo [3/3] Launching FastAPI Backend Server on http://127.0.0.1:8000...
start "MechTech Backend API" cmd /k "cd /d "%~dp0backend" && call ..\.venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:: 7. Launch Frontend Vite Dev Server in a new window
echo Launching Vite Frontend on http://localhost:5173...
start "MechTech Frontend UI" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: 8. Wait 3 seconds and launch browser
timeout /t 3 /nobreak >nul
echo Opening MechTech in browser...
start http://localhost:5173

echo.
echo =====================================================================
echo [SUCCESS] MechTech is now running!
echo.
echo - Frontend (Apple Liquid Glass UI): http://localhost:5173
echo - Backend API ^& Swagger Docs:       http://127.0.0.1:8000/docs
echo.
echo Demo Login Credentials:
echo   Administrator: demo.admin@example.com      / demo-password-123
echo   Maintainer:    demo.maintainer@example.com / demo-password-123
echo   Viewer:        demo.viewer@example.com     / demo-password-123
echo =====================================================================
pause
