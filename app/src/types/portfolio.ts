/**
 * TypeScript interfaces for the QUBO Portfolio API.
 * These EXACTLY match the Pydantic schemas in backend/schemas.py.
 * If the solver output shape changes, TypeScript compilation will catch it.
 */

// ── Request Types ────────────────────────────────────────────

export interface QuboParams {
  cardinality: number;        // 5-25, default 15
  risk_tolerance: number;     // 0-2, default 0.5
  max_sector_exposure: number; // 0.1-0.5, default 0.25
  binary_bits: number;        // 5-8, default 7
  solver_mode: 'classical' | 'sb' | 'neal' | 'dwave_hybrid' | 'dwave_qpu' | 'qiskit_qaoa' | 'hybrid' | 'qiskit' | 'ballistic' | 'adiabatic';
  trajectories?: number;
  time_limit_seconds?: number | null;
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
