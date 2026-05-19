#!/usr/bin/env python3
"""
Debug script to isolate the exact source of the type validation error
"""

import sys
import numpy as np
sys.path.append('.')

from qubo_backend.optimization.portfolio import verify_constraints

# Test with exact same data that's failing
weights = np.array([0.0, 0.0, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333], dtype=float)
sectors = ['tech', 'tech', 'tech', 'tech', 'tech']
cardinality = 3
max_sector_exposure = 0.3

print("=== TYPE VALIDATION DEBUG ===")
print(f"weights: {weights}")
print(f"weights type: {type(weights)}")
print(f"weights dtype: {weights.dtype}")
print(f"sectors: {sectors}")
print(f"sectors type: {type(sectors)}")
print(f"cardinality: {cardinality}")
print(f"cardinality type: {type(cardinality)}")
print(f"max_sector_exposure: {max_sector_exposure}")
print(f"max_sector_exposure type: {type(max_sector_exposure)}")

try:
    result = verify_constraints(
        weights,
        sectors,
        cardinality,
        max_sector_exposure,
        sector_tolerance=1e-5,
    )
    print("✅ SUCCESS: verify_constraints completed")
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
