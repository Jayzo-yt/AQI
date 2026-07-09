import pandas as pd

ground = pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\archive\station_day.csv")  # the FULL 108,035-row file, not filtered_station_day.csv — confirm this is the right path/filename
sat_2019 = pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\output\satellite_era5_extracted_2019.csv")
sat_2020 = pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\output\satellite_era5_extracted_2020.csv")
satellite = pd.concat([sat_2019, sat_2020], ignore_index=True)

# Normalize dates the same way on both sides — check your actual ground date format first
print("Ground date sample:", ground['Date'].head(3).tolist())
print("Satellite date sample:", satellite['Date'].head(3).tolist())

ground['Date'] = pd.to_datetime(ground['Date']).dt.strftime('%Y-%m-%d')
satellite['Date'] = pd.to_datetime(satellite['Date']).dt.strftime('%Y-%m-%d')

ground['StationId'] = ground['StationId'].astype(str).str.strip().str.upper()
satellite['StationId'] = satellite['StationId'].astype(str).str.strip().str.upper()

final_dataset = pd.merge(ground, satellite, on=['StationId', 'Date'], how='inner')

print("\nGround rows:", len(ground))
print("Satellite rows:", len(satellite))
print("Final rows:", len(final_dataset))
print("Unique stations in final:", final_dataset['StationId'].nunique())
print("Date range:", final_dataset['Date'].min(), "to", final_dataset['Date'].max())
print("Missing PM2.5:", final_dataset['PM2.5'].isna().sum())

final_dataset.to_csv(r"C:\Users\Jayyanth\Desktop\ISRO\output\final_dataset_v2.csv", index=False)
print("\nSaved as final_dataset_v2.csv")