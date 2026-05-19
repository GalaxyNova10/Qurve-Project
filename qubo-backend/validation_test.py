#!/usr/bin/env python3
"""
Qurve AI Backend Startup Validation Script
Tests FastAPI startup, solver registry, and all imports
"""

import sys
import time
import logging

# Configure logging for validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== BACKEND STARTUP VALIDATION ===')
start_time = time.perf_counter()

try:
    # Test FastAPI startup
    print('Testing FastAPI import and initialization...')
    import sys
    sys.path.append('.')
    from main import app
    print('✅ FastAPI import successful')
    
    # Test solver registry
    print('Testing solver registry...')
    from qubo_backend.solvers.registry import available_solvers
    from qubo_backend.config import get_settings
    settings = get_settings()
    solvers = available_solvers(settings)
    print(f'✅ Solver registry initialized: {len(solvers)} solvers')
    for solver in solvers:
        print(f'  - {solver["id"]}: {solver["status"]}')
    
    # Test Braket imports
    print('Testing Braket imports...')
    try:
        from braket.circuits import Circuit, FreeParameter
        from braket.devices import LocalSimulator
        print('✅ Braket imports successful')
    except Exception as e:
        print(f'❌ Braket import failed: {e}')
    
    # Test Qiskit imports
    print('Testing Qiskit imports...')
    try:
        from qiskit_optimization.algorithms import MinimumEigenOptimizer
        from qiskit_optimization.converters import QuadraticProgramToQubo
        from qiskit_aer import AerSimulator
        print('✅ Qiskit imports successful')
    except Exception as e:
        print(f'❌ Qiskit import failed: {e}')
    
    # Test Neal initialization
    print('Testing Neal initialization...')
    try:
        from qubo_backend.optimization.dwave_sa_solver import NealSASolver
        solver = NealSASolver()
        print('✅ Neal initialization successful')
    except Exception as e:
        print(f'❌ Neal initialization failed: {e}')
    
    startup_time = (time.perf_counter() - start_time) * 1000
    print(f'✅ Backend startup completed in {startup_time:.2f}ms')
    
except Exception as e:
    print(f'❌ Backend startup failed: {e}')
    sys.exit(1)
