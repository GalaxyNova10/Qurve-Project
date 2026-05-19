#!/usr/bin/env python3
"""
QURVE AI - Working Braket Test
CORRECTED AWS Braket SDK usage with proper API calls.

This is NOT architecture work.
This IS runtime infrastructure repair.
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


class WorkingBraketTest:
    """
    Working Braket test with corrected API usage.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.boto3_session = None
        self.braket_client = None
        
        logger.info("Working Braket test initialized")
    
    def run_working_test(self) -> Dict[str, Any]:
        """Run working Braket test."""
        try:
            logger.info("Starting working Braket test...")
            
            # Step 1: Initialize boto3 session
            session_result = self._initialize_boto3_session()
            
            # Step 2: Initialize Braket client
            braket_result = self._initialize_braket_client()
            
            # Step 3: List available devices
            device_list_result = self._list_available_devices()
            
            # Step 4: Test device access with correct ARNs
            device_access_result = self._test_device_access_with_correct_arns()
            
            # Determine overall success
            all_passed = (
                session_result['success'] and
                braket_result['success'] and
                device_list_result['success'] and
                device_access_result['success']
            )
            
            return {
                'overall_success': all_passed,
                'session_result': session_result,
                'braket_result': braket_result,
                'device_list_result': device_list_result,
                'device_access_result': device_access_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Working Braket test failed: {str(e)}")
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
            
            return {
                'success': True,
                'region': self.aws_region,
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
    
    def _list_available_devices(self) -> Dict[str, Any]:
        """List available devices without filters."""
        try:
            # Get all devices without filters (this works)
            response = self.braket_client.search_devices()
            
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
    
    def _test_device_access_with_correct_arns(self) -> Dict[str, Any]:
        """Test device access with correct ARNs from device list."""
        try:
            # Get device list first
            device_list_result = self._list_available_devices()
            if not device_list_result['success']:
                return {
                    'success': False,
                    'error': 'Cannot get device list'
                }
            
            devices = device_list_result['all_devices']
            
            # Test access to each simulator
            access_results = {}
            
            for device in devices:
                device_arn = device.get('deviceArn', '')
                device_name = device.get('deviceName', '')
                device_type = device.get('deviceType', '')
                
                if 'simulator' in device_type.lower():
                    try:
                        # Use the actual ARN from the device list
                        device_response = self.braket_client.get_device(
                            deviceArn=device_arn
                        )
                        
                        access_results[device_name] = {
                            'accessible': True,
                            'arn': device_arn,
                            'status': device_response.get('status', 'unknown'),
                            'type': device_response.get('deviceType', 'unknown'),
                            'provider': device_response.get('providerName', 'unknown'),
                            'properties': device_response.get('deviceCapabilities', {})
                        }
                        
                    except Exception as e:
                        access_results[device_name] = {
                            'accessible': False,
                            'arn': device_arn,
                            'error': str(e)
                        }
            
            # Count accessible simulators
            accessible_count = sum(
                1 for result in access_results.values()
                if result.get('accessible', False)
            )
            
            return {
                'success': accessible_count > 0,
                'access_results': access_results,
                'accessible_count': accessible_count,
                'total_count': len(access_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print test results."""
        print("\n" + "="*80)
        print("WORKING BRAKET TEST RESULTS")
        print("="*80)
        
        # Overall status
        status_emoji = "✅" if results.get('overall_success', False) else "❌"
        print(f"\nOverall Status: {status_emoji} {'PASSED' if results.get('overall_success', False) else 'FAILED'}")
        
        # Session results
        session_result = results.get('session_result', {})
        if session_result.get('success', False):
            print(f"\n✅ AWS Session:")
            print(f"  Region: {session_result.get('region', 'unknown')}")
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
        
        # Device list results
        device_list_result = results.get('device_list_result', {})
        if device_list_result.get('success', False):
            print(f"\n✅ Device List:")
            print(f"  Total Devices: {device_list_result.get('total_devices', 0)}")
            print(f"  Simulators: {len(device_list_result.get('simulators', []))}")
            print(f"  QPUs: {len(device_list_result.get('qpns', []))}")
            
            # List available simulators with their correct ARNs
            simulators = device_list_result.get('simulators', [])
            if simulators:
                print(f"\n  Available Simulators:")
                for sim in simulators:
                    print(f"    - {sim.get('name', 'unknown')}")
                    print(f"      ARN: {sim.get('arn', 'unknown')}")
                    print(f"      Type: {sim.get('type', 'unknown')}")
                    print(f"      Status: {sim.get('status', 'unknown')}")
        else:
            print(f"\n❌ Device List: {device_list_result.get('error', 'unknown')}")
        
        # Device access results
        device_access_result = results.get('device_access_result', {})
        if device_access_result.get('success', False):
            print(f"\n✅ Device Access:")
            print(f"  Accessible: {device_access_result.get('accessible_count', 0)}/{device_access_result.get('total_count', 0)}")
            
            access_results = device_access_result.get('access_results', {})
            for sim_name, result in access_results.items():
                status_emoji = "✅" if result.get('accessible', False) else "❌"
                print(f"    {status_emoji} {sim_name}: {result.get('status', 'unknown')}")
        else:
            print(f"\n❌ Device Access: {device_access_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if results.get('overall_success', False):
            print("🏆 WORKING BRAKET TEST: PASSED")
            print("✅ AWS Braket SDK integration working")
            print("✅ Device discovery functional")
            print("✅ Simulator access validated")
        else:
            print("❌ WORKING BRAKET TEST: FAILED")
            print("❌ AWS Braket SDK integration needs repair")
        
        print("="*80)


def main():
    """Main test execution."""
    test = WorkingBraketTest()
    
    try:
        results = test.run_working_test()
        test.print_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Working Braket test interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Working Braket test failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
