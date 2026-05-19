#!/usr/bin/env python3
"""
QURVE AI - Working Cloud Execution Test
CORRECTED AWS Braket execution with proper device discovery.

This is NOT architecture work.
This IS runtime infrastructure repair.
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkingCloudExecutionTest:
    """
    Working cloud execution test with corrected device discovery.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.boto3_session = None
        self.braket_client = None
        
        logger.info("Working cloud execution test initialized")
    
    def run_execution_test(self) -> Dict[str, Any]:
        """Run working cloud execution test."""
        try:
            logger.info("Starting working cloud execution test...")
            
            # Step 1: Initialize AWS session
            session_result = self._initialize_aws_session()
            
            # Step 2: Initialize Braket client
            braket_result = self._initialize_braket_client()
            
            # Step 3: Discover available devices
            device_discovery_result = self._discover_available_devices()
            
            # Step 4: Create minimal circuit
            circuit_result = self._create_minimal_circuit()
            
            # Step 5: Execute on available simulator
            execution_result = self._execute_on_simulator(
                circuit_result['circuit'],
                device_discovery_result['simulators']
            )
            
            # Step 6: Analyze results
            analysis_result = self._analyze_results(execution_result)
            
            # Determine overall success
            all_passed = (
                session_result['success'] and
                braket_result['success'] and
                device_discovery_result['success'] and
                circuit_result['success'] and
                execution_result['success'] and
                analysis_result['success']
            )
            
            return {
                'overall_success': all_passed,
                'session_result': session_result,
                'braket_result': braket_result,
                'device_discovery_result': device_discovery_result,
                'circuit_result': circuit_result,
                'execution_result': execution_result,
                'analysis_result': analysis_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Working cloud execution test failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _initialize_aws_session(self) -> Dict[str, Any]:
        """Initialize AWS session."""
        try:
            import boto3
            
            # Create session
            self.boto3_session = boto3.Session(
                region_name=self.aws_region
            )
            
            # Test session by getting caller identity
            sts_client = self.boto3_session.client('sts')
            identity = sts_client.get_caller_identity()
            
            # Get credentials info (safely)
            credentials = self.boto3_session.get_credentials()
            credential_source = "unknown"
            
            if credentials:
                if credentials.method == 'env':
                    credential_source = "environment_variables"
                elif credentials.method == 'iam-role':
                    credential_source = "iam_role"
                elif credentials.method == 'shared-credentials-file':
                    credential_source = "shared_credentials_file"
            
            return {
                'success': True,
                'region': self.aws_region,
                'credential_source': credential_source,
                'identity_arn': identity.get('Arn', 'unknown'),
                'account_id': identity.get('Account', 'unknown'),
                'user_id': identity.get('UserId', 'unknown')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'region': self.aws_region
            }
    
    def _initialize_braket_client(self) -> Dict[str, Any]:
        """Initialize Braket client."""
        try:
            self.braket_client = self.boto3_session.client('braket')
            
            return {
                'success': True,
                'client_initialized': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _discover_available_devices(self) -> Dict[str, Any]:
        """Discover available devices."""
        try:
            # Get all devices with empty filters (this works)
            response = self.braket_client.search_devices(filters=[])
            
            devices = response.get('devices', [])
            
            # Categorize devices
            simulators = []
            qpns = []
            
            for device in devices:
                device_arn = device.get('deviceArn', '')
                device_name = device.get('deviceName', '')
                device_type = device.get('deviceType', '')
                
                device_info = {
                    'arn': device_arn,
                    'name': device_name,
                    'type': device_type,
                    'status': device.get('status', 'unknown'),
                    'provider': device.get('providerName', 'unknown')
                }
                
                if 'simulator' in device_type.lower():
                    simulators.append(device_info)
                elif 'qpu' in device_type.lower():
                    qpns.append(device_info)
            
            return {
                'success': True,
                'total_devices': len(devices),
                'simulators': simulators,
                'qpns': qpns,
                'all_devices': devices
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_minimal_circuit(self) -> Dict[str, Any]:
        """Create minimal Bell-state circuit."""
        try:
            # Import Braket SDK
            from braket.circuits import Circuit
            
            # Create minimal Bell state circuit (2 qubits)
            # H on qubit 0, CNOT from 0 to 1
            circuit = Circuit().h(0).cnot(0, 1)
            
            return {
                'success': True,
                'circuit': circuit,
                'qubit_count': circuit.qubit_count,
                'circuit_depth': circuit.depth,
                'circuit_instructions': str(circuit.instructions),
                'circuit_type': 'bell_state'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_on_simulator(self, circuit, simulators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute on available simulator."""
        try:
            if not simulators:
                return {
                    'success': False,
                    'error': 'No simulators available'
                }
            
            # Use first available simulator
            first_simulator = simulators[0]
            simulator_arn = first_simulator['arn']
            simulator_name = first_simulator['name']
            
            # Import Braket SDK
            from braket.aws import AwsDevice
            from braket.tasks import QuantumTask
            
            # Get device
            device = AwsDevice(simulator_arn)
            
            # Record start time
            task_start_time = time.time()
            
            # Execute circuit with minimal parameters
            task = device.run(
                circuit,
                shots=10,  # Minimal shots
                poll_timeout_seconds=300  # 5 minute timeout
            )
            
            # Record submission time
            submission_time = time.time() - task_start_time
            
            # Poll for completion
            poll_start_time = time.time()
            result = None
            
            while time.time() - poll_start_time < 300:  # 5 minute timeout
                try:
                    if task.state() == 'COMPLETED':
                        result = task.result()
                        break
                    elif task.state() == 'FAILED':
                        raise Exception(f"Task failed: {task.state()}")
                    
                    # Wait before next poll
                    time.sleep(2)
                    
                except Exception as e:
                    raise Exception(f"Task polling failed: {str(e)}")
            
            if result is None:
                raise Exception("Task timed out after 5 minutes")
            
            # Record completion time
            completion_time = time.time() - poll_start_time
            total_time = time.time() - task_start_time
            
            # Extract measurement results
            measurement_counts = result.measurement_counts
            
            return {
                'success': True,
                'task_id': task.id,
                'simulator_name': simulator_name,
                'simulator_arn': simulator_arn,
                'shots': 10,
                'qubits': circuit.qubit_count,
                'circuit_depth': circuit.depth,
                'submission_time_seconds': submission_time,
                'completion_time_seconds': completion_time,
                'total_time_seconds': total_time,
                'task_state': task.state(),
                'measurement_counts': measurement_counts,
                'result_metadata': result.task_metadata if hasattr(result, 'task_metadata') else {}
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_results(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze execution results."""
        try:
            if not execution_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Cannot analyze failed execution'
                }
            
            measurement_counts = execution_result.get('measurement_counts', {})
            total_time = execution_result.get('total_time_seconds', 0)
            
            # Analyze Bell state results
            expected_bell_states = {'00', '11'}  # Expected for Bell state
            measured_states = set(measurement_counts.keys())
            
            # Check if we got expected Bell states
            has_expected_states = expected_bell_states.intersection(measured_states)
            
            # Calculate distribution
            total_shots = sum(measurement_counts.values())
            state_distribution = {
                state: count / total_shots
                for state, count in measurement_counts.items()
            }
            
            # Bell state fidelity (simplified)
            bell_fidelity = 0.0
            if '00' in measurement_counts and '11' in measurement_counts:
                bell_fidelity = (measurement_counts['00'] + measurement_counts['11']) / total_shots
            
            return {
                'success': True,
                'bell_state_analysis': {
                    'expected_states': expected_bell_states,
                    'measured_states': measured_states,
                    'has_expected_states': has_expected_states,
                    'bell_fidelity': bell_fidelity,
                    'state_distribution': state_distribution
                },
                'performance_analysis': {
                    'total_time_seconds': total_time,
                    'submission_time_seconds': execution_result.get('submission_time_seconds', 0),
                    'completion_time_seconds': execution_result.get('completion_time_seconds', 0),
                    'shots_per_second': total_shots / total_time if total_time > 0 else 0
                },
                'execution_metadata': {
                    'task_id': execution_result.get('task_id', 'unknown'),
                    'simulator_name': execution_result.get('simulator_name', 'unknown'),
                    'simulator_arn': execution_result.get('simulator_arn', 'unknown'),
                    'shots': execution_result.get('shots', 0),
                    'qubits': execution_result.get('qubits', 0)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print test results."""
        print("\n" + "="*80)
        print("WORKING CLOUD EXECUTION TEST RESULTS")
        print("="*80)
        
        # Overall status
        status_emoji = "✅" if results.get('overall_success', False) else "❌"
        print(f"\nOverall Status: {status_emoji} {'PASSED' if results.get('overall_success', False) else 'FAILED'}")
        
        # Session results
        session_result = results.get('session_result', {})
        if session_result.get('success', False):
            print(f"\n✅ AWS Session:")
            print(f"  Region: {session_result.get('region', 'unknown')}")
            print(f"  Credential Source: {session_result.get('credential_source', 'unknown')}")
            print(f"  Account ID: {session_result.get('account_id', 'unknown')}")
            print(f"  User ID: {session_result.get('user_id', 'unknown')}")
        else:
            print(f"\n❌ AWS Session: {session_result.get('error', 'unknown')}")
        
        # Braket client results
        braket_result = results.get('braket_result', {})
        if braket_result.get('success', False):
            print(f"\n✅ Braket Client: Initialized")
        else:
            print(f"\n❌ Braket Client: {braket_result.get('error', 'unknown')}")
        
        # Device discovery results
        device_discovery_result = results.get('device_discovery_result', {})
        if device_discovery_result.get('success', False):
            print(f"\n✅ Device Discovery:")
            print(f"  Total Devices: {device_discovery_result.get('total_devices', 0)}")
            print(f"  Simulators: {len(device_discovery_result.get('simulators', []))}")
            print(f"  QPUs: {len(device_discovery_result.get('qpns', []))}")
            
            # List simulators
            simulators = device_discovery_result.get('simulators', [])
            if simulators:
                print(f"\n  Available Simulators:")
                for sim in simulators:
                    print(f"    - {sim.get('name', 'unknown')}: {sim.get('arn', 'unknown')}")
        else:
            print(f"\n❌ Device Discovery: {device_discovery_result.get('error', 'unknown')}")
        
        # Circuit results
        circuit_result = results.get('circuit_result', {})
        if circuit_result.get('success', False):
            print(f"\n✅ Circuit Creation:")
            print(f"  Circuit Type: {circuit_result.get('circuit_type', 'unknown')}")
            print(f"  Qubit Count: {circuit_result.get('qubit_count', 0)}")
            print(f"  Circuit Depth: {circuit_result.get('circuit_depth', 0)}")
        else:
            print(f"\n❌ Circuit Creation: {circuit_result.get('error', 'unknown')}")
        
        # Execution results
        execution_result = results.get('execution_result', {})
        if execution_result.get('success', False):
            print(f"\n✅ Cloud Execution:")
            print(f"  Task ID: {execution_result.get('task_id', 'unknown')}")
            print(f"  Simulator: {execution_result.get('simulator_name', 'unknown')}")
            print(f"  Shots: {execution_result.get('shots', 0)}")
            print(f"  Qubits: {execution_result.get('qubits', 0)}")
            print(f"  Submission Time: {execution_result.get('submission_time_seconds', 0):.2f}s")
            print(f"  Completion Time: {execution_result.get('completion_time_seconds', 0):.2f}s")
            print(f"  Total Time: {execution_result.get('total_time_seconds', 0):.2f}s")
            print(f"  Task State: {execution_result.get('task_state', 'unknown')}")
            print(f"  Measurement Counts: {execution_result.get('measurement_counts', {})}")
        else:
            print(f"\n❌ Cloud Execution: {execution_result.get('error', 'unknown')}")
        
        # Analysis results
        analysis_result = results.get('analysis_result', {})
        if analysis_result.get('success', False):
            bell_analysis = analysis_result.get('bell_state_analysis', {})
            perf_analysis = analysis_result.get('performance_analysis', {})
            
            print(f"\n✅ Results Analysis:")
            print(f"  Bell Fidelity: {bell_analysis.get('bell_fidelity', 0):.3f}")
            print(f"  Expected States: {bell_analysis.get('expected_states', set())}")
            print(f"  Measured States: {bell_analysis.get('measured_states', set())}")
            print(f"  State Distribution: {bell_analysis.get('state_distribution', {})}")
            print(f"  Shots/Second: {perf_analysis.get('shots_per_second', 0):.2f}")
        else:
            print(f"\n❌ Results Analysis: {analysis_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if results.get('overall_success', False):
            print("🏆 WORKING CLOUD EXECUTION TEST: PASSED")
            print("✅ Real AWS Braket execution successful")
            print("✅ Simulator accessible and functional")
            print("✅ Bell state circuit executed successfully")
            print("✅ Real quantum measurements obtained")
        else:
            print("❌ WORKING CLOUD EXECUTION TEST: FAILED")
            print("❌ AWS Braket execution needs repair")
        
        print("="*80)


def main():
    """Main test execution."""
    test = WorkingCloudExecutionTest()
    
    try:
        results = test.run_execution_test()
        test.print_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Working cloud execution test interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Working cloud execution test failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
