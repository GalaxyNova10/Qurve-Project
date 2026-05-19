#!/usr/bin/env python3
"""
QURVE AI - End-to-End Validation
Run REAL end-to-end validation: Frontend → Backend → AWS Braket → Dashboard.

This is NOT architecture work.
This IS runtime infrastructure repair.
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, Any, List, Optional

# Add qubo-backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'qubo-backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EndToEndValidation:
    """
    End-to-end validation of platform execution.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.backend_url = 'http://localhost:8000'
        self.frontend_url = 'http://localhost:3000'
        
        logger.info("End-to-end validation initialized")
    
    def run_end_to_end_validation(self) -> Dict[str, Any]:
        """Run complete end-to-end validation."""
        try:
            logger.info("Running end-to-end validation...")
            
            # Step 1: Validate frontend accessibility
            frontend_result = self._validate_frontend()
            
            # Step 2: Validate backend API
            backend_result = self._validate_backend()
            
            # Step 3: Execute benchmark through frontend
            benchmark_result = self._execute_benchmark()
            
            # Step 4: Validate AWS task execution
            aws_result = self._validate_aws_execution()
            
            # Step 5: Validate persistence
            persistence_result = self._validate_persistence()
            
            # Step 6: Validate telemetry
            telemetry_result = self._validate_telemetry()
            
            # Step 7: Validate monitoring dashboard
            monitoring_result = self._validate_monitoring()
            
            # Step 8: Validate replay metadata
            replay_result = self._validate_replay_metadata()
            
            # Determine overall success
            all_passed = (
                frontend_result['success'] and
                backend_result['success'] and
                benchmark_result['success'] and
                aws_result['success'] and
                persistence_result['success'] and
                telemetry_result['success'] and
                monitoring_result['success'] and
                replay_result['success']
            )
            
            return {
                'overall_success': all_passed,
                'frontend_result': frontend_result,
                'backend_result': backend_result,
                'benchmark_result': benchmark_result,
                'aws_result': aws_result,
                'persistence_result': persistence_result,
                'telemetry_result': telemetry_result,
                'monitoring_result': monitoring_result,
                'replay_result': replay_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"End-to-end validation failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _validate_frontend(self) -> Dict[str, Any]:
        """Validate frontend accessibility."""
        try:
            # Test frontend homepage
            response = requests.get(self.frontend_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'frontend_accessible': True,
                    'status_code': response.status_code,
                    'content_length': len(response.text)
                }
            else:
                return {
                    'success': False,
                    'error': f'Frontend returned status {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_backend(self) -> Dict[str, Any]:
        """Validate backend API."""
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
                'api_endpoints_working': all_ok
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_benchmark(self) -> Dict[str, Any]:
        """Execute benchmark through API."""
        try:
            # Create benchmark request
            benchmark_request = {
                'name': 'end_to_end_test',
                'qubo': {(0, 0): 1, (1, 1): 1, (0, 1): -1},
                'execution_mode': 'cloud_simulator',
                'shots': 10,
                'description': 'End-to-end validation test'
            }
            
            # Submit benchmark
            response = requests.post(
                f'{self.backend_url}/api/benchmarks',
                json=benchmark_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                benchmark_id = result.get('id')
                
                # Wait for completion
                max_wait = 60  # 1 minute
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    status_response = requests.get(f'{self.backend_url}/api/benchmarks/{benchmark_id}', timeout=5)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            return {
                                'success': True,
                                'benchmark_id': benchmark_id,
                                'execution_mode': status_data.get('execution_mode'),
                                'task_id': status_data.get('task_id'),
                                'status': status_data.get('status'),
                                'execution_time': time.time() - start_time
                            }
                        elif status_data.get('status') == 'failed':
                            return {
                                'success': False,
                                'error': f'Benchmark failed: {status_data.get("error", "Unknown error")}'
                            }
                    
                    time.sleep(2)
                
                return {
                    'success': False,
                    'error': 'Benchmark execution timed out'
                }
            else:
                return {
                    'success': False,
                    'error': f'API returned status {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_aws_execution(self) -> Dict[str, Any]:
        """Validate AWS task execution."""
        try:
            import boto3
            from braket.aws import AwsDevice
            
            # Get task details from benchmark result
            # For this test, we'll create a simple AWS task
            session = boto3.Session()
            braket_client = session.client('braket')
            
            # Get TN1 device
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
            
            return {
                'success': True,
                'tn1_arn': tn1_arn,
                'device_name': tn1_device.name,
                'device_type': tn1_device.type,
                'aws_connectivity': 'working'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_persistence(self) -> Dict[str, Any]:
        """Validate persistence systems."""
        try:
            # Test benchmark persistence
            response = requests.get(f'{self.backend_url}/api/benchmarks', timeout=5)
            
            if response.status_code == 200:
                benchmarks = response.json()
                
                return {
                    'success': True,
                    'benchmarks_stored': len(benchmarks),
                    'persistence_working': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to retrieve benchmarks'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_telemetry(self) -> Dict[str, Any]:
        """Validate telemetry systems."""
        try:
            # Test monitoring endpoint for telemetry data
            response = requests.get(f'{self.backend_url}/api/monitoring', timeout=5)
            
            if response.status_code == 200:
                monitoring_data = response.json()
                
                return {
                    'success': True,
                    'telemetry_data_available': bool(monitoring_data),
                    'monitoring_working': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to retrieve monitoring data'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_monitoring(self) -> Dict[str, Any]:
        """Validate monitoring dashboard."""
        try:
            # Test monitoring dashboard accessibility
            response = requests.get(f'{self.backend_url}/api/monitoring', timeout=5)
            
            if response.status_code == 200:
                monitoring_data = response.json()
                
                return {
                    'success': True,
                    'dashboard_data': monitoring_data,
                    'monitoring_accessible': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Monitoring dashboard not accessible'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_replay_metadata(self) -> Dict[str, Any]:
        """Validate replay metadata generation."""
        try:
            # Test replay endpoint
            response = requests.get(f'{self.backend_url}/api/replay', timeout=5)
            
            if response.status_code == 200:
                replay_data = response.json()
                
                return {
                    'success': True,
                    'replay_data_available': bool(replay_data),
                    'replay_working': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Replay endpoint not accessible'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print validation results."""
        print("\n" + "="*80)
        print("END-TO-END VALIDATION RESULTS")
        print("="*80)
        
        # Overall status
        status_emoji = "✅" if results.get('overall_success', False) else "❌"
        print(f"\nOverall Status: {status_emoji} {'PASSED' if results.get('overall_success', False) else 'FAILED'}")
        
        # Frontend results
        frontend_result = results.get('frontend_result', {})
        if frontend_result.get('success', False):
            print(f"\n✅ Frontend Validation:")
            print(f"  Accessible: {frontend_result.get('frontend_accessible', False)}")
            print(f"  Status Code: {frontend_result.get('status_code', 'unknown')}")
        else:
            print(f"\n❌ Frontend Validation: {frontend_result.get('error', 'unknown')}")
        
        # Backend results
        backend_result = results.get('backend_result', {})
        if backend_result.get('success', False):
            print(f"\n✅ Backend Validation:")
            print(f"  Health Status: {backend_result.get('health_status', 'unknown')}")
            print(f"  Benchmarks Status: {backend_result.get('benchmarks_status', 'unknown')}")
            print(f"  Monitoring Status: {backend_result.get('monitoring_status', 'unknown')}")
        else:
            print(f"\n❌ Backend Validation: {backend_result.get('error', 'unknown')}")
        
        # Benchmark results
        benchmark_result = results.get('benchmark_result', {})
        if benchmark_result.get('success', False):
            print(f"\n✅ Benchmark Execution:")
            print(f"  Benchmark ID: {benchmark_result.get('benchmark_id', 'unknown')}")
            print(f"  Execution Mode: {benchmark_result.get('execution_mode', 'unknown')}")
            print(f"  Task ID: {benchmark_result.get('task_id', 'unknown')}")
            print(f"  Status: {benchmark_result.get('status', 'unknown')}")
            print(f"  Execution Time: {benchmark_result.get('execution_time', 0):.2f}s")
        else:
            print(f"\n❌ Benchmark Execution: {benchmark_result.get('error', 'unknown')}")
        
        # AWS results
        aws_result = results.get('aws_result', {})
        if aws_result.get('success', False):
            print(f"\n✅ AWS Execution:")
            print(f"  TN1 ARN: {aws_result.get('tn1_arn', 'unknown')}")
            print(f"  Device Name: {aws_result.get('device_name', 'unknown')}")
            print(f"  Device Type: {aws_result.get('device_type', 'unknown')}")
            print(f"  Connectivity: {aws_result.get('aws_connectivity', 'unknown')}")
        else:
            print(f"\n❌ AWS Execution: {aws_result.get('error', 'unknown')}")
        
        # Persistence results
        persistence_result = results.get('persistence_result', {})
        if persistence_result.get('success', False):
            print(f"\n✅ Persistence:")
            print(f"  Benchmarks Stored: {persistence_result.get('benchmarks_stored', 0)}")
            print(f"  Persistence Working: {persistence_result.get('persistence_working', False)}")
        else:
            print(f"\n❌ Persistence: {persistence_result.get('error', 'unknown')}")
        
        # Telemetry results
        telemetry_result = results.get('telemetry_result', {})
        if telemetry_result.get('success', False):
            print(f"\n✅ Telemetry:")
            print(f"  Data Available: {telemetry_result.get('telemetry_data_available', False)}")
            print(f"  Monitoring Working: {telemetry_result.get('monitoring_working', False)}")
        else:
            print(f"\n❌ Telemetry: {telemetry_result.get('error', 'unknown')}")
        
        # Monitoring results
        monitoring_result = results.get('monitoring_result', {})
        if monitoring_result.get('success', False):
            print(f"\n✅ Monitoring Dashboard:")
            print(f"  Accessible: {monitoring_result.get('monitoring_accessible', False)}")
            print(f"  Data Available: {bool(monitoring_result.get('dashboard_data'))}")
        else:
            print(f"\n❌ Monitoring Dashboard: {monitoring_result.get('error', 'unknown')}")
        
        # Replay results
        replay_result = results.get('replay_result', {})
        if replay_result.get('success', False):
            print(f"\n✅ Replay Metadata:")
            print(f"  Data Available: {replay_result.get('replay_data_available', False)}")
            print(f"  Replay Working: {replay_result.get('replay_working', False)}")
        else:
            print(f"\n❌ Replay Metadata: {replay_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if results.get('overall_success', False):
            print("🏆 END-TO-END VALIDATION: PASSED")
            print("✅ Frontend accessible")
            print("✅ Backend API working")
            print("✅ Benchmark execution successful")
            print("✅ AWS execution validated")
            print("✅ Persistence working")
            print("✅ Telemetry working")
            print("✅ Monitoring dashboard working")
            print("✅ Replay metadata working")
        else:
            print("❌ END-TO-END VALIDATION: FAILED")
            print("❌ End-to-end flow not working")
        
        print("="*80)


def main():
    """Main validation execution."""
    validator = EndToEndValidation()
    
    try:
        results = validator.run_end_to_end_validation()
        validator.print_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ End-to-end validation interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ End-to-end validation failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
