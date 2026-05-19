import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class PortfolioCorrectnessValidator:
    """
    Validates the mathematical and financial correctness of an optimization result.
    This is an independent verification layer that runs outside the solver.
    """
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance

    def validate_result(self, 
                        weights: np.ndarray, 
                        mu: np.ndarray, 
                        sigma: np.ndarray, 
                        request: Any, 
                        reported_energy: float) -> Dict[str, Any]:
        """
        Perform comprehensive correctness validation on a single portfolio result.
        """
        validation = {
            "all_valid": True,
            "constraints": self.validate_constraints(weights, request),
            "objective": self.validate_objective(weights, mu, sigma, request, reported_energy),
            "telemetry": {}
        }
        
        validation["all_valid"] = (
            validation["constraints"]["all_satisfied"] and 
            validation["objective"]["energy_match"]
        )
        
        return validation

    def validate_constraints(self, weights: np.ndarray, request: Any) -> Dict[str, Any]:
        """
        Independent constraint verification.
        """
        w = np.asarray(weights)
        
        # 1. Budget Constraint: sum(weights) == 1
        budget_sum = float(np.sum(w))
        budget_ok = abs(budget_sum - 1.0) < self.tolerance
        
        # 2. Cardinality Constraint: count(weights > 0) == request.cardinality
        active_assets = int(np.sum(w > 1e-6))
        cardinality_ok = active_assets == request.cardinality
        
        # 3. Non-negativity and bounds
        bounds_ok = np.all(w >= -self.tolerance) and np.all(w <= 1.0 + self.tolerance)
        
        # 4. Sector constraints
        sector_violations = []
        if hasattr(request, 'sectors') and hasattr(request, 'max_sector_exposure'):
            sectors = request.sectors
            limit = request.max_sector_exposure
            
            unique_sectors = set(sectors)
            for s in unique_sectors:
                sector_weight = sum(w[i] for i, sector in enumerate(sectors) if sector == s)
                if sector_weight > limit + self.tolerance:
                    sector_violations.append({
                        "sector": s,
                        "weight": float(sector_weight),
                        "limit": limit
                    })

        all_satisfied = budget_ok and cardinality_ok and bounds_ok and not sector_violations
        
        return {
            "all_satisfied": all_satisfied,
            "budget_sum": budget_sum,
            "budget_ok": budget_ok,
            "active_assets": active_assets,
            "cardinality_ok": cardinality_ok,
            "bounds_ok": bounds_ok,
            "sector_violations": sector_violations
        }

    def validate_objective(self, 
                           weights: np.ndarray, 
                           mu: np.ndarray, 
                           sigma: np.ndarray, 
                           request: Any, 
                           reported_energy: float) -> Dict[str, Any]:
        """
        Recompute objective function (Energy) and compare with reported energy.
        Objective: risk_tolerance * variance - expected_return
        """
        w = np.asarray(weights)
        
        # Recompute Return
        expected_return = float(np.dot(w, mu))
        
        # Recompute Variance
        variance = float(w @ sigma @ w)
        
        # Recompute Total Objective
        risk_tolerance = getattr(request, 'risk_tolerance', 0.5)
        recomputed_energy = risk_tolerance * variance - expected_return
        
        # Comparison
        energy_diff = abs(recomputed_energy - reported_energy)
        energy_match = energy_diff < self.tolerance
        
        if not energy_match:
            logger.warning(f"[OBJECTIVE_MISMATCH] diff={energy_diff:.8f} recomputed={recomputed_energy:.8f} reported={reported_energy:.8f}")

        return {
            "recomputed_energy": recomputed_energy,
            "reported_energy": reported_energy,
            "energy_diff": energy_diff,
            "energy_match": energy_match,
            "expected_return": expected_return,
            "variance": variance
        }

def run_correctness_audit(result_dict: Dict[str, Any], request: Any, mu: np.ndarray, sigma: np.ndarray):
    """
    Helper to run audit on a benchmark result dictionary.
    """
    if result_dict.get("status") != "success" or result_dict.get("energy") is None:
        return None
        
    validator = PortfolioCorrectnessValidator()
    weights = np.array(result_dict.get("weights", []))
    
    if len(weights) == 0:
        return None
        
    return validator.validate_result(
        weights, 
        mu, 
        sigma, 
        request, 
        result_dict["energy"]
    )
