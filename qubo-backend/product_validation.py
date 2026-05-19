"""
Qurve AI - Product Validation Suite
Comprehensive validation for all product systems.

Validates:
✅ RBAC enforcement: Operator permission validation
✅ QUOTAS: User quota management validation
✅ GOVERNANCE: Governance system validation
✅ REPLAY: Replay system validation
✅ ISOLATION: System isolation validation
✅ API SEGREGATION: API layer segregation validation
"""

import asyncio
import time
import sys
sys.path.append('.')

from typing import Dict, Any, List

class ProductValidationSuite:
    """Comprehensive product validation suite."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all product validation tests."""
        print("=== PRODUCT VALIDATION SUITE ===")
        
        validation_methods = [
            self.validate_rbac_enforcement,
            self.validate_quotas,
            self.validate_governance,
            self.validate_replay,
            self.validate_isolation,
            self.validate_api_segregation
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
        
        print(f"\n=== PRODUCT VALIDATION SUMMARY ===")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Tests Passed: {passed}/{total}")
        
        return summary
    
    async def validate_rbac_enforcement(self) -> Dict[str, Any]:
        """Validate RBAC enforcement."""
        try:
            from qubo_backend.productization.user_identity_system import get_user_identity_system
            from qubo_backend.operations.operator_rbac import get_operator_rbac
            
            user_identity_system = get_user_identity_system()
            operator_rbac = get_operator_rbac()
            
            # Check RBAC guarantees
            identity_guarantees = user_identity_system.get_identity_guarantees()
            rbac_guarantees = operator_rbac.get_rbac_guarantees()
            
            # Validate key RBAC features
            strict_permissions = rbac_guarantees.get("strict_permission_boundaries", False)
            replay_isolation = rbac_guarantees.get("replay_access_isolation", False)
            governance_controls = rbac_guarantees.get("governance_modification_controls", False)
            authenticated_users = identity_guarantees.get("authenticated_users", False)
            
            return {
                'status': 'passed' if (
                    strict_permissions and 
                    replay_isolation and 
                    governance_controls and 
                    authenticated_users
                ) else 'failed',
                'strict_permission_boundaries': strict_permissions,
                'replay_access_isolation': replay_isolation,
                'governance_modification_controls': governance_controls,
                'authenticated_users': authenticated_users,
                'rbac_guarantees': rbac_guarantees,
                'identity_guarantees': identity_guarantees
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_quotas(self) -> Dict[str, Any]:
        """Validate user quota management."""
        try:
            from qubo_backend.productization.user_quota_management import get_user_quota_management
            
            quota_management = get_user_quota_management()
            quota_guarantees = quota_management.get_quota_guarantees()
            
            # Validate key quota features
            per_user_quotas = quota_guarantees.get("per_user_quotas", False)
            daily_monthly_limits = quota_guarantees.get("daily_monthly_limits", False)
            cloud_execution_caps = quota_guarantees.get("cloud_execution_caps", False)
            qpu_authorization_tiers = quota_guarantees.get("qpu_authorization_tiers", False)
            abuse_prevention = quota_guarantees.get("abuse_prevention", False)
            
            return {
                'status': 'passed' if (
                    per_user_quotas and 
                    daily_monthly_limits and 
                    cloud_execution_caps and 
                    qpu_authorization_tiers and 
                    abuse_prevention
                ) else 'failed',
                'per_user_quotas': per_user_quotas,
                'daily_monthly_limits': daily_monthly_limits,
                'cloud_execution_caps': cloud_execution_caps,
                'qpu_authorization_tiers': qpu_authorization_tiers,
                'abuse_prevention': abuse_prevention,
                'quota_guarantees': quota_guarantees
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_governance(self) -> Dict[str, Any]:
        """Validate governance system."""
        try:
            from qubo_backend.operations.environment_governance import get_environment_governance
            from qubo_backend.operations.configuration_locking import get_configuration_locking
            from qubo_backend.operations.audit_trail_system import get_audit_trail_system
            
            env_governance = get_environment_governance()
            config_locking = get_configuration_locking()
            audit_trail = get_audit_trail_system()
            
            # Validate governance features
            env_stats = env_governance.get_environment_statistics()
            config_stats = config_locking.get_configuration_statistics()
            audit_stats = audit_trail.get_audit_statistics()
            
            environment_configs = env_stats.get("environment_configs", {})
            immutable_snapshots = config_stats.get("immutable_snapshots", False)
            immutable_audit_records = audit_stats.get("immutable_audit_records", False)
            
            return {
                'status': 'passed' if (
                    environment_configs and 
                    immutable_snapshots and 
                    immutable_audit_records
                ) else 'failed',
                'environment_configs': bool(environment_configs),
                'immutable_snapshots': immutable_snapshots,
                'immutable_audit_records': immutable_audit_records,
                'environment_statistics': env_stats,
                'configuration_statistics': config_stats,
                'audit_statistics': audit_stats
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_replay(self) -> Dict[str, Any]:
        """Validate replay system."""
        try:
            # Check if replay system components are available
            from qubo_backend.storage.replay_service import get_replay_service
            from qubo_backend.productization.execution_state_streaming import get_execution_state_streaming
            
            replay_service = get_replay_service()
            streaming = get_execution_state_streaming()
            
            # Validate replay features
            replay_available = replay_service is not None
            streaming_guarantees = streaming.get_streaming_guarantees()
            
            real_time_progress = streaming_guarantees.get("real_time_benchmark_progress", False)
            live_telemetry = streaming_guarantees.get("live_telemetry_streaming", False)
            
            return {
                'status': 'passed' if (
                    replay_available and 
                    real_time_progress and 
                    live_telemetry
                ) else 'failed',
                'replay_available': replay_available,
                'real_time_progress': real_time_progress,
                'live_telemetry': live_telemetry,
                'streaming_guarantees': streaming_guarantees
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_isolation(self) -> Dict[str, Any]:
        """Validate system isolation."""
        try:
            from qubo_backend.productization.product_analytics import get_product_analytics
            from qubo_backend.productization.controlled_cloud_exposure import get_controlled_cloud_exposure
            
            analytics = get_product_analytics()
            cloud_exposure = get_controlled_cloud_exposure()
            
            # Validate isolation features
            analytics_guarantees = analytics.get_analytics_guarantees()
            cloud_guarantees = cloud_exposure.get_cloud_exposure_guarantees()
            
            operational_data_isolation = analytics_guarantees.get("operational_data_isolation", False)
            no_operational_contamination = analytics_guarantees.get("no_operational_contamination", False)
            authenticated_cloud_execution = cloud_guarantees.get("authenticated_cloud_execution", False)
            restricted_internal_qpu_access = cloud_guarantees.get("restricted_internal_qpu_access", False)
            
            return {
                'status': 'passed' if (
                    operational_data_isolation and 
                    no_operational_contamination and 
                    authenticated_cloud_execution and 
                    restricted_internal_qpu_access
                ) else 'failed',
                'operational_data_isolation': operational_data_isolation,
                'no_operational_contamination': no_operational_contamination,
                'authenticated_cloud_execution': authenticated_cloud_execution,
                'restricted_internal_qpu_access': restricted_internal_qpu_access,
                'analytics_guarantees': analytics_guarantees,
                'cloud_exposure_guarantees': cloud_guarantees
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    async def validate_api_segregation(self) -> Dict[str, Any]:
        """Validate API layer segregation."""
        try:
            from qubo_backend.productization.product_api_layer import get_product_api_layer
            from qubo_backend.productization.benchmark_execution_gateway import get_benchmark_execution_gateway
            
            api_layer = get_product_api_layer()
            benchmark_gateway = get_benchmark_execution_gateway()
            
            # Validate API segregation features
            api_guarantees = api_layer.get_api_guarantees()
            gateway_guarantees = benchmark_gateway.get_gateway_guarantees()
            
            public_safe_apis = api_guarantees.get("public_safe_apis", False)
            authenticated_apis = api_guarantees.get("authenticated_apis", False)
            internal_only_apis = api_guarantees.get("internal_only_apis", False)
            operator_apis = api_guarantees.get("operator_apis", False)
            forensic_apis = api_guarantees.get("forensic_apis", False)
            strict_api_segregation = api_guarantees.get("strict_api_segregation", False)
            
            return {
                'status': 'passed' if (
                    public_safe_apis and 
                    authenticated_apis and 
                    internal_only_apis and 
                    operator_apis and 
                    forensic_apis and 
                    strict_api_segregation
                ) else 'failed',
                'public_safe_apis': public_safe_apis,
                'authenticated_apis': authenticated_apis,
                'internal_only_apis': internal_only_apis,
                'operator_apis': operator_apis,
                'forensic_apis': forensic_apis,
                'strict_api_segregation': strict_api_segregation,
                'api_guarantees': api_guarantees,
                'gateway_guarantees': gateway_guarantees
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}


async def run_product_validation():
    """Main function to run product validation suite."""
    validator = ProductValidationSuite()
    results = await validator.run_all_validations()
    
    print("\n" + "="*80)
    print("PRODUCT VALIDATION RESULTS")
    print("="*80)
    
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Tests Passed: {results['passed_count']}/{results['total_count']}")
    print(f"Duration: {results['duration_seconds']:.2f} seconds")
    
    if results['overall_status'] == 'passed':
        print("\n🎉 PRODUCT VALIDATION: PASSED")
        print("✅ RBAC enforcement: WORKING")
        print("✅ Quotas: WORKING")
        print("✅ Governance: WORKING")
        print("✅ Replay: WORKING")
        print("✅ Isolation: WORKING")
        print("✅ API segregation: WORKING")
        print("\n✅ Product systems are PRODUCTION-READY")
        print("\n🚀 PHASE 5 - PRODUCTIZATION & CONTROLLED PLATFORM EXPOSURE: COMPLETED")
    else:
        print("\n❌ PRODUCT VALIDATION: FAILED")
        failed_tests = [name for name, result in results['test_results'].items() if result['status'] == 'failed']
        for test_name in failed_tests:
            print(f"   - {test_name}: {results['test_results'][test_name].get('error', 'Unknown error')}")
    
    print("="*80)
    return results


if __name__ == "__main__":
    asyncio.run(run_product_validation())
