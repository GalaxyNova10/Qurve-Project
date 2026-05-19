#!/usr/bin/env python3
"""
QURVE AI - Minimal Braket Device Discovery Test
REAL AWS Braket SDK validation without platform abstractions.

This is NOT architecture work.
This IS runtime infrastructure repair.

Features:
✅ Direct boto3 session initialization
✅ Direct Braket session initialization
✅ Direct device discovery
✅ Real simulator ARN validation
✅ No platform abstractions
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MinimalBraketTest:
    """
    Minimal Braket device discovery test.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.boto3_session = None
        self.braket_client = None
        
        logger.info("Minimal Braket test initialized")
    
    def run_discovery_test(self) -> Dict[str, Any]:
        """Run minimal device discovery test."""
        try:
            logger.info("Starting minimal Braket device discovery test...")
            
            # Step 1: Initialize boto3 session
            session_result = self._initialize_boto3_session()
            
            # Step 2: Initialize Braket client
            braket_result = self._initialize_braket_client()
            
            # Step 3: Discover available devices
            device_discovery_result = self._discover_devices()
            
            # Step 4: Validate specific simulators
            simulator_validation_result = self._validate_simulators()
            
            # Step 5: Test device access
            device_access_result = self._test_device_access()
            
            # Determine overall success
            all_passed = (
                session_result['success'] and
                braket_result['success'] and
                device_discovery_result['success'] and
                simulator_validation_result['success'] and
                device_access_result['success']
            )
            
            return {
                'overall_success': all_passed,
                'session_result': session_result,
                'braket_result': braket_result,
                'device_discovery_result': device_discovery_result,
                'simulator_validation_result': simulator_validation_result,
                'device_access_result': device_access_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Minimal Braket test failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _initialize_boto3_session(self) -> Dict[str, Any]:
        """Initialize boto3 session."""
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
            
            # Test client by checking service availability
            response = self.braket_client.search_devices(
                filters=[
                    {
                        'name': 'status',
                        'values': ['ONLINE']
                    }
                ]
            )
            
            return {
                'success': True,
                'devices_found': len(response.get('devices', [])),
                'service_available': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _discover_devices(self) -> Dict[str, Any]:
        """Discover available devices."""
        try:
            # Get all devices
            response = self.braket_client.search_devices(
                filters=[
                    {
                        'name': 'status',
                        'values': ['ONLINE']
                    }
                ]
            )
            
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
    
    def _validate_simulators(self) -> Dict[str, Any]:
        """Validate specific simulators."""
        try:
            # Known simulator ARNs (correct format)
            target_simulators = {
                'SV1': 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1',
                'TN1': 'arn:aws:braket::us-east-1:quantum-simulator/amazon/tn1',
                'DM1': 'arn:aws:braket::us-east-1:quantum-simulator/amazon/dm1'
            }
            
            validation_results = {}
            
            for simulator_name, simulator_arn in target_simulators.items():
                try:
                    # Get device details using correct API
                    device = self.braket_client.get_device(
                        deviceArn=simulator_arn
                    )
                    
                    validation_results[simulator_name] = {
                        'accessible': True,
                        'arn': simulator_arn,
                        'status': device.get('status', 'unknown'),
                        'type': device.get('deviceType', 'unknown'),
                        'provider': device.get('providerName', 'unknown'),
                        'properties': device.get('deviceCapabilities', {})
                    }
                    
                except Exception as e:
                    validation_results[simulator_name] = {
                        'accessible': False,
                        'arn': simulator_arn,
                        'error': str(e)
                    }
            
            # Count accessible simulators
            accessible_count = sum(
                1 for result in validation_results.values()
                if result.get('accessible', False)
            )
            
            return {
                'success': accessible_count > 0,
                'validation_results': validation_results,
                'accessible_count': accessible_count,
                'total_count': len(target_simulators)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_device_access(self) -> Dict[str, Any]:
        """Test device access for a specific simulator."""
        try:
            # Use SV1 for access test
            sv1_arn = 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1'
            
            # Get device details
            device = self.braket_client.get_device(deviceArn=sv1_arn)
            
            # Check device properties
            device_properties = device.get('deviceCapabilities', {})
            
            return {
                'success': True,
                'test_device': 'SV1',
                'device_arn': sv1_arn,
                'device_status': device.get('status', 'unknown'),
                'device_type': device.get('deviceType', 'unknown'),
                'device_properties': device_properties,
                'access_timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_device': 'SV1'
            }
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print test results."""
        print("\n" + "="*80)
        print("MINIMAL BRAKET DEVICE DISCOVERY TEST RESULTS")
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
            print(f"\n✅ Braket Client:")
            print(f"  Service Available: {braket_result.get('service_available', False)}")
            print(f"  Devices Found: {braket_result.get('devices_found', 0)}")
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
        
        # Simulator validation results
        simulator_validation_result = results.get('simulator_validation_result', {})
        if simulator_validation_result.get('success', False):
            print(f"\n✅ Simulator Validation:")
            print(f"  Accessible: {simulator_validation_result.get('accessible_count', 0)}/{simulator_validation_result.get('total_count', 0)}")
            
            validation_results = simulator_validation_result.get('validation_results', {})
            for sim_name, result in validation_results.items():
                status_emoji = "✅" if result.get('accessible', False) else "❌"
                print(f"    {status_emoji} {sim_name}: {result.get('status', 'unknown')}")
        else:
            print(f"\n❌ Simulator Validation: {simulator_validation_result.get('error', 'unknown')}")
        
        # Device access results
        device_access_result = results.get('device_access_result', {})
        if device_access_result.get('success', False):
            print(f"\n✅ Device Access Test:")
            print(f"  Test Device: {device_access_result.get('test_device', 'unknown')}")
            print(f"  Device ARN: {device_access_result.get('device_arn', 'unknown')}")
            print(f"  Device Status: {device_access_result.get('device_status', 'unknown')}")
            print(f"  Device Type: {device_access_result.get('device_type', 'unknown')}")
        else:
            print(f"\n❌ Device Access Test: {device_access_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if results.get('overall_success', False):
            print("🏆 MINIMAL BRAKET DEVICE DISCOVERY: PASSED")
            print("✅ AWS Braket SDK integration working")
            print("✅ Device discovery functional")
            print("✅ Simulator access validated")
        else:
            print("❌ MINIMAL BRAKET DEVICE DISCOVERY: FAILED")
            print("❌ AWS Braket SDK integration needs repair")
        
        print("="*80)


def main():
    """Main test execution."""
    test = MinimalBraketTest()
    
    try:
        results = test.run_discovery_test()
        test.print_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Minimal Braket test interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Minimal Braket test failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
