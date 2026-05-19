import asyncio
import httpx
import uvicorn
import multiprocessing
import time
import sys

def run_server():
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

async def test_endpoints():
    print("Starting server...")
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    
    # Wait for server to start
    time.sleep(3)
    
    endpoints = [
        ("GET", "http://localhost:8000/health"),
        ("GET", "http://localhost:8000/api/benchmarks"),
        ("GET", "http://localhost:8000/api/monitoring"),
    ]
    
    async with httpx.AsyncClient() as client:
        for method, url in endpoints:
            try:
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    response = await client.post(url, json={"test": "data"})
                print(f"{method} {url} -> Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"Failed to connect to {url}: {e}")
                
    server_process.terminate()
    server_process.join()

if __name__ == "__main__":
    asyncio.run(test_endpoints())
