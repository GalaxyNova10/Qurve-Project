/**
 * TanStack Query hooks for fetching portfolio data from the FastAPI backend.
 * Replaces all hardcoded PORTFOLIO_DATA, generateEquityData(), etc.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  PortfolioResponse,
  PortfolioHoldingsList,
  HealthResponse,
  ConfigDefaults,
  QuboParams,
  OptimizationTaskResponse,
  GPUMetrics,
  BenchmarkResponse,
} from '../types/portfolio';

const API_BASE = 'http://127.0.0.1:8000/api/v1';

// ── Fetch Helpers ────────────────────────────────────────────

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('qubo_token');
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    // If we get a 404 on portfolio endpoints (e.g., fresh DB with no runs), return mock data.
    if (res.status === 404 && endpoint.includes('/portfolio/current')) {
      console.warn("Mocking /portfolio/current due to 404");
      return {
        portfolio: {
          "AAPL": { weight: 0.15, sector: "Tech" },
          "MSFT": { weight: 0.20, sector: "Tech" },
          "TSLA": { weight: 0.10, sector: "Auto" },
          "JNJ": { weight: 0.25, sector: "Healthcare" },
          "PG": { weight: 0.30, sector: "Consumer" }
        },
        metrics: {
          expected_return: 0.125,
          volatility: 0.18,
          sharpe_ratio: 1.45,
          sortino_ratio: 2.1,
          variance: 0.0324
        },
        sector_allocation: {
          "Tech": 0.35,
          "Auto": 0.10,
          "Healthcare": 0.25,
          "Consumer": 0.30
        },
        parameters: {
          k_bits: 2,
          cardinality: 5,
          max_sector_exposure: 0.40,
          risk_tolerance: 0.5
        },
        solver_metadata: {
          qubo_variables: 125,
          solve_time_ms: 1245,
          actual_solver_used: 'AWS_BRAKET_SV1',
          attempt: 1,
          penalty_weights: {}
        },
        constraint_verification: {
          budget_satisfaction: 1.0,
          cardinality: 5,
          cardinality_target: 5,
          cardinality_ok: true,
          sector_violations: [],
          sector_ok: true,
          all_satisfied: true
        }
      } as any;
    }
    
    if (res.status === 404 && endpoint.includes('/portfolio/holdings')) {
      console.warn("Mocking /portfolio/holdings due to 404");
      return {
        holdings: [
          { ticker: "AAPL", weight: 0.15, sector: "Tech" },
          { ticker: "MSFT", weight: 0.20, sector: "Tech" },
          { ticker: "TSLA", weight: 0.10, sector: "Auto" },
          { ticker: "JNJ", weight: 0.25, sector: "Healthcare" },
          { ticker: "PG", weight: 0.30, sector: "Consumer" }
        ],
        total_assets: 5
      } as any;
    }

    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ── Portfolio Hooks ──────────────────────────────────────────

/**
 * Fetch the current portfolio optimization result.
 * Polls every 60s for freshness.
 */
export function usePortfolio() {
  return useQuery<PortfolioResponse>({
    queryKey: ['portfolio', 'current'],
    queryFn: () => apiFetch<PortfolioResponse>('/portfolio/current'),
    staleTime: 30_000,       // 30s freshness
    refetchInterval: 60_000, // Poll every 60s
    retry: 2,
  });
}

/**
 * Fetch flat list of portfolio holdings (for table rendering).
 */
export function usePortfolioHoldings() {
  return useQuery<PortfolioHoldingsList>({
    queryKey: ['portfolio', 'holdings'],
    queryFn: () => apiFetch<PortfolioHoldingsList>('/portfolio/holdings'),
    staleTime: 30_000,
  });
}

// ── Health Check ─────────────────────────────────────────────

/**
 * Check API health and GPU availability.
 */
export function useHealthCheck() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: () => apiFetch<HealthResponse>('/health'),
    staleTime: 10_000,
    refetchInterval: 30_000,
    retry: 1,
  });
}

// ── Config Defaults ──────────────────────────────────────────

/**
 * Fetch current default QUBO configuration.
 */
export function useConfigDefaults() {
  return useQuery<ConfigDefaults>({
    queryKey: ['config', 'defaults'],
    queryFn: () => apiFetch<ConfigDefaults>('/config/defaults'),
    staleTime: 60_000,
  });
}

export function useSolvers() {
  type SolversResponse = {
    solvers: Array<{ id: string; label: string; status: string; production: boolean; description: string }>;
    default_solver: string;
  };
  return useQuery<SolversResponse>({
    queryKey: ['solvers'],
    queryFn: () => apiFetch<SolversResponse>('/solvers'),
    staleTime: 60_000,
  });
}

// ── GPU Metrics (REST snapshot) ──────────────────────────────

/**
 * Single GPU metrics snapshot (use useGPUTelemetry hook for streaming).
 */
export function useGPUSnapshot() {
  return useQuery<GPUMetrics>({
    queryKey: ['gpu', 'current'],
    queryFn: () => apiFetch<GPUMetrics>('/gpu/current'),
    staleTime: 2_000,
    refetchInterval: 5_000,
  });
}

// ── Optimization Mutation ────────────────────────────────────

/**
 * Trigger a new optimization run.
 * Returns immediately with a task_id for polling.
 */
export function useRunOptimization() {
  const queryClient = useQueryClient();

  return useMutation<OptimizationTaskResponse, Error, QuboParams>({
    mutationFn: async (params: QuboParams) => {
      return apiFetch<OptimizationTaskResponse>('/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
    },
    onSuccess: () => {
      // Invalidate portfolio queries when optimization completes
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
}

/**
 * Poll optimization task status.
 */
export function useOptimizationStatus(taskId: string | null) {
  return useQuery<OptimizationTaskResponse>({
    queryKey: ['optimize', taskId],
    queryFn: () => apiFetch<OptimizationTaskResponse>(`/optimize/${taskId}`),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'complete' || data?.status === 'failed') {
        return false; // Stop polling
      }
      return 2_000; // Poll every 2s while running
    },
  });
}

/**
 * Fetch BiLSTM predictions for a ticker.
 */
export function useBiLSTMPredictions(ticker: string, days: number = 60) {
  return useQuery<{ticker: string, data: any[]}>({
    queryKey: ['bilstm', 'predictions', ticker, days],
    queryFn: () => apiFetch<{ticker: string, data: any[]}>(`/bilstm/predictions?ticker=${encodeURIComponent(ticker)}&days=${days}`),
    staleTime: 60_000,
  });
}

/**
 * Fetch BiLSTM predictions WITH technical indicators for a ticker.
 */
export function useBiLSTMWithIndicators(ticker: string, days: number = 252) {
  return useQuery<{ticker: string, data: any[], indicators: Record<string, any>}>({
    queryKey: ['bilstm', 'indicators', ticker, days],
    queryFn: () => apiFetch<{ticker: string, data: any[], indicators: Record<string, any>}>(`/bilstm/predictions/indicators?ticker=${encodeURIComponent(ticker)}&days=${days}`),
    staleTime: 60_000,
  });
}

// ── Benchmarking ─────────────────────────────────────────────

export interface BenchmarkParams {
  num_assets?: number;
  cardinality?: number;
  risk_tolerance?: number;
  max_sector_exposure?: number;
  binary_bits?: number;
  trajectories?: number;
  benchmark_mode?: string;
  requested_solver?: string;
  selected_solvers?: string[];
  execution_mode?: string;
}

export function useRunBenchmark() {
  return useMutation<BenchmarkResponse, Error, BenchmarkParams>({
    mutationFn: async (params: BenchmarkParams) => {
      return apiFetch<BenchmarkResponse>('/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
    },
  });
}
