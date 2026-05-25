import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GroundTruthValidator:
    """
    Validates optimization results against analytically known optimal solutions.
    Essential for verifying decode_fidelity and energy reconstruction before freezing baselines.
    """
    
    # Tiny Deterministic Case: 3 Assets
    # Analytical solution: Equal weights (0.33, 0.33, 0.33) if returns and variance are identical
    CASE_3_ASSETS = {
        "mu": np.array([0.1, 0.1, 0.1]),
        "sigma": np.eye(3) * 0.01,
        "optimal_weights": np.array([1/3, 1/3, 1/3]),
        "optimal_energy": -0.09888888, # risk_tol=0.5: 0.5*(0.33^2*0.01*3) - 0.1 = 0.5*(0.0011) - 0.1 = 0.00055 - 0.1 = -0.09945
    }

    def __init__(self, tolerance: float = 1e-4):
        self.tolerance = tolerance

    def validate_case_3(self, weights: np.ndarray, reported_energy: float) -> Dict[str, Any]:
        """
        Verify the 3-asset deterministic case.
        """
        expected_w = self.CASE_3_ASSETS["optimal_weights"]
        
        # 1. Weight deviation
        weight_diff = np.abs(weights - expected_w)
        weights_ok = np.all(weight_diff < self.tolerance)
        
        # 2. Energy Verification
        # recompute manually: risk_tol * (w.T @ sigma @ w) - return
        mu = self.CASE_3_ASSETS["mu"]
        sigma = self.CASE_3_ASSETS["sigma"]
        recomputed_energy = 0.5 * (weights @ sigma @ weights) - np.dot(weights, mu)
        
        energy_match = abs(recomputed_energy - reported_energy) < self.tolerance
        
        # 3. Approximation Ratio
        # approx = recomputed_energy / optimal_energy (since energy is negative, 1.0 is perfect)
        # For minimization, ratio = optimal_energy / recomputed_energy
        approx_ratio = self.CASE_3_ASSETS["optimal_energy"] / recomputed_energy if recomputed_energy != 0 else 0
        
        return {
            "case": "3_assets_deterministic",
            "weights_match": bool(weights_ok),
            "energy_match": bool(energy_match),
            "recomputed_energy": float(recomputed_energy),
            "reported_energy": float(reported_energy),
            "approximation_ratio": float(approx_ratio),
            "weight_diff_max": float(np.max(weight_diff))
        }

def run_ground_truth_audit(solver_result: Dict[str, Any]):
    """
    Helper to run ground truth audit on a specific result.
    """
    if solver_result.get("status") != "success":
        return None
        
    validator = GroundTruthValidator()
    weights = np.array(solver_result.get("weights", []))
    energy = solver_result.get("energy", 0)
    
    if len(weights) == 3:
        return validator.validate_case_3(weights, energy)
    
    return None
