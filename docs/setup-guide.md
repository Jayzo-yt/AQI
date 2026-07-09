# 🚀 ISRO AQI Monitoring System - Setup & Installation Guide

## 📖 Complete Setup Instructions

This guide will help you set up and run the stunning ISRO AQI Monitoring System website.

---

## ✅ Prerequisites

Before starting, make sure you have:

1. **Python 3.8+**
   - Download from: https://www.python.org/downloads/
   - **Windows**: Check "Add Python to PATH" during installation
   - Verify: `python --version`

2. **Node.js 18+ with npm**
   - Download from: https://nodejs.org/
   - Choose "LTS" version
   - Verify: `node --version` and `npm --version`

3. **Git** (optional but recommended)
   - Download from: https://git-scm.com/

---

## 🎯 Option 1: Quick Start (Recommended for Windows Users)

### Single-Click Setup

#### For Windows (CMD):
1. Double-click **`START_WEBSITE.bat`** in the ISRO folder
2. Wait for both terminals to open
3. Visit `http://localhost:3000` in your browser

#### For Windows (PowerShell):
1. Right-click **`START_WEBSITE.ps1`**
2. Select "Run with PowerShell"
3. Wait for both terminals to open
4. Visit `http://localhost:3000` in your browser

#### For Linux/Mac:
```bash
chmod +x START_WEBSITE.sh
./START_WEBSITE.sh
```

---

## 🎯 Option 2: Manual Setup

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Troubleshooting:**
- If `pip` is not recognized, try `pip3` instead
- On Windows, you might need to use the full Python path: `C:\Python311\Scripts\pip install -r requirements.txt`

### Step 2: Start the Backend

```bash
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

### Step 3: Install Frontend Dependencies (New Terminal/Tab)

```bash
cd website
npm install
```

### Step 4: Start the Frontend

```bash
cd website
npm run dev
```

You should see:
```
▲ Next.js 14.0.0
- Local:        http://localhost:3000
```

---

## 🌐 Access the Website

Once both services are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (auto-generated Swagger)
- **Health Check**: http://localhost:8000/health

---

## 🔍 Verifying Everything Works

### Check Backend

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "operational",
  "timestamp": "2026-06-22T...",
  "model_loaded": true,
  "data_loaded": true
}
```

### Check Frontend

Open http://localhost:3000 in your browser. You should see:
- ISRO AQI Monitoring System dashboard
- Loading animation (first time)
- Interactive map of India
- Control panels on left and right
- Time slider at the bottom

---

## 📦 Project Structure

```
ISRO/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── __pycache__/       # Python cache (auto-created)
│
├── website/
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   └── components/    # React components
│   ├── public/            # Static assets
│   ├── node_modules/      # Dependencies (auto-created)
│   ├── .next/             # Build output (auto-created)
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── postcss.config.js
│
├── START_WEBSITE.bat      # Windows batch startup script
├── START_WEBSITE.ps1      # Windows PowerShell startup script
├── START_WEBSITE.sh       # Linux/Mac bash startup script
└── SETUP_GUIDE.md        # This file
```

---

## ⚙️ Configuration

### Backend Configuration

Edit `backend/app.py` to customize:

```python
# Paths to data and models
BASE_PATH = Path(r"C:\Users\Jayyanth\Desktop\ISRO")
OUTPUT_PATH = BASE_PATH / "output"
MODELS_PATH = OUTPUT_PATH / "models"
```

### Frontend Configuration

Create `website/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting

### "Port 8000 already in use"
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Kill the process or use a different port
python -m uvicorn app:app --port 8001
```

### "Port 3000 already in use"
```bash
npm run dev -- -p 3001
```

### "Python not found"
- Ensure Python is in PATH
- On Windows, add Python to PATH: `C:\Python311\;C:\Python311\Scripts\`
- Or use full path: `C:\Python311\python.exe -m uvicorn app:app --reload`

### "npm install fails"
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### "Backend connects but frontend doesn't load data"
1. Check browser console for errors (F12)
2. Verify backend is running: http://localhost:8000/health
3. Check CORS is enabled in `backend/app.py`
4. Try refreshing the page

### "Leaflet map doesn't appear"
This is normal in development. The map container should render but may need:
1. A browser refresh
2. Checking browser console for errors
3. Ensuring Leaflet CSS is loaded

---

## 🚀 Running in Production

### Build Frontend for Production

```bash
cd website
npm run build
npm start
```

### Run Backend with Gunicorn

```bash
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## 📱 Browser Compatibility

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## 🔗 API Endpoints Reference

```
GET  /health                    # System health
GET  /api/stations              # All monitoring stations
GET  /api/cities                # Cities with stations
GET  /api/predict               # Predict PM2.5/AQI
GET  /api/hotspots              # Top pollution hotspots
GET  /api/statistics            # National statistics
GET  /api/time-series           # Historical data
GET  /api/available-dates       # Available dates for slider
GET  /api/feature-importance    # Model feature importance
GET  /api/methodology           # Research methodology
GET  /api/model-performance     # Validation metrics
```

---

## 📚 Additional Resources

- **Next.js Docs**: https://nextjs.org/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Leaflet Documentation**: https://leafletjs.com/

---

## 💡 Tips

1. **Keep both terminals open** - The backend and frontend must both be running
2. **First load may be slow** - JavaScript compilation happens on first visit
3. **Development server auto-reloads** - Changes to code are reflected automatically
4. **Use browser DevTools** - Press F12 to debug issues
5. **Check Network tab** - Verify API calls are succeeding

---

## 🎉 You're All Set!

Your ISRO AQI Monitoring System is now ready to use!

Visit: **http://localhost:3000**

---

## 📞 Support

If you encounter issues:

1. Check this troubleshooting section
2. Review error messages in terminals
3. Check browser console (F12)
4. Verify all prerequisites are installed
5. Try restarting both services

---

**Made with ❤️ for ISRO Hackathon**
