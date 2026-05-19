"""
Benchmark Persistence for QUBO Portfolio Optimizer
Stores and displays historical benchmark results with comparison dashboards.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
import uuid

from .config import get_settings
from .cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Individual benchmark result data structure."""
    
    id: str
    solver_name: str
    solver_type: str
    problem_hash: str
    num_assets: int
    binary_bits: int
    risk_tolerance: float
    cardinality: int
    
    # Performance metrics
    solve_time_seconds: float
    sharpe_ratio: float
    energy_state: float
    convergence_iterations: int
    
    # Hardware info
    hardware_used: str
    gpu_used: bool
    cpu_cores: int
    memory_mb: int
    
    # Quality metrics
    constraint_satisfaction: float
    portfolio_variance: float
    expected_return: float
    
    # Metadata
    timestamp: datetime
    execution_id: str
    user_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkComparison:
    """Comparison data for leaderboard-style dashboards."""
    
    solver_name: str
    total_runs: int
    average_sharpe_ratio: float
    best_sharpe_ratio: float
    worst_sharpe_ratio: float
    average_solve_time: float
    success_rate: float
    last_run: datetime
    rank: int = 0


class BenchmarkPersistence:
    """
    Persistent storage and analysis for benchmark results.
    
    Features:
    - Store solve time, Sharpe ratio, energy state, convergence metrics
    - Hardware used, solver selected, execution timestamps
    - Leaderboard-style comparison dashboards
    - Historical trend analysis
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.benchmark_dir = self.settings.output_dir / "benchmarks"
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        
        # Index files
        self.results_file = self.benchmark_dir / "results.jsonl"
        self.index_file = self.benchmark_dir / "index.json"
        
        # In-memory cache
        self._results_cache: Dict[str, BenchmarkResult] = {}
        self._cache_dirty = False
        
        # Load existing data
        self._load_benchmarks()
    
    def _load_benchmarks(self) -> None:
        """Load existing benchmark results from storage."""
        try:
            # Load index
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    index_data = json.load(f)
                    
                # Reconstruct BenchmarkResult objects
                for result_id, result_data in index_data.items():
                    result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                    self._results_cache[result_id] = BenchmarkResult(**result_data)
            
            logger.info(f"Loaded {len(self._results_cache)} benchmark results from storage")
            
        except Exception as e:
            logger.error(f"Failed to load benchmark results: {e}")
            self._results_cache = {}
    
    def _save_benchmarks(self) -> None:
        """Save benchmark results to storage."""
        try:
            # Save index
            index_data = {}
            for result_id, result in self._results_cache.items():
                result_dict = asdict(result)
                result_dict['timestamp'] = result.timestamp.isoformat()
                index_data[result_id] = result_dict
            
            with open(self.index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            # Append to results log
            with open(self.results_file, 'a') as f:
                for result_id, result in self._results_cache.items():
                    if not self._result_exists_in_log(result_id):
                        result_dict = asdict(result)
                        result_dict['timestamp'] = result.timestamp.isoformat()
                        f.write(json.dumps(result_dict) + '\n')
            
            self._cache_dirty = False
            logger.info(f"Saved {len(self._results_cache)} benchmark results to storage")
            
        except Exception as e:
            logger.error(f"Failed to save benchmark results: {e}")
    
    def _result_exists_in_log(self, result_id: str) -> bool:
        """Check if result already exists in log file."""
        if not self.results_file.exists():
            return False
        
        try:
            with open(self.results_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get('id') == result_id:
                            return True
            return False
        except Exception:
            return False
    
    async def store_benchmark_result(self, result: BenchmarkResult) -> str:
        """
        Store a new benchmark result.
        
        Args:
            result: Benchmark result to store
            
        Returns:
            ID of stored result
        """
        # Generate unique ID if not provided
        if not result.id:
            result.id = str(uuid.uuid4())
        
        # Set timestamp if not provided
        if not result.timestamp:
            result.timestamp = datetime.now()
        
        # Store in cache
        self._results_cache[result.id] = result
        self._cache_dirty = True
        
        # Update cache
        problem_key = f"{result.solver_name}:{result.problem_hash}"
        CACHE_MANAGER.set_benchmark_result(result.solver_name, result.problem_hash, asdict(result))
        
        logger.info(f"Stored benchmark result: {result.id} ({result.solver_name})")
        return result.id
    
    def get_benchmark_result(self, result_id: str) -> Optional[BenchmarkResult]:
        """Get a specific benchmark result by ID."""
        return self._results_cache.get(result_id)
    
    def get_benchmark_results(self,
                            solver_name: Optional[str] = None,
                            problem_hash: Optional[str] = None,
                            since: Optional[datetime] = None,
                            limit: int = 100) -> List[BenchmarkResult]:
        """
        Get benchmark results with optional filtering.
        
        Args:
            solver_name: Filter by solver name
            problem_hash: Filter by problem hash
            since: Filter results since this datetime
            limit: Maximum number of results to return
            
        Returns:
            List of matching benchmark results
        """
        results = list(self._results_cache.values())
        
        # Apply filters
        if solver_name:
            results = [r for r in results if r.solver_name == solver_name]
        
        if problem_hash:
            results = [r for r in results if r.problem_hash == problem_hash]
        
        if since:
            results = [r for r in results if r.timestamp >= since]
        
        # Sort by timestamp (newest first) and limit
        results.sort(key=lambda r: r.timestamp, reverse=True)
        return results[:limit]
    
    def get_solver_leaderboard(self, 
                             days: int = 30,
                             min_runs: int = 5) -> List[BenchmarkComparison]:
        """
        Get leaderboard-style comparison of solver performance.
        
        Args:
            days: Number of days to consider for leaderboard
            min_runs: Minimum number of runs required for ranking
            
        Returns:
            List of solver comparisons ranked by performance
        """
        since = datetime.now() - timedelta(days=days)
        recent_results = [
            r for r in self._results_cache.values()
            if r.timestamp >= since
        ]
        
        # Group by solver
        solver_groups: Dict[str, List[BenchmarkResult]] = {}
        for result in recent_results:
            if result.solver_name not in solver_groups:
                solver_groups[result.solver_name] = []
            solver_groups[result.solver_name].append(result)
        
        # Calculate statistics for each solver
        comparisons = []
        for solver_name, results in solver_groups.items():
            if len(results) < min_runs:
                continue
            
            sharpe_ratios = [r.sharpe_ratio for r in results]
            solve_times = [r.solve_time_seconds for r in results]
            
            comparison = BenchmarkComparison(
                solver_name=solver_name,
                total_runs=len(results),
                average_sharpe_ratio=sum(sharpe_ratios) / len(sharpe_ratios),
                best_sharpe_ratio=max(sharpe_ratios),
                worst_sharpe_ratio=min(sharpe_ratios),
                average_solve_time=sum(solve_times) / len(solve_times),
                success_rate=100.0,  # All stored results are successful
                last_run=max(r.timestamp for r in results)
            )
            comparisons.append(comparison)
        
        # Sort by average Sharpe ratio (descending) and assign ranks
        comparisons.sort(key=lambda c: c.average_sharpe_ratio, reverse=True)
        for i, comparison in enumerate(comparisons):
            comparison.rank = i + 1
        
        return comparisons
    
    def get_performance_trends(self,
                             solver_name: str,
                             days: int = 90) -> Dict[str, Any]:
        """
        Get performance trends for a specific solver.
        
        Args:
            solver_name: Name of solver to analyze
            days: Number of days to analyze
            
        Returns:
            Performance trend data
        """
        since = datetime.now() - timedelta(days=days)
        results = [
            r for r in self._results_cache.values()
            if r.solver_name == solver_name and r.timestamp >= since
        ]
        
        if not results:
            return {
                "solver_name": solver_name,
                "period_days": days,
                "total_runs": 0,
                "trend": "no_data"
            }
        
        # Sort by time
        results.sort(key=lambda r: r.timestamp)
        
        # Calculate trends
        sharpe_series = [r.sharpe_ratio for r in results]
        time_series = [r.timestamp for r in results]
        solve_time_series = [r.solve_time_seconds for r in results]
        
        # Simple trend calculation (linear regression slope)
        if len(results) >= 2:
            import numpy as np
            x = np.arange(len(results))
            
            sharpe_slope = np.polyfit(x, sharpe_series, 1)[0]
            time_slope = np.polyfit(x, solve_time_series, 1)[0]
            
            sharpe_trend = "improving" if sharpe_slope > 0 else "declining"
            time_trend = "improving" if time_slope < 0 else "declining"
        else:
            sharpe_trend = "insufficient_data"
            time_trend = "insufficient_data"
            sharpe_slope = 0
            time_slope = 0
        
        return {
            "solver_name": solver_name,
            "period_days": days,
            "total_runs": len(results),
            "first_run": results[0].timestamp.isoformat(),
            "last_run": results[-1].timestamp.isoformat(),
            "performance_metrics": {
                "average_sharpe_ratio": sum(sharpe_series) / len(sharpe_series),
                "best_sharpe_ratio": max(sharpe_series),
                "worst_sharpe_ratio": min(sharpe_series),
                "average_solve_time": sum(solve_time_series) / len(solve_time_series),
                "best_solve_time": min(solve_time_series),
                "worst_solve_time": max(solve_time_series)
            },
            "trends": {
                "sharpe_ratio_trend": sharpe_trend,
                "sharpe_ratio_slope": sharpe_slope,
                "solve_time_trend": time_trend,
                "solve_time_slope": time_slope
            },
            "time_series": [
                {
                    "timestamp": t.isoformat(),
                    "sharpe_ratio": s,
                    "solve_time_seconds": st
                }
                for t, s, st in zip(time_series, sharpe_series, solve_time_series)
            ]
        }
    
    def compare_solvers_for_problem(self,
                                  problem_hash: str,
                                  num_assets: int,
                                  binary_bits: int) -> List[Dict[str, Any]]:
        """
        Compare all solvers for a specific problem.
        
        Args:
            problem_hash: Hash of the problem definition
            num_assets: Number of assets in problem
            binary_bits: Number of binary bits
            
        Returns:
            Comparison results for all solvers that solved this problem
        """
        results = [
            r for r in self._results_cache.values()
            if (r.problem_hash == problem_hash and
                r.num_assets == num_assets and
                r.binary_bits == binary_bits)
        ]
        
        # Group by solver and get best result for each
        solver_best = {}
        for result in results:
            if (result.solver_name not in solver_best or
                result.sharpe_ratio > solver_best[result.solver_name].sharpe_ratio):
                solver_best[result.solver_name] = result
        
        # Convert to comparison format
        comparisons = []
        for solver_name, result in solver_best.items():
            comparisons.append({
                "solver_name": solver_name,
                "solver_type": result.solver_type,
                "sharpe_ratio": result.sharpe_ratio,
                "solve_time_seconds": result.solve_time_seconds,
                "energy_state": result.energy_state,
                "convergence_iterations": result.convergence_iterations,
                "constraint_satisfaction": result.constraint_satisfaction,
                "hardware_used": result.hardware_used,
                "timestamp": result.timestamp.isoformat(),
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by Sharpe ratio and assign ranks
        comparisons.sort(key=lambda c: c["sharpe_ratio"], reverse=True)
        for i, comparison in enumerate(comparisons):
            comparison["rank"] = i + 1
        
        return comparisons
    
    def get_benchmark_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get overall benchmark statistics."""
        since = datetime.now() - timedelta(days=days)
        recent_results = [
            r for r in self._results_cache.values()
            if r.timestamp >= since
        ]
        
        if not recent_results:
            return {
                "period_days": days,
                "total_runs": 0,
                "unique_solvers": 0,
                "average_sharpe_ratio": 0.0
            }
        
        # Calculate statistics
        solver_names = set(r.solver_name for r in recent_results)
        sharpe_ratios = [r.sharpe_ratio for r in recent_results]
        solve_times = [r.solve_time_seconds for r in recent_results]
        
        return {
            "period_days": days,
            "total_runs": len(recent_results),
            "unique_solvers": len(solver_names),
            "average_sharpe_ratio": sum(sharpe_ratios) / len(sharpe_ratios),
            "best_sharpe_ratio": max(sharpe_ratios),
            "worst_sharpe_ratio": min(sharpe_ratios),
            "average_solve_time": sum(solve_times) / len(solve_times),
            "best_solve_time": min(solve_times),
            "solver_breakdown": {
                solver: len([r for r in recent_results if r.solver_name == solver])
                for solver in solver_names
            }
        }
    
    async def cleanup_old_results(self, days_to_keep: int = 365) -> int:
        """Clean up old benchmark results."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        old_results = [
            result_id for result_id, result in self._results_cache.items()
            if result.timestamp < cutoff_date
        ]
        
        for result_id in old_results:
            del self._results_cache[result_id]
        
        if old_results:
            self._cache_dirty = True
            await self._save_benchmarks()
        
        logger.info(f"Cleaned up {len(old_results)} old benchmark results")
        return len(old_results)
    
    async def flush_to_disk(self) -> None:
        """Force save cached results to disk."""
        if self._cache_dirty:
            await self._save_benchmarks()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "total_results": len(self._results_cache),
            "cache_dirty": self._cache_dirty,
            "storage_directory": str(self.benchmark_dir),
            "results_file": str(self.results_file),
            "index_file": str(self.index_file),
            "file_size_mb": self._get_file_size_mb()
        }
    
    def _get_file_size_mb(self) -> float:
        """Get total size of benchmark files in MB."""
        total_size = 0
        
        if self.results_file.exists():
            total_size += self.results_file.stat().st_size
        
        if self.index_file.exists():
            total_size += self.index_file.stat().st_size
        
        return total_size / (1024 * 1024)


# Global benchmark persistence instance
BENCHMARK_PERSISTENCE = BenchmarkPersistence()
