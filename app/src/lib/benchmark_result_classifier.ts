import type { BenchmarkResult, IsolationStatus } from '@/types/portfolio';

export interface ClassifiedResult {
  isolationStatus: IsolationStatus | string;
  badgeBg: string;
  badgeText: string;
  badgeLabel: string;
  badgeBorder: string;
}

export interface KPIs {
  attempted: number;
  feasibleCount: number;
  bestEnergy: number | null;
  totalTime: number;
}

export interface ChartDataPoint {
  name: string;
  energy: number;
  time: number;
  isFeasible: boolean;
  classification: string;
}

export function classifyResult(res: BenchmarkResult): ClassifiedResult {
  const status = res.status;
  const feasible = res.feasible;
  const isolation = res.isolation_status;

  if (status === 'skipped') {
    return {
      isolationStatus: 'SKIPPED',
      badgeBg: 'bg-slate-500/10',
      badgeText: 'text-slate-400',
      badgeLabel: 'SKIPPED',
      badgeBorder: 'border-slate-500/20',
    };
  }

  if (status === 'error' || status === 'SCIENTIFIC_VIOLATION') {
    return {
      isolationStatus: 'ISOLATED_FAILURE',
      badgeBg: 'bg-red-500/10',
      badgeText: 'text-red-400',
      badgeLabel: 'ERROR',
      badgeBorder: 'border-red-500/20',
    };
  }

  if (status === 'fallback') {
    return {
      isolationStatus: 'DEGRADED',
      badgeBg: 'bg-amber-500/10',
      badgeText: 'text-amber-400',
      badgeLabel: 'FALLBACK',
      badgeBorder: 'border-amber-500/20',
    };
  }

  if (!feasible) {
    return {
      isolationStatus: 'NON_COMPARABLE',
      badgeBg: 'bg-yellow-500/10',
      badgeText: 'text-yellow-300',
      badgeLabel: 'INFEASIBLE',
      badgeBorder: 'border-yellow-500/20',
    };
  }

  if (isolation === 'COMPARABLE' || res.scientific_comparability === true) {
    return {
      isolationStatus: 'COMPARABLE',
      badgeBg: 'bg-emerald-500/10',
      badgeText: 'text-emerald-400',
      badgeLabel: 'COMPARABLE',
      badgeBorder: 'border-emerald-500/20',
    };
  }

  if (isolation === 'VALID') {
    return {
      isolationStatus: 'VALID',
      badgeBg: 'bg-blue-500/10',
      badgeText: 'text-blue-400',
      badgeLabel: 'VALID',
      badgeBorder: 'border-blue-500/20',
    };
  }

  return {
    isolationStatus: isolation || 'VALID',
    badgeBg: 'bg-blue-500/10',
    badgeText: 'text-blue-400',
    badgeLabel: 'SUCCESS',
    badgeBorder: 'border-blue-500/20',
  };
}

export function computeKPIs(results: BenchmarkResult[]): KPIs {
  const attempted = results.length;
  const feasibleCount = results.filter(r => r.feasible && r.status === 'success').length;
  const feasibleEnergies = results
    .filter(r => r.feasible && r.energy !== null)
    .map(r => r.energy as number);
  const bestEnergy = feasibleEnergies.length > 0 ? Math.min(...feasibleEnergies) : null;
  const totalTime = results.reduce((sum, r) => sum + r.solve_time_ms, 0);

  return { attempted, feasibleCount, bestEnergy, totalTime };
}

export function buildChartData(results: BenchmarkResult[]): ChartDataPoint[] {
  return results
    .filter(r => r.energy !== null)
    .map(r => {
      const c = classifyResult(r);
      return {
        name: r.solver,
        energy: r.energy as number,
        time: r.solve_time_ms,
        isFeasible: r.feasible,
        classification: c.badgeLabel,
      };
    });
}
