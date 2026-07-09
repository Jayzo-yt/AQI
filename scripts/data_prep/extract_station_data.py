"""
Satellite + ERA5 Extraction Pipeline — FULLY VALIDATED VERSION
================================================================

This script merges three independently tested and confirmed fixes:

1. TROPOMI (NO2, SO2, CO, O3, HCHO):
   - Use .mosaic() across the day's swaths (NOT .first() — single swaths
     often don't cover your station at all, confirmed by testing)
   - Use reduceRegions() with a mean reducer (NOT sampleRegions() — that
     returns multiple raw pixels per station-buffer, silently corrupting
     your data with overwrite/duplication bugs, confirmed by testing)
   - No QA filter — 'qa_value' is not a valid band/property on this
     specific GEE collection (confirmed: caused a silent zero-band image
     and a hard crash when filtered as a property)

2. AOD (MODIS):
   - Same .mosaic() + reduceRegions(mean) pattern as TROPOMI

3. ERA5 (meteorology):
   - 'relative_humidity_2m' does NOT exist as a band in ECMWF/ERA5/HOURLY
     (confirmed via band listing) — RH is DERIVED from temperature_2m and
     dewpoint_temperature_2m using the Magnus formula
   - 'boundary_layer_height' DOES exist and works correctly
   - Wind speed derived from u/v components
   - Same reduceRegions(mean) pattern

VALIDATED TEST RESULT (2019-01-10, Delhi, single station):
  NO2 (reduceRegion):  0.0001262295342326478
  NO2 (reduceRegions): 0.0001262295342326478   <- matches exactly
  ERA5: temp=285.86K, dewpoint=280.15K, RH=68.2%, BLH=241.7m, wind=0.86 m/s
  All values physically plausible for winter Delhi (low BLH + low wind +
  high RH = the classic stagnant-air pollution-trapping pattern)

CHECKPOINTING:
  Progress is saved after EVERY date (both the output CSV row and a
  progress log entry). Safe to stop (Ctrl+C) and re-run — it will skip
  completed dates and continue, NOT restart from scratch.

BEFORE RUNNING AT FULL SCALE:
  Run this on a 5-day range first (see TEST MODE below). Check the
  output CSV has exactly one row per station per date, with believable
  values, before committing to the full multi-year run.
"""

import ee
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# =====================================================================
# ======================== CONFIGURATION ==============================
# =====================================================================

PROJECT_ID = 'aqi-data-500013'

STATIONS_CSV = r'C:\Users\Jayyanth\Desktop\ISRO\data\processed\merged_with_coordinates.csv'
LAT_COL = 'Latitude'
LON_COL = 'Longitude'
ID_COL = 'StationId'

# ---- TEST MODE ----
# Set TEST_MODE = True first and confirm everything works on a small
# range before switching to False and running the full date range.
TEST_MODE = False

if TEST_MODE:
    START_DATE = '2019-01-10'
    END_DATE = '2019-01-14'
    OUTPUT_CSV = r'C:\Users\Jayyanth\Desktop\ISRO\output\TEST_satellite_era5_extracted.csv'
    PROGRESS_LOG = r'C:\Users\Jayyanth\Desktop\ISRO\output\TEST_extraction_progress.txt'
else:
    START_DATE = '2020-01-01'
    END_DATE = '2020-12-31'
    OUTPUT_CSV = r'C:\Users\Jayyanth\Desktop\ISRO\output\satellite_era5_extracted_2020.csv'
    PROGRESS_LOG = r'C:\Users\Jayyanth\Desktop\ISRO\output\extraction_progress_2020.txt'

BUFFER_METERS = 10000
SCALE_TROPOMI = 5000
SCALE_AOD = 1000
SCALE_ERA5 = 25000

# =====================================================================
# ======================= DATASET DEFINITIONS ==========================
# =====================================================================

TROPOMI_DATASETS = {
    'NO2_sat':  ('COPERNICUS/S5P/OFFL/L3_NO2',  'tropospheric_NO2_column_number_density'),
    'SO2_sat':  ('COPERNICUS/S5P/OFFL/L3_SO2',  'SO2_column_number_density'),
    'CO_sat':   ('COPERNICUS/S5P/OFFL/L3_CO',   'CO_column_number_density'),
    'O3_sat':   ('COPERNICUS/S5P/OFFL/L3_O3',   'O3_column_number_density'),
    'HCHO_sat': ('COPERNICUS/S5P/OFFL/L3_HCHO', 'tropospheric_HCHO_column_number_density'),
}

AOD_DATASET = 'MODIS/061/MCD19A2_GRANULES'
AOD_BAND = 'Optical_Depth_047'

ERA5_RAW_BANDS = [
    'temperature_2m',
    'dewpoint_temperature_2m',
    'u_component_of_wind_10m',
    'v_component_of_wind_10m',
    'boundary_layer_height'
]

# =====================================================================
# ========================= INITIALIZATION =============================
# =====================================================================

print("Initializing Earth Engine...")
ee.Initialize(project=PROJECT_ID)
print("Earth Engine ready.\n")

if TEST_MODE:
    print("=" * 60)
    print("RUNNING IN TEST MODE — 5 day range, separate output files")
    print("Set TEST_MODE = False once you've verified this works.")
    print("=" * 60 + "\n")

stations = pd.read_csv(STATIONS_CSV)
stations = stations.dropna(subset=[LAT_COL, LON_COL])
print(f"Loaded {len(stations)} stations.\n")


def build_station_fc():
    features = []
    for _, row in stations.iterrows():
        geom = ee.Geometry.Point([row[LON_COL], row[LAT_COL]]).buffer(BUFFER_METERS)
        feat = ee.Feature(geom, {
            'StationId': row[ID_COL],
            'Latitude': row[LAT_COL],
            'Longitude': row[LON_COL]
        })
        features.append(feat)
    return ee.FeatureCollection(features)

station_fc = build_station_fc()

start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")
all_dates = []
d = start_dt
while d <= end_dt:
    all_dates.append(d.strftime("%Y-%m-%d"))
    d += timedelta(days=1)

completed_dates = set()
if os.path.exists(PROGRESS_LOG):
    with open(PROGRESS_LOG, 'r') as f:
        completed_dates = set(line.strip() for line in f if line.strip())

remaining_dates = [d for d in all_dates if d not in completed_dates]

print(f"Total dates: {len(all_dates)}")
print(f"Already completed: {len(completed_dates)}")
print(f"Remaining: {len(remaining_dates)}\n")

if len(remaining_dates) == 0:
    print("All dates already processed for this mode. Nothing to do.")
    print(f"Check {OUTPUT_CSV} for results, or delete {PROGRESS_LOG} to redo.")
    exit()

# =====================================================================
# ====================== EXTRACTION FUNCTIONS ==========================
# =====================================================================

def extract_tropomi(date_str, dataset_id, band):
    """Validated: .mosaic() + reduceRegions(mean). No QA filter (band doesn't exist)."""
    end_str = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    collection = (
        ee.ImageCollection(dataset_id)
        .filterDate(date_str, end_str)
        .select(band)
    )
    image = collection.mosaic()
    reduced = image.reduceRegions(
        collection=station_fc,
        reducer=ee.Reducer.mean(),
        scale=SCALE_TROPOMI
    )
    return reduced.getInfo()['features']


def extract_aod(date_str):
    """Validated pattern: .mosaic() + reduceRegions(mean), same as TROPOMI."""
    end_str = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    image = (
        ee.ImageCollection(AOD_DATASET)
        .filterDate(date_str, end_str)
        .select(AOD_BAND)
        .mosaic()
    )
    reduced = image.reduceRegions(
        collection=station_fc,
        reducer=ee.Reducer.mean(),
        scale=SCALE_AOD
    )
    return reduced.getInfo()['features']


def extract_era5(date_str):
    """
    Validated: RH derived via Magnus formula from temperature_2m and
    dewpoint_temperature_2m (relative_humidity_2m is NOT a real band).
    Wind speed derived from u/v components. BLH used directly (confirmed
    valid band). All combined then passed through reduceRegions(mean).
    """
    end_str = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    image = (
        ee.ImageCollection("ECMWF/ERA5/HOURLY")
        .filterDate(date_str, end_str)
        .select(ERA5_RAW_BANDS)
        .mean()
    )

    t = image.select('temperature_2m').subtract(273.15)
    td = image.select('dewpoint_temperature_2m').subtract(273.15)
    rh = image.expression(
        '100 * (exp((17.625*td)/(243.04+td)) / exp((17.625*t)/(243.04+t)))',
        {'t': t, 'td': td}
    ).rename('relative_humidity_2m')

    wind_speed = image.expression(
        'sqrt(u*u + v*v)',
        {
            'u': image.select('u_component_of_wind_10m'),
            'v': image.select('v_component_of_wind_10m')
        }
    ).rename('wind_speed')

    full_image = image.addBands(rh).addBands(wind_speed)

    reduced = full_image.reduceRegions(
        collection=station_fc,
        reducer=ee.Reducer.mean(),
        scale=SCALE_ERA5
    )
    return reduced.getInfo()['features']


# =====================================================================
# ============================= MAIN LOOP ==============================
# =====================================================================

print("Starting extraction. Progress is saved after every date.")
print("Safe to stop (Ctrl+C) and re-run later to resume.\n")

file_exists = os.path.exists(OUTPUT_CSV)

for i, date_str in enumerate(remaining_dates):
    print(f"[{i+1}/{len(remaining_dates)}] Processing {date_str}...")
    t0 = time.time()

    try:
        rows = {}
        for _, row in stations.iterrows():
            rows[row[ID_COL]] = {
                'StationId': row[ID_COL],
                'Date': date_str,
                'Latitude': row[LAT_COL],
                'Longitude': row[LON_COL]
            }

        # ---------------- TROPOMI ----------------
        for col_name, (dataset_id, band) in TROPOMI_DATASETS.items():
            features = extract_tropomi(date_str, dataset_id, band)
            for f in features:
                sid = f['properties']['StationId']
                rows[sid][col_name] = f['properties'].get('mean', f['properties'].get(band))

        # ---------------- AOD ----------------
        features = extract_aod(date_str)
        for f in features:
            sid = f['properties']['StationId']
            rows[sid]['AOD'] = f['properties'].get('mean', f['properties'].get(AOD_BAND))

        # ---------------- ERA5 ----------------
        features = extract_era5(date_str)
        for f in features:
            sid = f['properties']['StationId']
            props = f['properties']
            rows[sid]['temperature_K'] = props.get('temperature_2m')
            rows[sid]['relative_humidity'] = props.get('relative_humidity_2m')
            rows[sid]['BLH'] = props.get('boundary_layer_height')
            rows[sid]['wind_speed'] = props.get('wind_speed')

        # Save this date's rows
        df_chunk = pd.DataFrame(rows.values())
        df_chunk.to_csv(OUTPUT_CSV, mode='a', header=not file_exists, index=False)
        file_exists = True

        with open(PROGRESS_LOG, 'a') as f:
            f.write(date_str + "\n")

        n_valid_no2 = df_chunk['NO2_sat'].notna().sum() if 'NO2_sat' in df_chunk else 0
        print(f"    Done in {time.time()-t0:.1f}s "
              f"({n_valid_no2}/{len(df_chunk)} stations had valid NO2)")

    except Exception as e:
        print(f"    FAILED: {e}")
        print("    Skipping for now — will retry on next run since not marked complete.")
        time.sleep(5)
        continue

print("\nExtraction run finished (completed or interrupted).")
print(f"Results: {OUTPUT_CSV}")
print(f"Progress log: {PROGRESS_LOG}")

if TEST_MODE:
    print("\n" + "=" * 60)
    print("TEST MODE CHECKLIST — verify before running full scale:")
    print("1. Open the CSV — exactly one row per station per date?")
    print("2. Spot check a few NO2/AOD/ERA5 values — physically plausible?")
    print("3. Stop this script mid-run (Ctrl+C) and re-run it — does it")
    print("   correctly skip already-completed dates instead of redoing them?")
    print("4. Once all 3 pass, set TEST_MODE = False and run the full range.")
    print("=" * 60)