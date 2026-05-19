import asyncio
import httpx
import uvicorn
import multiprocessing
import time
import sys
import json

def run_server():
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

async def test_endpoints():
    print("Starting server...")
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    
    # Wait for server to start
    print("Waiting for server to boot...")
    for _ in range(10):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://127.0.0.1:8000/health")
                if resp.status_code == 200:
                    print("Server is up!")
                    break
        except:
            time.sleep(1)
            
    endpoints = [
        ("GET", "http://127.0.0.1:8000/health"),
        ("GET", "http://127.0.0.1:8000/api/benchmarks"),
        ("GET", "http://127.0.0.1:8000/api/monitoring"),
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Test basic GETs
        for method, url in endpoints:
            try:
                if method == "GET":
                    response = await client.get(url)
                print(f"{method} {url} -> Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"Failed to connect to {url}: {e}")
                
        # 2. Test REAL BENCHMARK Execution
        print("\n--- Executing REAL Benchmark through API ---")
        payload = {
            "requested_solver": "braket",
            "cardinality": 2,
            "max_sector_exposure": 0.5,
            "risk_tolerance": 0.5,
            "binary_bits": 2,
            "trajectories": 10,
            "num_assets": 2
        }
        url = "http://127.0.0.1:8000/api/benchmarks"
        try:
            print(f"Submitting payload to {url}: {json.dumps(payload)}")
            # Need to provide auth or does it mock?
            # Looking at routes.py:
            # current_user: auth.User = Depends(auth.get_current_active_user)
            # auth.py expects token. But since this is a local test, maybe auth is relaxed? Let's pass a dummy token.
            headers = {"Authorization": "Bearer demo_token"} 
            # In qubo-backend, local debugging might accept demo_token or anything. Let's see.
            
            response = await client.post(url, json=payload, headers=headers)
            print(f"POST {url} -> Status: {response.status_code}")
            print(f"Response snippet: {response.text[:500]}")
            if response.status_code == 200:
                print("AWS Braket execution via API successful!")
        except Exception as e:
            print(f"Failed POST {url}: {e}")
                
    server_process.terminate()
    server_process.join()

if __name__ == "__main__":
    asyncio.run(test_endpoints())
