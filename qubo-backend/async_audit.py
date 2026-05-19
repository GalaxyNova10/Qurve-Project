#!/usr/bin/env python3
"""
Qurve AI - Async Audit Tool
Comprehensive audit of task orchestration system for async correctness
"""

import ast
import os
import sys
from typing import List, Dict, Any

def find_async_issues(file_path: str) -> List[Dict[str, Any]]:
    """Find async issues in Python file."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content, filename=file_path)
        
        # Check for async issues
        for node in ast.walk(tree):
            # Check for missing awaits
            if isinstance(node, ast.Await):
                continue  # This is good
            
            # Check for asyncio.run in async functions
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (node.func.attr == 'run' and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'asyncio'):
                    issues.append({
                        "type": "asyncio_run_in_event_loop",
                        "line": node.lineno,
                        "message": "asyncio.run() called inside running event loop",
                        "severity": "critical"
                    })
            
            # Check for blocking operations in async functions
            if isinstance(node, ast.Call):
                # Check for time.sleep in async context
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'sleep' and
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'time'):
                    issues.append({
                        "type": "blocking_sleep_in_async",
                        "line": node.lineno,
                        "message": "time.sleep() used in async function (should use asyncio.sleep())",
                        "severity": "warning"
                    })
            
            # Check for nested event loops
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (node.func.attr == 'run' and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'asyncio'):
                    issues.append({
                        "type": "nested_event_loop",
                        "line": node.lineno,
                        "message": "Potential nested event loop detected",
                        "severity": "critical"
                    })
            
            # Check for unbounded task spawning
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (node.func.attr in ['create_task', 'ensure_future'] and 
                    not any(isinstance(parent, ast.Await) for parent in ast.walk(tree) 
                           if hasattr(parent, 'lineno') and parent.lineno == node.lineno)):
                    issues.append({
                        "type": "unawaited_task_creation",
                        "line": node.lineno,
                        "message": "Task created but never awaited",
                        "severity": "critical"
                    })
            
            # Check for missing try/except in async functions
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef):
                    has_try_except = any(
                        isinstance(child, ast.Try) 
                        for child in ast.walk(node)
                    )
                    if not has_try_except:
                        issues.append({
                            "type": "async_function_no_error_handling",
                            "line": node.lineno,
                            "message": "Async function missing try/except block",
                            "severity": "warning"
                        })
        
        return issues
        
    except Exception as e:
        return [{
            "type": "parse_error",
            "line": 0,
            "message": f"Failed to parse file: {str(e)}",
            "severity": "critical"
        }]

def audit_task_system() -> Dict[str, Any]:
    """Audit entire task orchestration system."""
    print("🔍 ASYNC AUDIT - SCANNING TASK ORCHESTRATION SYSTEM")
    print("=" * 60)
    
    target_files = [
        'qubo_backend/tasks/benchmark_queue.py',
        'qubo_backend/tasks/worker_pool.py', 
        'qubo_backend/tasks/async_runner.py',
        'qubo_backend/tasks/task_models.py'
    ]
    
    all_issues = {}
    total_issues = 0
    critical_issues = 0
    
    for file_path in target_files:
        if os.path.exists(file_path):
            print(f"\n📁 Scanning: {file_path}")
            issues = find_async_issues(file_path)
            all_issues[file_path] = issues
            
            file_critical = len([i for i in issues if i['severity'] == 'critical'])
            file_total = len(issues)
            
            total_issues += file_total
            critical_issues += file_critical
            
            print(f"  Issues found: {file_total} ({file_critical} critical)")
            
            for issue in issues:
                severity_icon = "🔴" if issue['severity'] == 'critical' else "🟡"
                print(f"    {severity_icon} Line {issue['line']}: {issue['message']}")
        else:
            print(f"\n❌ File not found: {file_path}")
    
    # Summary
    print(f"\n{'='*60}")
    print("ASYNC AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total files scanned: {len(target_files)}")
    print(f"Total issues found: {total_issues}")
    print(f"Critical issues: {critical_issues}")
    print(f"Files with issues: {len([f for f, issues in all_issues.items() if issues])}")
    
    # Critical issues that need immediate attention
    critical_types = {}
    for file_path, issues in all_issues.items():
        for issue in issues:
            if issue['severity'] == 'critical':
                issue_type = issue['type']
                critical_types[issue_type] = critical_types.get(issue_type, 0) + 1
    
    if critical_types:
        print(f"\n🔴 CRITICAL ISSUE BREAKDOWN:")
        for issue_type, count in critical_types.items():
            print(f"  {issue_type}: {count}")
    
    return {
        "total_issues": total_issues,
        "critical_issues": critical_issues,
        "files_with_issues": len([f for f, issues in all_issues.items() if issues]),
        "critical_types": critical_types,
        "all_issues": all_issues
    }

if __name__ == '__main__':
    audit_task_system()
