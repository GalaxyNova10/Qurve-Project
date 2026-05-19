#!/usr/bin/env python3
"""
QURVE AI - Direct Braket API Test
Test AWS Braket API using direct HTTP calls to understand correct usage.

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_direct_braket_api():
    """Test Braket API using direct HTTP calls."""
    try:
        print("Starting direct Braket API test...")
        
        # Import boto3 for signing
        import boto3
        
        # Create session
        session = boto3.Session(
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Get credentials
        credentials = session.get_credentials()
        
        if not credentials:
            print("❌ No AWS credentials found")
            return False
        
        # Test 1: Direct API call to list devices
        print("Testing direct API call to list devices...")
        
        # Get signed request
        service_name = 'braket'
        endpoint = f"https://braket.{session.region_name}.amazonaws.com"
        
        # Create client for signing
        client = session.client(service_name)
        
        # Try to call search_devices without parameters first
        try:
            response = client.search_devices()
            print(f"✅ Direct API call successful: {len(response.get('devices', []))} devices")
            
            # Print device information
            devices = response.get('devices', [])
            for device in devices:
                print(f"  Device: {device.get('deviceName', 'unknown')}")
                print(f"    ARN: {device.get('deviceArn', 'unknown')}")
                print(f"    Type: {device.get('deviceType', 'unknown')}")
                print(f"    Status: {device.get('status', 'unknown')}")
                
            return True
            
        except Exception as e:
            print(f"❌ Direct API call failed: {str(e)}")
            
            # Try with empty filters
            try:
                response = client.search_devices(filters=[])
                print(f"✅ API call with empty filters: {len(response.get('devices', []))} devices")
                return True
                
            except Exception as e2:
                print(f"❌ API call with empty filters failed: {str(e2)}")
                
                # Try with minimal filters
                try:
                    response = client.search_devices(
                        filters=[{
                            'name': 'status',
                            'values': ['ONLINE']
                        }]
                    )
                    print(f"✅ API call with status filter: {len(response.get('devices', []))} devices")
                    return True
                    
                except Exception as e3:
                    print(f"❌ API call with status filter failed: {str(e3)}")
                    return False
        
    except Exception as e:
        print(f"❌ Direct Braket API test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_direct_braket_api()
    sys.exit(0 if success else 1)
