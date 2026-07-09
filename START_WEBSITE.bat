@echo off
REM ISRO AQI Monitoring System - Startup Script for Windows
REM Starts both backend (FastAPI) and frontend (Next.js)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     ISRO AQI MONITORING SYSTEM - STARTUP SCRIPT              ║
echo ║  AI-Based Nationwide Surface PM2.5 and AQI Mapping          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Change to ISRO directory
cd /d "%~dp0.."

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python not found! Please install Python 3.8+
    exit /b 1
)
echo ✓ Python found

echo.
echo [2/4] Starting FastAPI backend...
start "ISRO Backend - FastAPI" cmd /k "cd backend && python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

echo.
echo [3/4] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Node.js not found! Please install Node.js 18+
    exit /b 1
)
echo ✓ Node.js found

echo.
echo [4/4] Starting Next.js frontend...
start "ISRO Frontend - Next.js" cmd /k "cd website && npm run dev"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                 STARTUP COMPLETE!                            ║
echo ║                                                              ║
echo ║  Backend API:    http://localhost:8000                      ║
echo ║  Frontend:       http://localhost:3000                      ║
echo ║  Health Check:   http://localhost:8000/health              ║
echo ║                                                              ║
echo ║  New terminal windows have been opened for both services.  ║
echo ║  Keep them running while using the application.            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

pause
