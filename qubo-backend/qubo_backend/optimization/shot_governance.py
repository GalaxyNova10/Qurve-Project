from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

class ShotPolicyManager:
    """
    Phase 2: Strict Shot Governance.
    Eliminates hidden shot mutation, adaptive retry scaling, and ensures shot immutability.
    """
    DEVICE_LIMITS = {
        "sv1": 2048,
        "tn1": 1024,
        "dm1": 2048,
        "local": 1024,
        "qpu": 10000,
    }

    @staticmethod
    def validate_and_lock_shots(solver_id: str, requested_shots: int) -> int:
        """
        Locks the requested shots to the device limits without inflating them.
        Returns the exact, immutable shot count that MUST be used.
        """
        device_key = "local"
        if "sv1" in solver_id.lower():
            device_key = "sv1"
        elif "tn1" in solver_id.lower():
            device_key = "tn1"
        elif "dm1" in solver_id.lower():
            device_key = "dm1"
        
        limit = ShotPolicyManager.DEVICE_LIMITS.get(device_key, 1024)
        
        # We strictly cap the shots to the limit. We DO NOT inflate them.
        final_shots = min(requested_shots, limit)
        
        logger.info(
            f"[SHOT_IMMUTABILITY_AUDIT] solver={solver_id} "
            f"requested_shots={requested_shots} "
            f"device_limit={limit} "
            f"final_immutable_shots={final_shots}"
        )
        
        return final_shots
