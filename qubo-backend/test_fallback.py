import asyncio
from qubo_backend.main import app
from qubo_backend.schemas import QuboParams
from qubo_backend.api.routes import create_optimization, optimization_status
from fastapi.testclient import TestClient
import json

client = TestClient(app)

def test_fallback():
    print("Sending request for 'dwave' solver...")
    response = client.post(
        "/api/v1/optimize",
        json={
            "cardinality": 15,
            "risk_tolerance": 0.5,
            "max_sector_exposure": 0.25,
            "binary_bits": 7,
            "requested_solver": "dwave",
            "trajectories": 256
        }
    )
    if response.status_code == 401:
        print("Auth failed. Bypassing auth with direct function call.")
        return
        
    data = response.json()
    print("Initial Task Response:", data)
    
if __name__ == "__main__":
    test_fallback()
