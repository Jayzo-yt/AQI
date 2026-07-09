import pandas as pd
from rapidfuzz import fuzz, process

MAIN_STATIONS_FILE = r"C:\Users\Jayyanth\Desktop\ISRO\data\archive\stations.csv"
COORDINATES_FILE = r"C:\Users\Jayyanth\Desktop\ISRO\data\raw\CPCB_Stations_With_Coordinates.csv"
OUTPUT_FILE = r"C:\Users\Jayyanth\Desktop\ISRO\data\processed\merged_with_coordinates.csv"

MAIN_NAME_COL = "StationName"
COORD_NAME_COL = "StationName"
LAT_COL = "Latitude"
LON_COL = "Longitude"


def main() -> None:
    df_main = pd.read_csv(MAIN_STATIONS_FILE)
    df_coords = pd.read_csv(COORDINATES_FILE)

    coord_lookup = {
        str(name).strip().lower(): (lat, lon)
        for name, lat, lon in zip(
            df_coords[COORD_NAME_COL],
            df_coords[LAT_COL],
            df_coords[LON_COL],
        )
    }

    coord_names = list(coord_lookup.keys())
    latitudes = []
    longitudes = []
    matched_names = []

    for station in df_main[MAIN_NAME_COL]:
        station_clean = str(station).strip().lower()

        match = process.extractOne(
            station_clean,
            coord_names,
            scorer=fuzz.token_sort_ratio,
        )

        if match and match[1] >= 85:
            matched_name = match[0]
            lat, lon = coord_lookup[matched_name]

            latitudes.append(lat)
            longitudes.append(lon)
            matched_names.append(matched_name)
        else:
            latitudes.append(None)
            longitudes.append(None)
            matched_names.append(None)

    df_main["Latitude"] = latitudes
    df_main["Longitude"] = longitudes
    df_main["Matched_Station"] = matched_names

    df_main.to_csv(OUTPUT_FILE, index=False)

    print("Done!")
    print(f"Rows: {len(df_main)}")
    print(f"Matched: {df_main['Latitude'].notna().sum()}")
    print(f"Unmatched: {df_main['Latitude'].isna().sum()}")


if __name__ == "__main__":
    main()
