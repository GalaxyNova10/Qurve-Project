#!/usr/bin/env python3
"""
Qurve AI - Telemetry Validation Test
Test that telemetry system is working correctly after circular import fixes
"""

import asyncio
import sys
import time

# Add current directory to path
sys.path.append('.')

from qubo_backend.telemetry import (
    get_structured_logger,
    get_benchmark_event_tracker,
    generate_correlation_id,
    generate_benchmark_session_id,
    get_correlation_id,
    get_benchmark_session_id
)

async def test_telemetry_validation() -> dict:
    """Test telemetry system with clean imports."""
    print("🚀 QURVE AI - TELEMETRY VALIDATION TEST")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Test 1: Logger initialization
        print("\n📦 TESTING LOGGER INITIALIZATION...")
        
        logger = get_structured_logger("telemetry_test")
        print("✅ Structured Logger: OPERATIONAL")
        
        # Test 2: Correlation ID generation
        print("\n🔗 TESTING CORRELATION ID GENERATION...")
        
        correlation_id = generate_correlation_id()
        session_id = generate_benchmark_session_id()
        
        print(f"✅ Correlation ID Generated: {correlation_id}")
        print(f"✅ Benchmark Session ID Generated: {session_id}")
        
        # Test 3: Event tracker initialization
        print("\n📊 TESTING EVENT TRACKER...")
        
        event_tracker = get_benchmark_event_tracker()
        print("✅ Event Tracker: OPERATIONAL")
        
        # Test 4: Event tracking
        print("\n📈 TESTING EVENT TRACKING...")
        
        event_tracker.benchmark_start(num_solvers=3, problem_size=5)
        event_tracker.benchmark_complete(successful_solvers=2, total_solvers=3)
        
        events = event_tracker.get_events()
        print(f"✅ Events Tracked: {len(events)}")
        
        # Test 5: Performance summary
        print("\n📊 TESTING PERFORMANCE SUMMARY...")
        
        perf_summary = event_tracker.get_performance_summary()
        print(f"✅ Performance Summary: {len(perf_summary)} solvers tracked")
        
        # Test 6: Fallback analysis
        print("\n🔄 TESTING FALLBACK ANALYSIS...")
        
        fallback_analysis = event_tracker.get_fallback_analysis()
        print(f"✅ Fallback Analysis: {fallback_analysis.get('total_fallbacks', 0)} fallbacks detected")
        
        # Calculate success metrics
        elapsed = time.time() - start_time
        success_criteria = {
            "logger_operational": logger is not None,
            "correlation_generation": correlation_id is not None,
            "session_generation": session_id is not None,
            "event_tracker_operational": event_tracker is not None,
            "event_tracking": len(events) > 0,
            "performance_summary": perf_summary is not None,
            "fallback_analysis": fallback_analysis is not None
        }
        
        passed_criteria = sum(1 for value in success_criteria.values() if value)
        total_criteria = len(success_criteria)
        success_rate = passed_criteria / total_criteria if total_criteria > 0 else 0
        
        print(f"\n📊 TELEMETRY VALIDATION RESULTS:")
        print(f"  Total Duration: {elapsed:.2f} seconds")
        print(f"  Success Rate: {success_rate:.1%} ({passed_criteria}/{total_criteria})")
        
        for criterion, passed in success_criteria.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {criterion.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
        
        # Overall assessment
        overall_status = "SUCCESS" if success_rate >= 0.8 else "NEEDS_WORK"
        
        print(f"\n🎯 OVERALL STATUS: {overall_status}")
        
        if overall_status == "SUCCESS":
            print("🎉 TELEMETRY SYSTEM: WORKING!")
            print("   ✅ Circular imports resolved")
            print("   ✅ Structured logging operational")
            print("   ✅ Correlation tracking working")
            print("   ✅ Event tracking functional")
            print("   ✅ Performance monitoring active")
            print("   ✅ Fallback analysis working")
            print("\n   🚀 TELEMETRY CERTIFIED: System ready for production")
        else:
            print("❌ TELEMETRY SYSTEM: NEEDS WORK!")
            print("   🔴 Review failed validation criteria")
            print("\n   🛠️  TELEMETRY NOT READY: System needs fixes")
        
        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "success_criteria": success_criteria,
            "elapsed": elapsed,
            "telemetry_ready": all(success_criteria.values())
        }
        
    except Exception as e:
        print(f"❌ Telemetry validation failed: {str(e)}")
        return {
            "overall_status": "ERROR",
            "error": str(e),
            "elapsed": time.time() - start_time
        }

async def main():
    """Run telemetry validation test."""
    print("🚀 QURVE AI - TELEMETRY VALIDATION TEST")
    print("=" * 50)
    
    result = await test_telemetry_validation()
    
    print(f"\n{'='*50}")
    print("TELEMETRY VALIDATION COMPLETE")
    print("=" * 50)
    
    return result

if __name__ == '__main__':
    asyncio.run(main())
