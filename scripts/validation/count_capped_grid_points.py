import pandas as pd
df = pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\output\grid\grid_with_predictions_2020-01-15.csv")
print("Capped points:", df['aqi_capped'].sum())