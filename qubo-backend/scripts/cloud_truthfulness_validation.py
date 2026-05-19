from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class CloudTruthfulnessAuditor:
    """
    Audits the platform's honesty regarding cloud execution.
    Ensures that 'Cloud' claims are backed by physical evidence (ARNs).
    """
    
    def audit_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        solver = result.get("solver", "unknown")
        origin = result.get("execution_origin")
        task_arn = result.get("task_arn")
        device_arn = result.get("device_arn")
        provenance = result.get("execution_provenance", {})
        
        is_cloud_solver = solver.startswith("AWS_BRAKET") and solver != "AWS_BRAKET_LOCAL"
        
        audit = {
            "solver": solver,
            "origin_honest": True,
            "arn_present": bool(task_arn or device_arn),
            "provenance_match": True,
            "verdict": "PASS"
        }
        
        # 1. Origin Honesty: If origin is 'cloud', we MUST have proof.
        if origin == "cloud" and not audit["arn_present"]:
            audit["origin_honest"] = False
            audit["verdict"] = "DISHONEST_CLOUD_CLAIM"
            logger.error(f"[TRUTHFULNESS_AUDIT] {solver} claims CLOUD but lacks ARN.")
            
        # 2. Local-as-Cloud Detection: If solver is cloud but origin is local.
        if is_cloud_solver and origin == "local":
            if not result.get("fallback_triggered"):
                audit["origin_honest"] = False
                audit["verdict"] = "SILENT_LOCAL_SUBSTITUTION"
                logger.error(f"[TRUTHFULNESS_AUDIT] {solver} ran LOCAL without fallback flag.")

        # 3. Provenance Match
        if provenance:
            if provenance.get("actual_solver") != result.get("actual_solver"):
                audit["provenance_match"] = False
                audit["verdict"] = "PROVENANCE_MISMATCH"
                
        return audit

def run_truthfulness_suite(benchmark_results: List[Dict[str, Any]]):
    auditor = CloudTruthfulnessAuditor()
    audits = [auditor.audit_result(r) for r in benchmark_results]
    
    failed = [a for a in audits if a["verdict"] != "PASS"]
    
    return {
        "passed": len(audits) - len(failed),
        "failed": len(failed),
        "audit_logs": audits
    }
