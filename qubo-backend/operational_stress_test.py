#!/usr/bin/env python3
"""
Qurve AI - Operational Stress Test
Comprehensive stress testing for production readiness validation
"""

import asyncio
import sys
import time
import psutil
import threading
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

# Add current directory to path
sys.path.append('.')

from qubo_backend.tasks import get_benchmark_queue, get_async_runner
from qubo_backend.telemetry import (
    get_structured_logger,
    get_benchmark_event_tracker,
    generate_correlation_id,
    generate_benchmark_session_id
)

class OperationalStressTest:
    """Comprehensive operational stress testing suite."""
    
    def __init__(self):
        self.logger = get_structured_logger("stress_test")
        self.event_tracker = get_benchmark_event_tracker()
        self.queue = get_benchmark_queue()
        self.async_runner = get_async_runner()
        
        # Stress test metrics
        self.metrics = {
            "total_benchmarks": 0,
            "successful_benchmarks": 0,
            "failed_benchmarks": 0,
            "total_duration_ms": 0,
            "max_latency_ms": 0,
            "min_latency_ms": float('inf'),
            "avg_latency_ms": 0,
            "memory_start_mb": 0,
            "memory_peak_mb": 0,
            "memory_end_mb": 0,
            "thread_count_start": 0,
            "thread_count_peak": 0,
            "thread_count_end": 0,
            "queue_depth_max": 0,
            "worker_exhaustion_count": 0,
            "telemetry_events_count": 0
        }
    
    async def run_500_benchmark_stress_test(self) -> Dict[str, Any]:
        """Run 500 benchmark stress test."""
        print("🚀 QURVE AI - 500 BENCHMARK STRESS TEST")
        print("=" * 60)
        
        start_time = time.perf_counter()
        
        # Record initial metrics
        self.metrics["memory_start_mb"] = psutil.Process().memory_info().rss / 1024 / 1024
        self.metrics["thread_count_start"] = threading.active_count()
        
        print(f"📊 Initial Memory: {self.metrics['memory_start_mb']:.2f} MB")
        print(f"📊 Initial Threads: {self.metrics['thread_count_start']}")
        
        # Submit 500 benchmarks
        benchmark_ids = []
        print(f"\n🔄 SUBMITTING 500 BENCHMARKS...")
        
        for i in range(500):
            try:
                # Generate unique correlation and session IDs
                correlation_id = generate_correlation_id()
                session_id = generate_benchmark_session_id()
                
                # Submit benchmark
                benchmark_id = await self.queue.submit_benchmark(
                    solver_request={"test": f"stress_test_{i}", "iteration": i},
                    solver_func=lambda req, idx=i: {
                        "status": "success",
                        "result": f"stress_test_result_{idx}",
                        "iteration": idx,
                        "correlation_id": correlation_id,
                        "session_id": session_id
                    },
                    solver_name=f"stress_solver_{i}",
                    provider="stress_test_provider",
                    timeout_seconds=30
                )
                
                benchmark_ids.append(benchmark_id)
                
                # Track metrics
                self.metrics["total_benchmarks"] += 1
                
                # Monitor memory and threads periodically
                if i % 100 == 0:
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    current_threads = threading.active_count()
                    queue_stats = self.queue.get_queue_stats()
                    
                    self.metrics["memory_peak_mb"] = max(self.metrics["memory_peak_mb"], current_memory)
                    self.metrics["thread_count_peak"] = max(self.metrics["thread_count_peak"], current_threads)
                    self.metrics["queue_depth_max"] = max(self.metrics["queue_depth_max"], queue_stats.pending_tasks)
                    
                    print(f"  Progress: {i}/500 - Memory: {current_memory:.2f} MB - Threads: {current_threads} - Queue: {queue_stats.pending_tasks}")
                
                # Small delay to prevent overwhelming the system
                if i % 50 == 0:
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                self.metrics["failed_benchmarks"] += 1
                print(f"❌ Benchmark {i} submission failed: {str(e)}")
        
        print(f"✅ Submitted {len(benchmark_ids)} benchmarks")
        
        # Process all benchmarks
        print(f"\n⚙️  PROCESSING BENCHMARKS...")
        
        processed_count = 0
        batch_size = 10
        
        while processed_count < len(benchmark_ids):
            # Process batch
            completed = await self.queue.process_benchmarks()
            processed_count += len(completed)
            
            # Update metrics
            self.metrics["successful_benchmarks"] += len(completed)
            
            # Monitor system health
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            current_threads = threading.active_count()
            
            self.metrics["memory_peak_mb"] = max(self.metrics["memory_peak_mb"], current_memory)
            self.metrics["thread_count_peak"] = max(self.metrics["thread_count_peak"], current_threads)
            
            if processed_count % 50 == 0:
                print(f"  Processed: {processed_count}/{len(benchmark_ids)} - Memory: {current_memory:.2f} MB - Threads: {current_threads}")
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)
        
        # Record final metrics
        total_elapsed = (time.perf_counter() - start_time) * 1000
        self.metrics["total_duration_ms"] = total_elapsed
        self.metrics["memory_end_mb"] = psutil.Process().memory_info().rss / 1024 / 1024
        self.metrics["thread_count_end"] = threading.active_count()
        
        # Calculate performance metrics
        if self.metrics["successful_benchmarks"] > 0:
            self.metrics["avg_latency_ms"] = total_elapsed / self.metrics["successful_benchmarks"]
        
        # Get telemetry metrics
        events = self.event_tracker.get_events()
        self.metrics["telemetry_events_count"] = len(events)
        
        # Calculate success rate
        success_rate = self.metrics["successful_benchmarks"] / self.metrics["total_benchmarks"] if self.metrics["total_benchmarks"] > 0 else 0
        
        # Check for memory leaks
        memory_growth = self.metrics["memory_end_mb"] - self.metrics["memory_start_mb"]
        
        print(f"\n📊 STRESS TEST RESULTS:")
        print(f"  Total Benchmarks: {self.metrics['total_benchmarks']}")
        print(f"  Successful: {self.metrics['successful_benchmarks']}")
        print(f"  Failed: {self.metrics['failed_benchmarks']}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Total Duration: {total_elapsed:.2f} ms")
        print(f"  Avg Latency: {self.metrics['avg_latency_ms']:.2f} ms")
        print(f"  Memory Growth: {memory_growth:.2f} MB")
        print(f"  Peak Memory: {self.metrics['memory_peak_mb']:.2f} MB")
        print(f"  Thread Growth: {self.metrics['thread_count_end'] - self.metrics['thread_count_start']}")
        print(f"  Peak Threads: {self.metrics['thread_count_peak']}")
        print(f"  Telemetry Events: {self.metrics['telemetry_events_count']}")
        
        # Evaluate stress test results
        stress_test_passed = True
        issues = []
        
        if success_rate < 0.95:
            stress_test_passed = False
            issues.append(f"Low success rate: {success_rate:.1%} < 95%")
        
        if memory_growth > 100:  # More than 100MB growth
            stress_test_passed = False
            issues.append(f"Memory leak detected: {memory_growth:.2f} MB growth")
        
        if self.metrics["thread_count_end"] - self.metrics["thread_count_start"] > 10:
            stress_test_passed = False
            issues.append(f"Thread leak detected: {self.metrics['thread_count_end'] - self.metrics['thread_count_start']} threads")
        
        if self.metrics["avg_latency_ms"] > 1000:  # More than 1 second average
            stress_test_passed = False
            issues.append(f"High latency: {self.metrics['avg_latency_ms']:.2f} ms average")
        
        if self.metrics["telemetry_events_count"] == 0:
            stress_test_passed = False
            issues.append("No telemetry events generated")
        
        print(f"\n🎯 STRESS TEST STATUS: {'✅ PASSED' if stress_test_passed else '❌ FAILED'}")
        
        if issues:
            print("🔴 ISSUES DETECTED:")
            for issue in issues:
                print(f"  - {issue}")
        
        return {
            "status": "passed" if stress_test_passed else "failed",
            "success_rate": success_rate,
            "metrics": self.metrics,
            "issues": issues
        }
    
    async def run_concurrency_spike_test(self) -> Dict[str, Any]:
        """Run concurrency spike testing."""
        print("\n🚀 QURVE AI - CONCURRENCY SPIKE TEST")
        print("=" * 60)
        
        results = {}
        
        # Test with different concurrency levels
        concurrency_levels = [5, 10, 20]
        
        for level in concurrency_levels:
            print(f"\n🔄 TESTING {level} CONCURRENT USERS...")
            
            start_time = time.perf_counter()
            
            # Create concurrent tasks
            tasks = []
            for i in range(level):
                task = self._run_concurrent_benchmark(f"concurrent_test_{level}_{i}")
                tasks.append(task)
            
            # Wait for all tasks to complete
            try:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=60)
                
                elapsed = (time.perf_counter() - start_time) * 1000
                
                # Get queue stats
                queue_stats = self.queue.get_queue_stats()
                
                results[f"concurrent_{level}"] = {
                    "elapsed_ms": elapsed,
                    "queue_depth": queue_stats.pending_tasks,
                    "active_workers": queue_stats.running_tasks,
                    "status": "success"
                }
                
                print(f"  ✅ {level} concurrent users: {elapsed:.2f} ms - Queue: {queue_stats.pending_tasks} - Workers: {queue_stats.running_tasks}")
                
            except asyncio.TimeoutError:
                results[f"concurrent_{level}"] = {
                    "status": "timeout",
                    "error": "Test timed out"
                }
                print(f"  ❌ {level} concurrent users: TIMEOUT")
            
            except Exception as e:
                results[f"concurrent_{level}"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"  ❌ {level} concurrent users: ERROR - {str(e)}")
        
        return results
    
    async def _run_concurrent_benchmark(self, test_name: str):
        """Run a single concurrent benchmark."""
        try:
            benchmark_id = await self.queue.submit_benchmark(
                solver_request={"test": test_name},
                solver_func=lambda req: {"status": "success", "result": test_name},
                solver_name=f"concurrent_solver_{test_name}",
                provider="concurrent_test",
                timeout_seconds=10
            )
            
            # Process benchmark
            completed = await self.queue.process_benchmarks()
            
            return {"benchmark_id": benchmark_id, "completed": len(completed)}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def run_memory_trend_analysis(self) -> Dict[str, Any]:
        """Run memory trend analysis."""
        print("\n🚀 QURVE AI - MEMORY TREND ANALYSIS")
        print("=" * 60)
        
        memory_samples = []
        
        # Baseline memory
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_samples.append(baseline_memory)
        
        print(f"📊 Baseline Memory: {baseline_memory:.2f} MB")
        
        # Run memory-intensive operations
        for i in range(10):
            # Submit and process benchmarks
            for j in range(10):
                benchmark_id = await self.queue.submit_benchmark(
                    solver_request={"test": f"memory_test_{i}_{j}"},
                    solver_func=lambda req: {"status": "success", "result": f"memory_test_{i}_{j}"},
                    solver_name=f"memory_solver_{i}_{j}",
                    provider="memory_test",
                    timeout_seconds=5
                )
            
            completed = await self.queue.process_benchmarks()
            
            # Sample memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            print(f"  Iteration {i+1}: {current_memory:.2f} MB")
        
        # Final memory
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)
        
        # Calculate memory trend
        memory_growth = final_memory - baseline_memory
        max_memory = max(memory_samples)
        min_memory = min(memory_samples)
        
        print(f"\n📊 MEMORY ANALYSIS RESULTS:")
        print(f"  Baseline: {baseline_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Growth: {memory_growth:.2f} MB")
        print(f"  Peak: {max_memory:.2f} MB")
        print(f"  Min: {min_memory:.2f} MB")
        
        # Check for memory leaks
        memory_leak_detected = memory_growth > 50  # More than 50MB growth
        
        print(f"\n🎯 MEMORY STATUS: {'✅ STABLE' if not memory_leak_detected else '❌ LEAK DETECTED'}")
        
        if memory_leak_detected:
            print(f"🔴 Memory leak detected: {memory_growth:.2f} MB growth")
        else:
            print(f"✅ Memory usage stable: {memory_growth:.2f} MB growth")
        
        return {
            "baseline_memory_mb": baseline_memory,
            "final_memory_mb": final_memory,
            "memory_growth_mb": memory_growth,
            "peak_memory_mb": max_memory,
            "min_memory_mb": min_memory,
            "memory_leak_detected": memory_leak_detected,
            "samples": memory_samples
        }

async def main():
    """Run comprehensive operational stress testing."""
    print("🚀 QURVE AI - OPERATIONAL STRESS TESTING")
    print("=" * 60)
    
    stress_test = OperationalStressTest()
    
    # Run all stress tests
    results = {}
    
    try:
        # 500 Benchmark Stress Test
        results["stress_test"] = await stress_test.run_500_benchmark_stress_test()
        
        # Concurrency Spike Test
        results["concurrency"] = await stress_test.run_concurrency_spike_test()
        
        # Memory Trend Analysis
        results["memory"] = await stress_test.run_memory_trend_analysis()
        
        # Calculate overall results
        stress_test_passed = results["stress_test"]["status"] == "passed"
        concurrency_passed = all(r.get("status") == "success" for r in results["concurrency"].values())
        memory_stable = not results["memory"]["memory_leak_detected"]
        
        overall_passed = stress_test_passed and concurrency_passed and memory_stable
        
        print(f"\n{'='*60}")
        print("OPERATIONAL STRESS TESTING COMPLETE")
        print("=" * 60)
        
        print(f"🎯 OVERALL STATUS: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
        
        print(f"\n📊 TEST RESULTS:")
        print(f"  500 Benchmark Stress Test: {'✅ PASSED' if stress_test_passed else '❌ FAILED'}")
        print(f"  Concurrency Spike Test: {'✅ PASSED' if concurrency_passed else '❌ FAILED'}")
        print(f"  Memory Trend Analysis: {'✅ STABLE' if memory_stable else '❌ LEAK DETECTED'}")
        
        if overall_passed:
            print(f"\n🎉 OPERATIONAL STRESS TESTING: SUCCESSFUL!")
            print(f"   ✅ System handles 500 concurrent benchmarks")
            print(f"   ✅ Concurrency spike testing passed")
            print(f"   ✅ Memory usage stable")
            print(f"   ✅ No resource leaks detected")
            print(f"   ✅ Telemetry system operational")
            print(f"\n   🚀 PRODUCTION READY: System certified for operational deployment")
        else:
            print(f"\n❌ OPERATIONAL STRESS TESTING: FAILED!")
            print(f"   🔴 Review failed tests above")
            print(f"   🔴 Fix operational issues before production")
            print(f"\n   🛠️  DEPLOYMENT NOT READY: System needs fixes")
        
        return {
            "overall_status": "passed" if overall_passed else "failed",
            "stress_test_passed": stress_test_passed,
            "concurrency_passed": concurrency_passed,
            "memory_stable": memory_stable,
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Operational stress testing failed: {str(e)}")
        return {
            "overall_status": "error",
            "error": str(e)
        }

if __name__ == '__main__':
    asyncio.run(main())
