#!/usr/bin/env python3
"""
QURVE AI - Activate Website Execution
Enable frontend benchmark execution using REAL cloud execution.

This is NOT architecture work.
This IS runtime infrastructure repair.
"""

import os
import sys
import json
import time
import logging
import subprocess
from typing import Dict, Any, List, Optional

# Add qubo-backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'qubo-backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ActivateWebsiteExecution:
    """
    Activate website benchmark execution.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.backend_port = 8000
        self.frontend_port = 3000
        
        logger.info("Website execution activation initialized")
    
    def activate_website_execution(self) -> Dict[str, Any]:
        """Activate website execution."""
        try:
            logger.info("Activating website execution...")
            
            # Step 1: Start backend server
            backend_result = self._start_backend_server()
            
            # Step 2: Start frontend server
            frontend_result = self._start_frontend_server()
            
            # Step 3: Test API connectivity
            api_result = self._test_api_connectivity()
            
            # Step 4: Test cloud execution through API
            cloud_api_result = self._test_cloud_execution_api()
            
            # Step 5: Validate frontend integration
            frontend_result = self._validate_frontend_integration()
            
            # Determine overall success
            all_passed = (
                backend_result['success'] and
                frontend_result['success'] and
                api_result['success'] and
                cloud_api_result['success'] and
                frontend_result['success']
            )
            
            return {
                'overall_success': all_passed,
                'backend_result': backend_result,
                'frontend_result': frontend_result,
                'api_result': api_result,
                'cloud_api_result': cloud_api_result,
                'frontend_integration_result': frontend_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Website execution activation failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _start_backend_server(self) -> Dict[str, Any]:
        """Start backend server."""
        try:
            # Change to backend directory
            backend_dir = os.path.join(os.getcwd(), 'qubo-backend')
            
            # Start backend server in background
            process = subprocess.Popen(
                [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', str(self.backend_port)],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(5)
            
            # Check if server is running
            if process.poll() is None:
                return {
                    'success': True,
                    'backend_port': self.backend_port,
                    'process_id': process.pid,
                    'server_running': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Backend server failed to start'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _start_frontend_server(self) -> Dict[str, Any]:
        """Start frontend server."""
        try:
            # Change to frontend directory
            frontend_dir = os.path.join(os.getcwd(), 'app')
            
            # Start frontend server in background
            process = subprocess.Popen(
                ['npm', 'start'],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(10)
            
            # Check if server is running
            if process.poll() is None:
                return {
                    'success': True,
                    'frontend_port': self.frontend_port,
                    'process_id': process.pid,
                    'server_running': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Frontend server failed to start'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_api_connectivity(self) -> Dict[str, Any]:
        """Test API connectivity."""
        try:
            import requests
            
            # Test health endpoint
            health_response = requests.get(f'http://localhost:{self.backend_port}/health', timeout=5)
            
            # Test benchmark endpoint
            benchmark_response = requests.get(f'http://localhost:{self.backend_port}/api/benchmarks', timeout=5)
            
            return {
                'success': health_response.status_code == 200 and benchmark_response.status_code == 200,
                'health_status': health_response.status_code,
                'benchmark_status': benchmark_response.status_code,
                'api_accessible': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_cloud_execution_api(self) -> Dict[str, Any]:
        """Test cloud execution through API."""
        try:
            import requests
            
            # Create benchmark request
            benchmark_request = {
                'name': 'test_cloud_benchmark',
                'qubo': {(0, 0): 1, (1, 1): 1, (0, 1): -1},
                'execution_mode': 'cloud_simulator',
                'shots': 10
            }
            
            # Submit benchmark
            response = requests.post(
                f'http://localhost:{self.backend_port}/api/benchmarks',
                json=benchmark_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'benchmark_id': result.get('id', 'unknown'),
                    'execution_mode': result.get('execution_mode', 'unknown'),
                    'task_id': result.get('task_id', 'unknown'),
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
    
    def _validate_frontend_integration(self) -> Dict[str, Any]:
        """Validate frontend integration."""
        try:
            import requests
            
            # Test frontend accessibility
            frontend_response = requests.get(f'http://localhost:{self.frontend_port}', timeout=5)
            
            if frontend_response.status_code == 200:
                return {
                    'success': True,
                    'frontend_accessible': True,
                    'frontend_status': frontend_response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f'Frontend returned status {frontend_response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print activation results."""
        print("\n" + "="*80)
        print("WEBSITE EXECUTION ACTIVATION RESULTS")
        print("="*80)
        
        # Overall status
        status_emoji = "✅" if results.get('overall_success', False) else "❌"
        print(f"\nOverall Status: {status_emoji} {'PASSED' if results.get('overall_success', False) else 'FAILED'}")
        
        # Backend results
        backend_result = results.get('backend_result', {})
        if backend_result.get('success', False):
            print(f"\n✅ Backend Server:")
            print(f"  Port: {backend_result.get('backend_port', 'unknown')}")
            print(f"  Process ID: {backend_result.get('process_id', 'unknown')}")
            print(f"  Running: {backend_result.get('server_running', False)}")
        else:
            print(f"\n❌ Backend Server: {backend_result.get('error', 'unknown')}")
        
        # Frontend results
        frontend_result = results.get('frontend_result', {})
        if frontend_result.get('success', False):
            print(f"\n✅ Frontend Server:")
            print(f"  Port: {frontend_result.get('frontend_port', 'unknown')}")
            print(f"  Process ID: {frontend_result.get('process_id', 'unknown')}")
            print(f"  Running: {frontend_result.get('server_running', False)}")
        else:
            print(f"\n❌ Frontend Server: {frontend_result.get('error', 'unknown')}")
        
        # API results
        api_result = results.get('api_result', {})
        if api_result.get('success', False):
            print(f"\n✅ API Connectivity:")
            print(f"  Health Status: {api_result.get('health_status', 'unknown')}")
            print(f"  Benchmark Status: {api_result.get('benchmark_status', 'unknown')}")
            print(f"  API Accessible: {api_result.get('api_accessible', False)}")
        else:
            print(f"\n❌ API Connectivity: {api_result.get('error', 'unknown')}")
        
        # Cloud API results
        cloud_api_result = results.get('cloud_api_result', {})
        if cloud_api_result.get('success', False):
            print(f"\n✅ Cloud Execution API:")
            print(f"  Benchmark ID: {cloud_api_result.get('benchmark_id', 'unknown')}")
            print(f"  Execution Mode: {cloud_api_result.get('execution_mode', 'unknown')}")
            print(f"  Task ID: {cloud_api_result.get('task_id', 'unknown')}")
            print(f"  Status: {cloud_api_result.get('status', 'unknown')}")
        else:
            print(f"\n❌ Cloud Execution API: {cloud_api_result.get('error', 'unknown')}")
        
        # Frontend integration results
        frontend_integration_result = results.get('frontend_integration_result', {})
        if frontend_integration_result.get('success', False):
            print(f"\n✅ Frontend Integration:")
            print(f"  Frontend Accessible: {frontend_integration_result.get('frontend_accessible', False)}")
            print(f"  Frontend Status: {frontend_integration_result.get('frontend_status', 'unknown')}")
        else:
            print(f"\n❌ Frontend Integration: {frontend_integration_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if results.get('overall_success', False):
            print("🏆 WEBSITE EXECUTION ACTIVATION: PASSED")
            print("✅ Backend server running")
            print("✅ Frontend server running")
            print("✅ API connectivity working")
            print("✅ Cloud execution API working")
            print("✅ Frontend integration working")
        else:
            print("❌ WEBSITE EXECUTION ACTIVATION: FAILED")
            print("❌ Website execution not ready")
        
        print("="*80)


def main():
    """Main activation execution."""
    activator = ActivateWebsiteExecution()
    
    try:
        results = activator.activate_website_execution()
        activator.print_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Website execution activation interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Website execution activation failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
