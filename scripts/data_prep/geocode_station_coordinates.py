import time

import pandas as pd
import requests
from tqdm import tqdm

API_KEY = "4fdb272bd5df4c1096955eacb0cb4be7"

INPUT_FILE = r"C:\Users\Jayyanth\Desktop\ISRO\archive\stations.csv"
OUTPUT_FILE = r"C:\Users\Jayyanth\Desktop\ISRO\archive\stations_with_coordinates.csv"


def get_coordinates(address: str):
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": address,
        "key": API_KEY,
        "limit": 1,
        "countrycode": "in",
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            lat = data["results"][0]["geometry"]["lat"]
            lng = data["results"][0]["geometry"]["lng"]
            return lat, lng

    return None, None


def main() -> None:
    df = pd.read_csv(INPUT_FILE)

    df["Full_Address"] = df["StationName"] + ", " + df["City"] + ", " + df["State"] + ", India"
    df["Latitude"] = None
    df["Longitude"] = None

    print("Fetching coordinates...")

    for index, row in tqdm(df.iterrows(), total=len(df)):
        lat, lng = get_coordinates(row["Full_Address"])
        df.at[index, "Latitude"] = lat
        df.at[index, "Longitude"] = lng
        time.sleep(1)

    df.drop(columns=["Full_Address"], inplace=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("Done! File saved as:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
