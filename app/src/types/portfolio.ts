/**
 * TypeScript interfaces for the QUBO Portfolio API.
 * These EXACTLY match the Pydantic schemas in backend/schemas.py.
 * If the solver output shape changes, TypeScript compilation will catch it.
 */

// ── Request Types ────────────────────────────────────────────

export type SolverId =
  | 'classical'
  | 'neal'
  | 'AWS_BRAKET_LOCAL'
  | 'qiskit_qaoa'
  | 'AWS_BRAKET_SV1'
  | 'AWS_BRAKET_TN1'
  | 'AWS_BRAKET_DM1';

export type ExecutionMode =
  | 'LOCAL_ONLY'
  | 'CLOUD_ONLY'
  | 'QUANTUM_ONLY'
  | 'CLASSICAL_ONLY'
  | 'FULL_STACK';

export type SolverStatus =
  | 'enabled'
  | 'disabled'
  | 'unavailable'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'isolated_failure';

export type BenchmarkStatus =
  | 'SUCCESS'
  | 'PARTIAL_SUCCESS'
  | 'FAILED';

export type IsolationStatus =
  | 'SUCCESS'
  | 'VALID'
  | 'COMPARABLE'
  | 'DEGRADED'
  | 'FAILED'
  | 'SKIPPED'
  | 'ISOLATED_FAILURE'
  | 'NON_COMPARABLE';

export interface QuboParams {
  cardinality: number;
  risk_tolerance: number;
  max_sector_exposure: number;
  binary_bits: number;
  requested_solver: 'auto' | 'classical' | 'gpu' | 'dwave' | 'qiskit' | 'sb' | 'neal' | 'dwave_hybrid' | 'dwave_qpu' | 'qiskit_qaoa' | 'hybrid' | string;
  trajectories?: number;
  time_limit_seconds?: number | null;
  benchmark_mode?: string;
  num_assets?: number;
  selected_solvers?: SolverId[];
  execution_mode?: ExecutionMode;
}

// ── Portfolio Response Types ─────────────────────────────────

export interface HoldingInfo {
  weight: number;
  sector: string;
}

export interface Holding {
  ticker: string;
  weight: number;
  sector: string;
}

export interface RiskMetrics {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  variance: number;
}

export interface SolverMetadata {
  qubo_variables: number;
  solve_time_ms: number;
  actual_solver_used?: string | null;
  attempt: number;
  penalty_weights: Record<string, string | number | boolean | null>;
}

export interface SectorViolation {
  sector: string;
  exposure: number;
  limit: number;
  excess: number;
}

export interface ConstraintVerification {
  budget_satisfaction: number;
  cardinality: number;
  cardinality_target: number;
  cardinality_ok: boolean;
  sector_violations: SectorViolation[];
  sector_ok: boolean;
  all_satisfied: boolean;
}

export interface PortfolioParameters {
  k_bits: number;
  cardinality: number;
  max_sector_exposure: number;
  risk_tolerance: number;
}

export interface PortfolioResponse {
  portfolio: Record<string, HoldingInfo>;
  metrics: RiskMetrics;
  sector_allocation: Record<string, number>;
  parameters: PortfolioParameters;
  solver_metadata?: SolverMetadata;
  constraint_verification?: ConstraintVerification;
}

export interface PortfolioHoldingsList {
  holdings: Holding[];
  total_assets: number;
}

// ── GPU Telemetry Types ──────────────────────────────────────

export interface GPUMetrics {
  utilization: number;       // % from nvidia-smi
  vram_used_mb: number;      // MB allocated
  vram_total_mb: number;     // 8192 for RTX 4060
  temperature_c: number;     // degrees Celsius
  power_draw_w: number;      // Watts
  cuda_alloc_mb: number;     // PyTorch CUDA allocation
  gpu_name: string;
  timestamp: string;
}

// ── Optimization Task Types ──────────────────────────────────

export interface OptimizationTaskResponse {
  task_id: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  progress: number;          // 0-100
  step: string;              // Current step description
  result?: PortfolioResponse;
  error?: string;
}

// ── Health Check ─────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  gpu_available: boolean;
  gpu_name: string;
  cuda_version: string;
  output_dir_exists: boolean;
  alpha_data_exists: boolean;
  optimal_weights_exists: boolean;
  timestamp: string;
}

// ── Config Defaults ──────────────────────────────────────────

export interface ConfigDefaults {
  cardinality: number;
  binary_bits: number;
  max_sector_exposure: number;
  risk_tolerance: number;
  solver_mode: string;
  trajectories: number;
}

// ── Benchmarking Types ───────────────────────────────────────

export interface BenchmarkResult {
  rank?: number;
  solver: string;
  actual_solver?: string;
  status: 'success' | 'fallback' | 'skipped' | 'error' | 'SCIENTIFIC_VIOLATION';
  fallback_reason?: string | null;
  reason?: string;
  traceback?: string;
  energy: number | null;
  raw_bqm_energy?: number | null;
  portfolio_objective_energy?: number | null;
  raw_energy?: number | null;
  normalized_energy?: number | null | 'CALIBRATION_INCOMPLETE';
  comparable_energy?: number | null;
  scientific_comparability?: boolean;
  solve_time_ms: number;
  feasible: boolean;
  provider?: string;
  backend?: string;
  metrics?: RiskMetrics;
  selected_assets?: number;
  
  // Cloud Telemetry Fields
  execution_origin?: 'local' | 'cloud' | 'fallback';
  execution_mode?: string;
  execution_provenance?: {
    requested_solver: string;
    actual_solver: string;
    execution_origin: string;
    repair_used: boolean;
    fallback_triggered: boolean;
    benchmark_mode?: string;
  };
  task_arn?: string;
  device_arn?: string;
  fallback_triggered?: boolean;
  fallback_chain?: string[];
  native_execution?: boolean;
  is_energy_comparable?: boolean;
  
  // Isolation Fields (Phase 3/5)
  isolation_status?: IsolationStatus;
  
  // Scientific Gate (Phase 7)
  scientific_gate?: {
    strict_ratio: number;
    raw_ratio: number;
    entropy: number;
    inversion_detected: boolean;
    manifold_status: string;
    comparability_status: string;
  };
  
  benchmark_fingerprint?: {
    semantic_version: string;
    portfolio_hash: string;
    covariance_hash: string;
    constraint_hash: string;
    solver_config_hash: string;
    normalization_version: string;
  };
  operational_certification?: {
    status: 'CERTIFIED' | 'DEGRADED' | 'FAILED';
    latency_ok: boolean;
    reliability_ok: boolean;
    stability_ok: boolean;
    reason?: string;
  };
  scientific_certification?: {
    status: 'CERTIFIED' | 'RESEARCH_GRADE' | 'UX_GRADE' | 'NON_COMPARABLE';
    feasibility_ok: boolean;
    approximation_ok: boolean;
    decode_integrity_ok: boolean;
    comparability_ok: boolean;
    reason?: string;
  };

  // Optimization Quality Fields
  optimization_status?: string;
  comparison_status?: string;
  execution_status?: string;

  // Advanced Quality Metrics
  execution_confidence?: number;
  approximation_ratio?: number | null;
  constraint_satisfaction_score?: number;
  allocation_sparsity?: number;
  cardinality_deviation?: number;
}

export interface BenchmarkSummary {
  total_solvers_attempted: number;
  successful: number;
  fallbacks: number;
  skipped: number;
  errors: number;
  scientific_violations?: number;
  feasible_solutions: number;
  scientifically_comparable: number;
  best_solver: string | null;
  best_energy: number | null;
  total_benchmark_time_ms: number;
  benchmark_status?: BenchmarkStatus;
  execution_mode?: ExecutionMode;
  selected_solvers?: SolverId[];
  problem_size: {
    assets: number;
    cardinality: number;
    binary_bits: number;
  };
  isolation_audit?: Array<{
    solver: string;
    started: number;
    completed: number | null;
    failed: boolean;
    isolated: boolean;
    propagated: boolean;
  }>;
}

export interface BenchmarkResponse {
  results: BenchmarkResult[];
  ranking: { rank: number; solver: string; energy: number }[];
  summary: BenchmarkSummary;
}
