#!/usr/bin/env python3
"""
Test script for Braket adapter validation
Tests safe circuit execution and adapter functionality
"""

import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add current directory to path
sys.path.append('.')

from qubo_backend.optimization.braket_adapter import get_braket_adapter, is_braket_available

async def test_braket_adapter():
    """Test Braket adapter functionality."""
    
    print("=== BRAKET ADAPTER VALIDATION ===")
    
    # Test 1: Basic availability check
    print("\n1. Testing Braket availability...")
    adapter = get_braket_adapter()
    status = adapter.check_availability()
    
    print(f"   Available: {status.available}")
    print(f"   SDK Version: {status.sdk_version}")
    print(f"   Simulator Available: {status.simulator_available}")
    print(f"   Pydantic Compatible: {status.pydantic_compatible}")
    print(f"   Error: {status.error}")
    
    # Test 2: Environment validation
    print("\n2. Testing environment validation...")
    env_status = adapter.validate_environment()
    
    for key, value in env_status.items():
        print(f"   {key}: {value}")
    
    # Test 3: Circuit creation
    print("\n3. Testing circuit creation...")
    circuit = adapter.create_circuit(2)
    
    if circuit:
        print("   ✅ Circuit created successfully")
    else:
        print("   ❌ Circuit creation failed")
        return
    
    # Test 4: Circuit execution
    print("\n4. Testing circuit execution...")
    if status.simulator_available:
        execution_result = await adapter.run_local_task(circuit, shots=10)
        
        if execution_result and execution_result.get('success'):
            print(f"   ✅ Circuit execution successful")
            print(f"   Execution time: {execution_result.get('execution_time_ms', 0):.2f}ms")
            print(f"   Measurement counts: {execution_result.get('measurement_counts', {})}")
        else:
            print(f"   ❌ Circuit execution failed: {execution_result.get('error') if execution_result else 'Unknown error'}")
    else:
        print("   ⚠️  Skipping execution test (simulator not available)")
    
    # Test 5: Safe execution context
    print("\n5. Testing safe execution context...")
    try:
        with adapter.safe_execution_context():
            # This should not crash even if Braket fails
            circuit = adapter.create_circuit(2)
            if circuit:
                print("   ✅ Safe execution context working")
            else:
                print("   ⚠️  Safe execution context: circuit creation failed")
    except Exception as e:
        print(f"   ❌ Safe execution context error: {e}")
    
    print("\n=== BRAKET ADAPTER VALIDATION COMPLETE ===")

if __name__ == '__main__':
    asyncio.run(test_braket_adapter())
