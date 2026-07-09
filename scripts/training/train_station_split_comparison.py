"""
Fix AOD Scale Factor + Refit Final Model
===========================================

CONTEXT: AOD values in final_dataset_v2.csv were extracted as raw MAIAC
band values, which Google's own Earth Engine documentation displays
with a typical range up to ~1100 -- the correct physical AOD scale
factor is 0.001 (confirmed against the MCD19A2 product documentation).
Mean AOD in the existing dataset was 827.6, max 5203.7 -- both
physically impossible for real AOD (which rarely exceeds ~5 even in
extreme dust events), confirming the raw/unscaled values were used.

WHY THIS DOESN'T INVALIDATE THE EXISTING MODEL:
Tree-based models split on relative thresholds, not absolute physical
units. A uniform x1000 rescaling does not change relative ordering, so
RMSE/MAE/R from the previous training run are unaffected and remain a
valid result. This script exists purely so future reports/plots show
physically correct AOD values, and so the GRID extraction (used for
the spatial map) is generated using the SAME scale convention the
model will actually be applied with going forward.

WHAT THIS SCRIPT DOES:
  1. Loads final_dataset_v2.csv, multiplies AOD by 0.001, saves as
     final_dataset_v3.csv (does NOT overwrite v2 -- keep the old file
     in case you need to compare or revert)
  2. Refits the model using the EXACT best hyperparameters already
     found by RandomizedSearchCV in the previous tuning run (no new
     search needed -- rescaling AOD does not change which
     hyperparameters are best, since it's still the same relative
     feature, just on a corrected scale)
  3. Re-evaluates on the same station-holdout split for a clean
     before/after comparison
  4. Saves the corrected model

AFTER RUNNING THIS: use final_dataset_v3.csv and this new saved model
going forward. Apply the SAME 0.001 scale factor in the grid
extraction script before running the model on grid data.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import json
import os
from datetime import datetime

# =====================================================================
# CONFIG
# =====================================================================

INPUT_CSV_OLD = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\final_dataset_v2.csv"
OUTPUT_CSV_NEW = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\final_dataset_v3.csv"
MODEL_DIR = r"C:\Users\Jayyanth\Desktop\ISRO\data\models\final"

FEATURE_COLS = [
    'NO2_sat', 'SO2_sat', 'CO_sat', 'O3_sat', 'HCHO_sat', 'AOD',
    'temperature_K', 'relative_humidity', 'BLH', 'wind_speed'
]
TARGET_COL = 'PM2.5'
STATION_COL = 'StationId'
RANDOM_SEED = 42

AOD_SCALE_FACTOR = 0.001

# Best hyperparameters found by the earlier RandomizedSearchCV run --
# paste these EXACTLY as printed in your previous tuning run's output.
# (Filled in here using the result you already obtained.)
BEST_PARAMS = {
    'subsample': 0.9,
    'reg_lambda': 2.0,
    'reg_alpha': 1.0,
    'n_estimators': 800,
    'min_child_weight': 7,
    'max_depth': 10,
    'learning_rate': 0.01,
    'colsample_bytree': 0.8,
}

# Sample weighting that won in the previous tuning run (3x weight, PM2.5>150)
WEIGHT_THRESHOLD = 150
WEIGHT_VALUE = 3.0

# =====================================================================
# STEP 1 — FIX THE SCALE AND SAVE A NEW FILE (does not touch v2)
# =====================================================================

print("Loading existing dataset...")
df = pd.read_csv(INPUT_CSV_OLD)
print(f"Rows: {len(df)}")

print(f"\nBEFORE fix: AOD describe()")
print(df['AOD'].describe())

df['AOD'] = df['AOD'] * AOD_SCALE_FACTOR

print(f"\nAFTER fix (x{AOD_SCALE_FACTOR}): AOD describe()")
print(df['AOD'].describe())

df.to_csv(OUTPUT_CSV_NEW, index=False)
print(f"\nSaved corrected dataset to: {OUTPUT_CSV_NEW}")
print("(Original final_dataset_v2.csv left untouched for comparison/rollback.)")

# =====================================================================
# STEP 2 — SAME STATION-HOLDOUT SPLIT AS THE ORIGINAL TUNING RUN
# =====================================================================

df = df[df[TARGET_COL].notna()].copy()
df['PM2.5_log'] = np.log1p(df[TARGET_COL])

stations = df[STATION_COL].unique()
rng = np.random.RandomState(RANDOM_SEED)
stations_shuffled = stations.copy()
rng.shuffle(stations_shuffled)

n = len(stations_shuffled)
train_st = set(stations_shuffled[:int(0.6 * n)])
val_st = set(stations_shuffled[int(0.6 * n):int(0.8 * n)])
test_st = set(stations_shuffled[int(0.8 * n):])

train_mask = df[STATION_COL].isin(train_st)
test_mask = df[STATION_COL].isin(test_st)

X_train = df.loc[train_mask, FEATURE_COLS]
X_test = df.loc[test_mask, FEATURE_COLS]
y_train_log = df.loc[train_mask, 'PM2.5_log']
y_train_raw = df.loc[train_mask, TARGET_COL]
y_test_raw = df.loc[test_mask, TARGET_COL]

print(f"\nStation split: train={len(train_st)} stations ({len(X_train)} rows), "
      f"test={len(test_st)} stations ({len(X_test)} rows)")

# =====================================================================
# STEP 3 — REFIT USING KNOWN-BEST HYPERPARAMETERS + SAMPLE WEIGHTING
# =====================================================================

print("\nRefitting model with corrected AOD scale, using previously-found "
      "best hyperparameters (no new search needed)...")

sample_weights = np.where(y_train_raw > WEIGHT_THRESHOLD, WEIGHT_VALUE, 1.0)

model = xgb.XGBRegressor(**BEST_PARAMS, random_state=RANDOM_SEED, eval_metric='rmse')
model.fit(X_train, y_train_log, sample_weight=sample_weights)

preds_log = model.predict(X_test)
preds = np.clip(np.expm1(preds_log), 0, None)

rmse = np.sqrt(mean_squared_error(y_test_raw, preds))
mae = mean_absolute_error(y_test_raw, preds)
r = np.corrcoef(y_test_raw, preds)[0, 1]

print(f"\nCorrected-AOD model (station holdout test): RMSE={rmse:.2f}  MAE={mae:.2f}  R={r:.3f}")
print("\nCompare against the PREVIOUS (unscaled-AOD) result: RMSE=32.17  MAE=19.10  R=0.866")
print("These should be very close (likely near-identical) -- confirming the rescaling")
print("does not change model performance, only the physical interpretability of AOD values.")

# =====================================================================
# STEP 4 — SAVE THE CORRECTED MODEL
# =====================================================================

os.makedirs(MODEL_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = os.path.join(MODEL_DIR, f"final_pm25_model_corrected_aod_{timestamp}.joblib")
joblib.dump(model, model_path)

metadata = {
    "model_type": "XGBRegressor",
    "target_transform": "log1p (predictions must be inverted with expm1, then clipped at 0)",
    "aod_scale_factor_applied": AOD_SCALE_FACTOR,
    "note": "AOD in this model's training data was corrected from raw MAIAC band "
            "values to physical AOD units (x0.001). Any new data fed to this model "
            "MUST have the same 0.001 scale factor applied to its AOD column before "
            "prediction, or predictions will be wrong.",
    "split_strategy": "station_holdout",
    "feature_columns_in_order": FEATURE_COLS,
    "hyperparameters_used": BEST_PARAMS,
    "sample_weighting": {"threshold": WEIGHT_THRESHOLD, "weight": WEIGHT_VALUE},
    "test_metrics": {"rmse": rmse, "mae": mae, "r": r},
    "previous_unscaled_aod_metrics": {"rmse": 32.17, "mae": 19.10, "r": 0.866},
    "trained_on_rows": len(X_train),
    "saved_at": timestamp,
}
metadata_path = os.path.join(MODEL_DIR, f"final_pm25_model_corrected_aod_{timestamp}_metadata.json")
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\nSaved corrected model to: {model_path}")
print(f"Saved metadata to: {metadata_path}")
print("\nUSE THIS MODEL (not the earlier unscaled-AOD one) for the grid/spatial map step.")
print("Remember to apply the SAME 0.001 AOD scale factor in the grid extraction script.")