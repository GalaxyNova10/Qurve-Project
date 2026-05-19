#!/usr/bin/env python3
"""
Qurve AI - Import Graph Audit Tool
Comprehensive analysis of circular import dependencies
"""

import ast
import os
import sys
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, deque

def extract_imports(file_path: str) -> List[Tuple[str, str]]:
    """Extract all imports from a Python file."""
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((file_path, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append((file_path, f"{node.module}.{alias.name}"))
                else:
                    for alias in node.names:
                        imports.append((file_path, alias.name))
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def build_dependency_graph(root_dir: str) -> Dict[str, Set[str]]:
    """Build dependency graph from source files."""
    graph = defaultdict(set)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__ and other non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Extract imports for each file
    all_imports = {}
    for file_path in python_files:
        imports = extract_imports(file_path)
        all_imports[file_path] = imports
    
    # Build dependency graph
    for file_path, imports in all_imports.items():
        for source_file, import_name in imports:
            # Check if import is within the project
            if import_name.startswith('qubo_backend'):
                # Convert module path to file path
                module_parts = import_name.split('.')
                potential_file = os.path.join(root_dir, *module_parts) + '.py'
                
                if os.path.exists(potential_file):
                    graph[file_path].add(potential_file)
    
    return graph

def find_circular_dependencies(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Find all circular dependencies in the graph."""
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: str, path: List[str]) -> bool:
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph[node]:
            if dfs(neighbor, path):
                return True
        
        rec_stack.remove(node)
        path.pop()
        return False
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles

def analyze_telemetry_imports() -> Dict[str, Any]:
    """Analyze telemetry-specific import issues."""
    print("🔍 TELEMETRY IMPORT ANALYSIS")
    print("=" * 60)
    
    root_dir = "qubo_backend"
    
    # Build dependency graph
    print("📊 Building dependency graph...")
    graph = build_dependency_graph(root_dir)
    
    # Find circular dependencies
    print("🔄 Detecting circular dependencies...")
    cycles = find_circular_dependencies(graph)
    
    # Analyze telemetry module imports
    telemetry_modules = []
    for file_path in graph.keys():
        if 'telemetry' in file_path:
            telemetry_modules.append(file_path)
    
    print(f"✅ Found {len(telemetry_modules)} telemetry modules")
    print(f"✅ Found {len(cycles)} circular dependencies")
    
    # Report findings
    report = {
        "total_modules": len(graph),
        "telemetry_modules": len(telemetry_modules),
        "circular_dependencies": len(cycles),
        "cycles": cycles,
        "telemetry_modules_list": telemetry_modules
    }
    
    if cycles:
        print(f"\n🔴 CIRCULAR DEPENDENCIES FOUND:")
        for i, cycle in enumerate(cycles, 1):
            print(f"  Cycle {i}: {' -> '.join([os.path.basename(f) for f in cycle])}")
    
    # Check telemetry-specific issues
    telemetry_imports = {}
    for module in telemetry_modules:
        imports = []
        for neighbor in graph[module]:
            if 'telemetry' in neighbor:
                imports.append(neighbor)
        telemetry_imports[module] = imports
    
    print(f"\n📊 TELEMETRY MODULE DEPENDENCIES:")
    for module, deps in telemetry_imports.items():
        module_name = os.path.basename(module)
        dep_names = [os.path.basename(d) for d in deps]
        print(f"  {module_name}: {dep_names}")
    
    return report

def main():
    """Run import audit analysis."""
    print("🚀 QURVE AI - IMPORT GRAPH AUDIT")
    print("=" * 60)
    
    try:
        report = analyze_telemetry_imports()
        
        print(f"\n{'='*60}")
        print("IMPORT AUDIT SUMMARY")
        print("=" * 60)
        print(f"Total modules analyzed: {report['total_modules']}")
        print(f"Telemetry modules: {report['telemetry_modules']}")
        print(f"Circular dependencies: {report['circular_dependencies']}")
        
        if report['circular_dependencies'] > 0:
            print(f"\n🔴 CRITICAL: {report['circular_dependencies']} circular dependencies found")
            print("   These must be resolved for production deployment")
        else:
            print(f"\n✅ No circular dependencies detected")
        
        return report
        
    except Exception as e:
        print(f"❌ Import audit failed: {str(e)}")
        return {"error": str(e)}

if __name__ == '__main__':
    main()
