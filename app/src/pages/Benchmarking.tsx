import { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Play, Activity, Cpu, Shield, Clock, BarChart3, Loader2, Settings, Check, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useRunBenchmark } from '@/hooks/usePortfolioData';
import { BenchmarkResponse, SolverId, ExecutionMode } from '@/types/portfolio';
import { toast } from 'sonner';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { classifyResult, computeKPIs, buildChartData } from '@/lib/benchmark_result_classifier';

const SOLVER_CATALOG: Array<{ id: SolverId; label: string; category: string; defaultEnabled: boolean }> = [
  { id: 'classical', label: 'Classical', category: 'LOCAL', defaultEnabled: true },
  { id: 'neal', label: 'Neal (SA)', category: 'LOCAL', defaultEnabled: true },
  { id: 'AWS_BRAKET_LOCAL', label: 'Braket Local', category: 'LOCAL', defaultEnabled: true },
  { id: 'qiskit_qaoa', label: 'Qiskit QAOA', category: 'CLOUD', defaultEnabled: false },
  { id: 'AWS_BRAKET_SV1', label: 'Braket SV1', category: 'CLOUD', defaultEnabled: false },
  { id: 'AWS_BRAKET_TN1', label: 'Braket TN1', category: 'CLOUD', defaultEnabled: false },
];

const EXECUTION_MODES: Array<{ id: ExecutionMode; label: string; description: string }> = [
  { id: 'LOCAL_ONLY', label: 'LOCAL ONLY', description: 'classical + neal + Braket Local' },
  { id: 'CLOUD_ONLY', label: 'CLOUD ONLY', description: 'SV1 + TN1' },
  { id: 'QUANTUM_ONLY', label: 'QUANTUM ONLY', description: 'Qiskit + Braket solvers' },
  { id: 'CLASSICAL_ONLY', label: 'CLASSICAL ONLY', description: 'classical + neal' },
  { id: 'FULL_STACK', label: 'FULL STACK', description: 'All solvers' },
];

export default function Benchmarking() {
  const runBenchmark = useRunBenchmark();
  
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);
  const [sessionId, setSessionId] = useState('');
  const sessionIdRef = useRef('');
  
  const [numAssets, setNumAssets] = useState([50]);
  const [binaryBits, setBinaryBits] = useState([7]);
  const [riskTolerance, setRiskTolerance] = useState('0.5');
  const [maxSectorExposure, setMaxSectorExposure] = useState('0.25');
  const [benchmarkMode, setBenchmarkMode] = useState('BALANCED');
  
  const [selectedSolvers, setSelectedSolvers] = useState<SolverId[]>(['classical', 'neal', 'AWS_BRAKET_LOCAL']);
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('LOCAL_ONLY');
  const [showSolverPanel, setShowSolverPanel] = useState(false);

  const toggleSolver = (id: SolverId) => {
    setSelectedSolvers(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  };

  const applyExecutionMode = (mode: ExecutionMode) => {
    setExecutionMode(mode);
    const modeMap: Record<ExecutionMode, SolverId[]> = {
      LOCAL_ONLY: ['classical', 'neal', 'AWS_BRAKET_LOCAL'],
      CLOUD_ONLY: ['AWS_BRAKET_SV1', 'AWS_BRAKET_TN1'],
      QUANTUM_ONLY: ['qiskit_qaoa', 'AWS_BRAKET_LOCAL', 'AWS_BRAKET_SV1', 'AWS_BRAKET_TN1'],
      CLASSICAL_ONLY: ['classical', 'neal'],
      FULL_STACK: ['classical', 'neal', 'AWS_BRAKET_LOCAL', 'qiskit_qaoa', 'AWS_BRAKET_SV1', 'AWS_BRAKET_TN1'],
    };
    setSelectedSolvers(modeMap[mode]);
  };

  const handleRunBenchmark = useCallback(() => {
    const newSessionId = crypto.randomUUID();
    sessionIdRef.current = newSessionId;
    setSessionId(newSessionId);
    setBenchmarkData(null);

    console.log(`[BENCHMARK_SESSION_RESET] session_id=${newSessionId} timestamp=${new Date().toISOString()}`);
    toast.info('Starting benchmark session...', { description: `Session: ${newSessionId.slice(0, 8)}` });

    if (selectedSolvers.length === 0) {
      toast.error('No solvers selected', { description: 'Select at least one solver to run benchmark' });
      return;
    }

    const payload = {
        num_assets: numAssets[0],
        cardinality: Math.min(15, numAssets[0]),
        risk_tolerance: parseFloat(riskTolerance),
        max_sector_exposure: parseFloat(maxSectorExposure),
        binary_bits: binaryBits[0],
        trajectories: 256,
        benchmark_mode: benchmarkMode,
        requested_solver: 'auto',
        selected_solvers: selectedSolvers,
        execution_mode: executionMode,
      };
      
      console.log(`[FRONTEND_BENCHMARK_MODE] selected_mode=${benchmarkMode}`);
      console.log(`[FRONTEND_SOLVER_SELECTION] selected_solvers=${JSON.stringify(selectedSolvers)} execution_mode=${executionMode}`);
      console.log(`[FRONTEND_BENCHMARK_MODE] outgoing_payload=`, payload);

      runBenchmark.mutate(payload,
      {
        onSuccess: (data) => {
          if (sessionIdRef.current !== newSessionId) {
            console.warn(`[BENCHMARK_SESSION_STALE] received=${newSessionId.slice(0, 8)} current=${sessionIdRef.current.slice(0, 8)} — discarding`);
            return;
          }
          setBenchmarkData(data);
          const status = data.summary?.benchmark_status || 'SUCCESS';
          toast.success(`Benchmark complete (${status})`, { description: `Ran across ${data.results.length} solvers.` });
        },
        onError: (err) => {
          if (sessionIdRef.current !== newSessionId) return;
          toast.error('Benchmark failed', { description: err.message });
        },
      }
    );
  }, [numAssets, binaryBits, riskTolerance, maxSectorExposure, benchmarkMode, selectedSolvers, executionMode, runBenchmark]);

  const results = benchmarkData?.results || [];
  const kpis = results.length > 0 ? computeKPIs(results) : null;
  const chartData = buildChartData(results);

  const chartEnergies = chartData.map(d => d.energy);
  const isLowVariance =
    chartEnergies.length > 1 &&
    Math.max(...chartEnergies) - Math.min(...chartEnergies) < 1e-9;

  const benchmarkStatus = benchmarkData?.summary?.benchmark_status;
  const statusColor = benchmarkStatus === 'SUCCESS' ? 'text-emerald-400' : benchmarkStatus === 'PARTIAL_SUCCESS' ? 'text-yellow-400' : 'text-red-400';

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between pb-4 border-b border-border"
      >
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Activity className="w-5 h-5 text-primary" />
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Solver Benchmarking</h1>
          </div>
          <p className="text-muted-foreground text-sm">Isolated distributed solver execution with partial success handling</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSolverPanel(!showSolverPanel)}
            className="text-xs"
          >
            <Settings className="w-3 h-3 mr-1" />
            Solvers ({selectedSolvers.length})
          </Button>
          <Button
            onClick={handleRunBenchmark}
            disabled={runBenchmark.isPending || selectedSolvers.length === 0}
            className="bg-primary hover:bg-primary/90 text-primary-foreground glow-purple"
          >
            {runBenchmark.isPending ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Running...</>
            ) : (
              <><Play className="w-4 h-4 mr-2" />Run Benchmark</>
            )}
          </Button>
        </div>
      </motion.div>

      {/* Solver Selection Panel */}
      {showSolverPanel && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm">Solver Selection & Execution Mode</CardTitle>
              <CardDescription className="text-muted-foreground">
                Presets configure assets/bits/risk only. Solver routing is explicitly controlled here.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Execution Mode Buttons */}
              <div>
                <Label className="text-xs text-muted-foreground uppercase tracking-wider">Execution Mode</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {EXECUTION_MODES.map(mode => (
                    <Button
                      key={mode.id}
                      variant={executionMode === mode.id ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => applyExecutionMode(mode.id)}
                      className="text-[10px] h-7"
                      title={mode.description}
                    >
                      {mode.label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Individual Solver Toggles */}
              <div>
                <Label className="text-xs text-muted-foreground uppercase tracking-wider">Individual Solvers</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                  {SOLVER_CATALOG.map(solver => {
                    const isSelected = selectedSolvers.includes(solver.id);
                    return (
                      <button
                        key={solver.id}
                        onClick={() => toggleSolver(solver.id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs transition-all ${
                          isSelected
                            ? 'bg-primary/10 border-primary/30 text-primary'
                            : 'bg-muted/30 border-border text-muted-foreground hover:border-muted'
                        }`}
                      >
                        {isSelected ? <Check className="w-3 h-3" /> : <X className="w-3 h-3 opacity-40" />}
                        <span>{solver.label}</span>
                        <Badge variant="outline" className="text-[8px] h-4 px-1 ml-auto">
                          {solver.category}
                        </Badge>
                      </button>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Configuration Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Settings className="w-5 h-5 text-primary" />
              Benchmark Configuration
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              Presets configure optimization parameters only. Solver routing is controlled via the Solvers panel.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="space-y-2">
                <Label htmlFor="num-assets" className="text-sm font-medium text-foreground">
                  Number of Assets: <span className="text-primary font-mono">{numAssets[0]}</span>
                </Label>
                <Slider id="num-assets" min={5} max={100} step={1} value={numAssets} onValueChange={setNumAssets} className="w-full" />
                <div className="flex justify-between text-xs text-muted-foreground"><span>5</span><span>100</span></div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="binary-bits" className="text-sm font-medium text-foreground">
                  Binary Resolution (Bits): <span className="text-primary font-mono">{binaryBits[0]}</span>
                </Label>
                <Slider id="binary-bits" min={2} max={10} step={1} value={binaryBits} onValueChange={setBinaryBits} className="w-full" />
                <div className="flex justify-between text-xs text-muted-foreground"><span>2</span><span>10</span></div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="risk-tolerance" className="text-sm font-medium text-foreground">Risk Tolerance</Label>
                <Input id="risk-tolerance" type="number" min="0" max="1" step="0.1" value={riskTolerance} onChange={(e) => setRiskTolerance(e.target.value)} className="w-full" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-sector-exposure" className="text-sm font-medium text-foreground">Max Sector Exposure</Label>
                <Input id="max-sector-exposure" type="number" min="0" max="1" step="0.05" value={maxSectorExposure} onChange={(e) => setMaxSectorExposure(e.target.value)} className="w-full" />
              </div>

              <div className="lg:col-span-2 space-y-2">
                <Label className="text-sm font-medium text-foreground">Operational Benchmark Mode</Label>
                <div className="flex flex-wrap gap-2">
                  {['FAST', 'BALANCED', 'RESEARCH', 'STRESS', 'CLOUD_ONLY'].map((m) => (
                    <Button
                      key={m}
                      variant={benchmarkMode === m ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setBenchmarkMode(m)}
                      className={`text-[10px] h-7 ${benchmarkMode === m ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                    >
                      {m}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Quick Presets */}
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">Quick Presets:</div>
              <div className="flex gap-2 flex-wrap">
                <Button variant="outline" size="sm" onClick={() => { setNumAssets([6]); setBinaryBits([3]); toast.info('Applied AWS Braket LocalSimulator preset'); }}>
                  AWS Braket LocalSimulator
                </Button>
                <Button variant="outline" size="sm" onClick={() => { setNumAssets([20]); setBinaryBits([5]); toast.info('Applied Standard preset'); }}>
                  Standard
                </Button>
                <Button variant="outline" size="sm" onClick={() => { setNumAssets([50]); setBinaryBits([7]); toast.info('Applied Full preset'); }}>
                  Full
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Summary Stats */}
      {benchmarkData && kpis && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-muted-foreground text-xs uppercase mb-1">Status</p>
                <p className={`text-lg font-bold font-mono ${statusColor}`}>{benchmarkStatus || 'N/A'}</p>
              </div>
              <Shield className="w-8 h-8 opacity-50" />
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-muted-foreground text-xs uppercase mb-1">Solvers Attempted</p>
                <p className="text-2xl font-bold text-foreground font-mono">{kpis.attempted}</p>
              </div>
              <Cpu className="w-8 h-8 text-[#06B6D4] opacity-50" />
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-muted-foreground text-xs uppercase mb-1">Feasible Solutions</p>
                <p className="text-2xl font-bold text-[#10B981] font-mono">{kpis.feasibleCount}</p>
              </div>
              <Shield className="w-8 h-8 text-[#10B981] opacity-50" />
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-muted-foreground text-xs uppercase mb-1">Best Energy</p>
                <p className="text-2xl font-bold text-primary font-mono">{kpis.bestEnergy !== null ? kpis.bestEnergy.toFixed(3) : 'N/A'}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-primary opacity-50" />
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-muted-foreground text-xs uppercase mb-1">Total Time</p>
                <p className="text-2xl font-bold text-[#a855f7] font-mono">{(kpis.totalTime / 1000).toFixed(1)}s</p>
              </div>
              <Clock className="w-8 h-8 text-[#a855f7] opacity-50" />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Charts & Table */}
      {benchmarkData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Energy Comparison Chart */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card className="bg-card border-border h-full flex flex-col">
              <CardHeader>
                <CardTitle className="text-foreground flex justify-between items-center">
                  <span>Normalized Energy (0–1)</span>
                  {isLowVariance && (
                    <span className="text-xs px-2 py-1 rounded bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">Low Variance</span>
                  )}
                </CardTitle>
                <CardDescription className="text-muted-foreground">Lower is better · Comparable feasible solvers only</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 min-h-[300px]">
                {chartData.length >= 1 ? (
                  <ResponsiveContainer key={`energy-${sessionId}`} width="100%" height="100%">
                    <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
                      <XAxis type="number" stroke="#64748B" domain={[0, 1]} />
                      <YAxis dataKey="name" type="category" stroke="#64748B" width={100} tick={{ fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '12px' }}
                        itemStyle={{ color: '#7C3AED' }}
                        formatter={(value: number, _name: string, props: any) => [
                          <div className="space-y-1">
                            <div className="text-primary font-bold">{value.toFixed(4)}</div>
                            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">
                              {props.payload.isFeasible ? '✓ Feasible' : '✗ Infeasible'} | {props.payload.classification}
                            </div>
                          </div>,
                          'Normalization Score'
                        ]}
                      />
                      <Bar dataKey="energy" name="Normalized Energy" radius={[0, 4, 4, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.isFeasible ? '#7C3AED' : '#EF4444'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm space-y-2">
                    <Activity className="w-8 h-8 opacity-20" />
                    <p>No comparable feasible results to chart</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Time Comparison Chart */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card className="bg-card border-border h-full flex flex-col">
              <CardHeader>
                <CardTitle className="text-foreground">Solve Times (ms)</CardTitle>
                <CardDescription className="text-muted-foreground">Execution speed per solver</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 min-h-[300px]">
                <ResponsiveContainer key={`time-${sessionId}`} width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                    <XAxis dataKey="name" stroke="#64748B" tick={{ fontSize: 12 }} angle={-45} textAnchor="end" height={60} />
                    <YAxis stroke="#64748B" />
                    <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '6px' }} itemStyle={{ color: '#06B6D4' }} />
                    <Bar dataKey="time" name="Time (ms)" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          {/* Detailed Results Table */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="lg:col-span-2">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-foreground">Detailed Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left text-muted-foreground">
                    <thead className="text-xs uppercase border-b border-border">
                      <tr>
                        <th className="px-4 py-3">Rank</th>
                        <th className="px-4 py-3">Solver</th>
                        <th className="px-4 py-3 text-right">Portfolio Obj.</th>
                        <th className="px-4 py-3 text-right">Time (ms)</th>
                        <th className="px-4 py-3 text-center">Confidence</th>
                        <th className="px-4 py-3 text-center">Constraints</th>
                        <th className="px-4 py-3 text-center">Scientific</th>
                        <th className="px-4 py-3 text-center">Isolation</th>
                        <th className="px-4 py-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...results].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)).map((res, i) => {
                        const c = classifyResult(res);
                        return (
                        <tr key={i} className="border-b border-border hover:bg-muted/50 transition-colors">
                          <td className="px-4 py-3 font-mono">{res.rank === 999 ? '-' : (res.rank || '-')}</td>
                          <td className="px-4 py-3 font-medium text-foreground">{res.solver}</td>
                          <td className="px-4 py-3 text-right font-mono text-foreground font-bold">
                            {res.portfolio_objective_energy != null ? res.portfolio_objective_energy.toFixed(6) : (res.energy?.toFixed(6) || '-')}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-foreground">{res.solve_time_ms.toFixed(1)}</td>

                          <td className="px-4 py-3 text-center">
                            {res.execution_confidence != null ? (
                              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                res.execution_confidence >= 0.8 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                res.execution_confidence >= 0.5 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                                'bg-red-500/20 text-red-400 border border-red-500/30'
                              }`}>
                                {(res.execution_confidence * 100).toFixed(0)}%
                              </span>
                            ) : '-'}
                          </td>

                          <td className="px-4 py-3 text-center">
                            {res.constraint_satisfaction_score != null ? (
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                res.constraint_satisfaction_score >= 100 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                res.constraint_satisfaction_score >= 75 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                                'bg-red-500/20 text-red-400 border border-red-500/30'
                              }`}>
                                {res.constraint_satisfaction_score.toFixed(0)}%
                              </span>
                            ) : '-'}
                          </td>

                          <td className="px-4 py-3 text-center">
                            {res.scientific_comparability !== undefined ? (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                                res.scientific_comparability ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                              }`}>
                                {res.scientific_comparability ? 'COMPARABLE' : 'NON-COMPARABLE'}
                              </span>
                            ) : '-'}
                          </td>

                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              c.isolationStatus === 'COMPARABLE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                              c.isolationStatus === 'VALID' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                              c.isolationStatus === 'DEGRADED' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                              c.isolationStatus === 'ISOLATED_FAILURE' ? 'bg-red-500/10 text-red-300 border-red-500/20' :
                              c.isolationStatus === 'NON_COMPARABLE' ? 'bg-yellow-500/10 text-yellow-300 border-yellow-500/20' :
                              c.isolationStatus === 'SKIPPED' ? 'bg-slate-500/10 text-slate-400 border-slate-500/20' :
                              'bg-red-500/10 text-red-400 border-red-500/20'
                            }`}>
                              {c.isolationStatus}
                            </span>
                          </td>

                          <td className="px-4 py-3 text-center">
                            <div className="flex flex-col items-center gap-1">
                              <span className={`px-2 py-1 rounded-full text-xs ${c.badgeBg} ${c.badgeText} border ${c.badgeBorder}`}>
                                {c.badgeLabel}
                              </span>
                              {!res.feasible && res.status !== 'skipped' && res.status !== 'error' && (
                                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-500/20 text-red-400 border border-red-500/30">INFEASIBLE</span>
                              )}
                              {res.reason && res.status === 'error' && (
                                <span className="text-[9px] text-red-400 max-w-[150px] truncate" title={res.reason}>{res.reason}</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Empty State */}
      {!benchmarkData && !runBenchmark.isPending && (
        <Card className="bg-card border-border border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-20">
            <Activity className="w-12 h-12 text-muted-foreground mb-4 opacity-50" />
            <h3 className="text-lg font-medium text-foreground mb-2">No Benchmark Data</h3>
            <p className="text-muted-foreground text-center max-w-sm">
              Select solvers and click "Run Benchmark" to evaluate performance with isolated execution.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
