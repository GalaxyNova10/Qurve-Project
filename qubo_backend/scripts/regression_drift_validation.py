import json
import os
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class RegressionDriftValidator:
    """
    Detects scientific and operational drift by comparing current results against goldens.
    """
    
    def __init__(self, goldens_dir: str):
        self.goldens_dir = goldens_dir

    def load_golden(self, assets: int, solver: str) -> Dict[str, Any]:
        path = os.path.join(self.goldens_dir, f"golden_{assets}_{solver}.json")
        if not os.path.exists(path):
            return {}
        with open(path, 'r') as f:
            return json.load(f)

    def detect_drift(self, current_result: Dict[str, Any], golden: Dict[str, Any]) -> Dict[str, Any]:
        if not golden:
            return {"status": "NO_GOLDEN", "message": "No baseline found for comparison"}
            
        drift = {
            "latency_drift": 0.0,
            "energy_drift": 0.0,
            "sparsity_drift": 0.0,
            "verdict": "STABLE"
        }
        
        # 1. Latency Drift (Operational)
        cur_latency = current_result.get("solve_time_ms", 0)
        gold_latency = golden.get("solve_time_ms", 1)
        drift["latency_drift"] = (cur_latency - gold_latency) / gold_latency
        
        if drift["latency_drift"] > 0.5: # 50% slower
            drift["verdict"] = "DEGRADED_OPERATIONAL"
            
        # 2. Energy/Approximation Drift (Scientific)
        cur_energy = current_result.get("energy", 0)
        gold_energy = golden.get("energy", 0)
        if gold_energy != 0:
            drift["energy_drift"] = abs(cur_energy - gold_energy) / abs(gold_energy)
            
        if drift["energy_drift"] > 0.05: # 5% quality loss
            drift["verdict"] = "DEGRADED_SCIENTIFIC"
            
        # 3. Sparsity Drift
        cur_sparsity = current_result.get("allocation_sparsity", 0)
        gold_sparsity = golden.get("allocation_sparsity", 0)
        drift["sparsity_drift"] = cur_sparsity - gold_sparsity
        
        return drift

def validate_benchmark_drift(results: List[Dict[str, Any]], goldens_dir: str):
    validator = RegressionDriftValidator(goldens_dir)
    assets = len(results[0].get("weights", [])) if results else 0
    
    drifts = {}
    for r in results:
        solver = r["solver"]
        golden = validator.load_golden(assets, solver)
        drifts[solver] = validator.detect_drift(r, golden)
        
    return drifts
