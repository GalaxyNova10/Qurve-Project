#!/usr/bin/env python3
"""
QURVE AI - Simple Braket Test
Direct AWS Braket API test without complex parameters.

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


def test_simple_braket():
    """Simple Braket API test."""
    try:
        print("Starting simple Braket test...")
        
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
        
        # Create Braket client
        braket_client = session.client('braket')
        
        # Test 1: Simple search without filters
        print("Testing search_devices without filters...")
        try:
            response = braket_client.search_devices()
            devices = response.get('devices', [])
            print(f"✅ Found {len(devices)} devices")
            
            # Print device info
            for device in devices:
                print(f"  - {device.get('deviceName', 'unknown')}: {device.get('deviceArn', 'unknown')}")
                
        except Exception as e:
            print(f"❌ Search failed: {str(e)}")
            return False
        
        # Test 2: Get device details for first simulator
        print("Testing get_device for first simulator...")
        simulators = [d for d in devices if 'simulator' in d.get('deviceType', '').lower()]
        
        if simulators:
            first_simulator = simulators[0]
            simulator_arn = first_simulator.get('deviceArn', '')
            
            try:
                device_details = braket_client.get_device(deviceArn=simulator_arn)
                print(f"✅ Device details: {device_details.get('deviceName', 'unknown')}")
                print(f"  Status: {device_details.get('status', 'unknown')}")
                print(f"  Type: {device_details.get('deviceType', 'unknown')}")
                return True
                
            except Exception as e:
                print(f"❌ Get device failed: {str(e)}")
                return False
        else:
            print("❌ No simulators found")
            return False
            
    except Exception as e:
        print(f"❌ Simple Braket test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_simple_braket()
    sys.exit(0 if success else 1)
