"""
Spatial Grid Extraction for India-Wide PM2.5/AQI Map
========================================================

Builds a 0.25-degree grid covering India (~6,800 points) and extracts
satellite + ERA5 features for ONE target date, using the SAME
validated method as the station extraction:

    .mosaic() per day -> 10km buffer -> reduceRegions(mean)

KNOWN RISK, STATED EXPLICITLY:
  6,800 points is ~31x more than the 218-station extraction that took
  35-200+ seconds per date. A single reduceRegions() call across the
  full grid may be slow and carries a real risk of GEE computation
  timeout. This script defends against that by:

    1. CHUNKING the grid into batches (default 500 points/chunk) so
       one slow/failing chunk doesn't cost you the whole grid
    2. CHECKPOINTING after every chunk (same discipline validated on
       the station extraction earlier in this project)
    3. Defaulting to ONE single date, not a date range — combining
       fine grid + date range was explicitly rejected as too risky

If a chunk times out or fails, it is logged and skipped — you can
lower CHUNK_SIZE and re-run to pick up only the missing chunks.

BEFORE RUNNING:
  - Set TARGET_DATE to the date you want the map for
  - Confirm PROJECT_ID matches your registered GEE project
  - Run with a SMALL chunk count first (see TEST_MODE) before
    committing to the full ~6,800-point grid
"""

import ee
import pandas as pd
import numpy as np
import os
import time
import json
from datetime import datetime, timedelta

# =====================================================================
# CONFIG
# =====================================================================

PROJECT_ID = 'aqi-data-500013'

TARGET_DATE = '2020-01-15'   # pick a date with known-good coverage based on past testing

# India bounding box (approximate, slightly generous to ensure full coverage)
LAT_MIN, LAT_MAX = 8.0, 37.0
LON_MIN, LON_MAX = 68.0, 97.5
GRID_STEP = 0.25  # degrees -> ~6,800 points over this bounding box

BUFFER_METERS = 10000
SCALE_TROPOMI = 5000
SCALE_AOD = 1000
SCALE_ERA5 = 25000

AOD_SCALE_FACTOR = 0.001  # MAIAC raw band -> physical AOD units (see fix_aod_and_refit.py)

CHUNK_SIZE = 500   # points per reduceRegions() call -- the key defense against timeouts

OUTPUT_DIR = r"C:\Users\Jayyanth\Desktop\ISRO\output\grid"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, f"grid_extracted_{TARGET_DATE}.csv")
PROGRESS_LOG = os.path.join(OUTPUT_DIR, f"grid_progress_{TARGET_DATE}.txt")

# ---- TEST MODE ----
# Run a tiny slice first (one chunk, ~500 points) before committing to
# the full ~6,800-point grid. This costs a couple of minutes and tells
# you whether chunk size / timeout risk is actually manageable on your
# connection before you commit to 14 sequential chunks.
TEST_MODE = False
TEST_MAX_CHUNKS = 1

TROPOMI_DATASETS = {
    'NO2_sat':  ('COPERNICUS/S5P/OFFL/L3_NO2',  'tropospheric_NO2_column_number_density'),
    'SO2_sat':  ('COPERNICUS/S5P/OFFL/L3_SO2',  'SO2_column_number_density'),
    'CO_sat':   ('COPERNICUS/S5P/OFFL/L3_CO',   'CO_column_number_density'),
    'O3_sat':   ('COPERNICUS/S5P/OFFL/L3_O3',   'O3_column_number_density'),
    'HCHO_sat': ('COPERNICUS/S5P/OFFL/L3_HCHO', 'tropospheric_HCHO_column_number_density'),
}
AOD_DATASET = 'MODIS/061/MCD19A2_GRANULES'
AOD_BAND = 'Optical_Depth_047'
ERA5_RAW_BANDS = ['temperature_2m', 'dewpoint_temperature_2m',
                   'u_component_of_wind_10m', 'v_component_of_wind_10m',
                   'boundary_layer_height']

# =====================================================================
# INITIALIZATION
# =====================================================================

print("Initializing Earth Engine...")
ee.Initialize(project=PROJECT_ID)
print("Earth Engine ready.\n")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================================
# BUILD THE GRID
# =====================================================================

lats = np.arange(LAT_MIN, LAT_MAX + GRID_STEP, GRID_STEP)
lons = np.arange(LON_MIN, LON_MAX + GRID_STEP, GRID_STEP)

grid_points = []
point_id = 0
for lat in lats:
    for lon in lons:
        grid_points.append({'point_id': point_id, 'Latitude': round(lat, 4), 'Longitude': round(lon, 4)})
        point_id += 1

grid_df = pd.DataFrame(grid_points)
print(f"Grid built: {len(grid_df)} points "
      f"({len(lats)} lat steps x {len(lons)} lon steps, {GRID_STEP} degree spacing)")

# Split into chunks
n_chunks = int(np.ceil(len(grid_df) / CHUNK_SIZE))
chunks = [grid_df.iloc[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE] for i in range(n_chunks)]
print(f"Split into {n_chunks} chunks of up to {CHUNK_SIZE} points each.\n")

if TEST_MODE:
    print("=" * 60)
    print(f"TEST MODE: only processing the first {TEST_MAX_CHUNKS} chunk(s).")
    print("Set TEST_MODE = False once you've confirmed this works.")
    print("=" * 60 + "\n")
    chunks = chunks[:TEST_MAX_CHUNKS]

# =====================================================================
# RESUME LOGIC — per chunk, not per point
# =====================================================================

completed_chunks = set()
if os.path.exists(PROGRESS_LOG):
    with open(PROGRESS_LOG, 'r') as f:
        completed_chunks = set(int(line.strip()) for line in f if line.strip())
    print(f"Found existing progress: {len(completed_chunks)} chunks already done.")

# =====================================================================
# EXTRACTION FUNCTIONS — same validated method as station extraction
# =====================================================================

def build_chunk_fc(chunk_df):
    features = []
    for _, row in chunk_df.iterrows():
        geom = ee.Geometry.Point([row['Longitude'], row['Latitude']]).buffer(BUFFER_METERS)
        feat = ee.Feature(geom, {
            'point_id': int(row['point_id']),
            'Latitude': row['Latitude'],
            'Longitude': row['Longitude']
        })
        features.append(feat)
    return ee.FeatureCollection(features)


def extract_tropomi_chunk(chunk_fc, dataset_id, band, date_str):
    end_str = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    image = ee.ImageCollection(dataset_id).filterDate(date_str, end_str).select(band).mosaic()
    reduced = image.reduceRegions(collection=chunk_fc, reducer=ee.Reducer.mean(), scale=SCALE_TROPOMI)
    return reduced.getInfo()['features']


def extract_aod_chunk(chunk_fc, date_str):
    """
    Applies the AOD scale factor (0.001) INSIDE the Earth Engine
    computation, before reduceRegions. This matches the correction
    applied to the training data in fix_aod_and_refit.py -- the model
    expects AOD in real physical units, not raw MAIAC band values.
    """
    end_str = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    image = (ee.ImageCollection(AOD_DATASET).filterDate(date_str, end_str)
              .select(AOD_BAND).mosaic()
              .multiply(AOD_SCALE_FACTOR))  # raw MAIAC band -> physical AOD units
    reduced = image.reduceRegions(collection=chunk_fc, reducer=ee.Reducer.mean(), scale=SCALE_AOD)
    return reduced.getInfo()['features']


def extract_era5_chunk(chunk_fc, date_str):
    end_str = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    image = ee.ImageCollection("ECMWF/ERA5/HOURLY").filterDate(date_str, end_str).select(ERA5_RAW_BANDS).mean()

    t = image.select('temperature_2m').subtract(273.15)
    td = image.select('dewpoint_temperature_2m').subtract(273.15)
    rh = image.expression('100 * (exp((17.625*td)/(243.04+td)) / exp((17.625*t)/(243.04+t)))',
                            {'t': t, 'td': td}).rename('relative_humidity_2m')
    wind_speed = image.expression('sqrt(u*u + v*v)',
                                    {'u': image.select('u_component_of_wind_10m'),
                                     'v': image.select('v_component_of_wind_10m')}).rename('wind_speed')
    full_image = image.addBands(rh).addBands(wind_speed)

    reduced = full_image.reduceRegions(collection=chunk_fc, reducer=ee.Reducer.mean(), scale=SCALE_ERA5)
    return reduced.getInfo()['features']


# =====================================================================
# MAIN LOOP — one chunk at a time, checkpointed
# =====================================================================

print(f"Starting grid extraction for {TARGET_DATE}.")
print("Progress is saved after every chunk. Safe to stop and re-run.\n")

file_exists = os.path.exists(OUTPUT_CSV)

for chunk_idx, chunk_df in enumerate(chunks):
    if chunk_idx in completed_chunks:
        continue

    print(f"[Chunk {chunk_idx+1}/{len(chunks)}] {len(chunk_df)} points...")
    t0 = time.time()

    try:
        chunk_fc = build_chunk_fc(chunk_df)
        rows = {int(r['point_id']): {'point_id': int(r['point_id']),
                                       'Latitude': r['Latitude'],
                                       'Longitude': r['Longitude'],
                                       'Date': TARGET_DATE}
                for _, r in chunk_df.iterrows()}

        for col_name, (dataset_id, band) in TROPOMI_DATASETS.items():
            feats = extract_tropomi_chunk(chunk_fc, dataset_id, band, TARGET_DATE)
            for f in feats:
                pid = f['properties']['point_id']
                rows[pid][col_name] = f['properties'].get('mean')

        feats = extract_aod_chunk(chunk_fc, TARGET_DATE)
        for f in feats:
            pid = f['properties']['point_id']
            rows[pid]['AOD'] = f['properties'].get('mean')

        feats = extract_era5_chunk(chunk_fc, TARGET_DATE)
        for f in feats:
            pid = f['properties']['point_id']
            props = f['properties']
            rows[pid]['temperature_K'] = props.get('temperature_2m')
            rows[pid]['relative_humidity'] = props.get('relative_humidity_2m')
            rows[pid]['BLH'] = props.get('boundary_layer_height')
            rows[pid]['wind_speed'] = props.get('wind_speed')

        df_chunk = pd.DataFrame(rows.values())
        df_chunk.to_csv(OUTPUT_CSV, mode='a', header=not file_exists, index=False)
        file_exists = True

        with open(PROGRESS_LOG, 'a') as f:
            f.write(str(chunk_idx) + "\n")

        elapsed = time.time() - t0
        n_valid = df_chunk['AOD'].notna().sum() if 'AOD' in df_chunk else 0
        print(f"    Done in {elapsed:.1f}s ({n_valid}/{len(df_chunk)} points had valid AOD)")

    except Exception as e:
        print(f"    FAILED: {e}")
        print(f"    Chunk {chunk_idx} will be retried on next run (not marked complete).")
        print(f"    If this keeps failing, lower CHUNK_SIZE and re-run.")
        time.sleep(5)
        continue

print("\nGrid extraction run finished (completed or interrupted).")
print(f"Results: {OUTPUT_CSV}")
print(f"Progress log: {PROGRESS_LOG}")

if TEST_MODE:
    print("\n" + "=" * 60)
    print("TEST MODE CHECKLIST:")
    print("1. Did the single test chunk complete without timing out?")
    print("2. Check the output CSV - does it have ~500 rows with sane values?")
    print("3. If yes: set TEST_MODE = False and run the full grid.")
    print("4. If the chunk was slow or failed, lower CHUNK_SIZE (try 200)")
    print("   and re-test before running the full grid.")
    print("=" * 60)