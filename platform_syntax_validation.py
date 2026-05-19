#!/usr/bin/env python3
"""
QURVE AI - Platform Syntax Validation
Locate and repair all platform syntax errors.

This is NOT architecture work.
This IS runtime infrastructure repair.
"""

import os
import sys
import ast
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

# Add qubo-backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'qubo-backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlatformSyntaxValidator:
    """
    Validate and fix platform syntax errors.
    
    This is NOT architecture work.
    This IS runtime infrastructure repair.
    """
    
    def __init__(self):
        self.qubo_backend_path = os.path.join(os.getcwd(), 'qubo-backend')
        self.python_files = []
        
        logger.info("Platform syntax validator initialized")
    
    def validate_all_syntax(self) -> Dict[str, Any]:
        """Validate all Python files for syntax errors."""
        try:
            logger.info("Validating all platform syntax...")
            
            # Step 1: Find all Python files
            file_discovery_result = self._find_python_files()
            
            # Step 2: Validate syntax for all files
            syntax_validation_result = self._validate_syntax()
            
            # Step 3: Identify specific syntax errors
            error_analysis_result = self._analyze_syntax_errors()
            
            # Step 4: Generate fix recommendations
            fix_recommendations_result = self._generate_fix_recommendations()
            
            # Determine overall success
            all_passed = (
                file_discovery_result['success'] and
                syntax_validation_result['success'] and
                error_analysis_result['success'] and
                fix_recommendations_result['success']
            )
            
            return {
                'overall_success': all_passed,
                'file_discovery_result': file_discovery_result,
                'syntax_validation_result': syntax_validation_result,
                'error_analysis_result': error_analysis_result,
                'fix_recommendations_result': fix_recommendations_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Platform syntax validation failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _find_python_files(self) -> Dict[str, Any]:
        """Find all Python files in qubo-backend."""
        try:
            python_files = []
            
            for root, dirs, files in os.walk(self.qubo_backend_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        python_files.append(file_path)
            
            self.python_files = python_files
            
            return {
                'success': True,
                'total_files': len(python_files),
                'python_files': python_files
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_syntax(self) -> Dict[str, Any]:
        """Validate syntax for all Python files."""
        try:
            validation_results = {}
            
            for file_path in self.python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                    
                    # Try to parse the file
                    ast.parse(source)
                    
                    validation_results[file_path] = {
                        'valid': True,
                        'error': None
                    }
                    
                except SyntaxError as e:
                    validation_results[file_path] = {
                        'valid': False,
                        'error': f"SyntaxError: {str(e)}",
                        'line': e.lineno,
                        'offset': e.offset
                    }
                except Exception as e:
                    validation_results[file_path] = {
                        'valid': False,
                        'error': f"Error: {str(e)}"
                    }
            
            # Count valid files
            valid_count = sum(
                1 for result in validation_results.values()
                if result.get('valid', False)
            )
            
            return {
                'success': valid_count == len(self.python_files),
                'validation_results': validation_results,
                'valid_count': valid_count,
                'total_count': len(self.python_files)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_syntax_errors(self) -> Dict[str, Any]:
        """Analyze specific syntax errors."""
        try:
            error_analysis = {}
            
            # Known problematic files from previous validation
            problematic_files = [
                'user_quota_management.py',
                'execution_storage.py',
                'replay_service.py',
                'audit_trail_system.py',
                'monitoring_service.py'
            ]
            
            for problematic_file in problematic_files:
                file_path = os.path.join(self.qubo_backend_path, 'qubo_backend', 
                                       problematic_file.replace('.py', '').split('_')[0],
                                       problematic_file)
                
                # Try different possible paths
                possible_paths = [
                    os.path.join(self.qubo_backend_path, 'qubo_backend', 'productization', problematic_file),
                    os.path.join(self.qubo_backend_path, 'qubo_backend', 'storage', problematic_file),
                    os.path.join(self.qubo_backend_path, 'qubo_backend', 'operations', problematic_file),
                    os.path.join(self.qubo_backend_path, 'qubo_backend', 'monitoring', problematic_file)
                ]
                
                actual_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        actual_path = path
                        break
                
                if actual_path:
                    try:
                        with open(actual_path, 'r', encoding='utf-8') as f:
                            source = f.read()
                        
                        # Try to parse
                        ast.parse(source)
                        
                        error_analysis[problematic_file] = {
                            'has_error': False,
                            'error': None,
                            'path': actual_path
                        }
                        
                    except SyntaxError as e:
                        error_analysis[problematic_file] = {
                            'has_error': True,
                            'error': str(e),
                            'line': e.lineno,
                            'offset': e.offset,
                            'path': actual_path
                        }
                    except Exception as e:
                        error_analysis[problematic_file] = {
                            'has_error': True,
                            'error': str(e),
                            'path': actual_path
                        }
                else:
                    error_analysis[problematic_file] = {
                        'has_error': True,
                        'error': 'File not found',
                        'path': None
                    }
            
            # Check for missing modules
            missing_modules = []
            try:
                import qubo_backend.optimization.braket_cloud_execution
            except ImportError:
                missing_modules.append('qubo_backend.optimization.braket_cloud_execution')
            
            return {
                'success': len([e for e in error_analysis.values() if e.get('has_error', False)]) == 0,
                'error_analysis': error_analysis,
                'missing_modules': missing_modules
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_fix_recommendations(self) -> Dict[str, Any]:
        """Generate fix recommendations for syntax errors."""
        try:
            fix_recommendations = []
            
            # Based on known errors from previous validation
            known_errors = [
                {
                    'file': 'user_quota_management.py',
                    'error': 'non-default argument follows default argument (line 138)',
                    'fix': 'Reorder function arguments - non-default arguments must come before default arguments'
                },
                {
                    'file': 'execution_storage.py',
                    'error': 'non-default argument \'status\' follows default argument',
                    'fix': 'Move status parameter before default arguments in function definition'
                },
                {
                    'file': 'replay_service.py',
                    'error': 'non-default argument \'status\' follows default argument',
                    'fix': 'Move status parameter before default arguments in function definition'
                },
                {
                    'file': 'audit_trail_system.py',
                    'error': 'non-default argument \'resource\' follows default argument',
                    'fix': 'Move resource parameter before default arguments in function definition'
                },
                {
                    'file': 'monitoring_service.py',
                    'error': 'No module named \'qubo_backend.optimization.braket_cloud_execution\'',
                    'fix': 'Create missing braket_cloud_execution.py module or remove import'
                }
            ]
            
            for error_info in known_errors:
                fix_recommendations.append({
                    'file': error_info['file'],
                    'error': error_info['error'],
                    'fix': error_info['fix'],
                    'priority': 'high'
                })
            
            return {
                'success': True,
                'fix_recommendations': fix_recommendations,
                'total_recommendations': len(fix_recommendations)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """Print validation results."""
        print("\n" + "="*80)
        print("PLATFORM SYNTAX VALIDATION RESULTS")
        print("="*80)
        
        # Overall status
        status_emoji = "✅" if results.get('overall_success', False) else "❌"
        print(f"\nOverall Status: {status_emoji} {'PASSED' if results.get('overall_success', False) else 'FAILED'}")
        
        # File discovery results
        file_discovery_result = results.get('file_discovery_result', {})
        if file_discovery_result.get('success', False):
            print(f"\n✅ File Discovery:")
            print(f"  Total Python Files: {file_discovery_result.get('total_files', 0)}")
        else:
            print(f"\n❌ File Discovery: {file_discovery_result.get('error', 'unknown')}")
        
        # Syntax validation results
        syntax_validation_result = results.get('syntax_validation_result', {})
        if syntax_validation_result.get('success', False):
            print(f"\n✅ Syntax Validation:")
            print(f"  Valid Files: {syntax_validation_result.get('valid_count', 0)}/{syntax_validation_result.get('total_count', 0)}")
        else:
            print(f"\n❌ Syntax Validation:")
            print(f"  Valid Files: {syntax_validation_result.get('valid_count', 0)}/{syntax_validation_result.get('total_count', 0)}")
            
            # Show invalid files
            validation_results = syntax_validation_result.get('validation_results', {})
            invalid_files = [(file, result) for file, result in validation_results.items() if not result.get('valid', False)]
            
            if invalid_files:
                print(f"\n  Invalid Files:")
                for file_path, result in invalid_files[:10]:  # Show first 10
                    print(f"    ❌ {os.path.basename(file_path)}: {result.get('error', 'unknown')}")
        
        # Error analysis results
        error_analysis_result = results.get('error_analysis_result', {})
        if error_analysis_result.get('success', False):
            print(f"\n✅ Error Analysis:")
            print(f"  No critical syntax errors found")
        else:
            print(f"\n❌ Error Analysis:")
            
            error_analysis = error_analysis_result.get('error_analysis', {})
            for file_name, analysis in error_analysis.items():
                if analysis.get('has_error', False):
                    print(f"  ❌ {file_name}: {analysis.get('error', 'unknown')}")
            
            missing_modules = error_analysis_result.get('missing_modules', [])
            if missing_modules:
                print(f"\n  Missing Modules:")
                for module in missing_modules:
                    print(f"    ❌ {module}")
        
        # Fix recommendations results
        fix_recommendations_result = results.get('fix_recommendations_result', {})
        if fix_recommendations_result.get('success', False):
            print(f"\n✅ Fix Recommendations:")
            recommendations = fix_recommendations_result.get('fix_recommendations', [])
            for rec in recommendations:
                print(f"  📋 {rec['file']}:")
                print(f"     Error: {rec['error']}")
                print(f"     Fix: {rec['fix']}")
                print(f"     Priority: {rec['priority']}")
        else:
            print(f"\n❌ Fix Recommendations: {fix_recommendations_result.get('error', 'unknown')}")
        
        print("\n" + "="*80)
        
        # Final assessment
        if results.get('overall_success', False):
            print("🏆 PLATFORM SYNTAX VALIDATION: PASSED")
            print("✅ All Python files have valid syntax")
            print("✅ No critical syntax errors found")
            print("✅ Platform ready for import validation")
        else:
            print("❌ PLATFORM SYNTAX VALIDATION: FAILED")
            print("❌ Syntax errors need to be fixed")
            print("❌ Follow fix recommendations to repair")
        
        print("="*80)


def main():
    """Main validation execution."""
    validator = PlatformSyntaxValidator()
    
    try:
        results = validator.validate_all_syntax()
        validator.print_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Platform syntax validation interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Platform syntax validation failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
