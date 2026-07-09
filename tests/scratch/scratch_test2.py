import asyncio
import sys
import json
sys.path.append('backend')
from app import get_stations, startup_event

async def test():
    await startup_event()
    print("Startup done")
    try:
        res = await get_stations()
        json.dumps(res)
        print("JSON serialization successful")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
