import ee
try:
    print("Initializing Earth Engine...")
    ee.Initialize(project='aqi-data-500013')
    print("Earth Engine ready.")
except Exception as e:
    print("Error:", e)
