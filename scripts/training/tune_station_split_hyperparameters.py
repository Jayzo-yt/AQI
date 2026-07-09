"""
PM2.5 Model Tuning — Improved Version
========================================

Builds on the validated baseline (RF/XGBoost, station-holdout split)
and applies four concrete, evidence-based improvements, each isolated
so you can see what each one actually contributes:

  1. LOG-TRANSFORM the target (log1p(PM2.5)) before training, since
     Indian PM2.5 is heavily right-skewed (occasional huge winter
     spikes). RMSE in log-space penalizes large absolute errors less
     unfairly and is standard practice in the published literature on
     this exact problem.

  2. REAL hyperparameter search via RandomizedSearchCV using the
     TRAINING set with cross-validation — not the manual single-pass
     depth sweep from before. This actually tunes learning_rate,
     max_depth, n_estimators, subsample, colsample_bytree together,
     instead of guessing one parameter in isolation.

  3. PER-STATION error breakdown on the test set — tells you whether
     error is spread evenly or concentrated in a handful of stations
     (e.g. extreme-pollution cities), which changes how you interpret
     the aggregate RMSE.

  4. ERROR vs PM2.5-LEVEL breakdown — tells you whether the model is
     uniformly accurate or specifically bad at high-pollution days
     (the days that matter most for AQI alerts).

USES THE SAME station-holdout split as before for a fair before/after
comparison — only the modeling choices change, not the data split.

BEFORE RUNNING:
  pip install xgboost scikit-learn --break-system-packages
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error
import xgboost as xgb
import joblib
import json
import os
from datetime import datetime

# =====================================================================
# CONFIG
# =====================================================================

INPUT_CSV = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\final_dataset_v2.csv"

FEATURE_COLS = [
    'NO2_sat', 'SO2_sat', 'CO_sat', 'O3_sat', 'HCHO_sat', 'AOD',
    'temperature_K', 'relative_humidity', 'BLH', 'wind_speed'
]
TARGET_COL = 'PM2.5'
STATION_COL = 'StationId'
RANDOM_SEED = 42
MODEL_DIR = r"C:\Users\Jayyanth\Desktop\ISRO\data\models\staging\models"

# =====================================================================
# LOAD AND PREPARE
# =====================================================================

print("Loading data...")
df = pd.read_csv(INPUT_CSV)
df = df[df[TARGET_COL].notna()].copy()
print(f"Rows with valid PM2.5: {len(df)}")

# XGBoost handles missing features natively — only target required.
# Build the log-transformed target now, used for ALL training below.
df['PM2.5_log'] = np.log1p(df[TARGET_COL])

# =====================================================================
# SAME STATION-HOLDOUT SPLIT AS BASELINE — for a fair before/after comparison
# =====================================================================

stations = df[STATION_COL].unique()
rng = np.random.RandomState(RANDOM_SEED)
stations_shuffled = stations.copy()
rng.shuffle(stations_shuffled)

n = len(stations_shuffled)
train_st = set(stations_shuffled[:int(0.6 * n)])
val_st = set(stations_shuffled[int(0.6 * n):int(0.8 * n)])
test_st = set(stations_shuffled[int(0.8 * n):])

train_mask = df[STATION_COL].isin(train_st)
val_mask = df[STATION_COL].isin(val_st)
test_mask = df[STATION_COL].isin(test_st)

X_train = df.loc[train_mask, FEATURE_COLS]
X_val = df.loc[val_mask, FEATURE_COLS]
X_test = df.loc[test_mask, FEATURE_COLS]

y_train_log = df.loc[train_mask, 'PM2.5_log']
y_val_log = df.loc[val_mask, 'PM2.5_log']
y_test_log = df.loc[test_mask, 'PM2.5_log']

y_train_raw = df.loc[train_mask, TARGET_COL]
y_val_raw = df.loc[val_mask, TARGET_COL]
y_test_raw = df.loc[test_mask, TARGET_COL]

print(f"\nStation split: train={len(train_st)} stations ({len(X_train)} rows), "
      f"val={len(val_st)} stations ({len(X_val)} rows), "
      f"test={len(test_st)} stations ({len(X_test)} rows)")


def evaluate_raw_scale(model, X, y_true_raw, label="", is_log_model=True):
    """Predicts in log-space if is_log_model, converts back to real PM2.5
    units (µg/m³) before computing metrics — RMSE/MAE must be reported
    in real units, not log units, or the numbers aren't interpretable."""
    preds_log_or_raw = model.predict(X)
    if is_log_model:
        preds = np.expm1(preds_log_or_raw)  # invert log1p
        preds = np.clip(preds, 0, None)      # PM2.5 can't be negative
    else:
        preds = preds_log_or_raw

    rmse = np.sqrt(mean_squared_error(y_true_raw, preds))
    mae = mean_absolute_error(y_true_raw, preds)
    r = np.corrcoef(y_true_raw, preds)[0, 1]
    print(f"    {label}: RMSE={rmse:.2f}  MAE={mae:.2f}  R={r:.3f}")
    return {'rmse': rmse, 'mae': mae, 'r': r}, preds


# =====================================================================
# STEP 1 — BASELINE FOR COMPARISON: same XGBoost config as before, no log
# =====================================================================

print("\n" + "=" * 70)
print("STEP 1: BASELINE (raw PM2.5, fixed hyperparameters) — for comparison")
print("=" * 70)

baseline_model = xgb.XGBRegressor(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    random_state=RANDOM_SEED, early_stopping_rounds=30, eval_metric='rmse'
)
baseline_model.fit(X_train, y_train_raw, eval_set=[(X_val, y_val_raw)], verbose=False)
baseline_metrics, _ = evaluate_raw_scale(
    baseline_model, X_test, y_test_raw, "Baseline (raw target)", is_log_model=False)

# =====================================================================
# STEP 2 — LOG-TRANSFORM ONLY (same hyperparameters, just log target)
# =====================================================================

print("\n" + "=" * 70)
print("STEP 2: LOG-TRANSFORM target only (isolates this one change)")
print("=" * 70)

log_only_model = xgb.XGBRegressor(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    random_state=RANDOM_SEED, early_stopping_rounds=30, eval_metric='rmse'
)
log_only_model.fit(X_train, y_train_log, eval_set=[(X_val, y_val_log)], verbose=False)
log_only_metrics, _ = evaluate_raw_scale(
    log_only_model, X_test, y_test_raw, "Log-transform only", is_log_model=True)

# =====================================================================
# STEP 3 — LOG-TRANSFORM + REAL HYPERPARAMETER SEARCH
# =====================================================================

print("\n" + "=" * 70)
print("STEP 3: LOG-TRANSFORM + RandomizedSearchCV (this will take a while)")
print("=" * 70)

param_dist = {
    'n_estimators': [200, 300, 500, 800],
    'max_depth': [4, 5, 6, 7, 8, 10],
    'learning_rate': [0.01, 0.03, 0.05, 0.08, 0.1],
    'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
    'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
    'min_child_weight': [1, 3, 5, 7],
    'reg_alpha': [0, 0.1, 0.5, 1.0],
    'reg_lambda': [0.5, 1.0, 1.5, 2.0],
}

base_xgb = xgb.XGBRegressor(random_state=RANDOM_SEED, eval_metric='rmse')

search = RandomizedSearchCV(
    base_xgb,
    param_distributions=param_dist,
    n_iter=40,                  # 40 random combinations — reasonable for your time budget
    scoring='neg_root_mean_squared_error',
    cv=3,                       # 3-fold CV within the training set only
    random_state=RANDOM_SEED,
    n_jobs=-1,
    verbose=1
)

print("Running search (40 combinations x 3-fold CV = 120 fits, may take several minutes)...")
search.fit(X_train, y_train_log)

print(f"\nBest params found: {search.best_params_}")
print(f"Best CV RMSE (log-space): {-search.best_score_:.4f}")

tuned_model = search.best_estimator_
tuned_metrics, tuned_preds = evaluate_raw_scale(
    tuned_model, X_test, y_test_raw, "Log-transform + tuned hyperparameters", is_log_model=True)

# =====================================================================
# STEP 4 — SAMPLE WEIGHTING ON HIGH-PM2.5 ROWS
# =====================================================================
#
# Same tuned hyperparameters, same log-transformed target — the ONLY
# change is giving the loss function more weight on rows where the
# TRUE PM2.5 is high, so the model is penalized harder for getting
# severe/extreme pollution days wrong. This directly targets the
# weakness found in the pollution-level diagnostic, without needing
# more data or a different architecture.
#
# Tries two weight strengths so you can see the tradeoff, not just
# one arbitrary guess: weighting the top end always costs a little
# accuracy at the low end (the model spends more of its capacity on
# the rare, hard, high-value points) — that tradeoff needs to be
# visible, not hidden behind a single number.

print("\n" + "=" * 70)
print("STEP 4: SAMPLE WEIGHTING on high-PM2.5 training rows")
print("=" * 70)

weighting_configs = [
    {"label": "3x weight, PM2.5>150", "threshold": 150, "weight": 3.0},
    {"label": "5x weight, PM2.5>200", "threshold": 200, "weight": 5.0},
]

weighted_results = {}
weighted_models = {}

for cfg in weighting_configs:
    sample_weights = np.where(y_train_raw > cfg["threshold"], cfg["weight"], 1.0)
    n_weighted = (sample_weights > 1.0).sum()
    print(f"\n--- {cfg['label']} ({n_weighted} of {len(y_train_raw)} training rows upweighted) ---")

    w_model = xgb.XGBRegressor(**search.best_params_, random_state=RANDOM_SEED, eval_metric='rmse')
    w_model.fit(X_train, y_train_log, sample_weight=sample_weights)

    w_metrics, w_preds = evaluate_raw_scale(
        w_model, X_test, y_test_raw, cfg["label"], is_log_model=True)
    weighted_results[cfg["label"]] = w_metrics
    weighted_models[cfg["label"]] = (w_model, w_preds)

    # Show the SAME pollution-level breakdown for this weighted model,
    # so you can see exactly what was traded for what.
    test_df_w = df.loc[test_mask, [STATION_COL, TARGET_COL]].copy()
    test_df_w['predicted'] = w_preds
    test_df_w['abs_error'] = np.abs(test_df_w[TARGET_COL] - test_df_w['predicted'])
    bins = [0, 50, 100, 150, 200, 300, 1000]
    labels = ['0-50', '50-100', '100-150', '150-200', '200-300', '300+']
    test_df_w['pm25_bin'] = pd.cut(test_df_w[TARGET_COL], bins=bins, labels=labels)
    level_errors_w = test_df_w.groupby('pm25_bin', observed=True).agg(
        n_rows=('abs_error', 'size'), mae=('abs_error', 'mean')
    )
    print(level_errors_w.to_string())

# =====================================================================
# SUMMARY — BEFORE / AFTER COMPARISON
# =====================================================================

print("\n" + "=" * 70)
print("SUMMARY — STATION-HELD-OUT TEST SET (same split throughout)")
print("=" * 70)
print(f"{'Version':<45} {'RMSE':>8} {'MAE':>8} {'R':>8}")
print(f"{'1. Baseline (raw target, fixed params)':<45} "
      f"{baseline_metrics['rmse']:>8.2f} {baseline_metrics['mae']:>8.2f} {baseline_metrics['r']:>8.3f}")
print(f"{'2. + Log-transform target':<45} "
      f"{log_only_metrics['rmse']:>8.2f} {log_only_metrics['mae']:>8.2f} {log_only_metrics['r']:>8.3f}")
print(f"{'3. + Tuned hyperparameters':<45} "
      f"{tuned_metrics['rmse']:>8.2f} {tuned_metrics['mae']:>8.2f} {tuned_metrics['r']:>8.3f}")
for label, m in weighted_results.items():
    print(f"{'4. + ' + label:<45} {m['rmse']:>8.2f} {m['mae']:>8.2f} {m['r']:>8.3f}")

improvement_pct = 100 * (baseline_metrics['rmse'] - tuned_metrics['rmse']) / baseline_metrics['rmse']
print(f"\nTotal RMSE improvement (step 3 vs baseline): {improvement_pct:.1f}%")
print("\nCompare the weighted models' AGGREGATE rmse/mae above against the")
print("per-bin MAE printed just before this table — a weighted model can")
print("look worse in AGGREGATE RMSE while being meaningfully better at")
print("exactly the high-pollution bin that matters most for AQI alerts.")
print("Pick based on which tradeoff fits your actual reporting goal, not")
print("just whichever aggregate number is lowest.")

# =====================================================================
# DIAGNOSTIC 1 — PER-STATION ERROR BREAKDOWN
# =====================================================================

print("\n" + "=" * 70)
print("DIAGNOSTIC: Per-station error (tuned model, test set)")
print("=" * 70)

test_df = df.loc[test_mask, [STATION_COL, TARGET_COL]].copy()
test_df['predicted'] = tuned_preds
test_df['abs_error'] = np.abs(test_df[TARGET_COL] - test_df['predicted'])

station_errors = test_df.groupby(STATION_COL).agg(
    n_rows=('abs_error', 'size'),
    mean_pm25=(TARGET_COL, 'mean'),
    mae=('abs_error', 'mean')
).sort_values('mae', ascending=False)

print(station_errors.to_string())
print("\nIf a few stations dominate the error, the aggregate RMSE is being")
print("driven by specific locations (often extreme-pollution megacities),")
print("not uniform model weakness.")

# =====================================================================
# DIAGNOSTIC 2 — ERROR BY POLLUTION LEVEL
# =====================================================================

print("\n" + "=" * 70)
print("DIAGNOSTIC: Error by PM2.5 level (tuned model, test set)")
print("=" * 70)

bins = [0, 50, 100, 150, 200, 300, 1000]
labels = ['0-50 (Good/Satisfactory)', '50-100 (Moderate)', '100-150 (Poor)',
          '150-200 (Very Poor)', '200-300 (Severe)', '300+ (Extreme)']
test_df['pm25_bin'] = pd.cut(test_df[TARGET_COL], bins=bins, labels=labels)

level_errors = test_df.groupby('pm25_bin').agg(
    n_rows=('abs_error', 'size'),
    mean_actual=(TARGET_COL, 'mean'),
    mae=('abs_error', 'mean'),
    rmse=('abs_error', lambda x: np.sqrt(np.mean(x**2)))
)
print(level_errors.to_string())
print("\nIf MAE/RMSE rise sharply in the higher bins, the model is")
print("specifically weaker at exactly the pollution levels that matter")
print("most for health alerts — a real, reportable limitation, not")
print("something to hide in your write-up.")

# =====================================================================
# SAVE THE TUNED MODEL
# =====================================================================

os.makedirs(MODEL_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = os.path.join(MODEL_DIR, f"tuned_pm25_model_{timestamp}.joblib")
joblib.dump(tuned_model, model_path)

metadata = {
    "model_type": "XGBRegressor",
    "target_transform": "log1p (predictions must be inverted with expm1, then clipped at 0)",
    "split_strategy": "station_holdout",
    "feature_columns_in_order": FEATURE_COLS,
    "best_hyperparameters": search.best_params_,
    "test_metrics": tuned_metrics,
    "comparison_metrics": {
        "baseline": baseline_metrics,
        "log_only": log_only_metrics,
        "tuned": tuned_metrics,
        "weighted_variants": weighted_results
    },
    "rmse_improvement_pct": improvement_pct,
    "trained_on_rows": len(X_train),
    "saved_at": timestamp,
}
metadata_path = os.path.join(MODEL_DIR, f"tuned_pm25_model_{timestamp}_metadata.json")
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\nSaved tuned (unweighted) model to: {model_path}")
print(f"Saved metadata to: {metadata_path}")

for label, (w_model, _) in weighted_models.items():
    safe_label = label.replace(" ", "_").replace(",", "").replace(">", "gt")
    w_path = os.path.join(MODEL_DIR, f"weighted_pm25_model_{safe_label}_{timestamp}.joblib")
    joblib.dump(w_model, w_path)
    print(f"Saved weighted variant ({label}) to: {w_path}")

print("\nREMEMBER: ALL these models predict log1p(PM2.5). To get real PM2.5:")
print("    pred_log = model.predict(X_new)")
print("    pred_pm25 = np.clip(np.expm1(pred_log), 0, None)")
print("\nDECISION FOR YOU: pick the unweighted model if you want the best")
print("single aggregate RMSE/MAE/R to report. Pick a weighted variant if")
print("you want to emphasize accuracy at high-pollution/health-alert levels")
print("even at a small cost to aggregate metrics — state this tradeoff")
print("explicitly in your report rather than only reporting one number.")