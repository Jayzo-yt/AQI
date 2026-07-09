import asyncio
import sys
import math
sys.path.append('backend')
from app import get_stations, startup_event

async def test():
    await startup_event()
    print("Startup done")
    res = await get_stations()
    for s in res['stations']:
        for k, v in s.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                print(f"Invalid float found in key {k} for station {s.get('id', 'unknown')}: {v}")

asyncio.run(test())
