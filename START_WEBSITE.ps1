# ISRO AQI Monitoring System - Startup Script for Windows PowerShell
# Starts both backend (FastAPI) and frontend (Next.js)

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     ISRO AQI MONITORING SYSTEM - STARTUP SCRIPT              ║" -ForegroundColor Cyan
Write-Host "║  AI-Based Nationwide Surface PM2.5 and AQI Mapping          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get the script's directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check Python
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Start Backend
Write-Host ""
Write-Host "[2/4] Starting FastAPI backend..." -ForegroundColor Yellow
Write-Host "Opening new terminal for backend..." -ForegroundColor Gray

$backendPath = Join-Path $scriptPath "backend"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal -PassThru | Out-Null

Write-Host "✓ Backend started in new window" -ForegroundColor Green
Start-Sleep -Seconds 3

# Check Node.js
Write-Host ""
Write-Host "[3/4] Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = & node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found! Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Start Frontend
Write-Host ""
Write-Host "[4/4] Starting Next.js frontend..." -ForegroundColor Yellow
Write-Host "Opening new terminal for frontend..." -ForegroundColor Gray

$frontendPath = Join-Path $scriptPath "website"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm run dev" -WindowStyle Normal -PassThru | Out-Null

Write-Host "✓ Frontend started in new window" -ForegroundColor Green

# Display summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                 STARTUP COMPLETE!                            ║" -ForegroundColor Cyan
Write-Host "║                                                              ║" -ForegroundColor Cyan
Write-Host "║  Backend API:    http://localhost:8000                      ║" -ForegroundColor Green
Write-Host "║  Frontend:       http://localhost:3000                      ║" -ForegroundColor Green
Write-Host "║  Health Check:   http://localhost:8000/health              ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Cyan
Write-Host "║  New terminal windows have been opened for both services.  ║" -ForegroundColor Cyan
Write-Host "║  Keep them running while using the application.            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to continue"
