import pandas as pd

original_ground = pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\archive\station_day.csv")
ground_stations = set(original_ground['StationId'].unique())
coord_stations = set(pd.read_csv(r"C:\Users\Jayyanth\Desktop\ISRO\archive\stations_with_coordinates.csv"  )['StationId'].unique())

print("Stations in ground data:", len(ground_stations))
print("Stations in coordinates file:", len(coord_stations))
print("Overlap (usable for merge):", len(ground_stations & coord_stations))
print("In ground but missing coordinates:", len(ground_stations - coord_stations))
print("In coordinates but no ground data:", len(coord_stations - ground_stations))