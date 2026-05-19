#!/usr/bin/env python3
"""
QURVE AI - Debug Braket API
Debug AWS Braket API calls to identify correct usage patterns.

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


class DebugBraketAPI:
    """
    Debug Braket API calls.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.boto3_session = None
        self.braket_client = None
        
        logger.info("Debug Braket API initialized")
    
    def debug_api_calls(self) -> Dict[str, Any]:
        """Debug various Braket API calls."""
        try:
            logger.info("Starting Braket API debugging...")
            
            # Step 1: Initialize boto3 session
            session_result = self._initialize_boto3_session()
            
            # Step 2: Initialize Braket client
            braket_result = self._initialize_braket_client()
            
            # Step 3: Debug search_devices API
            search_devices_result = self._debug_search_devices()
            
            # Step 4: Debug get_device API
            get_device_result = self._debug_get_device()
            
            # Step 5: Try different ARN formats
            arn_format_result = self._debug_arn_formats()
            
            return {
                'session_result': session_result,
                'braket_result': braket_result,
                'search_devices_result': search_devices_result,
                'get_device_result': get_device_result,
                'arn_format_result': arn_format_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Braket API debugging failed: {str(e)}")
            return {
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
                'account_id': identity.get('Account', 'unknown')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
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
    
    def _debug_search_devices(self) -> Dict[str, Any]:
        """Debug search_devices API with different parameters."""
        try:
            results = {}
            
            # Test 1: No filters
            try:
                response = self.braket_client.search_devices()
                results['no_filters'] = {
                    'success': True,
                    'devices_found': len(response.get('devices', []))
                }
            except Exception as e:
                results['no_filters'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Test 2: Empty filters
            try:
                response = self.braket_client.search_devices(filters=[])
                results['empty_filters'] = {
                    'success': True,
                    'devices_found': len(response.get('devices', []))
                }
            except Exception as e:
                results['empty_filters'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Test 3: Status filter (original attempt)
            try:
                response = self.braket_client.search_devices(
                    filters=[
                        {
                            'name': 'status',
                            'values': ['ONLINE']
                        }
                    ]
                )
                results['status_filter'] = {
                    'success': True,
                    'devices_found': len(response.get('devices', []))
                }
            except Exception as e:
                results['status_filter'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Test 4: Device type filter
            try:
                response = self.braket_client.search_devices(
                    filters=[
                        {
                            'name': 'deviceType',
                            'values': ['SIMULATOR']
                        }
                    ]
                )
                results['device_type_filter'] = {
                    'success': True,
                    'devices_found': len(response.get('devices', []))
                }
            except Exception as e:
                results['device_type_filter'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Test 5: Try different filter structure
            try:
                response = self.braket_client.search_devices(
                    filters=[
                        {
                            'name': 'status',
                            'values': ['ONLINE']
                        },
                        {
                            'name': 'deviceType',
                            'values': ['SIMULATOR']
                        }
                    ]
                )
                results['multiple_filters'] = {
                    'success': True,
                    'devices_found': len(response.get('devices', []))
                }
            except Exception as e:
                results['multiple_filters'] = {
                    'success': False,
                    'error': str(e)
                }
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _debug_get_device(self) -> Dict[str, Any]:
        """Debug get_device API with different ARN formats."""
        try:
            results = {}
            
            # Test different ARN formats
            arn_formats = {
                'format_1': 'arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1',
                'format_2': 'arn:aws:braket:us-east-1::device/quantum-simulator/amazon/sv1',
                'format_3': 'arn:aws:braket:us-east-1:device/sv1',
                'format_4': 'arn:aws:braket:us-east-1::quantum-simulator/amazon/sv1'
            }
            
            for format_name, arn in arn_formats.items():
                try:
                    # Test with deviceArn parameter
                    response = self.braket_client.get_device(deviceArn=arn)
                    results[format_name] = {
                        'success': True,
                        'arn': arn,
                        'device_name': response.get('deviceName', 'unknown'),
                        'device_type': response.get('deviceType', 'unknown'),
                        'status': response.get('status', 'unknown')
                    }
                except Exception as e:
                    results[format_name] = {
                        'success': False,
                        'arn': arn,
                        'error': str(e)
                    }
            
            # Test with different parameter names
            try:
                response = self.braket_client.get_device(
                    arn='arn:aws:braket::us-east-1:quantum-simulator/amazon/sv1'
                )
                results['param_arn'] = {
                    'success': True,
                    'device_name': response.get('deviceName', 'unknown')
                }
            except Exception as e:
                results['param_arn'] = {
                    'success': False,
                    'error': str(e)
                }
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _debug_arn_formats(self) -> Dict[str, Any]:
        """Debug different ARN formats by listing devices."""
        try:
            # Get all devices without filters
            response = self.braket_client.search_devices()
            devices = response.get('devices', [])
            
            # Extract ARN patterns from actual devices
            arn_patterns = {}
            for device in devices:
                arn = device.get('deviceArn', '')
                device_name = device.get('deviceName', '')
                device_type = device.get('deviceType', '')
                
                arn_patterns[device_name] = {
                    'arn': arn,
                    'device_type': device_type,
                    'status': device.get('status', 'unknown')
                }
            
            return {
                'success': True,
                'total_devices': len(devices),
                'arn_patterns': arn_patterns
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_debug_results(self, results: Dict[str, Any]) -> None:
        """Print debug results."""
        print("\n" + "="*80)
        print("BRAKET API DEBUG RESULTS")
        print("="*80)
        
        # Session results
        session_result = results.get('session_result', {})
        if session_result.get('success', False):
            print(f"\n✅ AWS Session:")
            print(f"  Region: {session_result.get('region', 'unknown')}")
            print(f"  Account ID: {session_result.get('account_id', 'unknown')}")
            print(f"  Identity ARN: {session_result.get('identity_arn', 'unknown')}")
        else:
            print(f"\n❌ AWS Session: {session_result.get('error', 'unknown')}")
        
        # Braket client results
        braket_result = results.get('braket_result', {})
        if braket_result.get('success', False):
            print(f"\n✅ Braket Client: Initialized")
        else:
            print(f"\n❌ Braket Client: {braket_result.get('error', 'unknown')}")
        
        # Search devices results
        search_devices_result = results.get('search_devices_result', {})
        print(f"\n📋 Search Devices API Results:")
        for test_name, result in search_devices_result.items():
            status_emoji = "✅" if result.get('success', False) else "❌"
            print(f"  {status_emoji} {test_name}: {result.get('devices_found', 0)} devices")
            if not result.get('success', False):
                print(f"    Error: {result.get('error', 'unknown')}")
        
        # Get device results
        get_device_result = results.get('get_device_result', {})
        print(f"\n🔍 Get Device API Results:")
        for format_name, result in get_device_result.items():
            status_emoji = "✅" if result.get('success', False) else "❌"
            print(f"  {status_emoji} {format_name}: {result.get('device_name', 'unknown')}")
            if not result.get('success', False):
                print(f"    ARN: {result.get('arn', 'unknown')}")
                print(f"    Error: {result.get('error', 'unknown')}")
        
        # ARN format results
        arn_format_result = results.get('arn_format_result', {})
        if arn_format_result.get('success', False):
            print(f"\n📝 ARN Format Analysis:")
            print(f"  Total Devices: {arn_format_result.get('total_devices', 0)}")
            arn_patterns = arn_format_result.get('arn_patterns', {})
            for device_name, pattern in arn_patterns.items():
                print(f"    - {device_name}: {pattern.get('arn', 'unknown')}")
                print(f"      Type: {pattern.get('device_type', 'unknown')}")
                print(f"      Status: {pattern.get('status', 'unknown')}")
        else:
            print(f"\n❌ ARN Format Analysis: {arn_format_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)


def main():
    """Main debug execution."""
    debugger = DebugBraketAPI()
    
    try:
        results = debugger.debug_api_calls()
        debugger.print_debug_results(results)
        
    except KeyboardInterrupt:
        print("\n❌ Braket API debugging interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Braket API debugging failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
