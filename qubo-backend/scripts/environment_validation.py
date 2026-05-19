#!/usr/bin/env python3
"""
Qurve AI - Environment Validation Script
Comprehensive validation of production dependencies and compatibility
"""

import sys
import os
import importlib
import subprocess
import platform
from typing import Dict, List, Any


def check_python_version() -> Dict[str, Any]:
    """Validate Python version compatibility."""
    version = sys.version_info
    major, minor, micro = version[:3]
    
    result = {
        "version": f"{major}.{minor}.{micro}",
        "major": major,
        "minor": minor,
        "micro": micro,
        "compatible": True,
        "issues": []
    }
    
    # Check minimum requirements
    if major < 3 or (major == 3 and minor < 12):
        result["compatible"] = False
        result["issues"].append(f"Python {major}.{minor} < 3.12 required")
    
    # Check for Python 3.14+ compatibility warnings
    if major >= 3 and minor >= 14:
        result["issues"].append("Python 3.14+ may have compatibility issues with some packages")
    
    return result


def check_imports() -> Dict[str, Any]:
    """Validate critical imports and dependencies."""
    results = {}
    
    # Core dependencies
    core_imports = {
        "fastapi": "FastAPI",
        "pydantic": "Pydantic", 
        "numpy": "NumPy",
        "scipy": "SciPy",
        "asyncio": "Asyncio"
    }
    
    for module, name in core_imports.items():
        try:
            imported = importlib.import_module(module)
            version = getattr(imported, '__version__', 'unknown')
            
            results[module] = {
                "name": name,
                "imported": True,
                "version": version,
                "issues": []
            }
            
            # Module-specific checks
            if module == "pydantic":
                major_version = int(version.split('.')[0]) if version != 'unknown' else 0
                if major_version >= 2:
                    results[module]["pydantic_v2"] = True
                else:
                    results[module]["issues"].append(f"Pydantic V{major_version} may have compatibility issues")
            
            elif module == "numpy":
                try:
                    import numpy as np
                    test_array = np.array([1, 2, 3], dtype=float)
                    results[module]["array_creation"] = "success"
                except Exception as e:
                    results[module]["issues"].append(f"NumPy array creation failed: {e}")
            
        except ImportError as e:
            results[module] = {
                "name": name,
                "imported": False,
                "version": None,
                "error": str(e),
                "issues": [f"Import failed: {e}"]
            }
    
    # Quantum dependencies
    quantum_imports = {
        "qiskit": "Qiskit",
        "dwave": "DWave Ocean",
        "braket": "Amazon Braket SDK"
    }
    
    for module, name in quantum_imports.items():
        try:
            imported = importlib.import_module(module)
            version = getattr(imported, '__version__', 'unknown')
            
            results[module] = {
                "name": name,
                "imported": True,
                "version": version,
                "issues": []
            }
            
            # Module-specific checks
            if module == "braket":
                # Check for Pydantic compatibility
                try:
                    from braket.circuits import Circuit
                    results[module]["circuit_import"] = "success"
                except Exception as e:
                    if "validate_instructions" in str(e):
                        results[module]["issues"].append("Pydantic V1/V2 compatibility issue")
                    else:
                        results[module]["issues"].append(f"Circuit import failed: {e}")
            
            elif module == "qiskit":
                # Check AerSimulator availability
                try:
                    from qiskit.providers.aer import AerSimulator
                    results[module]["aer_simulator"] = "success"
                except ImportError:
                    results[module]["issues"].append("AerSimulator not available")
            
        except ImportError as e:
            results[module] = {
                "name": name,
                "imported": False,
                "version": None,
                "error": str(e),
                "issues": [f"Import failed: {e}"]
            }
    
    return results


def check_dtype_compatibility() -> Dict[str, Any]:
    """Validate NumPy/SciPy dtype compatibility."""
    results = {}
    
    try:
        import numpy as np
        import scipy.sparse as sp
        
        # Test sparse matrix creation
        test_matrix = sp.csr_matrix([[1, 2], [3, 4]], dtype=float)
        results["sparse_matrix_creation"] = {
            "success": True,
            "issues": []
        }
        
        # Test dtype handling
        try:
            # Test string dtype issue (common problem)
            string_matrix = sp.csr_matrix([['1', '2'], ['3', '4']], dtype=float)
            results["string_dtype_handling"] = {
                "success": True,
                "issues": []
            }
        except Exception as e:
            results["string_dtype_handling"] = {
                "success": False,
                "issues": [f"String dtype handling failed: {e}"]
            }
        
        # Test integer mapping
        try:
            test_array = np.array([1, 2, 3], dtype=np.int32)
            results["integer_mapping"] = {
                "success": True,
                "issues": []
            }
        except Exception as e:
            results["integer_mapping"] = {
                "success": False,
                "issues": [f"Integer mapping failed: {e}"]
            }
        
    except ImportError as e:
        results["import_error"] = {
            "success": False,
            "error": str(e),
            "issues": [f"Import failed: {e}"]
        }
    
    return results


def check_cuda_availability() -> Dict[str, Any]:
    """Check CUDA/GPU availability for quantum acceleration."""
    results = {
        "cuda_available": False,
        "cuda_version": None,
        "gpu_count": 0,
        "issues": []
    }
    
    try:
        import torch
        results["cuda_available"] = torch.cuda.is_available()
        if results["cuda_available"]:
            results["cuda_version"] = torch.version.cuda
            results["gpu_count"] = torch.cuda.device_count()
        else:
            results["issues"].append("CUDA not available")
    except ImportError:
        results["issues"].append("PyTorch not available for CUDA check")
    
    return results


def check_braket_compatibility() -> Dict[str, Any]:
    """Check Amazon Braket SDK compatibility with current environment."""
    results = {
        "braket_available": False,
        "pydantic_compatible": False,
        "simulator_available": False,
        "circuit_creation": False,
        "execution_test": False,
        "issues": []
    }
    
    try:
        # Import adapter to test
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from qubo_backend.optimization.braket_adapter import get_braket_adapter
        
        adapter = get_braket_adapter()
        status = adapter.check_availability()
        
        results["braket_available"] = status.available
        results["pydantic_compatible"] = status.pydantic_compatible
        results["simulator_available"] = status.simulator_available
        
        # Test circuit creation
        circuit = adapter.create_circuit(2)
        results["circuit_creation"] = circuit is not None
        
        # Test execution if simulator available
        if status.simulator_available and circuit:
            import asyncio
            execution_result = asyncio.run(adapter.run_local_task(circuit, shots=10))
            results["execution_test"] = execution_result and execution_result.get('success', False)
        
        # Collect issues
        if status.error:
            results["issues"].append(status.error)
        
        if not status.pydantic_compatible:
            results["issues"].append("Pydantic V1/V2 compatibility issue")
        
        if not status.simulator_available:
            results["issues"].append("LocalSimulator not available")
        
    except Exception as e:
        results["issues"].append(f"Braket compatibility check failed: {e}")
    
    return results


def check_system_resources() -> Dict[str, Any]:
    """Check system resources and constraints."""
    results = {
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "python_implementation": platform.python_implementation(),
        "memory_gb": None,
        "cpu_cores": os.cpu_count(),
        "issues": []
    }
    
    try:
        import psutil
        results["memory_gb"] = psutil.virtual_memory().total / (1024**3)
        
        # Check resource constraints
        if results["memory_gb"] < 4:
            results["issues"].append(f"Low memory: {results['memory_gb']:.1f}GB < 4GB recommended")
        
        if results["cpu_cores"] < 2:
            results["issues"].append(f"Low CPU cores: {results['cpu_cores']} < 2 recommended")
        
    except ImportError:
        results["issues"].append("psutil not available for resource monitoring")
    
    return results


def run_full_validation() -> Dict[str, Any]:
    """Run comprehensive environment validation."""
    print("=== QURVE AI ENVIRONMENT VALIDATION ===")
    
    validation_results = {
        "python_version": check_python_version(),
        "imports": check_imports(),
        "dtype_compatibility": check_dtype_compatibility(),
        "cuda_availability": check_cuda_availability(),
        "braket_compatibility": check_braket_compatibility(),
        "system_resources": check_system_resources(),
        "overall_status": "unknown",
        "critical_issues": [],
        "warnings": [],
        "recommendations": []
    }
    
    # Analyze results for critical issues
    all_issues = []
    
    # Python version issues
    if not validation_results["python_version"]["compatible"]:
        all_issues.extend(validation_results["python_version"]["issues"])
        validation_results["critical_issues"].extend(validation_results["python_version"]["issues"])
    
    # Import issues
    for module, result in validation_results["imports"].items():
        if not result["imported"]:
            all_issues.extend(result["issues"])
            validation_results["critical_issues"].append(f"{result['name']} import failed")
    
    # Braket compatibility issues
    if not validation_results["braket_compatibility"]["braket_available"]:
        all_issues.extend(validation_results["braket_compatibility"]["issues"])
        validation_results["critical_issues"].append("Braket SDK not available")
    
    # Dtype compatibility issues
    if "import_error" in validation_results["dtype_compatibility"]:
        all_issues.extend(validation_results["dtype_compatibility"]["import_error"]["issues"])
        validation_results["critical_issues"].append("Dtype compatibility import error")
    
    # Warnings
    if not validation_results["cuda_availability"]["cuda_available"]:
        validation_results["warnings"].append("CUDA not available for GPU acceleration")
    
    # System resource warnings
    if validation_results["system_resources"]["issues"]:
        validation_results["warnings"].extend(validation_results["system_resources"]["issues"])
    
    # Generate recommendations
    if validation_results["critical_issues"]:
        validation_results["recommendations"].append("Resolve critical issues before production deployment")
    else:
        validation_results["recommendations"].append("Environment appears production-ready")
        
        if validation_results["warnings"]:
            validation_results["recommendations"].append("Address warnings for optimal performance")
    
    # Set overall status
    if validation_results["critical_issues"]:
        validation_results["overall_status"] = "critical"
    elif all_issues:
        validation_results["overall_status"] = "warning"
    else:
        validation_results["overall_status"] = "healthy"
    
    # Print results
    print(f"\nPython Version: {validation_results['python_version']['version']} ({validation_results['python_version']['compatible'] and 'compatible' or 'incompatible'})")
    
    print(f"\nCore Dependencies:")
    for module, result in validation_results["imports"].items():
        status = "✅" if result["imported"] else "❌"
        version = f" v{result['version']}" if result['version'] != 'unknown' else ""
        print(f"  {status} {result['name']}{version} ({'imported' if result['imported'] else 'failed'})")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"    ⚠️  {issue}")
    
    print(f"\nQuantum Dependencies:")
    quantum_modules = ["qiskit", "dwave", "braket"]
    for module in quantum_modules:
        if module in validation_results["imports"]:
            result = validation_results["imports"][module]
            status = "✅" if result["imported"] else "❌"
            version = f" v{result['version']}" if result['version'] != 'unknown' else ""
            print(f"  {status} {result['name']}{version}")
        else:
            print(f"  ❌ {module} (not tested)")
    
    print(f"\nBraket Compatibility:")
    braket_results = validation_results["braket_compatibility"]
    braket_status = "✅" if braket_results["braket_available"] else "❌"
    print(f"  {braket_status} SDK Available: {braket_results['braket_available']}")
    print(f"  {'✅' if braket_results['pydantic_compatible'] else '❌'} Pydantic Compatible: {braket_results['pydantic_compatible']}")
    print(f"  {'✅' if braket_results['simulator_available'] else '❌'} LocalSimulator: {braket_results['simulator_available']}")
    print(f"  {'✅' if braket_results['circuit_creation'] else '❌'} Circuit Creation: {braket_results['circuit_creation']}")
    print(f"  {'✅' if braket_results['execution_test'] else '❌'} Execution Test: {braket_results['execution_test']}")
    
    if braket_results["issues"]:
        for issue in braket_results["issues"]:
            print(f"    ⚠️  {issue}")
    
    print(f"\nSystem Resources:")
    sys_results = validation_results["system_resources"]
    print(f"  Platform: {sys_results['platform']}")
    print(f"  Architecture: {sys_results['architecture'][0]}")
    print(f"  CPU Cores: {sys_results['cpu_cores']}")
    print(f"  Memory: {sys_results['memory_gb']:.1f}GB")
    
    if sys_results["issues"]:
        for issue in sys_results["issues"]:
            print(f"  ⚠️  {issue}")
    
    print(f"\nCUDA/GPU:")
    cuda_results = validation_results["cuda_availability"]
    print(f"  CUDA Available: {cuda_results['cuda_available']}")
    if cuda_results["cuda_available"]:
        print(f"  CUDA Version: {cuda_results['cuda_version']}")
        print(f"  GPU Count: {cuda_results['gpu_count']}")
    else:
        print(f"  Status: {cuda_results['issues'][0] if cuda_results['issues'] else 'Not available'}")
    
    print(f"\n=== VALIDATION SUMMARY ===")
    print(f"Overall Status: {validation_results['overall_status'].upper()}")
    
    if validation_results["critical_issues"]:
        print(f"\n🔴 CRITICAL ISSUES ({len(validation_results['critical_issues'])}):")
        for issue in validation_results["critical_issues"]:
            print(f"  - {issue}")
    
    if validation_results["warnings"]:
        print(f"\n🟡 WARNINGS ({len(validation_results['warnings'])}):")
        for warning in validation_results["warnings"]:
            print(f"  - {warning}")
    
    if validation_results["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in validation_results["recommendations"]:
            print(f"  - {rec}")
    
    print(f"\n=== VALIDATION COMPLETE ===")
    
    return validation_results


if __name__ == '__main__':
    run_full_validation()
