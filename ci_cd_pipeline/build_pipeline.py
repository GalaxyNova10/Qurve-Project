#!/usr/bin/env python3
"""
QURVE AI - CI/CD Build Pipeline
Automated regression validation, deployment validation, and release builds.

Features:
✅ Regression validation pipeline
✅ Replay determinism validation
✅ Governance validation
✅ Deployment validation
✅ Rollback validation
✅ Container integrity validation
✅ Automated release builds
"""

import os
import sys
import subprocess
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build status classifications."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationType(Enum):
    """Validation type classifications."""
    REGRESSION = "regression"
    REPLAY_DETERMINISM = "replay_determinism"
    GOVERNANCE = "governance"
    DEPLOYMENT = "deployment"
    ROLLBACK = "rollback"
    CONTAINER_INTEGRITY = "container_integrity"
    SECURITY = "security"


@dataclass
class ValidationResult:
    """Validation result definition."""
    validation_type: ValidationType
    status: BuildStatus
    message: str
    timestamp: float
    duration_seconds: float
    details: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class BuildStep:
    """Build step definition."""
    step_id: str
    name: str
    description: str
    command: str
    timeout_seconds: int
    required: bool = True
    artifacts: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class BuildPipeline:
    """Build pipeline definition."""
    pipeline_id: str
    name: str
    description: str
    steps: List[BuildStep]
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CICDPipeline:
    """
    Production-grade CI/CD pipeline.
    
    Features:
    - Regression validation pipeline
    - Replay determinism validation
    - Governance validation
    - Deployment validation
    - Rollback validation
    - Container integrity validation
    - Automated release builds
    """
    
    def __init__(self):
        self.workspace_root = Path.cwd()
        self.build_dir = self.workspace_root / "build"
        self.reports_dir = self.workspace_root / "reports"
        self.artifacts_dir = self.workspace_root / "artifacts"
        
        # Create directories
        self.build_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Pipeline state
        self.current_pipeline: Optional[BuildPipeline] = None
        self.build_results: Dict[str, ValidationResult] = {}
        self.start_time = time.time()
        
        # Define build pipelines
        self.pipelines = self._define_pipelines()
        
        logger.info("CI/CD pipeline initialized")
    
    def _define_pipelines(self) -> Dict[str, BuildPipeline]:
        """Define all build pipelines."""
        return {
            'main': BuildPipeline(
                pipeline_id='main',
                name='Main Build Pipeline',
                description='Primary build pipeline with all validations',
                steps=[
                    BuildStep(
                        step_id='setup',
                        name='Setup Build Environment',
                        description='Initialize build environment and dependencies',
                        command='python scripts/setup_build_env.py',
                        timeout_seconds=300,
                        artifacts=['setup.log']
                    ),
                    BuildStep(
                        step_id='lint',
                        name='Code Quality Checks',
                        description='Run linting and code quality checks',
                        command='python scripts/run_linting.py',
                        timeout_seconds=600,
                        artifacts=['lint-report.json', 'lint.log']
                    ),
                    BuildStep(
                        step_id='unit_tests',
                        name='Unit Tests',
                        description='Run unit test suite',
                        command='python scripts/run_unit_tests.py',
                        timeout_seconds=1200,
                        artifacts=['unit-test-results.xml', 'unit-test-report.json'],
                        dependencies=['lint']
                    ),
                    BuildStep(
                        step_id='integration_tests',
                        name='Integration Tests',
                        description='Run integration test suite',
                        command='python scripts/run_integration_tests.py',
                        timeout_seconds=1800,
                        artifacts=['integration-test-results.xml', 'integration-test-report.json'],
                        dependencies=['unit_tests']
                    ),
                    BuildStep(
                        step_id='regression_validation',
                        name='Regression Validation',
                        description='Validate against regression test suite',
                        command='python scripts/run_regression_validation.py',
                        timeout_seconds=2400,
                        artifacts=['regression-report.json', 'regression-results.xml'],
                        dependencies=['integration_tests']
                    ),
                    BuildStep(
                        step_id='replay_determinism',
                        name='Replay Determinism Validation',
                        description='Validate replay system determinism',
                        command='python scripts/run_replay_validation.py',
                        timeout_seconds=1800,
                        artifacts=['replay-determinism-report.json'],
                        dependencies=['regression_validation']
                    ),
                    BuildStep(
                        step_id='governance_validation',
                        name='Governance Validation',
                        description='Validate governance system integrity',
                        command='python scripts/run_governance_validation.py',
                        timeout_seconds=1200,
                        artifacts=['governance-validation-report.json'],
                        dependencies=['replay_determinism']
                    ),
                    BuildStep(
                        step_id='security_validation',
                        name='Security Validation',
                        description='Run security vulnerability scans',
                        command='python scripts/run_security_validation.py',
                        timeout_seconds=1800,
                        artifacts=['security-report.json', 'vulnerability-scan.json'],
                        dependencies=['governance_validation']
                    ),
                    BuildStep(
                        step_id='build_containers',
                        name='Build Containers',
                        description='Build Docker containers',
                        command='docker-compose -f docker-compose.prod.yml build',
                        timeout_seconds=2400,
                        artifacts=['container-build.log'],
                        dependencies=['security_validation']
                    ),
                    BuildStep(
                        step_id='container_integrity',
                        name='Container Integrity Validation',
                        description='Validate container integrity and security',
                        command='python scripts/validate_container_integrity.py',
                        timeout_seconds=600,
                        artifacts=['container-integrity-report.json'],
                        dependencies=['build_containers']
                    ),
                    BuildStep(
                        step_id='deployment_validation',
                        name='Deployment Validation',
                        description='Validate deployment configuration',
                        command='python scripts/validate_deployment.py',
                        timeout_seconds=1200,
                        artifacts=['deployment-validation-report.json'],
                        dependencies=['container_integrity']
                    ),
                    BuildStep(
                        step_id='rollback_validation',
                        name='Rollback Validation',
                        description='Validate rollback procedures',
                        command='python scripts/validate_rollback.py',
                        timeout_seconds=900,
                        artifacts=['rollback-validation-report.json'],
                        dependencies=['deployment_validation']
                    ),
                    BuildStep(
                        step_id='create_release',
                        name='Create Release',
                        description='Create release package and artifacts',
                        command='python scripts/create_release.py',
                        timeout_seconds=600,
                        artifacts=['release-package.tar.gz', 'release-notes.md'],
                        dependencies=['rollback_validation']
                    )
                ]
            ),
            'quick': BuildPipeline(
                pipeline_id='quick',
                name='Quick Build Pipeline',
                description='Fast build pipeline for quick validation',
                steps=[
                    BuildStep(
                        step_id='quick_setup',
                        name='Quick Setup',
                        description='Quick environment setup',
                        command='python scripts/quick_setup.py',
                        timeout_seconds=120,
                        artifacts=['quick-setup.log']
                    ),
                    BuildStep(
                        step_id='quick_tests',
                        name='Quick Tests',
                        description='Run essential tests only',
                        command='python scripts/quick_tests.py',
                        timeout_seconds=600,
                        artifacts=['quick-test-results.json'],
                        dependencies=['quick_setup']
                    ),
                    BuildStep(
                        step_id='quick_build',
                        name='Quick Build',
                        description='Quick container build',
                        command='docker-compose -f docker-compose.yml build',
                        timeout_seconds=900,
                        artifacts=['quick-build.log'],
                        dependencies=['quick_tests']
                    )
                ]
            ),
            'security_only': BuildPipeline(
                pipeline_id='security_only',
                name='Security Validation Pipeline',
                description='Security-focused validation pipeline',
                steps=[
                    BuildStep(
                        step_id='security_setup',
                        name='Security Setup',
                        description='Setup security validation environment',
                        command='python scripts/security_setup.py',
                        timeout_seconds=180,
                        artifacts=['security-setup.log']
                    ),
                    BuildStep(
                        step_id='vulnerability_scan',
                        name='Vulnerability Scan',
                        description='Run comprehensive vulnerability scan',
                        command='python scripts/run_vulnerability_scan.py',
                        timeout_seconds=2400,
                        artifacts=['vulnerability-report.json', 'security-scan.json'],
                        dependencies=['security_setup']
                    ),
                    BuildStep(
                        step_id='security_tests',
                        name='Security Tests',
                        description='Run security test suite',
                        command='python scripts/run_security_tests.py',
                        timeout_seconds=1200,
                        artifacts=['security-test-results.json'],
                        dependencies=['vulnerability_scan']
                    )
                ]
            )
        }
    
    async def run_pipeline(self, pipeline_name: str = 'main') -> Dict[str, Any]:
        """Run specified build pipeline."""
        try:
            logger.info(f"Starting CI/CD pipeline: {pipeline_name}")
            
            # Get pipeline definition
            pipeline = self.pipelines.get(pipeline_name)
            if not pipeline:
                raise ValueError(f"Unknown pipeline: {pipeline_name}")
            
            self.current_pipeline = pipeline
            
            # Initialize build results
            self.build_results = {}
            
            # Run pipeline steps
            for step in pipeline.steps:
                result = await self._run_step(step)
                self.build_results[step.step_id] = result
                
                # Check if step failed and is required
                if result.status == BuildStatus.FAILED and step.required:
                    logger.error(f"Required step {step.step_id} failed, stopping pipeline")
                    break
            
            # Generate build report
            build_report = self._generate_build_report(pipeline)
            
            # Save build report
            report_path = self.reports_dir / f"build-report-{pipeline_name}-{int(time.time())}.json"
            with open(report_path, 'w') as f:
                json.dump(build_report, f, indent=2)
            
            logger.info(f"Pipeline {pipeline_name} completed")
            return build_report
            
        except Exception as e:
            logger.error(f"Pipeline {pipeline_name} failed: {str(e)}")
            raise
    
    async def _run_step(self, step: BuildStep) -> ValidationResult:
        """Run individual build step."""
        try:
            logger.info(f"Running step: {step.step_id} - {step.name}")
            
            start_time = time.time()
            
            # Check dependencies
            for dependency in step.dependencies:
                if dependency in self.build_results:
                    dep_result = self.build_results[dependency]
                    if dep_result.status == BuildStatus.FAILED:
                        return ValidationResult(
                            validation_type=ValidationType.REGRESSION,
                            status=BuildStatus.FAILED,
                            message=f"Dependency {dependency} failed",
                            timestamp=start_time,
                            duration_seconds=0.0,
                            details={'failed_dependency': dependency}
                        )
            
            # Run step command
            process = await asyncio.create_subprocess_shell(
                step.command,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=step.timeout_seconds
                )
                return_code = process.returncode
            except asyncio.TimeoutError:
                process.kill()
                return_code = -1
                stdout = ""
                stderr = "Step timed out"
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Process step result
            if return_code == 0:
                status = BuildStatus.SUCCESS
                message = f"Step {step.step_id} completed successfully"
            else:
                status = BuildStatus.FAILED
                message = f"Step {step.step_id} failed with return code {return_code}"
            
            # Collect artifacts
            artifacts = []
            for artifact in step.artifacts:
                artifact_path = self.build_dir / artifact
                if artifact_path.exists():
                    artifacts.append(str(artifact_path))
            
            result = ValidationResult(
                validation_type=ValidationType.REGRESSION,
                status=status,
                message=message,
                timestamp=start_time,
                duration_seconds=duration,
                details={
                    'return_code': return_code,
                    'stdout': stdout,
                    'stderr': stderr
                },
                artifacts=artifacts
            )
            
            logger.info(f"Step {step.step_id} completed: {status.value} in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Step {step.step_id} failed with exception: {str(e)}")
            return ValidationResult(
                validation_type=ValidationType.REGRESSION,
                status=BuildStatus.FAILED,
                message=f"Step {step.step_id} failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0,
                details={'exception': str(e)}
            )
    
    def _generate_build_report(self, pipeline: BuildPipeline) -> Dict[str, Any]:
        """Generate comprehensive build report."""
        try:
            # Calculate statistics
            total_steps = len(pipeline.steps)
            successful_steps = sum(1 for result in self.build_results.values() if result.status == BuildStatus.SUCCESS)
            failed_steps = sum(1 for result in self.build_results.values() if result.status == BuildStatus.FAILED)
            total_duration = sum(result.duration_seconds for result in self.build_results.values())
            
            # Get all artifacts
            all_artifacts = []
            for result in self.build_results.values():
                all_artifacts.extend(result.artifacts)
            
            # Determine overall status
            if failed_steps == 0:
                overall_status = BuildStatus.SUCCESS
            elif failed_steps > 0:
                overall_status = BuildStatus.FAILED
            else:
                overall_status = BuildStatus.PENDING
            
            return {
                'pipeline': {
                    'pipeline_id': pipeline.pipeline_id,
                    'name': pipeline.name,
                    'description': pipeline.description,
                    'total_steps': total_steps
                },
                'results': {
                    'overall_status': overall_status.value,
                    'successful_steps': successful_steps,
                    'failed_steps': failed_steps,
                    'success_rate': (successful_steps / total_steps * 100) if total_steps > 0 else 0,
                    'total_duration_seconds': total_duration,
                    'start_time': self.start_time,
                    'end_time': time.time(),
                    'step_results': {
                        step_id: {
                            'status': result.status.value,
                            'message': result.message,
                            'duration_seconds': result.duration_seconds,
                            'timestamp': result.timestamp,
                            'artifacts': result.artifacts,
                            'details': result.details
                        }
                        for step_id, result in self.build_results.items()
                    }
                },
                'artifacts': all_artifacts,
                'metadata': {
                    'workspace_root': str(self.workspace_root),
                    'build_dir': str(self.build_dir),
                    'reports_dir': str(self.reports_dir),
                    'artifacts_dir': str(self.artifacts_dir),
                    'pipeline_environment': pipeline.environment
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate build report: {str(e)}")
            return {
                'error': str(e),
                'pipeline': {
                    'pipeline_id': pipeline.pipeline_id,
                    'name': pipeline.name
                }
            }
    
    def get_pipeline_status(self, pipeline_name: str = 'main') -> Dict[str, Any]:
        """Get current pipeline status."""
        try:
            if pipeline_name not in self.pipelines:
                return {'error': f'Unknown pipeline: {pipeline_name}'}
            
            pipeline = self.pipelines[pipeline_name]
            
            return {
                'pipeline': {
                    'pipeline_id': pipeline.pipeline_id,
                    'name': pipeline.name,
                    'description': pipeline.description,
                    'total_steps': len(pipeline.steps)
                },
                'status': {
                    'current_step': len(self.build_results),
                    'total_steps': len(pipeline.steps),
                    'is_running': self.current_pipeline == pipeline,
                    'start_time': self.start_time,
                    'elapsed_time': time.time() - self.start_time
                },
                'results': {
                    step_id: {
                        'status': result.status.value,
                        'message': result.message,
                        'duration_seconds': result.duration_seconds,
                        'timestamp': result.timestamp,
                        'artifacts': result.artifacts
                    }
                    for step_id, result in self.build_results.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {str(e)}")
            return {'error': str(e)}


# Global CI/CD pipeline instance
_cicd_pipeline: Optional[CICDPipeline] = None


def get_cicd_pipeline() -> CICDPipeline:
    """Get global CI/CD pipeline instance."""
    global _cicd_pipeline
    if _cicd_pipeline is None:
        _cicd_pipeline = CICDPipeline()
    return _cicd_pipeline


if __name__ == "__main__":
    import asyncio
    
    # Get pipeline name from command line arguments
    pipeline_name = sys.argv[1] if len(sys.argv) > 1 else 'main'
    
    # Run pipeline
    pipeline = get_cicd_pipeline()
    result = asyncio.run(pipeline.run_pipeline(pipeline_name))
    
    # Print results
    print(f"Pipeline: {result['pipeline']['name']}")
    print(f"Status: {result['results']['overall_status']}")
    print(f"Success Rate: {result['results']['success_rate']:.1f}%")
    print(f"Duration: {result['results']['total_duration_seconds']:.2f}s")
    
    if result['results']['overall_status'] == 'failed':
        print("Failed steps:")
        for step_id, step_result in result['results']['step_results'].items():
            if step_result['status'] == 'failed':
                print(f"  - {step_id}: {step_result['message']}")
    
    print(f"Report saved: reports/build-report-{pipeline_name}-{int(time.time())}.json")
