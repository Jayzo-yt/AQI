#!/bin/bash

# ISRO AQI Monitoring System - Startup Script for Linux/Mac
# Starts both backend (FastAPI) and frontend (Next.js)

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ISRO AQI MONITORING SYSTEM - STARTUP SCRIPT              ║"
echo "║  AI-Based Nationwide Surface PM2.5 and AQI Mapping          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python not found! Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION found"

# Start Backend
echo ""
echo "[2/4] Starting FastAPI backend..."
echo "Opening new terminal for backend..."

# Create a function to start backend in a new terminal if available
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$SCRIPT_DIR/backend' && python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -e "cd '$SCRIPT_DIR/backend' && python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000" &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal "$(printf '%s\n' 'cd '$SCRIPT_DIR/backend' && python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000')"
else
    # Fallback: run in background
    cd "$SCRIPT_DIR/backend"
    python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd "$SCRIPT_DIR"
fi

echo "✓ Backend started"
sleep 3

# Check Node.js
echo ""
echo "[3/4] Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "✗ Node.js not found! Please install Node.js 18+"
    exit 1
fi
NODE_VERSION=$(node --version)
echo "✓ Node.js $NODE_VERSION found"

# Start Frontend
echo ""
echo "[4/4] Starting Next.js frontend..."
echo "Opening new terminal for frontend..."

# Create a function to start frontend in a new terminal if available
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$SCRIPT_DIR/website' && npm run dev; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -e "cd '$SCRIPT_DIR/website' && npm run dev" &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal "$(printf '%s\n' 'cd '$SCRIPT_DIR/website' && npm run dev')"
else
    # Fallback: run in background
    cd "$SCRIPT_DIR/website"
    npm run dev &
    FRONTEND_PID=$!
    cd "$SCRIPT_DIR"
fi

echo "✓ Frontend started"

# Display summary
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 STARTUP COMPLETE!                            ║"
echo "║                                                              ║"
echo "║  Backend API:    http://localhost:8000                      ║"
echo "║  Frontend:       http://localhost:3000                      ║"
echo "║  Health Check:   http://localhost:8000/health              ║"
echo "║                                                              ║"
echo "║  New terminal windows have been opened for both services.  ║"
echo "║  Keep them running while using the application.            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Keep script running if needed
if [[ -n "$BACKEND_PID" ]] || [[ -n "$FRONTEND_PID" ]]; then
    wait
fi
