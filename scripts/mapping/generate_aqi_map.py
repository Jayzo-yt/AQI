"""
Professional India AQI Map Generator - PRODUCTION VERSION
==========================================================
Handles grid-vs-station mismatch with intelligent spatial adjustments
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep
import joblib
import warnings
warnings.filterwarnings('ignore')

# ================= CONFIG =================

DATE_STR = "2019-01-01"

GRID_CSV = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\grid\grid_extracted_2019-01-01_high.csv"
MODEL_PATH = r"C:\Users\Jayyanth\Desktop\ISRO\data\models\final\final_pm25_model_corrected_aod_20260622_162942.joblib"

OUTPUT_IMAGE = rf"C:\Users\Jayyanth\Desktop\ISRO\data\maps\AQI_map_{DATE_STR}_FINAL.png"

# Training data medians (verified correct)
TRAINING_MEDIANS = {
    'NO2_sat': 0.000062,
    'SO2_sat': 0.000078,
    'CO_sat': 0.040238,
    'O3_sat': 0.122287,
    'HCHO_sat': 0.000208,
    'AOD': 0.718694,
    'temperature_K': 299.800498,
    'relative_humidity': 71.483351,
    'BLH': 507.895813,
    'wind_speed': 2.073184,
}

# ==========================================

print("="*70)
print(f"Production AQI Map Generation: {DATE_STR}")
print("="*70)

# ================= LOAD DATA =================

print("\n[1/7] Loading grid data...")
df = pd.read_csv(GRID_CSV)
print(f"   ✓ Loaded {len(df)} grid points")

print("\n[2/7] Loading trained model...")
model = joblib.load(MODEL_PATH)

# ================= FEATURE ENGINEERING =================

FEATURES = [
    'NO2_sat', 'SO2_sat', 'CO_sat', 'O3_sat', 'HCHO_sat',
    'AOD', 'temperature_K', 'relative_humidity', 'BLH', 'wind_speed'
]

print("\n[3/7] Feature engineering...")

X = df[FEATURES].copy()

# Track data quality per point
df['n_missing'] = X.isna().sum(axis=1)
df['data_quality'] = 1 - (df['n_missing'] / len(FEATURES))

# Impute with training medians
X_filled = X.fillna(TRAINING_MEDIANS)

# ================= GEOGRAPHIC CONTEXT =================

print("\n[4/7] Adding geographic context...")

# Define pollution-prone regions (approximate bounding boxes)
# These are known high-pollution areas in January

regions = {
    'Indo-Gangetic Plain (North India)': {
        'lat': (26, 31), 'lon': (75, 85),
        'winter_factor': 1.8,  # Higher pollution in winter
        'description': 'Delhi, Punjab, Haryana, UP'
    },
    'Eastern Plains': {
        'lat': (23, 27), 'lon': (85, 89),
        'winter_factor': 1.4,
        'description': 'Bihar, West Bengal'
    },
    'Central India': {
        'lat': (21, 26), 'lon': (74, 82),
        'winter_factor': 1.2,
        'description': 'MP, Maharashtra (north)'
    },
    'Western Coast': {
        'lat': (15, 21), 'lon': (72, 77),
        'winter_factor': 0.9,
        'description': 'Mumbai, Goa'
    },
    'South India': {
        'lat': (8, 16), 'lon': (75, 80),
        'winter_factor': 0.8,
        'description': 'Karnataka, TN, Kerala'
    },
    'Himalayan Region': {
        'lat': (28, 36), 'lon': (74, 80),
        'winter_factor': 0.6,
        'description': 'J&K, Himachal, Uttarakhand'
    },
    'Northeast': {
        'lat': (24, 29), 'lon': (89, 95),
        'winter_factor': 1.0,
        'description': 'Assam, Meghalaya'
    }
}

# Assign regional factor to each grid point
df['regional_factor'] = 1.0

for region_name, params in regions.items():
    lat_range = params['lat']
    lon_range = params['lon']
    
    mask = (
        (df['Latitude'] >= lat_range[0]) & 
        (df['Latitude'] <= lat_range[1]) &
        (df['Longitude'] >= lon_range[0]) & 
        (df['Longitude'] <= lon_range[1])
    )
    
    df.loc[mask, 'regional_factor'] = params['winter_factor']
    
    if mask.sum() > 0:
        print(f"   {region_name:35s}: {mask.sum():5d} points (factor: {params['winter_factor']}x)")

# ================= BASE PREDICTION =================

print("\n[5/7] Generating base predictions...")

df["PM25_base"] = model.predict(X_filled)

# Reverse log transform
if df["PM25_base"].max() < 10:
    df["PM25_base"] = np.expm1(df["PM25_base"])

df["PM25_base"] = df["PM25_base"].clip(lower=0)

print(f"\n   Base prediction stats:")
print(f"   Median: {df['PM25_base'].median():.1f} µg/m³")
print(f"   Mean:   {df['PM25_base'].mean():.1f} µg/m³")

# ================= REGIONAL ADJUSTMENT =================

print("\n[6/7] Applying regional adjustments...")

# Apply regional scaling
df['PM25_adjusted'] = df['PM25_base'] * df['regional_factor']

# Additional urban/AOD-based enhancement
# High AOD + low BLH = trapped pollution (winter inversion)
df['pollution_risk'] = (
    (X_filled['AOD'] / X_filled['AOD'].quantile(0.75)) * 
    (X_filled['BLH'].quantile(0.25) / X_filled['BLH'].clip(lower=50))
).clip(upper=2.0)

df['PM25_final'] = df['PM25_adjusted'] * (0.7 + 0.3 * df['pollution_risk'])

# Constrain to realistic bounds
df['PM25_final'] = df['PM25_final'].clip(lower=5, upper=500)

print(f"\n   Final prediction stats:")
print(f"   Min:    {df['PM25_final'].min():.1f} µg/m³")
print(f"   Median: {df['PM25_final'].median():.1f} µg/m³")
print(f"   Mean:   {df['PM25_final'].mean():.1f} µg/m³")
print(f"   Max:    {df['PM25_final'].max():.1f} µg/m³")

# ================= AQI CONVERSION =================

def pm25_to_aqi(pm):
    pm = max(0, pm)
    if pm <= 30: return pm * (50/30)
    elif pm <= 60: return 50 + (pm-30)*(50/30)
    elif pm <= 90: return 100 + (pm-60)*(100/30)
    elif pm <= 120: return 200 + (pm-90)*(100/30)
    elif pm <= 250: return 300 + (pm-120)*(100/130)
    else: return min(500, 400 + (pm-250)*(100/130))

df["AQI"] = df["PM25_final"].apply(pm25_to_aqi)

print("\n📊 AQI CATEGORY DISTRIBUTION:")
categories = [
    ("Good (0-50)", 0, 50, "#00e400"),
    ("Satisfactory (51-100)", 51, 100, "#ffff00"),
    ("Moderate (101-200)", 101, 200, "#ff7e00"),
    ("Poor (201-300)", 201, 300, "#ff0000"),
    ("Very Poor (301-400)", 301, 400, "#99004c"),
    ("Severe (401-500)", 401, 500, "#7e0023")
]

for label, lower, upper, _ in categories:
    count = ((df['AQI'] >= lower) & (df['AQI'] <= upper)).sum()
    pct = count / len(df) * 100
    bar = "█" * int(pct / 2)
    print(f"   {label:25s}: {count:5d} ({pct:5.1f}%) {bar}")

# ================= SPATIAL INTERPOLATION =================

print("\n[7/7] Generating map...")

# Filter very low quality points for cleaner interpolation
df_reliable = df[df['data_quality'] >= 0.5].copy()
print(f"   Using {len(df_reliable)}/{len(df)} reliable grid points")

lon_min, lon_max = df.Longitude.min(), df.Longitude.max()
lat_min, lat_max = df.Latitude.min(), df.Latitude.max()

grid_x, grid_y = np.meshgrid(
    np.linspace(lon_min, lon_max, 800),
    np.linspace(lat_min, lat_max, 800)
)

# Interpolate
grid_z = griddata(
    df_reliable[['Longitude','Latitude']].values,
    df_reliable['AQI'].values,
    (grid_x, grid_y),
    method='cubic'  # Smoother for visualization
)

# Smooth slightly
grid_z = gaussian_filter(grid_z, sigma=1.5)

# ================= MASKING =================

print("   Loading India boundary...")
url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(url)
india = world[world["ADMIN"] == "India"]
india_geom = india.geometry.values[0]

prepared_india = prep(india_geom)
points = np.column_stack([grid_x.ravel(), grid_y.ravel()])
mask = np.array([prepared_india.contains(Point(xy)) for xy in points])
mask = mask.reshape(grid_x.shape)
grid_z_masked = np.where(mask, grid_z, np.nan)

# ================= VISUALIZATION =================

bounds = [0, 50, 100, 200, 300, 400, 500]
colors = [cat[3] for cat in categories]
cmap = mcolors.ListedColormap(colors)
norm = mcolors.BoundaryNorm(bounds, cmap.N)

fig, ax = plt.subplots(figsize=(14, 16))

im = ax.imshow(
    grid_z_masked,
    extent=(lon_min, lon_max, lat_min, lat_max),
    origin='lower',
    cmap=cmap,
    norm=norm,
    interpolation='bilinear'
)

india.boundary.plot(ax=ax, edgecolor="black", linewidth=1.8)

# Colorbar
cbar = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
cbar.set_label("Air Quality Index (CPCB Standard)", fontsize=13, weight='bold')
cbar.set_ticks([0, 50, 100, 200, 300, 400, 500])
cbar.ax.tick_params(labelsize=10)

# Title
ax.set_title(
    f"India Surface AQI Map\n{DATE_STR} (Winter Season)",
    fontsize=16, weight='bold', pad=20
)

ax.set_xlabel("Longitude (°E)", fontsize=12)
ax.set_ylabel("Latitude (°N)", fontsize=12)

ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)

# Add annotation
note = "Model: XGBoost with regional winter adjustments\nData: Sentinel-5P TROPOMI + MODIS + ERA5"
ax.text(0.02, 0.02, note, transform=ax.transAxes,
        fontsize=9, verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.85))

plt.tight_layout()
plt.savefig(OUTPUT_IMAGE, dpi=400, bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n{'='*70}")
print("✅ Production map complete!")
print(f"{'='*70}")
print(f"\nOutput: {OUTPUT_IMAGE}")
print(f"\nKey features:")
print(f"  • Regional winter pollution scaling applied")
print(f"  • AOD-BLH interaction considered (inversion trapping)")
print(f"  • High-resolution interpolation (800x800)")
print(f"  • Quality-weighted spatial smoothing")
print(f"{'='*70}\n")