#!/usr/bin/env python3
"""
Qurve AI Telemetry Validation - Structured Logs Consistency
Tests logging quality, consistency, and observability
"""

import sys
import time
import logging
import asyncio
import re
import json
from typing import List, Dict, Any
from collections import defaultdict, Counter

# Configure logging for validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== TELEMETRY VALIDATION - STRUCTURED LOGS CONSISTENCY ===')

# Add current directory to path
sys.path.append('.')

# Import required modules
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.benchmark import run_benchmark

def create_test_request() -> SolverRequest:
    """Create a test request for telemetry validation."""
    
    return SolverRequest(
        mu=[0.05, 0.08, 0.12, 0.15, 0.20],
        sigma=[[0.01, 0.002, 0.003, 0.004, 0.005],
            [0.002, 0.003, 0.004, 0.005, 0.006],
            [0.003, 0.004, 0.005, 0.006, 0.007],
            [0.004, 0.005, 0.006, 0.007, 0.008],
            [0.005, 0.006, 0.007, 0.008, 0.009]],
        tickers=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
        sectors=['tech', 'tech', 'tech', 'tech', 'tech'],
        cardinality=3,
        max_sector_exposure=0.3,
        risk_tolerance=0.5,
        binary_bits=3,
        solver='classical',
        trajectories=10,
        time_limit_seconds=30
    )

class LogCapture:
    """Capture and analyze log messages."""
    
    def __init__(self):
        self.logs = []
        self.handler = None
    
    def start_capture(self):
        """Start capturing logs."""
        self.logs = []
        
        # Create custom handler
        class ListHandler(logging.Handler):
            def __init__(self, log_list):
                super().__init__()
                self.log_list = log_list
            
            def emit(self, record):
                self.log_list.append(self.format(record))
        
        self.handler = ListHandler(self.logs)
        self.handler.setLevel(logging.INFO)
        
        # Add to all relevant loggers
        loggers = [
            logging.getLogger('qubo_backend.optimization.neal_solver'),
            logging.getLogger('qubo_backend.optimization.qiskit_solver'),
            logging.getLogger('qubo_backend.optimization.braket_solver'),
            logging.getLogger('qubo_backend.optimization.classical_solver'),
            logging.getLogger('qubo_backend.solvers.benchmark')
        ]
        
        for logger in loggers:
            logger.addHandler(self.handler)
            logger.setLevel(logging.INFO)
    
    def stop_capture(self):
        """Stop capturing logs."""
        if self.handler:
            # Remove from all loggers
            loggers = [
                logging.getLogger('qubo_backend.optimization.neal_solver'),
                logging.getLogger('qubo_backend.optimization.qiskit_solver'),
                logging.getLogger('qubo_backend.optimization.braket_solver'),
                logging.getLogger('qubo_backend.optimization.classical_solver'),
                logging.getLogger('qubo_backend.solvers.benchmark')
            ]
            for logger in loggers:
                logger.removeHandler(self.handler)
    
    def get_logs(self) -> List[str]:
        """Get captured logs."""
        return self.logs.copy()

def analyze_log_structure(logs: List[str]) -> Dict[str, Any]:
    """Analyze log structure and consistency."""
    
    analysis = {
        'total_logs': len(logs),
        'structured_logs': 0,
        'tagged_logs': 0,
        'solver_tags': Counter(),
        'execution_tags': Counter(),
        'error_tags': Counter(),
        'timestamp_consistency': 0,
        'format_consistency': 0,
        'missing_tags': [],
        'inconsistent_formats': []
    }
    
    # Expected tag patterns
    expected_solver_tags = [
        '[NEAL_', '[QISKIT_', '[BRAKET_', '[CLASSICAL_'
    ]
    expected_execution_tags = [
        '_EXECUTION_', '_PROFILE_', '_SUCCESS', '_FAILURE'
    ]
    expected_error_tags = [
        '_ERROR_', '_FAILURE', '_INIT_FAILURE'
    ]
    
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}'
    
    for log in logs:
        # Check for structured format
        if '[' in log and ']' in log:
            analysis['structured_logs'] += 1
        
        # Check for tags
        tags = re.findall(r'\[([^\]]+)\]', log)
        if tags:
            analysis['tagged_logs'] += 1
            
            # Categorize tags
            for tag in tags:
                # Solver tags
                for solver_tag in expected_solver_tags:
                    if tag.startswith(solver_tag):
                        analysis['solver_tags'][solver_tag] += 1
                        break
                
                # Execution tags
                for exec_tag in expected_execution_tags:
                    if exec_tag in tag:
                        analysis['execution_tags'][exec_tag] += 1
                        break
                
                # Error tags
                for error_tag in expected_error_tags:
                    if error_tag in tag:
                        analysis['error_tags'][error_tag] += 1
                        break
        
        # Check timestamp consistency
        if re.match(timestamp_pattern, log):
            analysis['timestamp_consistency'] += 1
        
        # Check format consistency (basic)
        if ' - ' in log and len(log.split(' - ')) >= 3:
            analysis['format_consistency'] += 1
        else:
            analysis['inconsistent_formats'].append(log[:100])  # First 100 chars
    
    # Calculate percentages
    if analysis['total_logs'] > 0:
        analysis['structured_percentage'] = (analysis['structured_logs'] / analysis['total_logs']) * 100
        analysis['tagged_percentage'] = (analysis['tagged_logs'] / analysis['total_logs']) * 100
        analysis['timestamp_consistency_percentage'] = (analysis['timestamp_consistency'] / analysis['total_logs']) * 100
        analysis['format_consistency_percentage'] = (analysis['format_consistency'] / analysis['total_logs']) * 100
    else:
        analysis['structured_percentage'] = 0
        analysis['tagged_percentage'] = 0
        analysis['timestamp_consistency_percentage'] = 0
        analysis['format_consistency_percentage'] = 0
    
    return analysis

async def run_telemetry_validation():
    """Run comprehensive telemetry validation."""
    
    print("Starting telemetry validation...")
    
    # Create log capture
    log_capture = LogCapture()
    
    # Start capturing
    log_capture.start_capture()
    
    try:
        # Run benchmark to generate logs
        test_request = create_test_request()
        result = await run_benchmark(test_request, timeout_ms=30000)
        
        # Wait a moment for all logs to flush
        await asyncio.sleep(0.5)
        
    except Exception as e:
        print(f"Error during benchmark: {e}")
    finally:
        # Stop capturing
        log_capture.stop_capture()
    
    # Get captured logs
    logs = log_capture.get_logs()
    
    print(f"Captured {len(logs)} log entries")
    
    # Analyze log structure
    analysis = analyze_log_structure(logs)
    
    # Print analysis results
    print(f"\n=== LOG STRUCTURE ANALYSIS ===")
    print(f"Total logs: {analysis['total_logs']}")
    print(f"Structured logs: {analysis['structured_logs']} ({analysis['structured_percentage']:.1f}%)")
    print(f"Tagged logs: {analysis['tagged_logs']} ({analysis['tagged_percentage']:.1f}%)")
    print(f"Timestamp consistency: {analysis['timestamp_consistency']} ({analysis['timestamp_consistency_percentage']:.1f}%)")
    print(f"Format consistency: {analysis['format_consistency']} ({analysis['format_consistency_percentage']:.1f}%)")
    
    print(f"\n=== SOLVER TAG ANALYSIS ===")
    for tag, count in analysis['solver_tags'].most_common():
        print(f"{tag}: {count} occurrences")
    
    print(f"\n=== EXECUTION TAG ANALYSIS ===")
    for tag, count in analysis['execution_tags'].most_common():
        print(f"{tag}: {count} occurrences")
    
    print(f"\n=== ERROR TAG ANALYSIS ===")
    for tag, count in analysis['error_tags'].most_common():
        print(f"{tag}: {count} occurrences")
    
    if analysis['inconsistent_formats']:
        print(f"\n=== INCONSISTENT FORMATS ===")
        for i, fmt in enumerate(analysis['inconsistent_formats'][:5]):  # First 5
            print(f"{i+1}. {fmt}")
    
    # Quality assessment
    print(f"\n=== TELEMETRY QUALITY ASSESSMENT ===")
    
    quality_score = 0
    
    # Structured logging (30% weight)
    structure_score = min(analysis['structured_percentage'] / 100 * 30, 30)
    quality_score += structure_score
    print(f"Structured logging score: {structure_score:.1f}/30")
    
    # Tag consistency (25% weight)
    tag_score = min(analysis['tagged_percentage'] / 100 * 25, 25)
    quality_score += tag_score
    print(f"Tag consistency score: {tag_score:.1f}/25")
    
    # Timestamp consistency (20% weight)
    timestamp_score = min(analysis['timestamp_consistency_percentage'] / 100 * 20, 20)
    quality_score += timestamp_score
    print(f"Timestamp consistency score: {timestamp_score:.1f}/20")
    
    # Format consistency (25% weight)
    format_score = min(analysis['format_consistency_percentage'] / 100 * 25, 25)
    quality_score += format_score
    print(f"Format consistency score: {format_score:.1f}/25")
    
    print(f"Overall telemetry quality score: {quality_score:.1f}/100")
    
    # Overall assessment
    if quality_score >= 80:
        print("✅ EXCELLENT: Highly structured and consistent logging")
    elif quality_score >= 60:
        print("⚠️  GOOD: Generally well-structured logging")
    elif quality_score >= 40:
        print("❌ POOR: Inconsistent logging structure")
    else:
        print("❌ CRITICAL: Major logging issues")
    
    # Specific recommendations
    print(f"\n=== TELEMETRY RECOMMENDATIONS ===")
    
    if analysis['structured_percentage'] < 80:
        print("• Improve structured logging consistency")
    
    if analysis['tagged_percentage'] < 80:
        print("• Add more descriptive tags to log messages")
    
    if analysis['timestamp_consistency_percentage'] < 90:
        print("• Standardize timestamp format across all loggers")
    
    if analysis['format_consistency_percentage'] < 90:
        print("• Standardize log message format")
    
    # Check for missing critical tags
    critical_tags = ['_EXECUTION_START', '_EXECUTION_SUCCESS', '_EXECUTION_FAILURE']
    found_critical = []
    for tag in critical_tags:
        if any(tag in log for log in logs):
            found_critical.append(tag)
    
    missing_critical = set(critical_tags) - set(found_critical)
    if missing_critical:
        print(f"• Missing critical execution tags: {missing_critical}")
    else:
        print("✅ All critical execution tags present")
    
    return analysis, quality_score

if __name__ == '__main__':
    asyncio.run(run_telemetry_validation())
