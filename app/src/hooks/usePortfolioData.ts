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
} from '../types/portfolio';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// ── Fetch Helpers ────────────────────────────────────────────

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('qubo_token');
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (!res.ok) {
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
