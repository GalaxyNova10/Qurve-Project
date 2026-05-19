"""
QURVE AI - Demo Mode Datasets
Deterministic datasets for investor and demo demonstrations.

Features:
✅ Deterministic demo datasets
✅ Replayable benchmark sessions
✅ Stable frontend walkthroughs
✅ Pre-seeded execution histories
✅ Deterministic cloud demonstrations
✅ Safe demo governance limits
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoDatasetType(Enum):
    """Demo dataset type classifications."""
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    SUPPLY_CHAIN = "supply_chain"
    SCHEDULING = "scheduling"
    RESOURCE_ALLOCATION = "resource_allocation"
    FINANCIAL_MODELING = "financial_modeling"
    LOGISTICS = "logistics"


class DemoScenario(Enum):
    """Demo scenario classifications."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"
    RESEARCH = "research"


@dataclass
class DemoDataset:
    """Demo dataset definition."""
    dataset_id: str
    name: str
    description: str
    dataset_type: DemoDatasetType
    scenario: DemoScenario
    size: int
    complexity: str
    expected_result: Dict[str, Any]
    execution_time_estimate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DemoSession:
    """Demo session definition."""
    session_id: str
    name: str
    description: str
    datasets: List[str]
    workflow_steps: List[Dict[str, Any]]
    expected_outcomes: List[str]
    duration_estimate: float
    governance_limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DemoModeManager:
    """
    Production-grade demo mode manager.
    
    Features:
    - Deterministic demo datasets
    - Replayable benchmark sessions
    - Stable frontend walkthroughs
    - Pre-seeded execution histories
    - Deterministic cloud demonstrations
    - Safe demo governance limits
    """
    
    def __init__(self):
        self.datasets: Dict[str, DemoDataset] = {}
        self.sessions: Dict[str, DemoSession] = {}
        self.execution_histories: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize demo datasets
        self._initialize_datasets()
        self._initialize_sessions()
        self._initialize_execution_histories()
        
        logger.info("Demo mode manager initialized")
    
    def _initialize_datasets(self) -> None:
        """Initialize deterministic demo datasets."""
        
        # Portfolio Optimization Dataset
        self.datasets['portfolio_basic'] = DemoDataset(
            dataset_id='portfolio_basic',
            name='Basic Portfolio Optimization',
            description='Small portfolio optimization problem for demonstration',
            dataset_type=DemoDatasetType.PORTFOLIO_OPTIMIZATION,
            scenario=DemoScenario.BASIC,
            size=50,
            complexity='basic',
            expected_result={
                'optimal_return': 0.0825,
                'optimal_risk': 0.156,
                'selected_assets': [1, 3, 7, 12, 15],
                'execution_time_ms': 1250,
                'iterations': 100
            },
            execution_time_estimate=1.5,
            metadata={
                'industry': 'finance',
                'use_case': 'portfolio_optimization',
                'data_source': 'synthetic',
                'deterministic_seed': 42
            }
        )
        
        self.datasets['portfolio_intermediate'] = DemoDataset(
            dataset_id='portfolio_intermediate',
            name='Intermediate Portfolio Optimization',
            description='Medium portfolio optimization problem for demonstration',
            dataset_type=DemoDatasetType.PORTFOLIO_OPTIMIZATION,
            scenario=DemoScenario.INTERMEDIATE,
            size=200,
            complexity='intermediate',
            expected_result={
                'optimal_return': 0.0942,
                'optimal_risk': 0.178,
                'selected_assets': [2, 5, 8, 11, 14, 18, 22, 25],
                'execution_time_ms': 3200,
                'iterations': 500
            },
            execution_time_estimate=3.5,
            metadata={
                'industry': 'finance',
                'use_case': 'portfolio_optimization',
                'data_source': 'synthetic',
                'deterministic_seed': 123
            }
        )
        
        # Supply Chain Dataset
        self.datasets['supply_chain_basic'] = DemoDataset(
            dataset_id='supply_chain_basic',
            name='Basic Supply Chain Optimization',
            description='Small supply chain optimization problem',
            dataset_type=DemoDatasetType.SUPPLY_CHAIN,
            scenario=DemoScenario.BASIC,
            size=75,
            complexity='basic',
            expected_result={
                'optimal_cost': 1250000,
                'optimal_routes': [[1, 3, 5], [2, 4, 6], [7, 8, 9]],
                'savings_percentage': 12.5,
                'execution_time_ms': 2100,
                'iterations': 150
            },
            execution_time_estimate=2.5,
            metadata={
                'industry': 'logistics',
                'use_case': 'supply_chain',
                'data_source': 'synthetic',
                'deterministic_seed': 789
            }
        )
        
        # Scheduling Dataset
        self.datasets['scheduling_intermediate'] = DemoDataset(
            dataset_id='scheduling_intermediate',
            name='Intermediate Job Scheduling',
            description='Medium job scheduling optimization problem',
            dataset_type=DemoDatasetType.SCHEDULING,
            scenario=DemoScenario.INTERMEDIATE,
            size=150,
            complexity='intermediate',
            expected_result={
                'optimal_makespan': 480,
                'resource_utilization': 0.87,
                'schedule_conflicts': 0,
                'execution_time_ms': 4100,
                'iterations': 300
            },
            execution_time_estimate=4.5,
            metadata={
                'industry': 'manufacturing',
                'use_case': 'job_scheduling',
                'data_source': 'synthetic',
                'deterministic_seed': 456
            }
        )
        
        # Resource Allocation Dataset
        self.datasets['resource_allocation_advanced'] = DemoDataset(
            dataset_id='resource_allocation_advanced',
            name='Advanced Resource Allocation',
            description='Complex resource allocation problem',
            dataset_type=DemoDatasetType.RESOURCE_ALLOCATION,
            scenario=DemoScenario.ADVANCED,
            size=300,
            complexity='advanced',
            expected_result={
                'optimal_allocation': {
                    'resource_1': [1, 2, 5, 8, 11],
                    'resource_2': [3, 4, 6, 9, 12],
                    'resource_3': [7, 10, 13, 14, 15]
                },
                'total_cost': 875000,
                'efficiency_score': 0.92,
                'execution_time_ms': 8500,
                'iterations': 1000
            },
            execution_time_estimate=9.0,
            metadata={
                'industry': 'enterprise',
                'use_case': 'resource_allocation',
                'data_source': 'synthetic',
                'deterministic_seed': 999
            }
        )
        
        logger.info(f"Initialized {len(self.datasets)} demo datasets")
    
    def _initialize_sessions(self) -> None:
        """Initialize demo sessions."""
        
        # Basic Demo Session
        self.sessions['basic_demo'] = DemoSession(
            session_id='basic_demo',
            name='Basic Platform Demo',
            description='Introduction to QURVE AI platform capabilities',
            datasets=['portfolio_basic', 'supply_chain_basic'],
            workflow_steps=[
                {
                    'step_id': 1,
                    'name': 'Welcome & Overview',
                    'description': 'Platform introduction and overview',
                    'duration': 300,
                    'actions': ['show_dashboard', 'explain_architecture']
                },
                {
                    'step_id': 2,
                    'name': 'Portfolio Optimization Demo',
                    'description': 'Demonstrate portfolio optimization',
                    'duration': 600,
                    'actions': ['load_dataset', 'run_optimization', 'show_results']
                },
                {
                    'step_id': 3,
                    'name': 'Supply Chain Demo',
                    'description': 'Demonstrate supply chain optimization',
                    'duration': 600,
                    'actions': ['load_dataset', 'run_optimization', 'show_results']
                },
                {
                    'step_id': 4,
                    'name': 'Results Analysis',
                    'description': 'Analyze and compare results',
                    'duration': 300,
                    'actions': ['compare_results', 'show_insights']
                }
            ],
            expected_outcomes=[
                'Successful portfolio optimization with 8.25% return',
                'Successful supply chain optimization with 12.5% cost savings',
                'Demonstration of platform UI and capabilities',
                'Understanding of quantum optimization benefits'
            ],
            duration_estimate=1800,  # 30 minutes
            governance_limits={
                'max_executions_per_hour': 10,
                'max_cloud_executions': 2,
                'qpu_access': False,
                'max_dataset_size': 200
            },
            metadata={
                'target_audience': 'potential_customers',
                'complexity': 'basic',
                'interactive_elements': True
            }
        )
        
        # Advanced Demo Session
        self.sessions['advanced_demo'] = DemoSession(
            session_id='advanced_demo',
            name='Advanced Platform Demo',
            description='Advanced QURVE AI platform capabilities',
            datasets=['portfolio_intermediate', 'scheduling_intermediate', 'resource_allocation_advanced'],
            workflow_steps=[
                {
                    'step_id': 1,
                    'name': 'Advanced Overview',
                    'description': 'Advanced platform capabilities overview',
                    'duration': 300,
                    'actions': ['show_advanced_dashboard', 'explain_governance']
                },
                {
                    'step_id': 2,
                    'name': 'Multi-Problem Optimization',
                    'description': 'Demonstrate multiple optimization problems',
                    'duration': 900,
                    'actions': ['load_datasets', 'run_parallel_optimization', 'show_results']
                },
                {
                    'step_id': 3,
                    'name': 'Replay System Demo',
                    'description': 'Demonstrate replay and forensic capabilities',
                    'duration': 600,
                    'actions': ['show_replay_history', 'run_replay_analysis', 'show_insights']
                },
                {
                    'step_id': 4,
                    'name': 'Cloud Execution Demo',
                    'description': 'Demonstrate cloud execution capabilities',
                    'duration': 600,
                    'actions': ['run_cloud_execution', 'show_cloud_results', 'explain_scaling']
                },
                {
                    'step_id': 5,
                    'name': 'Advanced Analytics',
                    'description': 'Show advanced analytics and insights',
                    'duration': 300,
                    'actions': ['show_analytics', 'explain_insights', 'show_roi']
                }
            ],
            expected_outcomes=[
                'Successful multi-problem optimization',
                'Demonstration of replay system capabilities',
                'Cloud execution with scaling benefits',
                'Advanced analytics and insights',
                'ROI analysis and business case'
            ],
            duration_estimate=3600,  # 60 minutes
            governance_limits={
                'max_executions_per_hour': 20,
                'max_cloud_executions': 5,
                'qpu_access': True,
                'max_dataset_size': 500
            },
            metadata={
                'target_audience': 'enterprise_customers',
                'complexity': 'advanced',
                'interactive_elements': True,
                'requires_cloud_access': True
            }
        )
        
        # Investor Demo Session
        self.sessions['investor_demo'] = DemoSession(
            session_id='investor_demo',
            name='Investor Demo',
            description='Investor-focused demonstration of QURVE AI',
            datasets=['portfolio_basic', 'portfolio_intermediate'],
            workflow_steps=[
                {
                    'step_id': 1,
                    'name': 'Market Opportunity',
                    'description': 'Market opportunity and value proposition',
                    'duration': 300,
                    'actions': ['show_market_analysis', 'explain_tam_sam']
                },
                {
                    'step_id': 2,
                    'name': 'Technology Demonstration',
                    'description': 'Core technology demonstration',
                    'duration': 600,
                    'actions': ['show_quantum_advantage', 'run_comparison', 'show_performance']
                },
                {
                    'step_id': 3,
                    'name': 'Business Model',
                    'description': 'Business model and revenue streams',
                    'duration': 300,
                    'actions': ['show_business_model', 'explain_pricing', 'show_unit_economics']
                },
                {
                    'step_id': 4,
                    'name': 'Traction & Roadmap',
                    'description': 'Current traction and future roadmap',
                    'duration': 300,
                    'actions': ['show_traction', 'explain_roadmap', 'show_milestones']
                }
            ],
            expected_outcomes=[
                'Understanding of market opportunity',
                'Demonstration of quantum advantage',
                'Clear business model understanding',
                'Confidence in team and roadmap'
            ],
            duration_estimate=1500,  # 25 minutes
            governance_limits={
                'max_executions_per_hour': 5,
                'max_cloud_executions': 1,
                'qpu_access': False,
                'max_dataset_size': 100
            },
            metadata={
                'target_audience': 'investors',
                'complexity': 'basic',
                'interactive_elements': False,
                'focus_on_business': True
            }
        )
        
        logger.info(f"Initialized {len(self.sessions)} demo sessions")
    
    def _initialize_execution_histories(self) -> None:
        """Initialize pre-seeded execution histories."""
        
        # Portfolio execution history
        self.execution_histories['portfolio_history'] = [
            {
                'execution_id': str(uuid.uuid4()),
                'dataset_id': 'portfolio_basic',
                'timestamp': time.time() - 86400 * 7,  # 7 days ago
                'status': 'completed',
                'solver': 'dwave',
                'execution_time_ms': 1250,
                'result': {
                    'optimal_return': 0.0825,
                    'optimal_risk': 0.156,
                    'selected_assets': [1, 3, 7, 12, 15],
                    'iterations': 100
                },
                'metadata': {
                    'user_id': 'demo_user_1',
                    'session_id': 'basic_demo',
                    'demo_mode': True
                }
            },
            {
                'execution_id': str(uuid.uuid4()),
                'dataset_id': 'portfolio_intermediate',
                'timestamp': time.time() - 86400 * 3,  # 3 days ago
                'status': 'completed',
                'solver': 'qiskit',
                'execution_time_ms': 3200,
                'result': {
                    'optimal_return': 0.0942,
                    'optimal_risk': 0.178,
                    'selected_assets': [2, 5, 8, 11, 14, 18, 22, 25],
                    'iterations': 500
                },
                'metadata': {
                    'user_id': 'demo_user_2',
                    'session_id': 'advanced_demo',
                    'demo_mode': True
                }
            }
        ]
        
        # Supply chain execution history
        self.execution_histories['supply_chain_history'] = [
            {
                'execution_id': str(uuid.uuid4()),
                'dataset_id': 'supply_chain_basic',
                'timestamp': time.time() - 86400 * 5,  # 5 days ago
                'status': 'completed',
                'solver': 'braket',
                'execution_time_ms': 2100,
                'result': {
                    'optimal_cost': 1250000,
                    'optimal_routes': [[1, 3, 5], [2, 4, 6], [7, 8, 9]],
                    'savings_percentage': 12.5,
                    'iterations': 150
                },
                'metadata': {
                    'user_id': 'demo_user_3',
                    'session_id': 'basic_demo',
                    'demo_mode': True
                }
            }
        ]
        
        logger.info(f"Initialized {len(self.execution_histories)} execution histories")
    
    def get_dataset(self, dataset_id: str) -> Optional[DemoDataset]:
        """Get demo dataset by ID."""
        return self.datasets.get(dataset_id)
    
    def get_session(self, session_id: str) -> Optional[DemoSession]:
        """Get demo session by ID."""
        return self.sessions.get(session_id)
    
    def get_execution_history(self, history_type: str) -> List[Dict[str, Any]]:
        """Get execution history by type."""
        return self.execution_histories.get(history_type, [])
    
    def get_all_datasets(self) -> Dict[str, DemoDataset]:
        """Get all demo datasets."""
        return self.datasets.copy()
    
    def get_all_sessions(self) -> Dict[str, DemoSession]:
        """Get all demo sessions."""
        return self.sessions.copy()
    
    def generate_qubo_matrix(self, dataset_id: str) -> Dict[str, Any]:
        """Generate QUBO matrix for demo dataset."""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {}
        
        # Generate deterministic QUBO matrix based on dataset seed
        seed = dataset.metadata.get('deterministic_seed', 42)
        
        # Simple deterministic QUBO generation
        import random
        random.seed(seed)
        
        size = dataset.size
        qubo = {}
        
        # Generate QUBO matrix
        for i in range(size):
            for j in range(i, size):
                if i == j:
                    # Diagonal terms
                    qubo[(i, j)] = random.uniform(-1, 1)
                else:
                    # Off-diagonal terms
                    qubo[(i, j)] = random.uniform(-0.5, 0.5)
                    qubo[(j, i)] = qubo[(i, j)]
        
        return {
            'qubo': qubo,
            'size': size,
            'dataset_id': dataset_id,
            'seed': seed,
            'metadata': dataset.metadata
        }
    
    def simulate_execution(self, 
                         dataset_id: str, 
                         solver: str = 'dwave',
                         cloud_execution: bool = False) -> Dict[str, Any]:
        """Simulate deterministic execution."""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {'error': f'Dataset {dataset_id} not found'}
        
        # Simulate execution based on expected result
        execution_time = dataset.execution_time_estimate
        
        # Add cloud execution overhead
        if cloud_execution:
            execution_time *= 1.5
        
        # Add solver-specific variations
        solver_overheads = {
            'dwave': 1.0,
            'qiskit': 1.2,
            'braket': 1.3
        }
        
        execution_time *= solver_overheads.get(solver, 1.0)
        
        # Generate deterministic result
        result = dataset.expected_result.copy()
        result['execution_time_ms'] = int(execution_time * 1000)
        result['solver'] = solver
        result['cloud_execution'] = cloud_execution
        result['dataset_id'] = dataset_id
        result['timestamp'] = time.time()
        
        return {
            'execution_id': str(uuid.uuid4()),
            'status': 'completed',
            'result': result,
            'metadata': {
                'demo_mode': True,
                'deterministic': True,
                'simulated': True
            }
        }
    
    def create_demo_environment(self, session_id: str) -> Dict[str, Any]:
        """Create demo environment configuration."""
        session = self.get_session(session_id)
        if not session:
            return {'error': f'Session {session_id} not found'}
        
        return {
            'session_id': session_id,
            'environment': 'demo',
            'governance_limits': session.governance_limits,
            'available_datasets': session.datasets,
            'workflow_steps': session.workflow_steps,
            'expected_outcomes': session.expected_outcomes,
            'metadata': {
                'demo_mode': True,
                'deterministic': True,
                'pre_seeded': True,
                'safe_governance': True
            }
        }
    
    def export_demo_package(self, session_id: str, output_path: str) -> bool:
        """Export demo package for offline demonstration."""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            demo_package = {
                'session': session,
                'datasets': {
                    dataset_id: self.datasets[dataset_id].__dict__
                    for dataset_id in session.datasets
                    if dataset_id in self.datasets
                },
                'execution_histories': {
                    history_type: self.execution_histories[history_type]
                    for history_type in self.execution_histories
                    if any(dataset_id in session.datasets for dataset_id in session.datasets)
                },
                'export_timestamp': time.time(),
                'version': '1.0.0',
                'metadata': {
                    'demo_mode': True,
                    'deterministic': True,
                    'offline_capable': True
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(demo_package, f, indent=2)
            
            logger.info(f"Demo package exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export demo package: {str(e)}")
            return False
    
    def validate_demo_integrity(self) -> Dict[str, Any]:
        """Validate demo mode integrity and determinism."""
        try:
            validation_results = {
                'dataset_integrity': True,
                'session_integrity': True,
                'determinism_validated': True,
                'governance_safety': True,
                'issues': [],
                'warnings': []
            }
            
            # Validate datasets
            for dataset_id, dataset in self.datasets.items():
                if not dataset.expected_result:
                    validation_results['issues'].append(f'Dataset {dataset_id} missing expected result')
                    validation_results['dataset_integrity'] = False
                
                if not dataset.execution_time_estimate:
                    validation_results['warnings'].append(f'Dataset {dataset_id} missing execution time estimate')
            
            # Validate sessions
            for session_id, session in self.sessions.items():
                if not session.workflow_steps:
                    validation_results['issues'].append(f'Session {session_id} missing workflow steps')
                    validation_results['session_integrity'] = False
                
                if not session.governance_limits:
                    validation_results['warnings'].append(f'Session {session_id} missing governance limits')
            
            # Validate determinism
            for dataset_id, dataset in self.datasets.items():
                seed = dataset.metadata.get('deterministic_seed')
                if not seed:
                    validation_results['issues'].append(f'Dataset {dataset_id} missing deterministic seed')
                    validation_results['determinism_validated'] = False
            
            # Validate governance safety
            for session_id, session in self.sessions.items():
                limits = session.governance_limits
                if limits.get('qpu_access', True) and session_id == 'investor_demo':
                    validation_results['issues'].append(f'Investor demo should not have QPU access')
                    validation_results['governance_safety'] = False
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Demo integrity validation failed: {str(e)}")
            return {
                'dataset_integrity': False,
                'session_integrity': False,
                'determinism_validated': False,
                'governance_safety': False,
                'issues': [f'Validation failed: {str(e)}'],
                'warnings': []
            }


# Global demo mode manager instance
_demo_mode_manager: Optional[DemoModeManager] = None


def get_demo_mode_manager() -> DemoModeManager:
    """Get global demo mode manager instance."""
    global _demo_mode_manager
    if _demo_mode_manager is None:
        _demo_mode_manager = DemoModeManager()
    return _demo_mode_manager


if __name__ == "__main__":
    # Test demo mode manager
    demo_manager = get_demo_mode_manager()
    
    # Validate demo integrity
    validation = demo_manager.validate_demo_integrity()
    print("Demo Mode Validation Results:")
    print(f"Dataset Integrity: {validation['dataset_integrity']}")
    print(f"Session Integrity: {validation['session_integrity']}")
    print(f"Determinism Validated: {validation['determinism_validated']}")
    print(f"Governance Safety: {validation['governance_safety']}")
    
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    # Export demo package
    demo_manager.export_demo_package('basic_demo', 'demo_package.json')
    
    print("\nDemo mode manager test completed successfully")
