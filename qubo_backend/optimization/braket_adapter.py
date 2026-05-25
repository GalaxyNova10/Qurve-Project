"""
Qurve AI - Isolated Braket Adapter Layer
Purpose: Fully isolate ALL Braket imports and prevent Pydantic V1/V2 conflicts
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class BraketStatus:
    """Structured Braket compatibility status object"""
    available: bool
    sdk_version: Optional[str] = None
    simulator_available: bool = False
    pydantic_compatible: bool = False
    error: Optional[str] = None
    import_error: Optional[str] = None

class BraketAdapter:
    """
    Isolated adapter for Amazon Braket quantum computing.
    All Braket imports are lazy and isolated within this adapter.
    """
    
    def __init__(self):
        self._status: Optional[BraketStatus] = None
        self._local_simulator = None
        self._import_cache = {}
    
    def check_availability(self) -> BraketStatus:
        """
        Check Braket SDK availability and compatibility.
        Returns structured status without crashing on import failures.
        """
        if self._status is not None:
            return self._status
        
        status = BraketStatus(
            available=False,
            sdk_version=None,
            simulator_available=False,
            pydantic_compatible=False
        )
        
        try:
            # Try to import Braket SDK components
            import braket
            status.sdk_version = getattr(braket, '__version__', 'unknown')
            status.available = True
            
            # Try to import LocalSimulator
            try:
                from braket.devices import LocalSimulator
                status.simulator_available = True
                self._import_cache['LocalSimulator'] = LocalSimulator
            except Exception as e:
                status.error = f"LocalSimulator import failed: {str(e)}"
                logger.warning(f"[BRAKET_ADAPTER] LocalSimulator import failed: {e}")
            
            # Try to import circuit components
            try:
                from braket.circuits import Circuit, FreeParameter
                self._import_cache['Circuit'] = Circuit
                self._import_cache['FreeParameter'] = FreeParameter
            except Exception as e:
                status.error = f"Circuit import failed: {str(e)}"
                logger.warning(f"[BRAKET_ADAPTER] Circuit import failed: {e}")
            
            # Check Pydantic compatibility
            try:
                # Test Pydantic V2 compatibility
                from pydantic import __version__ as pydantic_version
                major_version = int(pydantic_version.split('.')[0])
                status.pydantic_compatible = major_version >= 2
                
                if not status.pydantic_compatible:
                    status.error = f"Pydantic V{major_version} incompatible with Braket SDK"
                    logger.warning(f"[BRAKET_ADAPTER] Pydantic V{major_version} incompatibility detected")
                
            except Exception as e:
                status.error = f"Pydantic version check failed: {str(e)}"
                logger.warning(f"[BRAKET_ADAPTER] Pydantic version check failed: {e}")
            
            if status.simulator_available and status.pydantic_compatible:
                logger.info(f"[BRAKET_ADAPTER] Braket SDK v{status.sdk_version} available and compatible")
            else:
                logger.warning(f"[BRAKET_ADAPTER] Braket SDK available but with issues: {status.error}")
                
        except ImportError as e:
            status.import_error = str(e)
            status.error = f"Braket SDK not available: {str(e)}"
            logger.warning(f"[BRAKET_ADAPTER] Braket SDK import failed: {e}")
        except Exception as e:
            status.error = f"Unexpected error during Braket check: {str(e)}"
            logger.error(f"[BRAKET_ADAPTER] Unexpected error: {e}")
        
        self._status = status
        return status
    
    def get_local_simulator(self):
        """
        Get LocalSimulator instance with safe lazy loading.
        Returns None if unavailable.
        """
        status = self.check_availability()
        
        if not status.available or not status.simulator_available:
            return None
        
        try:
            if self._local_simulator is None:
                LocalSimulator = self._import_cache.get('LocalSimulator')
                if LocalSimulator:
                    self._local_simulator = LocalSimulator()
                    logger.info("[BRAKET_ADAPTER] LocalSimulator initialized successfully")
            
            return self._local_simulator
        except Exception as e:
            logger.error(f"[BRAKET_ADAPTER] LocalSimulator initialization failed: {e}")
            return None
    
    def create_circuit(self, num_qubits: int = 2):
        """
        Create a simple test circuit with safe lazy loading.
        Returns None if unavailable.
        """
        status = self.check_availability()
        
        if not status.available or 'Circuit' not in self._import_cache:
            return None
        
        try:
            Circuit = self._import_cache['Circuit']
            FreeParameter = self._import_cache.get('FreeParameter')
            
            # Create simple test circuit
            circuit = Circuit()
            
            # Add H gate to first qubit
            circuit.h(0)
            
            # Add CNOT if we have at least 2 qubits
            if num_qubits >= 2:
                circuit.cnot(0, 1)
            
            # Add measurements
            for i in range(num_qubits):
                circuit.measure(i)
            
            logger.info(f"[BRAKET_ADAPTER] Created {num_qubits}-qubit test circuit")
            return circuit
            
        except Exception as e:
            logger.error(f"[BRAKET_ADAPTER] Circuit creation failed: {e}")
            return None
    
    async def run_local_task(self, circuit, shots: int = 100) -> Optional[Dict[str, Any]]:
        """
        Run circuit on LocalSimulator in isolated thread.
        Returns result dict or None on failure.
        """
        simulator = self.get_local_simulator()
        if simulator is None:
            return None
        
        try:
            # Run in isolated thread to prevent event loop blocking
            result = await asyncio.to_thread(
                self._execute_circuit_sync, simulator, circuit, shots
            )
            
            logger.info(f"[BRAKET_ADAPTER] Circuit execution completed: {shots} shots")
            return result
            
        except Exception as e:
            logger.error(f"[BRAKET_ADAPTER] Circuit execution failed: {e}")
            return None
    
    def _execute_circuit_sync(self, simulator, circuit, shots: int) -> Dict[str, Any]:
        """
        Synchronous circuit execution for use in asyncio.to_thread().
        """
        start_time = time.perf_counter()
        
        try:
            # Execute circuit
            task = simulator.run(circuit, shots=shots)
            result = task.result()
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Extract measurement counts
            measurement_counts = {}
            if hasattr(result, 'measurement_counts'):
                measurement_counts = result.measurement_counts
            elif hasattr(result, 'counts'):
                measurement_counts = result.counts
            else:
                # Try to extract from result dict
                if isinstance(result, dict):
                    measurement_counts = result.get('measurement_counts', {})
            
            return {
                'success': True,
                'execution_time_ms': execution_time,
                'shots': shots,
                'measurement_counts': measurement_counts,
                'result': result,
                'error': None
            }
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return {
                'success': False,
                'execution_time_ms': execution_time,
                'shots': shots,
                'measurement_counts': {},
                'result': None,
                'error': str(e)
            }
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate Braket environment and return detailed status.
        """
        status = self.check_availability()
        
        validation_result = {
            'braket_available': status.available,
            'sdk_version': status.sdk_version,
            'simulator_available': status.simulator_available,
            'pydantic_compatible': status.pydantic_compatible,
            'import_error': status.import_error,
            'error': status.error,
            'circuit_test': None,
            'execution_test': None
        }
        
        # Test circuit creation
        if status.available:
            circuit = self.create_circuit(2)
            if circuit:
                validation_result['circuit_test'] = 'success'
            else:
                validation_result['circuit_test'] = 'failed'
        
        # Test execution
        if status.simulator_available:
            circuit = self.create_circuit(2)
            if circuit:
                # Run simple execution test
                try:
                    import asyncio
                    test_result = asyncio.run(self.run_local_task(circuit, shots=10))
                    if test_result and test_result.get('success'):
                        validation_result['execution_test'] = 'success'
                    else:
                        validation_result['execution_test'] = 'failed'
                except Exception as e:
                    validation_result['execution_test'] = f'error: {str(e)}'
            else:
                validation_result['execution_test'] = 'no_circuit'
        
        return validation_result
    
    @contextmanager
    def safe_execution_context(self):
        """
        Context manager for safe Braket execution.
        Catches and logs exceptions without propagating.
        """
        try:
            yield self
        except Exception as e:
            logger.error(f"[BRAKET_ADAPTER] Safe execution context error: {e}")
            # Re-raise with context for caller to handle
            raise

# Global adapter instance
_braket_adapter = None

def get_braket_adapter() -> BraketAdapter:
    """Get global Braket adapter instance."""
    global _braket_adapter
    if _braket_adapter is None:
        _braket_adapter = BraketAdapter()
    return _braket_adapter

# Convenience functions for backward compatibility
def is_braket_available() -> bool:
    """Check if Braket is available and compatible."""
    adapter = get_braket_adapter()
    status = adapter.check_availability()
    return status.available and status.simulator_available and status.pydantic_compatible

def get_braket_status() -> Dict[str, Any]:
    """Get comprehensive Braket status."""
    adapter = get_braket_adapter()
    return adapter.validate_environment()
