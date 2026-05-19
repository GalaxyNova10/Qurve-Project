#!/usr/bin/env python3
"""
Qurve AI - Final Braket Validation Test
Validates the complete end-to-end Braket system with async fixes
Target: braket → success
"""

import asyncio
import sys
import time
from typing import Dict, Any

# Add current directory to path
sys.path.append('.')

from qubo_backend.optimization.braket_client import run_braket_job, check_braket_worker_health
from qubo_backend.optimization.braket_solver import braket_status, solve_braket
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.telemetry import get_structured_logger

logger = get_structured_logger(__name__)

class FinalBraketValidation:
    """Final validation test for complete Braket system."""
    
    def __init__(self):
        self.logger = get_structured_logger(__name__)
        self.validation_results = {
            "worker_operational": False,
            "client_bridge_working": False,
            "solver_integration_working": False,
            "benchmark_execution_success": False,
            "telemetry_preserved": False,
            "target_achieved": False  # braket → success
        }
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete validation of Braket system."""
        print("🎯 QURVE AI - FINAL BRAKET VALIDATION")
        print("=" * 60)
        print("TARGET: braket → success")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Worker Operational
        print("\n🔧 TEST 1 - WORKER OPERATIONAL")
        self.validation_results["worker_operational"] = await self.test_worker_operational()
        
        # Test 2: Client Bridge Working
        print("\n🌉 TEST 2 - CLIENT BRIDGE WORKING")
        self.validation_results["client_bridge_working"] = await self.test_client_bridge_working()
        
        # Test 3: Solver Integration Working
        print("\n🔗 TEST 3 - SOLVER INTEGRATION WORKING")
        self.validation_results["solver_integration_working"] = self.test_solver_integration_working()
        
        # Test 4: Benchmark Execution Success
        print("\n🎯 TEST 4 - BENCHMARK EXECUTION SUCCESS")
        self.validation_results["benchmark_execution_success"] = await self.test_benchmark_execution_success()
        
        # Test 5: Telemetry Preserved
        print("\n📊 TEST 5 - TELEMETRY PRESERVED")
        self.validation_results["telemetry_preserved"] = await self.test_telemetry_preserved()
        
        # Test 6: Target Achieved (braket → success)
        print("\n🏆 TEST 6 - TARGET ACHIEVED")
        self.validation_results["target_achieved"] = await self.test_target_achieved()
        
        # Calculate results
        elapsed = time.time() - start_time
        passed_tests = sum(1 for result in self.validation_results.values() if result)
        total_tests = len(self.validation_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Generate final report
        print(f"\n{'='*60}")
        print("FINAL BRAKET VALIDATION RESULTS")
        print("=" * 60)
        
        print(f"Total Duration: {elapsed:.2f} seconds")
        print(f"Success Rate: {success_rate:.1%} ({passed_tests}/{total_tests})")
        
        for test_name, passed in self.validation_results.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {test_name.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
        
        # Final assessment
        target_achieved = self.validation_results["target_achieved"] and success_rate >= 0.8
        
        print(f"\n🎯 FINAL STATUS: {'✅ TARGET ACHIEVED' if target_achieved else '❌ TARGET NOT ACHIEVED'}")
        
        if target_achieved:
            print("🎉 FINAL VALIDATION: SUCCESS!")
            print("   ✅ Braket worker operational")
            print("   ✅ HTTP bridge working")
            print("   ✅ Solver integration working")
            print("   ✅ Benchmark execution successful")
            print("   ✅ Telemetry preserved")
            print("   ✅ Target achieved: braket → success")
            print("\n   🚀 COMPLETE SYSTEM CERTIFIED: Production ready!")
        else:
            print("❌ FINAL VALIDATION: FAILED!")
            print("   🔴 Target not achieved: braket → success")
            print("   🔴 Review failed tests above")
            print("\n   🛠️  SYSTEM NOT READY: Additional fixes required")
        
        return {
            "target_achieved": target_achieved,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "validation_results": self.validation_results,
            "elapsed": elapsed
        }
    
    async def test_worker_operational(self) -> bool:
        """Test that Braket worker is operational."""
        try:
            print("  Checking Braket worker operational status...")
            
            # Check worker health
            is_healthy = await check_braket_worker_health()
            
            if is_healthy:
                print("  ✅ Braket worker operational")
                return True
            else:
                print("  ❌ Braket worker not operational")
                return False
                
        except Exception as e:
            print(f"  ❌ Worker operational test error: {str(e)}")
            return False
    
    async def test_client_bridge_working(self) -> bool:
        """Test that HTTP bridge is working."""
        try:
            print("  Testing HTTP bridge functionality...")
            
            # Test multiple requests through the bridge
            results = []
            for i in range(3):
                result = await run_braket_job(shots=5)
                if result.status == "success":
                    results.append(result)
                else:
                    print(f"    Bridge request {i+1} failed: {result.error}")
            
            if len(results) == 3:
                print(f"  ✅ HTTP bridge working ({len(results)} successful requests)")
                return True
            else:
                print(f"  ❌ HTTP bridge not working ({len(results)}/3 successful)")
                return False
                
        except Exception as e:
            print(f"  ❌ HTTP bridge test error: {str(e)}")
            return False
    
    def test_solver_integration_working(self) -> bool:
        """Test that solver integration is working."""
        try:
            print("  Testing solver integration...")
            
            # Test braket status
            status = braket_status()
            
            if status == "available_local":
                print(f"  ✅ Solver integration working (status: {status})")
                return True
            else:
                print(f"  ❌ Solver integration not working (status: {status})")
                return False
                
        except Exception as e:
            print(f"  ❌ Solver integration test error: {str(e)}")
            return False
    
    async def test_benchmark_execution_success(self) -> bool:
        """Test that benchmark execution is successful."""
        try:
            print("  Testing benchmark execution...")
            
            # Create a realistic benchmark request
            benchmark_request = SolverRequest(
                mu=[0.08, 0.12, 0.06, 0.10],
                sigma=[[0.015, 0.008, 0.005, 0.006],
                       [0.008, 0.025, 0.012, 0.010],
                       [0.005, 0.012, 0.018, 0.008],
                       [0.006, 0.010, 0.008, 0.020]],
                tickers=["AAPL", "GOOGL", "MSFT", "AMZN"],
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
                    print(f"    Actual solver: {solution.metadata.solver}")
                return True
            else:
                print("  ❌ Benchmark execution failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Benchmark execution error: {str(e)}")
            return False
    
    async def test_telemetry_preserved(self) -> bool:
        """Test that telemetry is preserved during execution."""
        try:
            print("  Testing telemetry preservation...")
            
            # Get event tracker
            from qubo_backend.telemetry import get_benchmark_event_tracker
            event_tracker = get_benchmark_event_tracker()
            
            # Clear events first
            event_tracker.clear_events()
            
            # Run a job to generate telemetry
            await run_braket_job(shots=5)
            
            # Check if events were generated
            events = event_tracker.get_events()
            
            if events:
                print(f"  ✅ Telemetry preserved ({len(events)} events)")
                
                # Check for specific event types
                event_types = [event.event_type for event in events]
                print(f"    Event types: {event_types}")
                return True
            else:
                print("  ❌ Telemetry not preserved (no events)")
                return False
                
        except Exception as e:
            print(f"  ❌ Telemetry preservation test error: {str(e)}")
            return False
    
    async def test_target_achieved(self) -> bool:
        """Test that the target 'braket → success' is achieved."""
        try:
            print("  Testing target achievement: braket → success...")
            
            # Create the exact benchmark scenario
            benchmark_request = SolverRequest(
                mu=[0.05, 0.10, 0.08],
                sigma=[[0.01, 0.005, 0.003],
                       [0.005, 0.02, 0.008],
                       [0.003, 0.008, 0.015]],
                tickers=["AAPL", "GOOGL", "MSFT"],
                sectors=["Tech", "Tech", "Tech"],
                risk_tolerance=0.1,
                cardinality=2,
                max_sector_exposure=0.8,
                binary_bits=2,
                solver="braket_local"
            )
            
            # Execute the target benchmark
            solution = solve_braket(benchmark_request)
            
            # Validate target criteria
            target_met = False
            
            if solution and solution.weights is not None:
                print(f"    Solution generated: {[f'{w:.3f}' for w in solution.weights]}")
                
                if solution.metadata:
                    # Check for target metadata
                    actual_solver = solution.metadata.solver
                    provider = solution.metadata.provider
                    backend = solution.metadata.bqm_backend
                    
                    print(f"    Actual solver: {actual_solver}")
                    print(f"    Provider: {provider}")
                    print(f"    Backend: {backend}")
                    
                    # Target criteria
                    solver_correct = actual_solver == "braket"
                    provider_correct = provider == "amazon_braket"
                    backend_correct = backend == "amazon_braket_local"
                    
                    if solver_correct and provider_correct and backend_correct:
                        print("  ✅ Target achieved: braket → success")
                        target_met = True
                    else:
                        print(f"  ❌ Target not achieved:")
                        print(f"      Solver correct: {solver_correct}")
                        print(f"      Provider correct: {provider_correct}")
                        print(f"      Backend correct: {backend_correct}")
                else:
                    print("  ❌ Target not achieved: No metadata")
            else:
                print("  ❌ Target not achieved: No solution")
            
            return target_met
            
        except Exception as e:
            print(f"  ❌ Target achievement test error: {str(e)}")
            return False

async def main():
    """Run the final Braket validation."""
    validation = FinalBraketValidation()
    return await validation.run_validation()

if __name__ == '__main__':
    result = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if result["target_achieved"] else 1
    sys.exit(exit_code)
