#!/usr/bin/env python3
"""
QURVE AI - API Execution Flow Validation
Validate complete API execution flow: Frontend/API → Benchmark → Governance → Cloud Execution → AWS Braket → Persistence → Telemetry → Monitoring.

This is NOT architecture work.
This IS runtime infrastructure repair.
"""

import os
import sys
import time
import logging
import requests
from typing import Dict, Any

# Add qubo-backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'qubo-backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIExecutionFlowValidator:
    """
    Validate complete API execution flow.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.backend_url = 'http://localhost:8000'
        
        logger.info("API execution flow validator initialized")
    
    def validate_execution_flow(self) -> Dict[str, Any]:
        """Validate complete API execution flow."""
        try:
            logger.info("Validating API execution flow...")
            
            # Step 1: Test API connectivity
            connectivity_result = self._test_api_connectivity()
            
            # Step 2: Test benchmark submission
            benchmark_submission_result = self._test_benchmark_submission()
            
            # Step 3: Test governance integration
            governance_result = self._test_governance_integration()
            
            # Step 4: Test cloud execution
            cloud_execution_result = self._test_cloud_execution()
            
            # Step 5: Test persistence
            persistence_result = self._test_persistence()
            
            # Step 6: Test telemetry
            telemetry_result = self._test_telemetry()
            
            # Step 7: Test monitoring
            monitoring_result = self._test_monitoring()
            
            # Determine overall success
            all_passed = (
                connectivity_result['success'] and
                benchmark_submission_result['success'] and
                governance_result['success'] and
                cloud_execution_result['success'] and
                persistence_result['success'] and
                telemetry_result['success'] and
                monitoring_result['success']
            )
            
            return {
                'overall_success': all_passed,
                'connectivity_result': connectivity_result,
                'benchmark_submission_result': benchmark_submission_result,
                'governance_result': governance_result,
                'cloud_execution_result': cloud_execution_result,
                'persistence_result': persistence_result,
                'telemetry_result': telemetry_result,
                'monitoring_result': monitoring_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"API execution flow validation failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _test_api_connectivity(self) -> Dict[str, Any]:
        """Test API connectivity."""
        try:
            # Test health endpoint
            health_response = requests.get(f'{self.backend_url}/health', timeout=5)
            
            # Test benchmarks endpoint
            benchmarks_response = requests.get(f'{self.backend_url}/api/benchmarks', timeout=5)
            
            # Test monitoring endpoint
            monitoring_response = requests.get(f'{self.backend_url}/api/monitoring', timeout=5)
            
            all_ok = (
                health_response.status_code == 200 and
                benchmarks_response.status_code == 200 and
                monitoring_response.status_code == 200
            )
            
            return {
                'success': all_ok,
                'health_status': health_response.status_code,
                'benchmarks_status': benchmarks_response.status_code,
                'monitoring_status': monitoring_response.status_code,
                'api_accessible': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'api_accessible': False
            }
    
    def _test_benchmark_submission(self) -> Dict[str, Any]:
        """Test benchmark submission."""
        try:
            # Create benchmark request with string keys for JSON serialization
            qubo_dict = {"0,0": 1, "1,1": 1, "0,1": -1}
            benchmark_request = {
                'name': 'api_flow_test',
                'qubo': qubo_dict,
                'execution_mode': 'local',  # Use local for API flow test
                'shots': 10,
                'description': 'API execution flow test'
            }
            
            # Submit benchmark
            response = requests.post(
                f'{self.backend_url}/api/benchmarks',
                json=benchmark_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'benchmark_id': result.get('id', 'unknown'),
                    'execution_mode': result.get('execution_mode', 'unknown'),
                    'status': result.get('status', 'unknown')
                }
            else:
                return {
                    'success': False,
                    'error': f'API returned status {response.status_code}',
                    'response_text': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_governance_integration(self) -> Dict[str, Any]:
        """Test governance integration."""
        try:
            from qubo_backend.cost.cost_governance import CostGovernance, QuotaConfig, CloudDevice
            
            # Initialize governance with quota config
            quota_config = QuotaConfig()
            governance = CostGovernance(quota_config)
            
            # Test cost estimation with correct signature
            estimated_cost = governance.estimate_cost(CloudDevice.TN1_SIMULATOR, 10)
            
            return {
                'success': True,
                'estimated_cost': estimated_cost,
                'governance_operational': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'governance_operational': False
            }
    
    def _test_cloud_execution(self) -> Dict[str, Any]:
        """Test cloud execution with real AWS Braket."""
        try:
            import boto3
            from braket.aws import AwsDevice
            from braket.circuits import Circuit
            
            # Create session
            session = boto3.Session(region_name='us-east-1')
            
            # Get TN1 device
            braket_client = session.client('braket')
            devices = braket_client.search_devices(filters=[])
            tn1_arn = None
            for device in devices.get('devices', []):
                if device.get('deviceName') == 'TN1':
                    tn1_arn = device.get('deviceArn')
                    break
            
            if not tn1_arn:
                return {
                    'success': False,
                    'error': 'TN1 simulator not available'
                }
            
            # Create device
            tn1_device = AwsDevice(tn1_arn)
            
            # Create simple circuit
            circuit = Circuit().h(0).cnot(0, 1)
            
            # Execute
            task = tn1_device.run(circuit, shots=10)
            
            # Wait for completion
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if task.state() == 'COMPLETED':
                    result = task.result()
                    break
                elif task.state() == 'FAILED':
                    raise Exception(f'Task failed: {task.state()}')
                time.sleep(2)
            else:
                raise Exception('Task timed out')
            
            return {
                'success': True,
                'task_id': task.id,
                'device_arn': tn1_arn,
                'device_name': 'TN1',
                'shots': 10,
                'measurements': result.measurement_counts,
                'execution_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_persistence(self) -> Dict[str, Any]:
        """Test persistence systems."""
        try:
            from qubo_backend.storage.execution_storage import get_execution_storage, create_benchmark_run, create_solver_execution
            
            # Get storage instance
            storage = get_execution_storage()
            
            # Create test benchmark run
            benchmark = create_benchmark_run(
                correlation_id='api_flow_test',
                selected_solver='braket',
                execution_mode='local',
                num_assets=2
            )
            
            # Create test solver execution
            execution = create_solver_execution(
                benchmark_id=benchmark.benchmark_id,
                solver_name='braket',
                provider='aws',
                backend='braket'
            )
            
            return {
                'success': True,
                'benchmark_created': benchmark.benchmark_id,
                'execution_created': execution.execution_id,
                'persistence_operational': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'persistence_operational': False
            }
    
    def _test_telemetry(self) -> Dict[str, Any]:
        """Test telemetry systems."""
        try:
            from qubo_backend.telemetry.structured_telemetry import get_telemetry_state
            
            # Get telemetry state
            telemetry_state = get_telemetry_state()
            
            return {
                'success': True,
                'telemetry_state': telemetry_state,
                'telemetry_operational': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'telemetry_operational': False
            }
    
    def _test_monitoring(self) -> Dict[str, Any]:
        """Test monitoring systems."""
        try:
            from qubo_backend.monitoring.monitoring_service import get_monitoring_service
            
            # Get monitoring service
            monitoring = get_monitoring_service()
            
            # Get monitoring statistics
            stats = monitoring.get_system_metrics()
            
            return {
                'success': True,
                'monitoring_stats': stats,
                'monitoring_operational': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'monitoring_operational': False
            }
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print validation results."""
        print("\n" + "="*80)
        print("API EXECUTION FLOW VALIDATION RESULTS")
        print("="*80)
        
        # Overall status
        status_emoji = "✅" if results.get('overall_success', False) else "❌"
        print(f"\nOverall Status: {status_emoji} {'PASSED' if results.get('overall_success', False) else 'FAILED'}")
        
        # Connectivity results
        connectivity_result = results.get('connectivity_result', {})
        if connectivity_result.get('success', False):
            print(f"\n✅ API Connectivity:")
            print(f"  Health Status: {connectivity_result.get('health_status', 'unknown')}")
            print(f"  Benchmarks Status: {connectivity_result.get('benchmarks_status', 'unknown')}")
            print(f"  Monitoring Status: {connectivity_result.get('monitoring_status', 'unknown')}")
        else:
            print(f"\n❌ API Connectivity: {connectivity_result.get('error', 'unknown')}")
        
        # Benchmark submission results
        benchmark_submission_result = results.get('benchmark_submission_result', {})
        if benchmark_submission_result.get('success', False):
            print(f"\n✅ Benchmark Submission:")
            print(f"  Benchmark ID: {benchmark_submission_result.get('benchmark_id', 'unknown')}")
            print(f"  Execution Mode: {benchmark_submission_result.get('execution_mode', 'unknown')}")
            print(f"  Status: {benchmark_submission_result.get('status', 'unknown')}")
        else:
            print(f"\n❌ Benchmark Submission: {benchmark_submission_result.get('error', 'unknown')}")
        
        # Governance results
        governance_result = results.get('governance_result', {})
        if governance_result.get('success', False):
            print(f"\n✅ Governance Integration:")
            print(f"  Cost Estimation: {governance_result.get('estimated_cost', 'unknown')}")
            print(f"  Governance Operational: {governance_result.get('governance_operational', False)}")
        else:
            print(f"\n❌ Governance Integration: {governance_result.get('error', 'unknown')}")
        
        # Cloud execution results
        cloud_execution_result = results.get('cloud_execution_result', {})
        if cloud_execution_result.get('success', False):
            print(f"\n✅ Cloud Execution:")
            print(f"  Task ID: {cloud_execution_result.get('task_id', 'unknown')}")
            print(f"  Device: {cloud_execution_result.get('device_name', 'unknown')}")
            print(f"  Shots: {cloud_execution_result.get('shots', 0)}")
            print(f"  Measurements: {cloud_execution_result.get('measurements', {})}")
            print(f"  Execution Time: {cloud_execution_result.get('execution_time', 0):.2f}s")
        else:
            print(f"\n❌ Cloud Execution: {cloud_execution_result.get('error', 'unknown')}")
        
        # Persistence results
        persistence_result = results.get('persistence_result', {})
        if persistence_result.get('success', False):
            print(f"\n✅ Persistence:")
            print(f"  Benchmark Created: {persistence_result.get('benchmark_created', 'unknown')}")
            print(f"  Execution Created: {persistence_result.get('execution_created', 'unknown')}")
            print(f"  Persistence Operational: {persistence_result.get('persistence_operational', False)}")
        else:
            print(f"\n❌ Persistence: {persistence_result.get('error', 'unknown')}")
        
        # Telemetry results
        telemetry_result = results.get('telemetry_result', {})
        if telemetry_result.get('success', False):
            print(f"\n✅ Telemetry:")
            print(f"  Telemetry State: {telemetry_result.get('telemetry_state', 'unknown')}")
            print(f"  Telemetry Operational: {telemetry_result.get('telemetry_operational', False)}")
        else:
            print(f"\n❌ Telemetry: {telemetry_result.get('error', 'unknown')}")
        
        # Monitoring results
        monitoring_result = results.get('monitoring_result', {})
        if monitoring_result.get('success', False):
            print(f"\n✅ Monitoring:")
            print(f"  Monitoring Stats: {monitoring_result.get('monitoring_stats', 'unknown')}")
            print(f"  Monitoring Operational: {monitoring_result.get('monitoring_operational', False)}")
        else:
            print(f"\n❌ Monitoring: {monitoring_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if results.get('overall_success', False):
            print("🏆 API EXECUTION FLOW VALIDATION: PASSED")
            print("✅ API connectivity working")
            print("✅ Benchmark submission working")
            print("✅ Governance integration working")
            print("✅ Cloud execution working")
            print("✅ Persistence working")
            print("✅ Telemetry working")
            print("✅ Monitoring working")
        else:
            print("❌ API EXECUTION FLOW VALIDATION: FAILED")
            print("❌ API execution flow not complete")
        
        print("="*80)


def main():
    """Main validation execution."""
    validator = APIExecutionFlowValidator()
    
    try:
        results = validator.validate_execution_flow()
        validator.print_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ API execution flow validation interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ API execution flow validation failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
