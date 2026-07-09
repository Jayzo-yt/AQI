import sys
sys.path.append(r"C:\Users\Jayyanth\Desktop\ISRO\backend")
from app import _build_aqi_map_png, startup_event
import asyncio

async def test():
    await startup_event()
    _build_aqi_map_png("2020-01-15", "fast")

asyncio.run(test())
