"""
Apply Model to Grid + Convert PM2.5 to AQI
==============================================

Takes the extracted grid data (grid_extracted_<date>.csv), runs the
final corrected-AOD model on every point with COMPLETE features, and
converts predicted PM2.5 to AQI using the official CPCB breakpoint
table. This is the actual "surface AQI" deliverable the problem
statement asks for -- raw PM2.5 alone is not AQI.

HONEST LIMITATION (state this in your report, don't hide it):
Only points with all 10 features present get a prediction. On this
test date, that was 7,410 / 13,923 grid points (53.2%) -- the rest
have a gap in at least one TROPOMI band due to cloud cover / no
overpass that day, which is expected and was extensively validated
earlier in this project, not a new bug.

CPCB AQI BREAKPOINTS FOR PM2.5 (µg/m³, 24-hr average):
  0-30:    AQI 0-50      (Good)
  31-60:   AQI 51-100    (Satisfactory)
  61-90:   AQI 101-200   (Moderate)
  91-120:  AQI 201-300   (Poor)
  121-250: AQI 301-400   (Very Poor)
  251-380: AQI 401-450   (Severe)  -- NOTE: official table caps standard
                                       breakpoints around here; values
                                       above are extrapolated linearly,
                                       flagged separately below
  381+:    AQI 450+      (Severe+) -- extrapolated, not official CPCB
                                       breakpoint table; reported as
                                       "Severe (capped/extrapolated)"

These are the standard CPCB National AQI breakpoints (sub-index
formula: AQI = ((IHi-ILo)/(BPHi-BPLo)) * (Cp-BPLo) + ILo)
"""

import pandas as pd
import numpy as np
import joblib

# =====================================================================
# CONFIG
# =====================================================================

GRID_CSV = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\grid\grid_extracted_2020-01-15.csv"
MODEL_PATH = r"C:\Users\Jayyanth\Desktop\ISRO\data\models\final\final_pm25_model_corrected_aod_20260622_162942.joblib"
OUTPUT_CSV = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\grid\grid_with_predictions_2020-01-15.csv"

FEATURE_COLS = [
    'NO2_sat', 'SO2_sat', 'CO_sat', 'O3_sat', 'HCHO_sat', 'AOD',
    'temperature_K', 'relative_humidity', 'BLH', 'wind_speed'
]

# =====================================================================
# CPCB PM2.5 -> AQI BREAKPOINT TABLE
# =====================================================================
# Each tuple: (BP_low, BP_high, AQI_low, AQI_high)
# Official CPCB table goes up to 500 AQI (PM2.5 250-380 -> 401-450 Severe,
# but the actual NAQI spec only formally tabulates up to AQI 500 with
# PM2.5 cap around 500 ug/m3 in some versions -- using the widely-cited
# CPCB breakpoint table here, with values above 380 ug/m3 reported as
# capped at AQI 500 ("Severe") rather than extrapolated further, since
# extrapolating the AQI formula beyond the official table's range is
# not standard practice and would not be defensible in a report.

PM25_BREAKPOINTS = [
    (0,    30,   0,   50),
    (31,   60,   51,  100),
    (61,   90,   101, 200),
    (91,   120,  201, 300),
    (121,  250,  301, 400),
    (251,  380,  401, 500),
]

AQI_CATEGORIES = [
    (0,   50,  "Good"),
    (51,  100, "Satisfactory"),
    (101, 200, "Moderate"),
    (201, 300, "Poor"),
    (301, 400, "Very Poor"),
    (401, 500, "Severe"),
]


def pm25_to_aqi(pm25):
    """Converts a single PM2.5 value (ug/m3) to AQI using CPCB breakpoints.
    Values above the table's top breakpoint (380) are capped at AQI 500
    -- this is intentional and stated, not a bug: the official CPCB
    breakpoint table does not extend further, so capping is the
    correct, defensible behavior rather than extrapolating an
    unofficial formula past its valid range."""
    if pd.isna(pm25):
        return np.nan
    if pm25 < 0:
        return np.nan
    if pm25 > 380:
        return 500.0  # capped -- see docstring

    for bp_lo, bp_hi, aqi_lo, aqi_hi in PM25_BREAKPOINTS:
        if bp_lo <= pm25 <= bp_hi:
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + aqi_lo
            return round(aqi)
    return np.nan  # shouldn't happen given the table covers 0-380 fully


def aqi_to_category(aqi):
    if pd.isna(aqi):
        return None
    for lo, hi, label in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return label
    return "Severe"  # anything at the very top edge


# =====================================================================
# LOAD GRID, FILTER TO COMPLETE ROWS, PREDICT
# =====================================================================

print("Loading grid data...")
grid = pd.read_csv(GRID_CSV)
print(f"Total grid points: {len(grid)}")

complete = grid.dropna(subset=FEATURE_COLS).copy()
print(f"Points with complete features: {len(complete)} ({100*len(complete)/len(grid):.1f}%)")
print("(Remaining points lack a prediction due to satellite data gaps on this "
      "date -- expected and documented, not an error.)\n")

print("Loading trained model...")
model = joblib.load(MODEL_PATH)

print("Predicting PM2.5 (model outputs log1p(PM2.5) -- inverting now)...")
X = complete[FEATURE_COLS]
preds_log = model.predict(X)
preds_pm25 = np.clip(np.expm1(preds_log), 0, None)
complete['predicted_PM2.5'] = preds_pm25

print("Converting PM2.5 -> AQI using CPCB breakpoints...")
complete['predicted_AQI'] = complete['predicted_PM2.5'].apply(pm25_to_aqi)
complete['AQI_category'] = complete['predicted_AQI'].apply(aqi_to_category)

# Flag rows where the raw prediction exceeded the official breakpoint
# table's range, since their AQI value (500) is a CAP, not a precise score
complete['aqi_capped'] = complete['predicted_PM2.5'] > 380

n_capped = complete['aqi_capped'].sum()
if n_capped > 0:
    print(f"\nNote: {n_capped} points predicted PM2.5 > 380 ug/m3 -- AQI capped "
          f"at 500 for these (official CPCB table does not extend further).")

# =====================================================================
# SUMMARY AND SAVE
# =====================================================================

print("\nPredicted AQI category distribution across the grid:")
print(complete['AQI_category'].value_counts())

print("\nPredicted PM2.5 summary:")
print(complete['predicted_PM2.5'].describe())

complete.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved predictions to: {OUTPUT_CSV}")
print("\nColumns added: predicted_PM2.5, predicted_AQI, AQI_category, aqi_capped")