#!/usr/bin/env python3
"""
QURVE AI - Minimal Boto3 Test
Test basic AWS connectivity and Braket service availability.

This is NOT architecture work.
This IS runtime infrastructure repair.
"""

import os
import sys
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_boto3_braket():
    """Test basic boto3 and Braket connectivity."""
    try:
        print("Starting minimal boto3 and Braket test...")
        
        # Import boto3
        import boto3
        
        # Create session
        session = boto3.Session(
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Test session
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        
        print(f"✅ AWS Session: {identity.get('Account', 'unknown')}")
        print(f"  Region: {session.region_name}")
        print(f"  User: {identity.get('UserId', 'unknown')}")
        
        # Test Braket service availability
        print("Testing Braket service availability...")
        
        # Create Braket client
        braket_client = session.client('braket')
        
        # Test 1: Call get_service_limits (should work)
        try:
            limits = braket_client.get_service_limits()
            print(f"✅ Braket Service Limits: {len(limits.get('serviceLimits', []))} limits found")
        except Exception as e:
            print(f"❌ Get service limits failed: {str(e)}")
        
        # Test 2: Try to get device list with minimal parameters
        try:
            # Try with no parameters first
            devices = braket_client.search_devices()
            print(f"✅ Search Devices: {len(devices.get('devices', []))} devices found")
            
            # Show device info
            for device in devices.get('devices', [])[:5]:  # Show first 5
                print(f"  - {device.get('deviceName', 'unknown')}")
                print(f"    ARN: {device.get('deviceArn', 'unknown')}")
                print(f"    Type: {device.get('deviceType', 'unknown')}")
                print(f"    Status: {device.get('status', 'unknown')}")
                
            return True
            
        except Exception as e:
            print(f"❌ Search devices failed: {str(e)}")
            
            # Try with empty filters
            try:
                devices = braket_client.search_devices(filters=[])
                print(f"✅ Search with empty filters: {len(devices.get('devices', []))} devices found")
                return True
                
            except Exception as e2:
                print(f"❌ Search with empty filters failed: {str(e2)}")
                return False
        
    except Exception as e:
        print(f"❌ Boto3/Braket test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_boto3_braket()
    sys.exit(0 if success else 1)
