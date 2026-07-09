# ISRO Hackathon Final Showcase Website — Master Design & Development Prompt

Build a modern, premium, research-grade web application for an ISRO hackathon project titled:

**"AI-Based Nationwide Surface PM2.5 and AQI Mapping Using Satellite Observations and Meteorological Data"**

The website must feel like a professional Earth Observation platform rather than a student project. The design philosophy should be inspired by NASA EarthData, Google Earth Engine, Sentinel Hub, Windy, and modern scientific dashboards.

The overall theme must be **minimalist black-and-white**, with a premium dark aesthetic. The interface should look clean, futuristic, and highly polished. Avoid bright colors in the UI itself. The only vivid colors should appear inside the AQI visualization layers.

---

## DESIGN LANGUAGE

### Theme

* Pure dark mode.
* Background: near-black (#0A0A0A).
* Secondary panels: dark gray (#111111).
* Borders: subtle gray (#222222).
* Text: white and light gray.
* Accent color: white only.
* No unnecessary gradients.
* No flashy animations.
* Professional scientific appearance.

### Visual Feel

The user should immediately feel that they are using an operational satellite monitoring platform.

The interface should communicate:

* Precision
* Scientific credibility
* National-scale monitoring
* AI-powered analytics
* Earth observation technology

---

# APPLICATION STRUCTURE

The application should be a single-page dashboard with multiple expandable modules.

Layout:

1. Top Navigation Bar
2. Left Control Panel
3. Central Interactive Map
4. Right Analytics Panel
5. Bottom Insights Panel

The map should occupy approximately 70% of screen space.

---

# LANDING SECTION

Display:

Project Title:

AI-Powered Surface AQI Monitoring System for India

Subtitle:

Nationwide PM2.5 Estimation Using Satellite Observations, Meteorological Reanalysis Data, and Machine Learning

Display:

* ISRO Hackathon Logo Area
* PSG College Area
* Team Information Area

Include a professional loading animation:

"Initializing Earth Observation System..."

before dashboard loads.

---

# MAIN INTERACTIVE MAP

This is the core component.

Use:

* Leaflet
* Folium
* Geemap
* MapLibre
* CartoDB Dark Matter Basemap

Preferred:

Dark basemap with black oceans and dark landmass.

The map should support:

* Zoom
* Pan
* Fullscreen
* Layer switching
* Time updates
* Dynamic overlays

Default view:

India-centered.

---

# AQI HEATMAP LAYER

Primary layer:

Predicted AQI Surface.

Display:

* CPCB AQI color scale
* Smooth interpolation
* Dynamic transparency slider

User should be able to adjust:

0% to 100% opacity.

---

# TIME SLIDER

One of the most important features.

Provide a timeline control.

User can move through dates.

Examples:

2019-01-01

2019-06-01

2020-01-15

2020-12-31

When date changes:

* Map updates
* AQI updates
* Statistics update
* Hotspots update

Include play button.

Allow automatic animation through dates.

This instantly makes the project feel operational.

---

# LOCATION CLICK ANALYSIS

When user clicks any point on India:

Open a side panel displaying:

Latitude

Longitude

Predicted PM2.5

Predicted AQI

AQI Category

Good

Satisfactory

Moderate

Poor

Very Poor

Severe

Display large AQI badge.

---

# EXPLAINABLE AI MODULE

Very important.

When user clicks a location:

Show why the model predicted that AQI.

Display feature contributions.

Possible features:

AOD

NO2

SO2

CO

O3

HCHO

Temperature

Humidity

Boundary Layer Height

Wind Speed

Use:

SHAP values

or

Feature importance decomposition.

Show:

Top factors increasing pollution.

Top factors reducing pollution.

This creates trust in the AI system.

---

# POLLUTION HOTSPOT DETECTOR

Automatic ranking system.

Display:

Top 10 most polluted regions in India.

For each hotspot show:

Rank

State

Latitude

Longitude

AQI

PM2.5

Update dynamically based on selected date.

---

# AQI CATEGORY DISTRIBUTION

Display a live chart.

Show:

Percentage of India in:

Good

Satisfactory

Moderate

Poor

Very Poor

Severe

Use donut chart.

Dark theme.

Smooth animations.

---

# NATIONAL SUMMARY PANEL

Display live statistics.

Cards:

Average AQI

Maximum AQI

Minimum AQI

Most Polluted Region

Cleanest Region

Average PM2.5

Total Grid Points

Last Update Time

---

# CITY SEARCH

Search bar.

User types:

Delhi

Mumbai

Chennai

Kolkata

Bengaluru

Hyderabad

Ahmedabad

Patna

Lucknow

The map automatically zooms.

Display local prediction.

---

# HISTORICAL TREND ANALYSIS

When a city is selected:

Show time-series graph.

Display:

PM2.5 Trend

AQI Trend

Date vs Value

Allow comparison between cities.

---

# SATELLITE DATA LAYER CONTROL

Enable toggling of:

AOD Layer

NO2 Layer

SO2 Layer

CO Layer

O3 Layer

Temperature Layer

Humidity Layer

Wind Layer

Boundary Layer Height Layer

AQI Layer

Only one or multiple layers can be active.

---

# MODEL PERFORMANCE SECTION

Dedicated tab.

Display:

Training Results

RMSE

MAE

Correlation Coefficient

Station-Holdout Validation

Random Split Validation

Feature Importance Ranking

Confusion-style performance visualizations.

Demonstrate scientific rigor.

---

# RESEARCH METHODOLOGY PAGE

Show complete pipeline.

Visual workflow:

Satellite Data

↓

Preprocessing

↓

Feature Engineering

↓

ERA5 Integration

↓

Machine Learning

↓

AQI Estimation

↓

Interactive Mapping

Use modern flowchart design.

---

# INDIA AIR QUALITY STORYBOARD

Create narrative insights.

Examples:

Northern India experiences severe winter pollution due to atmospheric stagnation.

Southern India generally exhibits lower PM2.5 concentrations.

Indo-Gangetic Plain remains the dominant hotspot.

Automatically generate observations.

---

# EXPORT FUNCTIONS

Allow export:

PNG

CSV

GeoJSON

Predicted AQI grids

Downloaded reports should be professionally formatted.

---

# COMPARISON MODE

Allow comparison between:

Date A

Date B

Display split-screen maps.

Useful for seasonal analysis.

---

# ANIMATION MODE

Generate animated playback.

Observe pollution evolution over time.

Play controls:

Play

Pause

Speed

Loop

---

# PERFORMANCE REQUIREMENTS

Map loading:

< 2 seconds

Interaction:

Real-time

Charts:

Instant update

Smooth transitions

Responsive UI

---

# TECHNOLOGY STACK

Frontend:

Next.js

React

TypeScript

TailwindCSS

shadcn/ui

Framer Motion

Backend:

FastAPI

Python

Machine Learning:

XGBoost

Joblib

Geo Processing:

Geopandas

Rasterio

Folium

Leaflet

Geemap

Visualization:

Plotly

ECharts

MapLibre

Deck.gl

---

# JUDGE WOW FACTORS

The final system should make judges feel:

"This is not just a machine learning model."

"This looks like a deployable national air-quality monitoring platform."

"This could realistically support environmental agencies."

The map must remain the hero component of the application, occupying the majority of screen space and delivering a premium dark-mode Earth-observation experience with scientific credibility, explainability, temporal analysis, hotspot detection, and operational decision-support capabilities.
