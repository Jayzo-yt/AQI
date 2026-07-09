"""
PM2.5 Prediction Model Training — Objective 1
================================================

Trains and evaluates two models (Random Forest, XGBoost) using two
different train/val/test split strategies:

  1. RANDOM split  -> tells you how well the model predicts NEW DATES
                       at stations it has already seen during training
  2. STATION split -> tells you how well the model generalizes to
                       BRAND NEW LOCATIONS it has never seen — this is
                       the honest test of your "spatial AQI map across
                       India" claim from the problem statement

Report BOTH sets of numbers in your write-up. The station split will
likely look worse than the random split — that is expected and is the
more honest number, not a failure.

BEFORE RUNNING:
  - Edit INPUT_CSV to point to your final_dataset_v2.csv
  - Confirm feature_cols matches your actual column names exactly
  - pip install xgboost --break-system-packages   (if not already installed)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import xgboost as xgb

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

# =====================================================================
# LOAD DATA
# =====================================================================

print("Loading data...")
df = pd.read_csv(INPUT_CSV)
print(f"Raw rows: {len(df)}")

# Only require the TARGET to be present. Features can have some NaNs —
# Random Forest needs them dropped (sklearn can't handle NaN features),
# XGBoost can handle NaN features natively, so we build two dataframes.
df = df[df[TARGET_COL].notna()].copy()
print(f"Rows with valid {TARGET_COL}: {len(df)}")

df_rf = df.dropna(subset=FEATURE_COLS).copy()
print(f"Rows with ALL features present (for Random Forest): {len(df_rf)}")
print(f"Rows usable for XGBoost (target only required): {len(df)}")

# =====================================================================
# BUILD BOTH SPLIT STRATEGIES
# =====================================================================

def random_split(data, feature_cols, target_col, seed=RANDOM_SEED):
    """60/20/20 row-level random split."""
    n = len(data)
    idx = np.arange(n)
    rng = np.random.RandomState(seed)
    rng.shuffle(idx)

    train_end = int(0.6 * n)
    val_end = int(0.8 * n)

    train_idx = idx[:train_end]
    val_idx = idx[train_end:val_end]
    test_idx = idx[val_end:]

    X = data[feature_cols]
    y = data[target_col]

    return (X.iloc[train_idx], y.iloc[train_idx],
            X.iloc[val_idx], y.iloc[val_idx],
            X.iloc[test_idx], y.iloc[test_idx])


def station_split(data, feature_cols, target_col, station_col, seed=RANDOM_SEED):
    """60/20/20 split by STATION, not by row — tests spatial generalization."""
    stations = data[station_col].unique()
    rng = np.random.RandomState(seed)
    stations = stations.copy()
    rng.shuffle(stations)

    n = len(stations)
    train_st = set(stations[:int(0.6 * n)])
    val_st = set(stations[int(0.6 * n):int(0.8 * n)])
    test_st = set(stations[int(0.8 * n):])

    train_mask = data[station_col].isin(train_st)
    val_mask = data[station_col].isin(val_st)
    test_mask = data[station_col].isin(test_st)

    X = data[feature_cols]
    y = data[target_col]

    print(f"    Station split -> train: {len(train_st)} stations, "
          f"val: {len(val_st)} stations, test: {len(test_st)} stations")

    return (X[train_mask], y[train_mask],
            X[val_mask], y[val_mask],
            X[test_mask], y[test_mask])


def evaluate(model, X, y, label=""):
    preds = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, preds))
    mae = mean_absolute_error(y, preds)
    r = np.corrcoef(y, preds)[0, 1]
    print(f"    {label}: RMSE={rmse:.2f}  MAE={mae:.2f}  R={r:.3f}")
    return {'rmse': rmse, 'mae': mae, 'r': r}


results = {}

# =====================================================================
# RANDOM FOREST — needs complete (no-NaN) feature rows
# =====================================================================

print("\n" + "=" * 70)
print("RANDOM FOREST")
print("=" * 70)

print("\n--- Random split ---")
X_tr, y_tr, X_val, y_val, X_te, y_te = random_split(df_rf, FEATURE_COLS, TARGET_COL)
print(f"    Train: {len(X_tr)}  Val: {len(X_val)}  Test: {len(X_te)}")

best_rmse, best_depth = float('inf'), None
for depth in [8, 10, 12, 15, None]:
    m = RandomForestRegressor(n_estimators=300, max_depth=depth,
                                random_state=RANDOM_SEED, n_jobs=-1)
    m.fit(X_tr, y_tr)
    metrics = evaluate(m, X_val, y_val, f"depth={depth} | Val")
    if metrics['rmse'] < best_rmse:
        best_rmse, best_depth = metrics['rmse'], depth

print(f"    Best max_depth on validation: {best_depth}")
rf_random = RandomForestRegressor(n_estimators=300, max_depth=best_depth,
                                    random_state=RANDOM_SEED, n_jobs=-1)
rf_random.fit(X_tr, y_tr)
results['rf_random'] = evaluate(rf_random, X_te, y_te, "FINAL Test")

print("\n--- Station split (tests spatial generalization) ---")
X_tr_s, y_tr_s, X_val_s, y_val_s, X_te_s, y_te_s = station_split(
    df_rf, FEATURE_COLS, TARGET_COL, STATION_COL)
print(f"    Train: {len(X_tr_s)}  Val: {len(X_val_s)}  Test: {len(X_te_s)}")

best_rmse_s, best_depth_s = float('inf'), None
for depth in [8, 10, 12, 15, None]:
    m = RandomForestRegressor(n_estimators=300, max_depth=depth,
                                random_state=RANDOM_SEED, n_jobs=-1)
    m.fit(X_tr_s, y_tr_s)
    metrics = evaluate(m, X_val_s, y_val_s, f"depth={depth} | Val")
    if metrics['rmse'] < best_rmse_s:
        best_rmse_s, best_depth_s = metrics['rmse'], depth

print(f"    Best max_depth on validation: {best_depth_s}")
rf_station = RandomForestRegressor(n_estimators=300, max_depth=best_depth_s,
                                     random_state=RANDOM_SEED, n_jobs=-1)
rf_station.fit(X_tr_s, y_tr_s)
results['rf_station'] = evaluate(rf_station, X_te_s, y_te_s, "FINAL Test")

# =====================================================================
# XGBOOST — can use rows with some missing features (target still required)
# =====================================================================

print("\n" + "=" * 70)
print("XGBOOST")
print("=" * 70)

print("\n--- Random split ---")
X_tr, y_tr, X_val, y_val, X_te, y_te = random_split(df, FEATURE_COLS, TARGET_COL)
print(f"    Train: {len(X_tr)}  Val: {len(X_val)}  Test: {len(X_te)}")

xgb_random = xgb.XGBRegressor(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    random_state=RANDOM_SEED, early_stopping_rounds=30, eval_metric='rmse'
)
xgb_random.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
results['xgb_random'] = evaluate(xgb_random, X_te, y_te, "FINAL Test")

print("\n--- Station split (tests spatial generalization) ---")
X_tr_s, y_tr_s, X_val_s, y_val_s, X_te_s, y_te_s = station_split(
    df, FEATURE_COLS, TARGET_COL, STATION_COL)
print(f"    Train: {len(X_tr_s)}  Val: {len(X_val_s)}  Test: {len(X_te_s)}")

xgb_station = xgb.XGBRegressor(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    random_state=RANDOM_SEED, early_stopping_rounds=30, eval_metric='rmse'
)
xgb_station.fit(X_tr_s, y_tr_s, eval_set=[(X_val_s, y_val_s)], verbose=False)
results['xgb_station'] = evaluate(xgb_station, X_te_s, y_te_s, "FINAL Test")

# =====================================================================
# SUMMARY
# =====================================================================

print("\n" + "=" * 70)
print("SUMMARY — FINAL TEST METRICS (lower RMSE/MAE better, higher R better)")
print("=" * 70)
print(f"{'Model':<30} {'RMSE':>8} {'MAE':>8} {'R':>8}")
for name, m in results.items():
    print(f"{name:<30} {m['rmse']:>8.2f} {m['mae']:>8.2f} {m['r']:>8.3f}")

print("\nFeature importance (XGBoost, random split model):")
importances = sorted(zip(FEATURE_COLS, xgb_random.feature_importances_),
                       key=lambda x: -x[1])
for feat, imp in importances:
    print(f"    {feat:<20} {imp:.4f}")

print("\nDone. Compare random-split vs station-split numbers carefully —")
print("a big gap between them tells you the model memorizes station")
print("identity more than it learns the true satellite->ground relationship.")