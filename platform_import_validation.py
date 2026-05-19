#!/usr/bin/env python3
"""
QURVE AI - Platform Import Validation
Validate all platform imports and generate failure report.
"""

import os
import sys
import time
import logging

# Add qubo-backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'qubo-backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_platform_imports():
    """Validate all platform imports."""
    import_results = {}
    
    # Test imports
    test_imports = [
        'qubo_backend.cost.cost_governance',
        'qubo_backend.productization.user_quota_management',
        'qubo_backend.telemetry.structured_telemetry',
        'qubo_backend.storage.execution_storage',
        'qubo_backend.storage.replay_service',
        'qubo_backend.qpu.qpu_persistence',
        'qubo_backend.operations.audit_trail_system',
        'qubo_backend.monitoring.monitoring_service',
        'qubo_backend.qpu.qpu_fallback_chains',
        'qubo_backend.optimization.braket_solver'
    ]
    
    for import_name in test_imports:
        try:
            __import__(import_name)
            import_results[import_name] = {'success': True, 'error': None}
        except Exception as e:
            import_results[import_name] = {'success': False, 'error': str(e)}
    
    # Generate report
    successful = sum(1 for r in import_results.values() if r['success'])
    total = len(import_results)
    
    print(f"Import Validation: {successful}/{total}")
    for name, result in import_results.items():
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {name}")
        if not result['success']:
            print(f"    Error: {result['error']}")
    
    return successful == total


if __name__ == "__main__":
    success = validate_platform_imports()
    sys.exit(0 if success else 1)
