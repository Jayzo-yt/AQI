# ISRO AQI Monitoring System - Website

A stunning, fully functional web application for AI-Based Nationwide Surface PM2.5 and AQI Mapping using Satellite Observations and Meteorological Data.

## 🌍 Features

- **Interactive Dark-Mode Dashboard** - Premium Earth observation platform aesthetic
- **Real-Time AQI Mapping** - Dynamic heatmaps with satellite data overlay
- **Time Series Control** - Animated playback through historical dates
- **Location Analysis** - Click any location for detailed predictions with explainability
- **Pollution Hotspot Detection** - Automatic ranking of most polluted regions
- **National Statistics** - Live AQI distribution and air quality metrics
- **Feature Importance** - SHAP-style explainability for predictions
- **Responsive Design** - Optimized for modern web browsers

## 🛠 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **XGBoost** - Machine learning model serving
- **Pandas & NumPy** - Data processing
- **Uvicorn** - ASGI server

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Leaflet + React Leaflet** - Interactive mapping
- **Framer Motion** - Smooth animations
- **Recharts** - Data visualization

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

## 🚀 Quick Start

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

Health check: `http://localhost:8000/health`

### 3. Install Frontend Dependencies

```bash
cd website
npm install
# or
yarn install
```

### 4. Start the Frontend Development Server

```bash
cd website
npm run dev
# or
yarn dev
```

The website will be available at: `http://localhost:3000`

## 📁 Project Structure

```
ISRO/
├── backend/
│   ├── app.py                 # FastAPI application
│   └── requirements.txt       # Python dependencies
│
└── website/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx      # Main dashboard
    │   │   ├── layout.tsx    # Root layout
    │   │   ├── globals.css   # Global styles
    │   │   └── providers.tsx # React providers
    │   │
    │   └── components/
    │       ├── TopNavigation.tsx
    │       ├── InteractiveMap.tsx
    │       ├── LeftControlPanel.tsx
    │       ├── RightAnalyticsPanel.tsx
    │       ├── TimeSlider.tsx
    │       ├── LocationAnalysisPanel.tsx
    │       ├── BottomInsightsPanel.tsx
    │       └── LoadingScreen.tsx
    │
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── postcss.config.js
    └── next.config.ts
```

## 🔌 API Endpoints

### Health & Status
- `GET /health` - System health check

### Data Endpoints
- `GET /api/stations` - Get all CPCB monitoring stations
- `GET /api/cities` - Get list of cities with stations
- `GET /api/available-dates` - Get available dates for timeline

### Predictions & Analysis
- `GET /api/predict?latitude={lat}&longitude={lng}` - Get PM2.5/AQI prediction
- `GET /api/hotspots?date={date}&top_n=10` - Get top polluted regions
- `GET /api/statistics` - Get national statistics
- `GET /api/time-series?city={city}&days=30` - Get time series data
- `GET /api/feature-importance` - Get model feature importance

### Documentation
- `GET /api/methodology` - Research methodology
- `GET /api/model-performance` - Model validation metrics

## 🎨 Design Features

### Dark Theme
- Background: `#0A0A0A` (near-black)
- Panels: `#111111` (dark gray)
- Borders: `#222222` (subtle gray)
- Text: White and light gray

### Layout
1. **Top Navigation Bar** - Project title and controls
2. **Left Control Panel** - City search and layer controls
3. **Central Interactive Map** - 70% of screen space
4. **Right Analytics Panel** - Live statistics and metrics
5. **Bottom Insights Panel** - Hotspot carousel
6. **Time Slider** - Animated date control overlay

## 🔧 Configuration

### Backend Configuration
Edit `backend/app.py` to configure:
- Model path: `MODELS_PATH`
- Data path: `DATA_PATH`
- API host/port

### Frontend Configuration
Edit `website/.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 📊 Data Integration

The system uses:
- **Satellite Data**: MODIS AOD, Sentinel-5P (NO2, SO2, CO, O3, HCHO)
- **Meteorological Data**: ERA5 reanalysis (temperature, humidity, wind, BLH)
- **Ground Truth**: CPCB monitoring stations
- **Model**: XGBoost PM2.5 predictor

## 🚢 Deployment

### Production Build

Frontend:
```bash
cd website
npm run build
npm start
```

Backend:
```bash
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker (Optional)

Backend Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/app.py .
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Frontend Dockerfile:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY website .
RUN npm install && npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 📝 Notes

- The website fetches live data from the FastAPI backend
- Predictions are simulated in demo mode; integrate with actual model predictions
- Station data is loaded from `merged_with_coordinates.csv`
- Historical data comes from `final_dataset_v3.csv`

## 🎯 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🤝 Team

ISRO Hackathon Project  
AI-Based Nationwide Surface PM2.5 and AQI Mapping

## 📄 License

© 2026 ISRO Hackathon Project. All rights reserved.
