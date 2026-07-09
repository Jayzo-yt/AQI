import pandas as pd
final = pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\output\final_dataset_v2.csv")
ground_stations = set(pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\archive\station_day.csv")['StationId'].unique())
final_stations = set(final['StationId'].unique())
print("Stations dropped entirely:", ground_stations - final_stations)