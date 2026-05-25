from fastapi import FastAPI
from pydantic import BaseModel
from braket.circuits import Circuit
from braket.devices import LocalSimulator
import time
import json

app = FastAPI()

class BraketRequest(BaseModel):
    shots: int = 100

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "braket-worker"
    }

@app.post("/run")
def run_braket(req: BraketRequest):
    try:
        start = time.perf_counter()
        
        device = LocalSimulator()
        circuit = Circuit().h(0).cnot(0, 1)
        task = device.run(circuit, shots=req.shots)
        result = task.result()
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Debug: print the result type and shape
        print(f"Result type: {type(result.measurements)}")
        print(f"Result shape: {result.measurements.shape}")
        print(f"Result dtype: {result.measurements.dtype}")
        
        # Convert numpy array to list properly
        measurements_list = result.measurements.tolist()
        
        return {
            "status": "success",
            "measurements": measurements_list,
            "execution_time_ms": elapsed_ms,
            "backend": "amazon_braket_local"
        }
        
    except Exception as e:
        print(f"Error in run_braket: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": str(e),
            "error_type": str(type(e)),
            "backend": "amazon_braket_local"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8011)
