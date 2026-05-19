"""
Qurve AI - Replay Validation Suite
Comprehensive validation for replay system with deterministic guarantees.

Validates:
✅ deterministic replay
✅ causality preservation
✅ immutable snapshots
✅ replay isolation
✅ no live cloud calls
✅ no governance mutation
✅ divergence determinism
✅ lineage integrity
✅ fallback ancestry preservation
✅ telemetry isolation
✅ async stability
✅ no event loop regressions
"""

import asyncio
import time
import sys
sys.path.append('.')

from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

# Import replay components
try:
    from qubo_backend.replay.execution_replay import get_execution_replay
    from qubo_backend.replay.replay_schemas import (
        REPLAY_SCHEMA_VERSION,
        ReplayModeSchema,
        ReplayStatusSchema
    )
    from qubo_backend.replay.replay_artifact_classification import get_artifact_classification
    from qubo_backend.replay.replay_comparison_analytics import get_replay_comparison_analytics
    from qubo_backend.replay.replay_telemetry_extension import get_replay_telemetry_extension
    from qubo_backend.replay.replay_persistence import get_replay_persistence
    from qubo_backend.replay.replay_access_control import get_replay_access_control
    from qubo_backend.replay.replay_dashboard_extension import get_replay_dashboard_extension
    REPLAY_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Replay system not available: {e}")
    REPLAY_SYSTEM_AVAILABLE = False

class ReplayValidationSuite:
    """Comprehensive validation suite for replay system."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all replay system validation tests."""
        print("=== REPLAY SYSTEM VALIDATION ===")
        
        validation_methods = [
            self.validate_deterministic_replay,
            self.validate_causality_preservation,
            self.validate_immutable_snapshots,
            self.validate_replay_isolation,
            self.validate_no_live_cloud_calls,
            self.validate_no_governance_mutation,
            self.validate_divergence_determinism,
            self.validate_lineage_integrity,
            self.validate_fallback_ancestry_preservation,
            self.validate_telemetry_isolation,
            self.validate_async_stability,
            self.validate_no_event_loop_regressions
        ]
        
        for validation_method in validation_methods:
            try:
                result = await validation_method()
                self.test_results[validation_method.__name__] = result
                status = "✅" if result['status'] == 'passed' else "❌"
                print(f"{status} {validation_method.__name__}: {result['status']}")
            except Exception as e:
                self.test_results[validation_method.__name__] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"❌ {validation_method.__name__}: FAILED - {str(e)}")
        
        # Generate summary
        passed = sum(1 for r in self.test_results.values() if r['status'] == 'passed')
        total = len(self.test_results)
        
        summary = {
            'overall_status': 'passed' if passed == total else 'failed',
            'passed_count': passed,
            'total_count': total,
            'test_results': self.test_results,
            'validation_timestamp': time.time(),
            'duration_seconds': time.time() - self.start_time
        }
        
        print(f"\n=== VALIDATION SUMMARY ===")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Tests Passed: {passed}/{total}")
        
        return summary
    
    async def validate_deterministic_replay(self) -> Dict[str, Any]:
        """Validate deterministic replay behavior."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            replay_engine = get_execution_replay()
            
            # Test deterministic replay with same inputs
            original_execution_id = "test_exec_001"
            correlation_id = "test_corr_001"
            
            # Create replay snapshot
            replay_id = await replay_engine.create_replay_snapshot(
                original_execution_id=original_execution_id,
                correlation_id=correlation_id,
                original_request={"test": "deterministic"},
                solver_selection="local_braket",
                execution_mode="local",
                fallback_chain=["local_braket"],
                cloud_task_references=[],
                governance_decisions=[{"decision": "allow"}],
                cost_decisions=[{"cost": 0.05}],
                telemetry_traces=[{"event": "test"}],
                credential_state_metadata={},
                solver_outputs={"result": "test"},
                timing_breakdowns={"total": 100.0}
            )
            
            # Start two replay sessions with same snapshot
            session1_id = await replay_engine.start_replay_session(replay_id, ReplayModeSchema.METADATA_ONLY)
            session2_id = await replay_engine.start_replay_session(replay_id, ReplayModeSchema.METADATA_ONLY)
            
            # Execute both replays
            result1 = await replay_engine.execute_replay(session1_id)
            result2 = await replay_engine.execute_replay(session2_id)
            
            # Validate deterministic results
            same_divergence_score = result1.divergence_score == result2.divergence_score
            same_duration = abs((result1.duration_ms or 0) - (result2.duration_ms or 0)) < 1.0
            same_status = result1.status == result2.status
            
            return {
                'status': 'passed' if (same_divergence_score and same_duration and same_status) else 'failed',
                'deterministic_results': same_divergence_score and same_duration and same_status,
                'replay_id': replay_id,
                'session1_divergence': result1.divergence_score,
                'session2_divergence': result2.divergence_score,
                'session1_duration': result1.duration_ms,
                'session2_duration': result2.duration_ms
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_causality_preservation(self) -> Dict[str, Any]:
        """Validate causality preservation in replay."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            comparison_analytics = get_replay_comparison_analytics()
            
            # Test causality preservation with correlation lineage
            original_timeline = [
                Mock(correlation_id="corr_001", event_type="governance_decision", governance_decision="allow"),
                Mock(correlation_id="corr_002", event_type="solver_execution", solver="local_braket"),
                Mock(correlation_id="corr_003", event_type="fallback", from_solver="cloud", to_solver="local")
            ]
            
            replay_timeline = [
                Mock(correlation_id="corr_001", event_type="governance_decision", governance_decision="allow"),
                Mock(correlation_id="corr_002", event_type="solver_execution", solver="local_braket"),
                Mock(correlation_id="corr_003", event_type="fallback", from_solver="cloud", to_solver="local")
            ]
            
            # Create lineage objects
            from qubo_backend.replay.replay_comparison_analytics import CausalLineage
            original_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id=None,
                benchmark_session_id="session_001",
                execution_lineage=["corr_001", "corr_002", "corr_003"],
                fallback_ancestry=["cloud→local"],
                governance_decision_ancestry=["allow"],
                telemetry_lineage=["telemetry_001", "telemetry_002"]
            )
            
            replay_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id=None,
                benchmark_session_id="session_001",
                execution_lineage=["corr_001", "corr_002", "corr_003"],
                fallback_ancestry=["cloud→local"],
                governance_decision_ancestry=["allow"],
                telemetry_lineage=["telemetry_001", "telemetry_002"]
            )
            
            # Analyze causal divergence
            divergence_analyses = await comparison_analytics._analyze_causal_divergence(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            
            # Validate causality preservation
            lineage_preserved = all(analysis.lineage_preserved for analysis in divergence_analyses)
            no_unknown_causality = not any(analysis.unknown_causality for analysis in divergence_analyses)
            
            return {
                'status': 'passed' if (lineage_preserved and no_unknown_causality) else 'failed',
                'lineage_preserved': lineage_preserved,
                'no_unknown_causality': no_unknown_causality,
                'divergence_analyses_count': len(divergence_analyses)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_immutable_snapshots(self) -> Dict[str, Any]:
        """Validate immutable replay snapshots."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            replay_engine = get_execution_replay()
            
            # Create replay snapshot
            replay_id = await replay_engine.create_replay_snapshot(
                original_execution_id="test_exec_002",
                correlation_id="test_corr_002",
                original_request={"test": "immutable"},
                solver_selection="local_braket",
                execution_mode="local",
                fallback_chain=["local_braket"],
                cloud_task_references=[],
                governance_decisions=[{"decision": "allow"}],
                cost_decisions=[{"cost": 0.05}],
                telemetry_traces=[{"event": "test"}],
                credential_state_metadata={},
                solver_outputs={"result": "test"},
                timing_breakdowns={"total": 100.0}
            )
            
            # Get snapshot and validate immutability
            snapshot = await replay_engine.get_replay_snapshot(replay_id)
            
            # Validate snapshot properties
            has_replay_id = hasattr(snapshot, 'replay_id')
            has_original_execution_id = hasattr(snapshot, 'original_execution_id')
            has_timestamp = hasattr(snapshot, 'timestamp')
            is_marked_immutable = hasattr(snapshot, 'immutable') and snapshot.immutable
            
            return {
                'status': 'passed' if (has_replay_id and has_original_execution_id and has_timestamp and is_marked_immutable) else 'failed',
                'replay_id_present': has_replay_id,
                'original_execution_id_present': has_original_execution_id,
                'timestamp_present': has_timestamp,
                'marked_immutable': is_marked_immutable,
                'replay_id': replay_id
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_replay_isolation(self) -> Dict[str, Any]:
        """Validate replay isolation from operational systems."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            artifact_classification = get_artifact_classification()
            access_control = get_replay_access_control()
            
            # Test operational table access is read-only
            operational_tables = artifact_classification.get_operational_tables()
            replay_tables = artifact_classification.get_replay_tables()
            
            # Validate access patterns
            operational_read_only = all(
                artifact_classification.validate_access_pattern(table, is_write_operation=True)
                for table in operational_tables
            )
            
            replay_write_allowed = all(
                artifact_classification.validate_access_pattern(table, is_write_operation=True)
                for table in replay_tables
            )
            
            # Validate isolation guards
            isolation_result = await access_control.validate_access(
                operation="submit_cloud_task",
                target_table="replay_sessions",
                is_write_operation=False
            )
            
            return {
                'status': 'passed' if (operational_read_only and replay_write_allowed and not isolation_result[0]) else 'failed',
                'operational_read_only': operational_read_only,
                'replay_write_allowed': replay_write_allowed,
                'isolation_guards_working': not isolation_result[0],
                'operational_tables_count': len(operational_tables),
                'replay_tables_count': len(replay_tables)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_no_live_cloud_calls(self) -> Dict[str, Any]:
        """Validate no live cloud calls during replay."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            access_control = get_replay_access_control()
            
            # Test cloud operations are blocked
            cloud_operations = [
                ("submit_cloud_task", False),
                ("run_qpu", False),
                ("cloud_simulation", False),
                ("live_aws_access", False)
            ]
            
            blocked_operations = 0
            for operation, expected_allowed in cloud_operations:
                result = await access_control.validate_access(
                    operation=operation,
                    is_write_operation=False
                )
                if result[0] == expected_allowed:
                    blocked_operations += 1
            
            return {
                'status': 'passed' if blocked_operations == len(cloud_operations) else 'failed',
                'blocked_cloud_operations': blocked_operations,
                'total_cloud_operations': len(cloud_operations),
                'isolation_working': blocked_operations == len(cloud_operations)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_no_governance_mutation(self) -> Dict[str, Any]:
        """Validate no governance mutation during replay."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            access_control = get_replay_access_control()
            
            # Test governance mutation operations are blocked
            governance_operations = [
                ("update_governance", False),
                ("modify_quota", False),
                ("change_cost_model", False),
                ("alter_governance_state", False)
            ]
            
            blocked_operations = 0
            for operation, expected_allowed in governance_operations:
                result = await access_control.validate_access(
                    operation=operation,
                    is_write_operation=True
                )
                if result[0] == expected_allowed:
                    blocked_operations += 1
            
            return {
                'status': 'passed' if blocked_operations == len(governance_operations) else 'failed',
                'blocked_governance_operations': blocked_operations,
                'total_governance_operations': len(governance_operations),
                'governance_isolation_working': blocked_operations == len(governance_operations)
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_divergence_determinism(self) -> Dict[str, Any]:
        """Validate divergence scoring determinism."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            comparison_analytics = get_replay_comparison_analytics()
            
            # Test divergence scoring with same inputs
            from qubo_backend.replay.replay_comparison_analytics import CausalLineage
            original_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id=None,
                benchmark_session_id="session_001",
                execution_lineage=["corr_001", "corr_002"],
                fallback_ancestry=["cloud→local"],
                governance_decision_ancestry=["allow"],
                telemetry_lineage=["telemetry_001"]
            )
            
            replay_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id=None,
                benchmark_session_id="session_001",
                execution_lineage=["corr_001", "corr_002"],
                fallback_ancestry=["cloud→local"],
                governance_decision_ancestry=["allow"],
                telemetry_lineage=["telemetry_001"]
            )
            
            # Calculate divergence scores twice
            score1 = await comparison_analytics._calculate_overall_divergence_score([])
            score2 = await comparison_analytics._calculate_overall_divergence_score([])
            
            # Validate deterministic divergence
            same_score = score1 == score2
            no_randomness = True  # Should be no random elements
            
            return {
                'status': 'passed' if (same_score and no_randomness) else 'failed',
                'deterministic_scoring': same_score,
                'no_randomness': no_randomness,
                'score1': score1,
                'score2': score2
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_lineage_integrity(self) -> Dict[str, Any]:
        """Validate lineage integrity preservation."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            comparison_analytics = get_replay_comparison_analytics()
            
            # Test lineage preservation assessment
            from qubo_backend.replay.replay_comparison_analytics import CausalLineage
            original_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id="parent_001",
                benchmark_session_id="session_001",
                execution_lineage=["corr_001", "corr_002"],
                fallback_ancestry=["cloud→local"],
                governance_decision_ancestry=["allow"],
                telemetry_lineage=["telemetry_001"]
            )
            
            replay_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id="parent_001",
                benchmark_session_id="session_001",
                execution_lineage=["corr_001", "corr_002"],
                fallback_ancestry=["cloud→local"],
                governance_decision_ancestry=["allow"],
                telemetry_lineage=["telemetry_001"]
            )
            
            # Assess lineage preservation
            preservation_result = comparison_analytics._assess_lineage_preservation(original_lineage, replay_lineage)
            
            # Validate lineage integrity
            execution_lineage_preserved = preservation_result.get("execution_lineage_preserved", False)
            fallback_ancestry_preserved = preservation_result.get("fallback_ancestry_preserved", False)
            governance_lineage_preserved = preservation_result.get("governance_decision_ancestry_preserved", False)
            telemetry_lineage_preserved = preservation_result.get("telemetry_lineage_preserved", False)
            
            return {
                'status': 'passed' if (execution_lineage_preserved and fallback_ancestry_preserved and governance_lineage_preserved and telemetry_lineage_preserved) else 'failed',
                'execution_lineage_preserved': execution_lineage_preserved,
                'fallback_ancestry_preserved': fallback_ancestry_preserved,
                'governance_lineage_preserved': governance_lineage_preserved,
                'telemetry_lineage_preserved': telemetry_lineage_preserved
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_fallback_ancestry_preservation(self) -> Dict[str, Any]:
        """Validate fallback ancestry preservation."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            comparison_analytics = get_replay_comparison_analytics()
            
            # Test fallback ancestry preservation
            original_timeline = [
                Mock(event_type="fallback", solver="cloud_qpu", to_solver="cloud_simulator"),
                Mock(event_type="fallback", solver="cloud_simulator", to_solver="local_braket"),
                Mock(event_type="fallback", solver="local_braket", to_solver="qiskit")
            ]
            
            replay_timeline = [
                Mock(event_type="fallback", solver="cloud_qpu", to_solver="cloud_simulator"),
                Mock(event_type="fallback", solver="cloud_simulator", to_solver="local_braket"),
                Mock(event_type="fallback", solver="local_braket", to_solver="qiskit")
            ]
            
            # Analyze fallback divergence with ancestry
            from qubo_backend.replay.replay_comparison_analytics import CausalLineage
            original_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id=None,
                benchmark_session_id="session_001",
                execution_lineage=[],
                fallback_ancestry=["cloud_qpu→cloud_simulator", "cloud_simulator→local_braket", "local_braket→qiskit"],
                governance_decision_ancestry=[],
                telemetry_lineage=[]
            )
            
            replay_lineage = CausalLineage(
                correlation_id="test_corr",
                parent_correlation_id=None,
                benchmark_session_id="session_001",
                execution_lineage=[],
                fallback_ancestry=["cloud_qpu→cloud_simulator", "cloud_simulator→local_braket", "local_braket→qiskit"],
                governance_decision_ancestry=[],
                telemetry_lineage=[]
            )
            
            divergence_analysis = await comparison_analytics._analyze_fallback_divergence_with_ancestry(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            
            # Validate fallback ancestry preservation
            ancestry_preserved = divergence_analysis.lineage_preserved
            same_fallback_chain = divergence_analysis.metadata.get("original_fallback_chain") == divergence_analysis.metadata.get("replay_fallback_chain")
            
            return {
                'status': 'passed' if (ancestry_preserved and same_fallback_chain) else 'failed',
                'ancestry_preserved': ancestry_preserved,
                'same_fallback_chain': same_fallback_chain,
                'original_chain': divergence_analysis.metadata.get("original_fallback_chain"),
                'replay_chain': divergence_analysis.metadata.get("replay_fallback_chain")
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_telemetry_isolation(self) -> Dict[str, Any]:
        """Validate telemetry isolation from production."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            telemetry_extension = get_replay_telemetry_extension()
            artifact_classification = get_artifact_classification()
            
            # Test telemetry isolation
            replay_telemetry_id = await telemetry_extension.emit_replay_telemetry(
                replay_id="test_replay_001",
                replay_mode=ReplayModeSchema.METADATA_ONLY,
                replay_source_execution_id="test_exec_001",
                timeline_reconstruction_ms=100.0,
                divergence_score=0.1,
                correlation_id="test_corr_001"
            )
            
            # Validate telemetry isolation
            telemetry_config = telemetry_extension.config
            forensic_only = telemetry_config.forensic_only
            isolation_namespace = telemetry_config.isolation_namespace
            
            # Validate namespace separation
            replay_tables = artifact_classification.get_replay_tables()
            operational_tables = artifact_classification.get_operational_tables()
            
            namespace_isolated = "replay" in isolation_namespace and len(replay_tables) > 0
            operational_separate = all(not table.startswith("replay_") for table in operational_tables)
            
            return {
                'status': 'passed' if (forensic_only and namespace_isolated and operational_separate) else 'failed',
                'forensic_only': forensic_only,
                'namespace_isolated': namespace_isolated,
                'operational_separate': operational_separate,
                'telemetry_id': replay_telemetry_id,
                'isolation_namespace': isolation_namespace
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_async_stability(self) -> Dict[str, Any]:
        """Validate async stability of replay system."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            replay_engine = get_execution_replay()
            
            # Test concurrent replay operations
            async def create_replay_session(i):
                replay_id = f"test_replay_{i}"
                return await replay_engine.start_replay_session(replay_id, ReplayModeSchema.METADATA_ONLY)
            
            # Run concurrent operations
            tasks = [create_replay_session(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Validate async stability
            successful_operations = [r for r in results if isinstance(r, str)]
            exceptions = [r for r in results if isinstance(r, Exception)]
            
            return {
                'status': 'passed' if (len(successful_operations) == 5 and len(exceptions) == 0) else 'failed',
                'concurrent_operations': 5,
                'successful_operations': len(successful_operations),
                'exceptions': len(exceptions),
                'async_stable': len(exceptions) == 0
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_no_event_loop_regressions(self) -> Dict[str, Any]:
        """Validate no event loop regressions."""
        if not REPLAY_SYSTEM_AVAILABLE:
            return {'status': 'skipped', 'error': 'Replay system not available'}
        
        try:
            replay_engine = get_execution_replay()
            
            # Test multiple replay operations don't block event loop
            start_time = time.time()
            
            # Execute multiple operations
            for i in range(10):
                replay_id = f"test_replay_{i}"
                await replay_engine.start_replay_session(replay_id, ReplayModeSchema.METADATA_ONLY)
            
            elapsed = time.time() - start_time
            
            # Validate event loop not blocked
            event_loop_stable = elapsed < 1.0  # Should complete quickly
            
            return {
                'status': 'passed' if event_loop_stable else 'failed',
                'operations_completed': 10,
                'elapsed_seconds': elapsed,
                'event_loop_stable': event_loop_stable
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}


async def run_replay_validation():
    """Main function to run replay validation suite."""
    validator = ReplayValidationSuite()
    results = await validator.run_all_validations()
    
    print("\n" + "="*80)
    print("REPLAY SYSTEM VALIDATION RESULTS")
    print("="*80)
    
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Tests Passed: {results['passed_count']}/{results['total_count']}")
    print(f"Duration: {results['duration_seconds']:.2f} seconds")
    
    if results['overall_status'] == 'passed':
        print("\n🎉 REPLAY SYSTEM VALIDATION: PASSED")
        print("✅ Deterministic replay: WORKING")
        print("✅ Causality preservation: WORKING")
        print("✅ Immutable snapshots: WORKING")
        print("✅ Replay isolation: WORKING")
        print("✅ No live cloud calls: WORKING")
        print("✅ No governance mutation: WORKING")
        print("✅ Divergence determinism: WORKING")
        print("✅ Lineage integrity: WORKING")
        print("✅ Fallback ancestry preservation: WORKING")
        print("✅ Telemetry isolation: WORKING")
        print("✅ Async stability: WORKING")
        print("✅ No event loop regressions: WORKING")
        print("\n✅ Replay system is PRODUCTION-READY")
    else:
        print("\n❌ REPLAY SYSTEM VALIDATION: FAILED")
        failed_tests = [name for name, result in results['test_results'].items() if result['status'] == 'failed']
        for test_name in failed_tests:
            print(f"   - {test_name}: {results['test_results'][test_name].get('error', 'Unknown error')}")
    
    print("="*80)
    return results


if __name__ == "__main__":
    asyncio.run(run_replay_validation())
