"""
Extract Training Data Medians for Proper Imputation
"""
import pandas as pd
import numpy as np

# Load your MERGED training data (the file used to train the model)
# Replace this path with your actual merged training dataset
TRAINING_DATA = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\final_dataset_v3.csv"

df_train = pd.read_csv(TRAINING_DATA)

FEATURES = [
    'NO2_sat',
    'SO2_sat',
    'CO_sat',
    'O3_sat',
    'HCHO_sat',
    'AOD',
    'temperature_K',
    'relative_humidity',
    'BLH',
    'wind_speed'
]

print("="*70)
print("TRAINING DATA STATISTICS")
print("="*70)

print("\n📊 Feature Medians (USE THESE FOR IMPUTATION):\n")
print("TRAINING_MEDIANS = {")
for feat in FEATURES:
    if feat in df_train.columns:
        median_val = df_train[feat].median()
        print(f"    '{feat}': {median_val:.6f},")
    else:
        print(f"    '{feat}': None,  # NOT FOUND")
print("}")

print("\n📊 Feature Ranges (for reference):\n")
for feat in FEATURES:
    if feat in df_train.columns:
        print(f"{feat:20s}: min={df_train[feat].min():10.4f}, "
              f"median={df_train[feat].median():10.4f}, "
              f"max={df_train[feat].max():10.4f}")

print("\n" + "="*70)