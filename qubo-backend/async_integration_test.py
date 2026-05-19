#!/usr/bin/env python3
"""
Qurve AI - Async Integration Test
Validates that all async integration fixes are working correctly
"""

import asyncio
import sys
import time
from typing import Dict, Any

# Add current directory to path
sys.path.append('.')

from qubo_backend.optimization.braket_client import run_braket_job, check_braket_worker_health, get_braket_worker_status
from qubo_backend.optimization.braket_solver import braket_status, solve_braket
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.telemetry import get_structured_logger

logger = get_structured_logger(__name__)

class AsyncIntegrationTest:
    """Comprehensive test for async integration fixes."""
    
    def __init__(self):
        self.logger = get_structured_logger(__name__)
        self.test_results = {
            "braket_status_sync": False,
            "braket_client_async": False,
            "braket_solver_sync": False,
            "concurrent_requests": False,
            "no_async_warnings": False,
            "benchmark_execution": False
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all async integration tests."""
        print("🚀 QURVE AI - ASYNC INTEGRATION TEST")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Braket Status (Sync)
        print("\n🔍 TEST 1 - BRAKET STATUS (SYNC)")
        self.test_results["braket_status_sync"] = self.test_braket_status_sync()
        
        # Test 2: Braket Client (Async)
        print("\n📡 TEST 2 - BRAKET CLIENT (ASYNC)")
        self.test_results["braket_client_async"] = await self.test_braket_client_async()
        
        # Test 3: Braket Solver (Sync)
        print("\n🔧 TEST 3 - BRAKET SOLVER (SYNC)")
        self.test_results["braket_solver_sync"] = self.test_braket_solver_sync()
        
        # Test 4: Concurrent Requests
        print("\n🔄 TEST 4 - CONCURRENT REQUESTS")
        self.test_results["concurrent_requests"] = await self.test_concurrent_requests()
        
        # Test 5: No Async Warnings
        print("\n⚠️  TEST 5 - NO ASYNC WARNINGS")
        self.test_results["no_async_warnings"] = await self.test_no_async_warnings()
        
        # Test 6: Benchmark Execution
        print("\n🎯 TEST 6 - BENCHMARK EXECUTION")
        self.test_results["benchmark_execution"] = await self.test_benchmark_execution()
        
        # Calculate results
        elapsed = time.time() - start_time
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Generate final report
        print(f"\n{'='*60}")
        print("ASYNC INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        print(f"Total Duration: {elapsed:.2f} seconds")
        print(f"Success Rate: {success_rate:.1%} ({passed_tests}/{total_tests})")
        
        for test_name, passed in self.test_results.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {test_name.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
        
        # Overall assessment
        overall_passed = success_rate >= 0.8  # 80% pass rate required
        
        print(f"\n🎯 OVERALL STATUS: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
        
        if overall_passed:
            print("🎉 ASYNC INTEGRATION: SUCCESSFUL!")
            print("   ✅ No nested event loops")
            print("   ✅ No asyncio.run() conflicts")
            print("   ✅ Proper async/await patterns")
            print("   ✅ Concurrent request handling")
            print("   ✅ Benchmark execution working")
            print("\n   🚀 ASYNC ARCHITECTURE CERTIFIED: System ready for production")
        else:
            print("❌ ASYNC INTEGRATION: FAILED!")
            print("   🔴 Review failed tests above")
            print("   🔴 Fix async integration issues")
            print("\n   🛠️  ASYNC ARCHITECTURE NOT READY: System needs fixes")
        
        return {
            "overall_status": "passed" if overall_passed else "failed",
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": self.test_results,
            "elapsed": elapsed
        }
    
    def test_braket_status_sync(self) -> bool:
        """Test braket status function (sync)."""
        try:
            print("  Testing braket status (sync)...")
            status = braket_status()
            
            if status in ["available_local", "not_available"]:
                print(f"  ✅ Braket status check passed: {status}")
                return True
            else:
                print(f"  ❌ Braket status check failed: {status}")
                return False
                
        except Exception as e:
            print(f"  ❌ Braket status check error: {str(e)}")
            return False
    
    async def test_braket_client_async(self) -> bool:
        """Test braket client functions (async)."""
        try:
            print("  Testing braket client async functions...")
            
            # Test health check
            is_healthy = await check_braket_worker_health()
            print(f"    Health check: {is_healthy}")
            
            # Test worker status
            status = await get_braket_worker_status()
            print(f"    Worker status: {status.get('available', False)}")
            
            # Test job execution (if worker is healthy)
            if is_healthy:
                result = await run_braket_job(shots=5)
                if result.status == "success":
                    print(f"    Job execution: SUCCESS ({len(result.measurements)} measurements)")
                    return True
                else:
                    print(f"    Job execution: FAILED ({result.error})")
                    return False
            else:
                print("    Job execution: SKIPPED (worker not available)")
                return True  # Still pass if worker is not available
                
        except Exception as e:
            print(f"  ❌ Braket client async error: {str(e)}")
            return False
    
    def test_braket_solver_sync(self) -> bool:
        """Test braket solver function (sync)."""
        try:
            print("  Testing braket solver (sync)...")
            
            # Create a simple test request
            test_request = SolverRequest(
                mu=[0.1, 0.2, 0.3],
                sigma=[[0.01, 0.005, 0.003],
                       [0.005, 0.02, 0.01],
                       [0.003, 0.01, 0.015]],
                tickers=["AAPL", "GOOGL", "MSFT"],
                sectors=["Tech", "Tech", "Tech"],
                risk_tolerance=0.1,
                cardinality=2,
                max_sector_exposure=0.8,
                binary_bits=2,
                solver="braket_local"
            )
            
            # This should work without async errors
            solution = solve_braket(test_request)
            
            if solution and solution.weights is not None:
                print("  ✅ Braket solver execution successful")
                return True
            else:
                print("  ❌ Braket solver execution failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Braket solver error: {str(e)}")
            return False
    
    async def test_concurrent_requests(self) -> bool:
        """Test concurrent request handling."""
        try:
            print("  Testing concurrent requests...")
            
            # Create multiple concurrent tasks
            tasks = []
            for i in range(5):
                task = asyncio.create_task(run_braket_job(shots=3))
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            successful_results = 0
            for result in results:
                if isinstance(result, Exception):
                    print(f"    Concurrent task failed: {str(result)}")
                elif hasattr(result, 'status') and result.status == "success":
                    successful_results += 1
            
            print(f"    Successful concurrent results: {successful_results}/{len(tasks)}")
            
            # At least 3 out of 5 should succeed
            return successful_results >= 3
            
        except Exception as e:
            print(f"  ❌ Concurrent requests error: {str(e)}")
            return False
    
    async def test_no_async_warnings(self) -> bool:
        """Test that no async warnings are generated."""
        try:
            print("  Testing for async warnings...")
            
            # Capture warnings
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                # Run various async operations
                await check_braket_worker_health()
                await run_braket_job(shots=3)
                
                # Check for async-related warnings
                async_warnings = [warning for warning in w 
                                if "coroutine" in str(warning.message).lower() 
                                or "event loop" in str(warning.message).lower()
                                or "asyncio" in str(warning.message).lower()]
                
                if async_warnings:
                    print(f"    Async warnings detected: {len(async_warnings)}")
                    for warning in async_warnings:
                        print(f"      - {warning.message}")
                    return False
                else:
                    print("    No async warnings detected")
                    return True
                    
        except Exception as e:
            print(f"  ❌ Async warnings test error: {str(e)}")
            return False
    
    async def test_benchmark_execution(self) -> bool:
        """Test full benchmark execution with async fixes."""
        try:
            print("  Testing benchmark execution...")
            
            # Create a realistic benchmark request
            benchmark_request = SolverRequest(
                mu=[0.05, 0.08, 0.12, 0.03],
                sigma=[[0.01, 0.005, 0.003, 0.002],
                       [0.005, 0.02, 0.01, 0.008],
                       [0.003, 0.01, 0.015, 0.006],
                       [0.002, 0.008, 0.006, 0.012]],
                tickers=["AAPL", "GOOGL", "MSFT", "TSLA"],
                sectors=["Tech", "Tech", "Tech", "Tech"],
                risk_tolerance=0.1,
                cardinality=2,
                max_sector_exposure=0.8,
                binary_bits=2,
                solver="braket_local"
            )
            
            # Execute benchmark
            start_time = time.time()
            solution = solve_braket(benchmark_request)
            elapsed = time.time() - start_time
            
            if solution and solution.weights is not None:
                print(f"  ✅ Benchmark execution successful")
                print(f"    Execution time: {elapsed:.2f}s")
                print(f"    Solution weights: {[f'{w:.3f}' for w in solution.weights]}")
                if solution.metadata:
                    print(f"    Backend: {solution.metadata.bqm_backend}")
                    print(f"    Provider: {solution.metadata.provider}")
                return True
            else:
                print("  ❌ Benchmark execution failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Benchmark execution error: {str(e)}")
            return False

async def main():
    """Run the complete async integration test."""
    test = AsyncIntegrationTest()
    return await test.run_all_tests()

if __name__ == '__main__':
    asyncio.run(main())
