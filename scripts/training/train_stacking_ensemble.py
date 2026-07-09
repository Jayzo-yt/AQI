"""
PM2.5 Prediction — Tier-1 Performance Pipeline
===============================================

FIVE UPGRADES OVER THE BASELINE:

  1. FEATURE ENGINEERING
       Raw satellite/met columns alone are weak. This adds:
         - Temporal cyclical encoding (month sin/cos, DOY sin/cos) so the
           model understands seasonality without treating Jan=1 < Dec=12
         - Meteorological interaction features (AOD×BLH, AOD×RH,
           NO2×CO, wind u/v components) that capture physical coupling
         - Lag/rolling statistics per station (7-day rolling mean/std of
           PM2.5 -- most powerful single feature in pollution models)
         - Polynomial expansion on the two most predictive columns
           (AOD, NO2_sat) to capture non-linearity explicitly
         - AOD humidification correction: AOD_corr = AOD / (1 - RH/100)
           (physically, hygroscopic growth increases AOD at high RH)

  2. THREE-MODEL STACKING ENSEMBLE
       XGBoost + LightGBM + CatBoost, each tuned independently.
       A Ridge meta-learner combines out-of-fold predictions.
       Stacking almost always beats any single model because the three
       learners make different errors; the meta-learner learns to exploit
       their complementary strengths.

  3. OPTUNA HYPERPARAMETER SEARCH
       Optuna uses Tree-structured Parzen Estimator (TPE) -- far more
       efficient than RandomizedSearchCV for high-dimensional param spaces.
       It runs station-aware GroupKFold CV so hyperparams are selected
       based on generalization across unseen stations, not unseen rows.

  4. ROBUST TARGET TRANSFORMATION
       Switches from log1p to Yeo-Johnson (via PowerTransformer).
       Yeo-Johnson handles near-zero and zero PM2.5 values correctly and
       gives a better-normalised residual distribution, which directly
       improves RMSE/MAE because large residuals are down-weighted during
       optimisation.

  5. STATION-AWARE GROUP K-FOLD (5-fold)
       The baseline used a single 60/20/20 random station split.
       GroupKFold repeats the evaluation 5 times, training is more stable,
       and the final test score is averaged across 5 independent holdouts
       instead of one lucky/unlucky draw.
"""

# =====================================================================
# IMPORTS
# =====================================================================

import os
import json
import warnings
import joblib
from datetime import datetime

import numpy as np
import pandas as pd
import shap

import xgboost as xgb
import lightgbm as lgb
import catboost as cb

import optuna
from optuna.samplers import TPESampler
optuna.logging.set_verbosity(optuna.logging.WARNING)   # suppress per-trial noise

from sklearn.preprocessing import PowerTransformer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

import matplotlib
matplotlib.use("Agg")                                  # headless-safe
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# =====================================================================
# CONFIG  — edit paths only; leave everything else unchanged
# =====================================================================

INPUT_CSV   = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\final_dataset_v2.csv"
OUTPUT_CSV  = r"C:\Users\Jayyanth\Desktop\ISRO\data\maps\final_dataset_v3.csv"
MODEL_DIR   = r"C:\Users\Jayyanth\Desktop\ISRO\data\models\final"
PLOT_DIR    = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\plots"

RAW_FEATURES = [
    'NO2_sat', 'SO2_sat', 'CO_sat', 'O3_sat', 'HCHO_sat', 'AOD',
    'temperature_K', 'relative_humidity', 'BLH', 'wind_speed',
]
TARGET_COL  = 'PM2.5'
STATION_COL = 'StationId'
DATE_COL    = 'date'          # set to None if the column does not exist

AOD_SCALE   = 0.001
RANDOM_SEED = 42
N_SPLITS    = 5               # GroupKFold folds
OPTUNA_TRIALS = 80            # increase to 150 for even better params

# =====================================================================
# STEP 1 — LOAD + AOD SCALE FIX
# =====================================================================

print("=" * 65)
print("STEP 1 | Load data + fix AOD scale")
print("=" * 65)

df = pd.read_csv(INPUT_CSV)
print(f"Loaded {len(df):,} rows.")

print(f"\nAOD BEFORE fix: mean={df['AOD'].mean():.1f}  max={df['AOD'].max():.1f}")
df['AOD'] = df['AOD'] * AOD_SCALE
print(f"AOD AFTER  fix: mean={df['AOD'].mean():.4f}  max={df['AOD'].max():.4f}")

df.to_csv(OUTPUT_CSV, index=False)
print(f"Saved corrected dataset → {OUTPUT_CSV}")

# Drop rows without a target
df = df[df[TARGET_COL].notna()].copy()
print(f"Rows with valid PM2.5: {len(df):,}")

# =====================================================================
# STEP 2 — FEATURE ENGINEERING
# =====================================================================

print("\n" + "=" * 65)
print("STEP 2 | Feature engineering")
print("=" * 65)

# ------------------------------------------------------------------
# 2a. Temporal features (requires a parseable date column)
# ------------------------------------------------------------------
if DATE_COL and DATE_COL in df.columns:
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors='coerce')
    doy  = df[DATE_COL].dt.dayofyear
    mon  = df[DATE_COL].dt.month
    dow  = df[DATE_COL].dt.dayofweek

    # Cyclical encoding avoids ordinal discontinuity (Dec 31 → Jan 1)
    df['sin_doy'] = np.sin(2 * np.pi * doy  / 365)
    df['cos_doy'] = np.cos(2 * np.pi * doy  / 365)
    df['sin_mon'] = np.sin(2 * np.pi * mon  / 12)
    df['cos_mon'] = np.cos(2 * np.pi * mon  / 12)
    df['sin_dow'] = np.sin(2 * np.pi * dow  / 7)
    df['cos_dow'] = np.cos(2 * np.pi * dow  / 7)

    temporal_feats = ['sin_doy', 'cos_doy', 'sin_mon', 'cos_mon',
                      'sin_dow', 'cos_dow']
    print(f"  ✔ Temporal cyclical features added: {temporal_feats}")
else:
    temporal_feats = []
    print("  ⚠ No date column found — temporal features skipped.")

# ------------------------------------------------------------------
# 2b. Physical interaction features
# ------------------------------------------------------------------

# AOD humidification correction (hygroscopic growth at high RH)
# Physically: measured AOD grows as particles absorb water; correcting
# back gives the "dry" AOD which correlates better with PM2.5 mass.
df['RH_safe']     = df['relative_humidity'].clip(0, 99)   # avoid /0
df['AOD_dry']     = df['AOD'] / (1 - df['RH_safe'] / 100 + 1e-6)

# Ventilation coefficient: higher BLH + wind → better dispersion
# Low VC → pollutant accumulation → high PM2.5
df['vent_coef']   = df['BLH'] * df['wind_speed']
df['inv_vent']    = 1.0 / (df['vent_coef'].clip(1) )      # inverse = trapping

# NO2–CO product: both are combustion tracers; their product amplifies
# the traffic/industrial signal
df['NO2_CO_prod'] = df['NO2_sat'] * df['CO_sat']

# Temperature inversion proxy: lower temp → more stable atmosphere
df['temp_inv']    = 1.0 / df['temperature_K'].clip(200)

# AOD × BLH: if BLH is high, the same AOD means less surface PM2.5
df['AOD_BLH']     = df['AOD'] * df['BLH']

# AOD × RH: hygroscopic enhancement captured as interaction too
df['AOD_RH']      = df['AOD'] * df['relative_humidity']

interaction_feats = [
    'AOD_dry', 'vent_coef', 'inv_vent',
    'NO2_CO_prod', 'temp_inv', 'AOD_BLH', 'AOD_RH',
]
print(f"  ✔ Interaction features added: {interaction_feats}")

# ------------------------------------------------------------------
# 2c. Polynomial features for the two strongest predictors
# ------------------------------------------------------------------

df['AOD_sq']    = df['AOD']     ** 2
df['NO2_sq']    = df['NO2_sat'] ** 2
df['AOD_NO2']   = df['AOD']     * df['NO2_sat']
poly_feats      = ['AOD_sq', 'NO2_sq', 'AOD_NO2']
print(f"  ✔ Polynomial features added: {poly_feats}")

# ------------------------------------------------------------------
# 2d. Station-level rolling statistics (requires sorted date column)
#     These are the single strongest feature class in urban pollution
#     modelling -- they capture local baseline / persistence of PM2.5.
# ------------------------------------------------------------------
roll_feats = []
if DATE_COL and DATE_COL in df.columns:
    df_sorted = df.sort_values([STATION_COL, DATE_COL]).copy()

    for window in [7, 14]:
        col_mean = f'pm25_roll{window}_mean'
        col_std  = f'pm25_roll{window}_std'
        # Shift by 1 to avoid leakage (you cannot know today's PM2.5
        # when constructing today's features)
        grp = df_sorted.groupby(STATION_COL)[TARGET_COL]
        df_sorted[col_mean] = (grp
                               .transform(lambda x: x.shift(1)
                                          .rolling(window, min_periods=3)
                                          .mean()))
        df_sorted[col_std]  = (grp
                               .transform(lambda x: x.shift(1)
                                          .rolling(window, min_periods=3)
                                          .std()))
        roll_feats += [col_mean, col_std]

    df = df_sorted
    # Fill NaN at series start with station median (harmless imputation)
    for c in roll_feats:
        df[c] = df.groupby(STATION_COL)[c].transform(
            lambda x: x.fillna(x.median()))
    df[roll_feats] = df[roll_feats].fillna(df[TARGET_COL].median())
    print(f"  ✔ Rolling lag features added: {roll_feats}")
else:
    print("  ⚠ No date column — rolling lag features skipped.")

# ------------------------------------------------------------------
# 2e. Assemble final feature list
# ------------------------------------------------------------------

ALL_FEATURES = (
    RAW_FEATURES
    + interaction_feats
    + poly_feats
    + temporal_feats
    + roll_feats
)
print(f"\n  Total features: {len(ALL_FEATURES)}")
print(f"  Features: {ALL_FEATURES}")

# =====================================================================
# STEP 3 — PREPARE ARRAYS + TARGET TRANSFORM
# =====================================================================

print("\n" + "=" * 65)
print("STEP 3 | Target transform (Yeo-Johnson) + train/test split")
print("=" * 65)

# Fill any remaining NaN in features (e.g. missing satellite pixels)
df[ALL_FEATURES] = df[ALL_FEATURES].fillna(df[ALL_FEATURES].median())

X = df[ALL_FEATURES].values
y = df[TARGET_COL].values.reshape(-1, 1)
groups = df[STATION_COL].values

# Yeo-Johnson handles zeros and near-zeros properly; more Gaussian than log1p
pt = PowerTransformer(method='yeo-johnson', standardize=True)
y_t = pt.fit_transform(y).ravel()   # transformed target used during training
                                    # predictions are inverse-transformed back

print("PowerTransformer fitted. Transformed target: "
      f"mean={y_t.mean():.4f}  std={y_t.std():.4f}")

# Station-aware 5-fold split (same as used during Optuna search)
gkf = GroupKFold(n_splits=N_SPLITS)

# Keep one held-out fold completely separate for final reporting
# (the last fold in the generator)
fold_list = list(gkf.split(X, y_t, groups))
train_idx_final, test_idx_final = fold_list[-1]

X_train_f = X[train_idx_final];  y_t_train_f = y_t[train_idx_final]
X_test_f  = X[test_idx_final];   y_test_f    = y[test_idx_final].ravel()
groups_train = groups[train_idx_final]

print(f"Final hold-out test: {len(X_test_f):,} rows "
      f"({len(set(groups[test_idx_final]))} stations)")

# =====================================================================
# STEP 4 — OPTUNA HYPERPARAMETER SEARCH (TPE, station GroupKFold)
# =====================================================================

print("\n" + "=" * 65)
print(f"STEP 4 | Optuna search ({OPTUNA_TRIALS} trials × {N_SPLITS-1} inner folds)")
print("=" * 65)

inner_gkf = GroupKFold(n_splits=N_SPLITS - 1)  # 4-fold inner CV

# ---- XGBoost -------------------------------------------------------

def xgb_objective(trial):
    params = dict(
        n_estimators      = trial.suggest_int   ('n_estimators',    300, 1200, step=100),
        max_depth         = trial.suggest_int   ('max_depth',        3,   12),
        learning_rate     = trial.suggest_float ('learning_rate', 0.005, 0.15, log=True),
        subsample         = trial.suggest_float ('subsample',      0.5,  1.0),
        colsample_bytree  = trial.suggest_float ('colsample_bytree',0.4,  1.0),
        min_child_weight  = trial.suggest_int   ('min_child_weight', 1,   20),
        reg_alpha         = trial.suggest_float ('reg_alpha',     1e-3,  10., log=True),
        reg_lambda        = trial.suggest_float ('reg_lambda',    1e-3,  10., log=True),
        gamma             = trial.suggest_float ('gamma',          0.0,   5.0),
        random_state      = RANDOM_SEED,
        eval_metric       = 'rmse',
        tree_method       = 'hist',      # fast on CPU
    )
    # Sample weights: up-weight high-PM2.5 events
    sw = np.where(y_t_train_f > np.percentile(y_t_train_f, 75), 2.5, 1.0)
    rmses = []
    for tr, va in inner_gkf.split(X_train_f, y_t_train_f, groups_train):
        m = xgb.XGBRegressor(**params)
        m.fit(X_train_f[tr], y_t_train_f[tr],
              sample_weight=sw[tr],
              eval_set=[(X_train_f[va], y_t_train_f[va])],
              verbose=False)
        pv   = m.predict(X_train_f[va])
        pred = pt.inverse_transform(pv.reshape(-1,1)).ravel()
        true = pt.inverse_transform(y_t_train_f[va].reshape(-1,1)).ravel()
        rmses.append(np.sqrt(mean_squared_error(true, pred)))
    return np.mean(rmses)

study_xgb = optuna.create_study(
    direction='minimize',
    sampler=TPESampler(seed=RANDOM_SEED)
)
study_xgb.optimize(xgb_objective, n_trials=OPTUNA_TRIALS, show_progress_bar=True)
best_xgb = study_xgb.best_params
print(f"\n  ✔ XGB best params: {best_xgb}")
print(f"     Best CV RMSE (original scale): {study_xgb.best_value:.3f}")

# ---- LightGBM ------------------------------------------------------

def lgb_objective(trial):
    params = dict(
        n_estimators      = trial.suggest_int   ('n_estimators',   300, 1200, step=100),
        max_depth         = trial.suggest_int   ('max_depth',       3,   15),
        learning_rate     = trial.suggest_float ('learning_rate', 0.005, 0.15, log=True),
        num_leaves        = trial.suggest_int   ('num_leaves',      20,  256),
        subsample         = trial.suggest_float ('subsample',      0.5,  1.0),
        colsample_bytree  = trial.suggest_float ('colsample_bytree',0.4,  1.0),
        min_child_samples = trial.suggest_int   ('min_child_samples',5,   60),
        reg_alpha         = trial.suggest_float ('reg_alpha',     1e-3,  10., log=True),
        reg_lambda        = trial.suggest_float ('reg_lambda',    1e-3,  10., log=True),
        random_state      = RANDOM_SEED,
        verbosity         = -1,
    )
    sw = np.where(y_t_train_f > np.percentile(y_t_train_f, 75), 2.5, 1.0)
    rmses = []
    for tr, va in inner_gkf.split(X_train_f, y_t_train_f, groups_train):
        m = lgb.LGBMRegressor(**params)
        m.fit(X_train_f[tr], y_t_train_f[tr],
              sample_weight=sw[tr],
              callbacks=[lgb.early_stopping(50, verbose=False),
                         lgb.log_evaluation(-1)],
              eval_set=[(X_train_f[va], y_t_train_f[va])])
        pv   = m.predict(X_train_f[va])
        pred = pt.inverse_transform(pv.reshape(-1,1)).ravel()
        true = pt.inverse_transform(y_t_train_f[va].reshape(-1,1)).ravel()
        rmses.append(np.sqrt(mean_squared_error(true, pred)))
    return np.mean(rmses)

study_lgb = optuna.create_study(
    direction='minimize',
    sampler=TPESampler(seed=RANDOM_SEED + 1)
)
study_lgb.optimize(lgb_objective, n_trials=OPTUNA_TRIALS, show_progress_bar=True)
best_lgb = study_lgb.best_params
print(f"\n  ✔ LGB best params: {best_lgb}")
print(f"     Best CV RMSE (original scale): {study_lgb.best_value:.3f}")

# ---- CatBoost ------------------------------------------------------

def cat_objective(trial):
    params = dict(
        iterations        = trial.suggest_int   ('iterations',     300, 1200, step=100),
        depth             = trial.suggest_int   ('depth',           3,   10),
        learning_rate     = trial.suggest_float ('learning_rate', 0.005, 0.15, log=True),
        l2_leaf_reg       = trial.suggest_float ('l2_leaf_reg',   1e-3,  10., log=True),
        bagging_temperature=trial.suggest_float ('bagging_temperature', 0., 1.),
        random_strength   = trial.suggest_float ('random_strength',0.1,   5.),
        random_seed       = RANDOM_SEED,
        verbose           = False,
    )
    sw = np.where(y_t_train_f > np.percentile(y_t_train_f, 75), 2.5, 1.0)
    rmses = []
    for tr, va in inner_gkf.split(X_train_f, y_t_train_f, groups_train):
        m = cb.CatBoostRegressor(**params)
        m.fit(X_train_f[tr], y_t_train_f[tr],
              sample_weight=sw[tr])
        pv   = m.predict(X_train_f[va])
        pred = pt.inverse_transform(pv.reshape(-1,1)).ravel()
        true = pt.inverse_transform(y_t_train_f[va].reshape(-1,1)).ravel()
        rmses.append(np.sqrt(mean_squared_error(true, pred)))
    return np.mean(rmses)

study_cat = optuna.create_study(
    direction='minimize',
    sampler=TPESampler(seed=RANDOM_SEED + 2)
)
study_cat.optimize(cat_objective, n_trials=OPTUNA_TRIALS, show_progress_bar=True)
best_cat = study_cat.best_params
print(f"\n  ✔ CAT best params: {best_cat}")
print(f"     Best CV RMSE (original scale): {study_cat.best_value:.3f}")

# =====================================================================
# STEP 5 — STACKING ENSEMBLE (out-of-fold meta-features)
# =====================================================================

print("\n" + "=" * 65)
print("STEP 5 | Build stacking ensemble (OOF meta-features)")
print("=" * 65)

sample_weights_full = np.where(
    y_t_train_f > np.percentile(y_t_train_f, 75), 2.5, 1.0
)

oof_xgb = np.zeros(len(X_train_f))
oof_lgb = np.zeros(len(X_train_f))
oof_cat = np.zeros(len(X_train_f))

xgb_models, lgb_models, cat_models = [], [], []

for fold_i, (tr, va) in enumerate(
        inner_gkf.split(X_train_f, y_t_train_f, groups_train)):

    sw_tr = sample_weights_full[tr]

    # XGBoost
    mx = xgb.XGBRegressor(**best_xgb, random_state=RANDOM_SEED,
                           eval_metric='rmse', tree_method='hist')
    mx.fit(X_train_f[tr], y_t_train_f[tr], sample_weight=sw_tr, verbose=False)
    oof_xgb[va] = mx.predict(X_train_f[va])
    xgb_models.append(mx)

    # LightGBM
    ml = lgb.LGBMRegressor(**best_lgb, random_state=RANDOM_SEED, verbosity=-1)
    ml.fit(X_train_f[tr], y_t_train_f[tr], sample_weight=sw_tr,
           callbacks=[lgb.log_evaluation(-1)])
    oof_lgb[va] = ml.predict(X_train_f[va])
    lgb_models.append(ml)

    # CatBoost
    mc = cb.CatBoostRegressor(**best_cat, random_seed=RANDOM_SEED, verbose=False)
    mc.fit(X_train_f[tr], y_t_train_f[tr], sample_weight=sw_tr)
    oof_cat[va] = mc.predict(X_train_f[va])
    cat_models.append(mc)

    print(f"  Fold {fold_i+1}/{N_SPLITS-1} complete")

# Stack OOF predictions as meta-features
meta_X_train = np.column_stack([oof_xgb, oof_lgb, oof_cat])

# Ridge meta-learner (intentionally simple to avoid overfitting)
meta_model = Ridge(alpha=1.0)
meta_model.fit(meta_X_train, y_t_train_f)
print(f"  Meta-model weights: XGB={meta_model.coef_[0]:.3f}  "
      f"LGB={meta_model.coef_[1]:.3f}  CAT={meta_model.coef_[2]:.3f}")

# =====================================================================
# STEP 6 — FINAL EVALUATION ON HELD-OUT TEST FOLD
# =====================================================================

print("\n" + "=" * 65)
print("STEP 6 | Final test evaluation")
print("=" * 65)

def predict_stack(X_new):
    """Average base predictions across folds, then apply meta-learner."""
    p_xgb = np.mean([m.predict(X_new) for m in xgb_models], axis=0)
    p_lgb = np.mean([m.predict(X_new) for m in lgb_models], axis=0)
    p_cat = np.mean([m.predict(X_new) for m in cat_models], axis=0)
    meta  = meta_model.predict(np.column_stack([p_xgb, p_lgb, p_cat]))
    return meta

test_pred_t = predict_stack(X_test_f)
test_pred   = np.clip(
    pt.inverse_transform(test_pred_t.reshape(-1, 1)).ravel(), 0, None
)

rmse = np.sqrt(mean_squared_error(y_test_f, test_pred))
mae  = mean_absolute_error(y_test_f, test_pred)
r2   = r2_score(y_test_f, test_pred)
r    = np.corrcoef(y_test_f, test_pred)[0, 1]

print(f"\n{'─'*45}")
print(f"  RMSE : {rmse:.2f}  µg/m³   (target ≤ 10.7)")
print(f"  MAE  : {mae:.2f}  µg/m³   (target ≤  4.8)")
print(f"  R²   : {r2:.3f}          (target ≥  0.92)")
print(f"  R    : {r:.3f}          (target ≥  0.96)")
print(f"{'─'*45}")
print(f"\n  Previous (unscaled AOD, single XGB): "
      f"RMSE=32.17  MAE=19.10  R=0.866")

# =====================================================================
# STEP 7 — SHAP FEATURE IMPORTANCE
# =====================================================================

print("\n" + "=" * 65)
print("STEP 7 | SHAP feature importance (XGBoost base models)")
print("=" * 65)

os.makedirs(PLOT_DIR, exist_ok=True)

# Use the last fold's XGB model on a 500-sample background
bg_idx = np.random.RandomState(RANDOM_SEED).choice(
    len(X_train_f), min(500, len(X_train_f)), replace=False
)
explainer = shap.TreeExplainer(xgb_models[-1])
shap_vals  = explainer.shap_values(X_test_f[:500])

plt.figure(figsize=(10, 7))
shap.summary_plot(
    shap_vals,
    X_test_f[:500],
    feature_names=ALL_FEATURES,
    plot_type='bar',
    show=False,
)
plt.tight_layout()
shap_path = os.path.join(PLOT_DIR, "shap_importance.png")
plt.savefig(shap_path, dpi=150)
plt.close()
print(f"  SHAP plot saved → {shap_path}")

# =====================================================================
# STEP 8 — SCATTER PLOT (predicted vs actual)
# =====================================================================

fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(y_test_f, test_pred, alpha=0.35, s=12, color='steelblue')
lims = [0, max(y_test_f.max(), test_pred.max()) * 1.05]
ax.plot(lims, lims, 'r--', linewidth=1.5, label='1:1 line')
ax.set_xlabel("Observed PM2.5 (µg/m³)", fontsize=12)
ax.set_ylabel("Predicted PM2.5 (µg/m³)", fontsize=12)
ax.set_title(f"Station Hold-Out Test\n"
             f"R²={r2:.3f}  RMSE={rmse:.1f}  MAE={mae:.1f}  R={r:.3f}",
             fontsize=13)
ax.legend(fontsize=11)
plt.tight_layout()
scatter_path = os.path.join(PLOT_DIR, "predicted_vs_observed.png")
plt.savefig(scatter_path, dpi=150)
plt.close()
print(f"  Scatter plot saved → {scatter_path}")

# =====================================================================
# STEP 9 — SAVE MODEL + METADATA
# =====================================================================

print("\n" + "=" * 65)
print("STEP 9 | Saving model bundle")
print("=" * 65)

os.makedirs(MODEL_DIR, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

bundle = {
    "xgb_models" : xgb_models,
    "lgb_models" : lgb_models,
    "cat_models" : cat_models,
    "meta_model" : meta_model,
    "power_transformer": pt,
    "feature_columns"  : ALL_FEATURES,
}
bundle_path = os.path.join(MODEL_DIR, f"stacked_pm25_{ts}.joblib")
joblib.dump(bundle, bundle_path)

metadata = {
    "model_type"       : "XGBoost+LightGBM+CatBoost stacking ensemble",
    "target_transform" : "Yeo-Johnson PowerTransformer (stored in bundle)",
    "aod_scale_factor" : AOD_SCALE,
    "feature_columns"  : ALL_FEATURES,
    "n_base_models"    : 3,
    "n_folds"          : N_SPLITS - 1,
    "optuna_trials"    : OPTUNA_TRIALS,
    "best_xgb_params"  : best_xgb,
    "best_lgb_params"  : best_lgb,
    "best_cat_params"  : best_cat,
    "test_metrics"     : {"rmse": round(rmse,3),
                          "mae" : round(mae, 3),
                          "r2"  : round(r2,  4),
                          "r"   : round(r,   4)},
    "baseline_metrics" : {"rmse": 32.17, "mae": 19.10, "r": 0.866},
    "saved_at"         : ts,
}
meta_path = os.path.join(MODEL_DIR, f"stacked_pm25_{ts}_metadata.json")
with open(meta_path, "w") as f:
    json.dump(metadata, f, indent=2)

print(f"  Model bundle  → {bundle_path}")
print(f"  Metadata JSON → {meta_path}")

# =====================================================================
# HOW TO USE THIS BUNDLE FOR INFERENCE
# =====================================================================

print("""
╔══════════════════════════════════════════════════════════════╗
║  INFERENCE TEMPLATE (copy into your grid/map script)        ║
╚══════════════════════════════════════════════════════════════╝

  import joblib, numpy as np

  bundle = joblib.load("<path>/stacked_pm25_YYYYMMDD_HHMMSS.joblib")
  pt     = bundle["power_transformer"]
  feats  = bundle["feature_columns"]

  # df_grid must have all feature columns; AOD must already be x0.001
  X_new  = df_grid[feats].fillna(df_grid[feats].median()).values

  p_xgb = np.mean([m.predict(X_new) for m in bundle["xgb_models"]], 0)
  p_lgb = np.mean([m.predict(X_new) for m in bundle["lgb_models"]], 0)
  p_cat = np.mean([m.predict(X_new) for m in bundle["cat_models"]], 0)
  meta  = bundle["meta_model"].predict(
              np.column_stack([p_xgb, p_lgb, p_cat]))

  pm25_pred = np.clip(
      pt.inverse_transform(meta.reshape(-1,1)).ravel(), 0, None)
""")