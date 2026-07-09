import asyncio
import sys
sys.path.append('backend')
from app import get_stations, startup_event

async def test():
    await startup_event()
    print("Startup done")
    try:
        res = await get_stations()
        print(len(res['stations']))
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
