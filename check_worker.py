import sys
sys.path.insert(0, 'D:/QUBO/qubo-braket-worker')
import httpx
import asyncio

async def check():
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get('http://127.0.0.1:8011/health', timeout=3.0)
            print(f'Worker: {r.status_code} {r.json()}')
    except Exception as e:
        print(f'Worker DOWN: {e}')

asyncio.run(check())
