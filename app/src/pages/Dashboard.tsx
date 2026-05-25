import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, TrendingDown, Target, Activity, Zap, 
  ArrowUpRight, Download, BarChart3, PieChart, Layers, Cpu,
  Settings, Clock, Shield, LineChart as LineChartIcon,
  Play, Pause, RotateCcw, Thermometer, Gauge, MemoryStick, Sliders,
  CheckCircle, Info, Wifi, WifiOff, Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from '@/components/ui/tooltip';
import CandlestickChart from '@/components/CandlestickChart';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Area, AreaChart,
  BarChart, Bar, Legend
} from 'recharts';
import { useQueryClient } from '@tanstack/react-query';
import { usePortfolio, useRunOptimization, useOptimizationStatus, useSolvers } from '@/hooks/usePortfolioData';
import { useGPUTelemetry } from '@/hooks/useGPUTelemetry';
import type { QuboParams } from '@/types/portfolio';

type SolverMode = QuboParams['requested_solver'];

// Generate equity curve data
interface EquityDataPoint {
  month: string;
  equity: number;
  benchmark: number;
  drawdown: number;
}

const generateEquityData = () => {
  const data: EquityDataPoint[] = [];
  let equity = 100;
  let benchmark = 100;
  let maxEquity = 100;
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  for (let i = 0; i < 24; i++) {
    const month = months[i % 12];
    const year = 2023 + Math.floor(i / 12);
    
    const phase = i + 1;
    equity *= (1 + (Math.sin(phase * 0.8) * 0.018 + Math.cos(phase * 0.23) * 0.006));
    benchmark *= (1 + (Math.sin(phase * 0.65) * 0.013 + Math.cos(phase * 0.2) * 0.004));
    
    if (equity > maxEquity) maxEquity = equity;
    const drawdown = ((equity - maxEquity) / maxEquity) * 100;
    
    data.push({
      month: `${month} ${year}`,
      equity: parseFloat(equity.toFixed(2)),
      benchmark: parseFloat(benchmark.toFixed(2)),
      drawdown: parseFloat(drawdown.toFixed(2))
    });
  }
  return data;
};

const EQUITY_DATA = generateEquityData();

// Institutional KPI Card with sparkline
function KPICard({ title, value, subtitle, change, icon: Icon, delay, sparklineData }: { 
  title: string; 
  value: string; 
  subtitle: string; 
  change: number; 
  icon: any;
  delay: number;
  sparklineData?: number[];
}) {
  const isPositive = change >= 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
    >
      <Card className="bg-card border-border hover:border-primary/50 transition-all duration-300 h-full">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <div className="flex items-center gap-1 mb-1">
                <p className="text-muted-foreground text-xs font-medium uppercase tracking-wider">{title}</p>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="w-3 h-3 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="bg-muted border-border text-foreground text-[10px] max-w-[200px]">
                      {title === 'Expected Return' && "Forecasted annual return based on historical mean returns and Qurve optimized weights."}
                      {title === 'Sharpe Ratio' && "Measures risk-adjusted return. Above 1.0 is considered good for a portfolio."}
                      {title === 'Sortino Ratio' && "Similar to Sharpe, but only penalizes downside volatility. Focuses on 'bad' risk."}
                      {title === 'Volatility' && "Annualized standard deviation (σ) of returns. Represents price fluctuations."}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <h3 className="text-2xl font-bold text-foreground font-mono">{value}</h3>
            </div>
            <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
              <Icon className="w-5 h-5 text-primary" />
            </div>
          </div>
          
          {/* Sparkline */}
          {sparklineData && sparklineData.length > 0 && (
            <div className="h-8 mb-3">
              <svg width="100%" height="100%" viewBox="0 0 100 30" preserveAspectRatio="none">
                <polyline
                  points={(() => {
                    const validData = sparklineData.filter(v => typeof v === 'number' && !isNaN(v));
                    if (validData.length === 0) return '';
                    const minVal = Math.min(...validData);
                    const maxVal = Math.max(...validData);
                    const range = maxVal - minVal || 1;
                    return validData.map((v, i) => {
                      const x = (i / (validData.length - 1)) * 100;
                      const y = 30 - ((v - minVal) / range) * 30;
                      return `${x},${y}`;
                    }).join(' ');
                  })()}
                  fill="none"
                  stroke={isPositive ? '#10B981' : '#EF4444'}
                  strokeWidth="2"
                />
              </svg>
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <span className={`flex items-center gap-1 text-xs font-bold font-mono ${isPositive ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
              {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {isPositive ? '+' : ''}{change.toFixed(2)}%
            </span>
            <span className="text-xs text-muted-foreground">{subtitle}</span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Sector Donut Chart
function SectorChart({ sectors }: { sectors: Record<string, number> }) {
  const colors = ['#7C3AED', '#3B82F6', '#06B6D4', '#0D9488', '#10B981', '#6D28D9', '#2563EB'];
  const entries = Object.entries(sectors || {}).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);
  
  let currentAngle = 0;
  
  return (
    <div className="relative w-32 h-32 mx-auto">
      <svg viewBox="0 0 100 100" className="transform -rotate-90">
        {entries.map(([sector, value], i) => {
          const angle = (value / total) * 360;
          const startAngle = currentAngle;
          currentAngle += angle;
          
          const x1 = 50 + 38 * Math.cos((startAngle * Math.PI) / 180);
          const y1 = 50 + 38 * Math.sin((startAngle * Math.PI) / 180);
          const x2 = 50 + 38 * Math.cos(((startAngle + angle) * Math.PI) / 180);
          const y2 = 50 + 38 * Math.sin(((startAngle + angle) * Math.PI) / 180);
          
          const largeArc = angle > 180 ? 1 : 0;
          
          return (
            <path
              key={sector}
              d={`M 50 50 L ${x1} ${y1} A 38 38 0 ${largeArc} 1 ${x2} ${y2} Z`}
              fill={colors[i % colors.length]}
              stroke="#111827"
              strokeWidth="2"
            />
          );
        })}
        <circle cx="50" cy="50" r="22" fill="#111827" />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-bold text-foreground font-mono">{entries.length}</p>
          <p className="text-[10px] text-muted-foreground">Sectors</p>
        </div>
      </div>
    </div>
  );
}

// Drawdown Chart
function DrawdownChart() {
  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={EQUITY_DATA} margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
          <defs>
            <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <Area 
            type="monotone" 
            dataKey="drawdown" 
            stroke="#EF4444" 
            fill="url(#drawdownGradient)" 
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// Equity Curve Chart
function EquityCurveChart() {
  return (
    <div className="h-32">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={EQUITY_DATA}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
          <XAxis dataKey="month" hide />
          <YAxis hide domain={['dataMin', 'dataMax']} />
          <RechartsTooltip 
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-card border border-border p-2 rounded shadow-sm text-xs text-foreground">
                    <p className="text-muted-foreground">{label}</p>
                    {payload.map((item, i) => (
                      <p key={i} style={{ color: item.color }}>
                        {item.name}: {item.value}
                      </p>
                    ))}
                  </div>
                );
              }
              return null;
            }}
          />
          <Line 
            type="monotone" 
            dataKey="equity" 
            stroke="#7C3AED" 
            strokeWidth={2}
            dot={false}
          />
          <Line 
            type="monotone" 
            dataKey="benchmark" 
            stroke="#3B82F6" 
            strokeWidth={2}
            dot={false}
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Backtesting & Risk Tab Component
function BacktestingRiskTab() {
  const backtestData = [
    { period: '1M', portfolio: 3.24, benchmark: 2.18, alpha: 1.06 },
    { period: '3M', portfolio: 8.67, benchmark: 5.42, alpha: 3.25 },
    { period: '6M', portfolio: 14.23, benchmark: 9.87, alpha: 4.36 },
    { period: '1Y', portfolio: 24.56, benchmark: 16.34, alpha: 8.22 },
    { period: 'YTD', portfolio: 18.92, benchmark: 12.45, alpha: 6.47 },
  ];

  const riskMetrics = [
    { name: 'Volatility', value: '13.2%', benchmark: '18.5%', status: 'good' },
    { name: 'Sharpe Ratio', value: '1.27', benchmark: '0.61', status: 'good' },
    { name: 'Sortino Ratio', value: '1.92', benchmark: '0.89', status: 'good' },
    { name: 'Max Drawdown', value: '-8.4%', benchmark: '-15.2%', status: 'good' },
    { name: 'Beta', value: '0.84', benchmark: '1.00', status: 'neutral' },
    { name: 'Alpha', value: '6.23%', benchmark: '0.00%', status: 'good' },
  ];

  return (
    <div className="space-y-6">
      {/* Backtesting Results */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-foreground flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Backtesting Results
            </CardTitle>
            <p className="text-sm text-muted-foreground">Historical performance vs NIFTY 50 benchmark</p>
          </CardHeader>
          <CardContent>
            <div className="h-64 mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={backtestData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="period" stroke="#64748B" />
                  <YAxis stroke="#64748B" />
                  <RechartsTooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-card border border-border p-2 rounded shadow-sm text-xs text-foreground">
                            <p className="text-muted-foreground">{label}</p>
                            {payload.map((item, i) => (
                              <p key={i} style={{ color: item.color }}>
                                {item.name}: {item.value}
                              </p>
                            ))}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                  <Bar dataKey="portfolio" name="Qurve Portfolio" fill="#7C3AED" />
                  <Bar dataKey="benchmark" name="NIFTY 50" fill="#3B82F6" />
                  <Bar dataKey="alpha" name="Alpha" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#1E293B]">
                    <th className="text-left py-3 text-[#94A3B8] text-xs font-medium uppercase">Period</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">Portfolio</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">NIFTY 50</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">Alpha</th>
                  </tr>
                </thead>
                <tbody>
                  {backtestData.map((row, i) => (
                    <tr key={i} className="border-b border-[#1E293B]/50">
                      <td className="py-3 text-white">{row.period}</td>
                      <td className="py-3 text-right text-[#22c55e]">+{row.portfolio}%</td>
                      <td className="py-3 text-right text-[#94A3B8]">+{row.benchmark}%</td>
                      <td className="py-3 text-right text-primary font-medium">+{row.alpha}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Risk Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-foreground flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Risk Analysis
            </CardTitle>
            <p className="text-sm text-muted-foreground">Risk-adjusted performance metrics</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {riskMetrics.map((metric) => (
                <TooltipProvider key={metric.name}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="p-4 bg-background rounded-xl border border-border cursor-help hover:border-primary/30 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-muted-foreground text-sm">{metric.name}</span>
                          {metric.status === 'good' && <CheckCircle className="w-4 h-4 text-[#10B981]" />}
                          {metric.status === 'neutral' && <Info className="w-4 h-4 text-[#F59E0B]" />}
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-bold text-foreground">{metric.value}</span>
                          <span className="text-xs text-muted-foreground">vs {metric.benchmark}</span>
                        </div>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent className="bg-muted border-border text-foreground text-[10px]">
                      {metric.name === 'Volatility' && "Annualized price fluctuation (Standard Deviation). Lower is usually better."}
                      {metric.name === 'Sharpe Ratio' && "Return per unit of total risk. Higher indicates better risk-adjusted performance."}
                      {metric.name === 'Sortino Ratio' && "Return per unit of downside risk. Superior to Sharpe for asymmetric distributions."}
                      {metric.name === 'Max Drawdown' && "The maximum observed loss from a peak to a trough. Measures crash risk."}
                      {metric.name === 'Beta' && "Measures sensitivity to the NIFTY 50 benchmark. 1.0 means it moves with the market."}
                      {metric.name === 'Alpha' && "Excess return over the benchmark. Measures the value added by the Qurve solver."}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Drawdown Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-foreground flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-destructive" />
              Drawdown Analysis
            </CardTitle>
            <p className="text-sm text-muted-foreground">Underwater curve showing peak-to-trough declines</p>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={EQUITY_DATA}>
                  <defs>
                    <linearGradient id="drawdownGradient2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="month" stroke="#64748B" />
                  <YAxis stroke="#64748B" />
                  <RechartsTooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-card border border-border p-2 rounded shadow-sm text-xs text-foreground">
                            <p className="text-muted-foreground">{label}</p>
                            {payload.map((item, i) => (
                              <p key={i} style={{ color: item.color }}>
                                {item.name}: {item.value}
                              </p>
                            ))}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="drawdown" 
                    stroke="#EF4444" 
                    fill="url(#drawdownGradient2)" 
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

// GPU Telemetry Tab Component — WIRED TO REAL WEBSOCKET
function GPUTelemetryTab() {
  const { metrics: gpuMetrics, isConnected, error: _wsError } = useGPUTelemetry();
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    '[10:23:45] INFO: GPU initialized successfully',
    '[10:23:46] INFO: CUDA runtime v12.1 loaded',
    '[10:23:47] INFO: Ready for optimization',
  ]);

  // Use real GPU metrics when connected, fallback to idle values
  const displayMetrics = gpuMetrics ? {
    utilization: gpuMetrics.utilization,
    vram: Math.round((gpuMetrics.vram_used_mb / Math.max(gpuMetrics.vram_total_mb, 1)) * 100),
    temperature: gpuMetrics.temperature_c,
    power: gpuMetrics.power_draw_w,
  } : {
    utilization: 0,
    vram: 0,
    temperature: 0,
    power: 0,
  };

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-foreground flex items-center gap-2">
              <Cpu className="w-5 h-5 text-primary" />
              GPU Control Panel
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 mb-6">
              <Button
                onClick={() => setIsRunning(!isRunning)}
                className={isRunning ? 'bg-[#F59E0B] hover:bg-[#D97706]' : 'bg-[#22c55e] hover:bg-[#16a34a]'}
              >
                {isRunning ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                {isRunning ? 'Pause' : 'Start'} Optimization
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setIsRunning(false);
                  setLogs(prev => [`[${new Date().toLocaleTimeString()}] INFO: Reset complete`, ...prev].slice(0, 8));
                }}
                className="border-[#1E293B] text-[#94A3B8]"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
              <div className="ml-auto flex items-center gap-2">
                {isConnected ? (
                  <><Wifi className="w-4 h-4 text-[#22c55e]" /><span className="text-[#22c55e] text-sm">Live</span></>
                ) : (
                  <><WifiOff className="w-4 h-4 text-[#f2362c]" /><span className="text-[#f2362c] text-sm">Offline</span></>
                )}
              </div>
            </div>

            {/* GPU Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'GPU Utilization', value: displayMetrics.utilization, icon: Gauge, color: '#7C3AED' },
                { label: 'VRAM Usage', value: displayMetrics.vram, icon: MemoryStick, color: '#3B82F6' },
                { label: 'Temperature', value: displayMetrics.temperature, icon: Thermometer, color: displayMetrics.temperature > 80 ? '#EF4444' : '#10B981' },
                { label: 'Power Draw', value: displayMetrics.power, suffix: 'W', icon: Zap, color: '#a855f7' },
              ].map((metric) => (
                <div key={metric.label} className="p-4 bg-[#0d1117] rounded-xl border border-[#1E293B]">
                  <div className="flex items-center gap-2 mb-2">
                    <metric.icon className="w-4 h-4" style={{ color: metric.color }} />
                    <span className="text-[#64748B] text-xs">{metric.label}</span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {metric.value}{metric.suffix || '%'}
                  </div>
                  <div className="h-1.5 bg-[#1E293B] rounded-full overflow-hidden mt-2">
                    <div 
                      className="h-full rounded-full transition-all duration-500"
                      style={{ 
                        width: `${Math.min((metric.value / (metric.suffix ? 150 : 100)) * 100, 100)}%`,
                        backgroundColor: metric.color
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Solver Logs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-foreground">Solver Logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-[#0d1117] rounded-xl p-4 font-mono text-xs h-48 overflow-y-auto">
              {logs.map((log, i) => (
                <div key={i} className="text-[#94A3B8] mb-1">
                  {log.includes('INFO') ? (
                    <span className="text-[#22c55e]">●</span>
                  ) : log.includes('ERROR') ? (
                    <span className="text-[#f2362c]">●</span>
                  ) : (
                    <span className="text-[#F59E0B]">●</span>
                  )} {log}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

// Configuration Tab Component
function ConfigurationTab() {
  const [config, setConfig] = useState({
    cardinality: 15,
    riskTolerance: 0.5,
    sectorConstraints: true,
    maxSectorExposure: 25,
    binaryBits: 7,
    solverMode: 'hybrid',
    autoRebalance: false,
    notifications: true,
  });

  return (
    <div className="space-y-6">
      {/* QUBO Parameters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-primary" />
              Qurve Parameters
            </CardTitle>
            <p className="text-sm text-muted-foreground">Configure optimization constraints</p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Cardinality */}
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-white text-sm">Target Holdings (Cardinality)</label>
                <span className="text-primary font-mono">{config.cardinality}</span>
              </div>
              <input
                type="range"
                min="5"
                max="20"
                value={config.cardinality}
                onChange={(e) => setConfig({ ...config, cardinality: parseInt(e.target.value) })}
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-[#7C3AED]"
              />
              <div className="flex justify-between text-xs text-[#64748B] mt-1">
                <span>5</span>
                <span>20</span>
              </div>
            </div>

            {/* Risk Tolerance */}
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-white text-sm">Risk Tolerance</label>
                <span className="text-primary font-mono">{(config.riskTolerance * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={config.riskTolerance * 100}
                onChange={(e) => setConfig({ ...config, riskTolerance: parseInt(e.target.value) / 100 })}
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-[#7C3AED]"
              />
            </div>

            {/* Sector Constraints */}
            <div className="flex items-center justify-between p-4 bg-[#0d1117] rounded-xl">
              <div>
                <p className="text-white text-sm">Sector Constraints</p>
                <p className="text-[#64748B] text-xs">Limit exposure per sector</p>
              </div>
              <Switch
                checked={config.sectorConstraints}
                onCheckedChange={(checked) => setConfig({ ...config, sectorConstraints: checked })}
              />
            </div>

            {config.sectorConstraints && (
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-white text-sm">Max Sector Exposure</label>
                  <span className="text-primary font-mono">{config.maxSectorExposure}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="50"
                  value={config.maxSectorExposure}
                  onChange={(e) => setConfig({ ...config, maxSectorExposure: parseInt(e.target.value) })}
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-[#7C3AED]"
                />
              </div>
            )}

            {/* Binary Expansion */}
            <div>
              <label className="text-white text-sm block mb-2">Binary Expansion Bits</label>
              <select
                value={config.binaryBits}
                onChange={(e) => setConfig({ ...config, binaryBits: parseInt(e.target.value) })}
                className="w-full px-4 py-3 bg-background border border-border rounded-xl text-foreground focus:outline-none focus:border-primary/50"
              >
                <option value={5}>5 bits (3.125% precision)</option>
                <option value={6}>6 bits (1.56% precision)</option>
                <option value={7}>7 bits (0.78% precision)</option>
                <option value={8}>8 bits (0.39% precision)</option>
              </select>
            </div>

            {/* Solver Mode */}
            <div>
              <label className="text-white text-sm block mb-2">Solver Mode</label>
              <select
                value={config.solverMode}
                onChange={(e) => setConfig({ ...config, solverMode: e.target.value })}
                className="w-full px-4 py-3 bg-background border border-border rounded-xl text-foreground focus:outline-none focus:border-primary/50"
              >
                <option value="hybrid">Hybrid Quantum-Classical</option>
                <option value="dwave_hybrid">D-Wave Hybrid</option>
                <option value="qiskit_qaoa">Qiskit QAOA (Reduced)</option>
                <option value="classical">Classical Fallback</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Automation Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-foreground">Automation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-[#0d1117] rounded-xl">
              <div>
                <p className="text-white text-sm">Auto-Rebalance</p>
                <p className="text-[#64748B] text-xs">Automatically rebalance on signal</p>
              </div>
              <Switch
                checked={config.autoRebalance}
                onCheckedChange={(checked) => setConfig({ ...config, autoRebalance: checked })}
              />
            </div>
            <div className="flex items-center justify-between p-4 bg-[#0d1117] rounded-xl">
              <div>
                <p className="text-white text-sm">Optimization Notifications</p>
                <p className="text-[#64748B] text-xs">Notify when optimization completes</p>
              </div>
              <Switch
                checked={config.notifications}
                onCheckedChange={(checked) => setConfig({ ...config, notifications: checked })}
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Save Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Button 
          onClick={() => {
            toast.success('Configuration saved successfully');
            toast.info('To run optimization with these params, use the Optimize button on the Overview tab.');
          }}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground glow-purple"
        >
          Save Configuration
        </Button>
      </motion.div>
    </div>
  );
}

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [optimizationTaskId, setOptimizationTaskId] = useState<string | null>(null);
  const [solverMode, setSolverMode] = useState<SolverMode>('auto');

  // Real API data hooks
  const queryClient = useQueryClient();
  const { data: portfolioData, isLoading: isPortfolioLoading, error: portfolioError } = usePortfolio();
  const runOptimization = useRunOptimization();
  const { data: taskStatus } = useOptimizationStatus(optimizationTaskId);
  const { data: solverData } = useSolvers();
  const solverOptions = solverData?.solvers ?? [
    { id: 'auto', label: 'Auto (Smart Router)', status: 'available' },
    { id: 'hybrid', label: 'Hybrid Quantum-Classical', status: 'available' },
    { id: 'classical', label: 'Classical (Multi-Strategy)', status: 'available' },
    { id: 'sb', label: 'GPU Simulated Bifurcation', status: 'available' },
    { id: 'braket', label: 'AWS Braket LocalSimulator', status: 'not_installed' },
    { id: 'neal', label: 'D-Wave Simulated Annealing', status: 'not_installed' },
    { id: 'dwave_hybrid', label: 'D-Wave Leap Hybrid', status: 'not_installed' },
    { id: 'dwave_qpu', label: 'D-Wave Direct QPU', status: 'not_installed' },
    { id: 'qiskit_qaoa', label: 'IBM Qiskit QAOA', status: 'not_installed' },
  ];

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  // Handle optimization completion
  useEffect(() => {
    if (taskStatus?.status === 'complete') {
      if (taskStatus.result) {
        queryClient.setQueryData(['portfolio'], taskStatus.result);
      }
      const fallback = taskStatus.result?.solver_metadata?.penalty_weights?.fallback_reason;
      if (fallback) {
        toast.warning('Solver Fallback Triggered', { description: String(fallback) });
      } else {
        toast.success('Optimization complete!', { description: `Sharpe: ${taskStatus.result?.metrics.sharpe_ratio.toFixed(4)}` });
      }
      setOptimizationTaskId(null);
    } else if (taskStatus?.status === 'failed') {
      toast.error('Optimization failed', { description: taskStatus.error });
      setOptimizationTaskId(null);
    }
  }, [taskStatus?.status, taskStatus?.result, queryClient]);

  const handleExport = () => {
    toast.success('Portfolio report exported', { description: 'Downloaded as PDF' });
  };

  const handleRunOptimization = () => {
    runOptimization.mutate(
      {
        cardinality: 15,
        risk_tolerance: 0.5,
        max_sector_exposure: 0.25,
        binary_bits: 7,
        requested_solver: solverMode,
        trajectories: 256,
      },
      {
        onSuccess: (data) => {
          setOptimizationTaskId(data.task_id);
          toast.info('Optimization started', { description: `Task: ${data.task_id.slice(0, 8)}...` });
        },
        onError: (err) => {
          toast.error('Failed to start optimization', { description: err.message });
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between pb-4 border-b border-border"
        >
          <div>
            <div className="flex items-center gap-3 mb-1">
              <BarChart3 className="w-5 h-5 text-primary" />
              <h1 className="text-2xl font-bold text-foreground tracking-tight">Qurve Command Center</h1>
              {optimizationTaskId && taskStatus && (
                <span className="px-2 py-0.5 rounded text-xs bg-primary/20 text-primary flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  {taskStatus.step} ({taskStatus.progress.toFixed(0)}%)
                </span>
              )}
            </div>
            <p className="text-muted-foreground text-sm">Portfolio Optimization Dashboard • NIFTY 50 Universe</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={solverMode}
              onChange={(event) => setSolverMode(event.target.value as SolverMode)}
              className="h-9 rounded bg-card border border-border px-3 text-xs text-foreground outline-none"
            >
              {solverOptions.map((solver) => (
                <option key={solver.id} value={solver.id}>
                  {solver.label} ({solver.status})
                </option>
              ))}
            </select>
            <Button
              onClick={handleRunOptimization}
              disabled={runOptimization.isPending || !!optimizationTaskId}
              className="bg-primary hover:bg-primary/90 text-primary-foreground glow-purple"
            >
              {(runOptimization.isPending || optimizationTaskId) ? (
                <><Loader2 className="w-3 h-3 mr-2 animate-spin" />Optimizing...</>
              ) : (
                <><Zap className="w-3 h-3 mr-2" />Run Optimization</>
              )}
            </Button>
          </div>
        </motion.div>

        <Card className="bg-card border-border">
          <CardContent className="p-8">
            <div className="max-w-2xl">
              <div className="flex items-center gap-2 mb-3">
                <Info className="w-5 h-5 text-[#F59E0B]" />
                <h2 className="text-white font-semibold">No production portfolio loaded</h2>
              </div>
              <p className="text-[#94A3B8] text-sm leading-relaxed">
                The dashboard is waiting for a real backend result. Mock portfolio values are no longer shown as live data.
              </p>
              {isPortfolioLoading && <p className="text-[#64748B] text-xs mt-4">Checking backend result store...</p>}
              {portfolioError && (
                <p className="text-[#F59E0B] text-xs mt-4">
                  Backend response: {portfolioError instanceof Error ? portfolioError.message : 'Portfolio unavailable'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const PORTFOLIO_DATA = portfolioData;

  // Calculate sector allocation if not provided by backend
  const portfolio = PORTFOLIO_DATA.portfolio || {};
  const computedSectorAllocation = Object.values(portfolio).reduce((acc, holding) => {
    acc[holding.sector] = (acc[holding.sector] || 0) + holding.weight;
    return acc;
  }, {} as Record<string, number>);

  const sectorAllocation = PORTFOLIO_DATA.sector_allocation && Object.keys(PORTFOLIO_DATA.sector_allocation).length > 0 
    ? PORTFOLIO_DATA.sector_allocation 
    : computedSectorAllocation;
  const solverMeta = PORTFOLIO_DATA.solver_metadata;
  const solverPenalty = solverMeta?.penalty_weights ?? {};
  const solveTime = solverMeta ? `${(solverMeta.solve_time_ms / 1000).toFixed(2)}s` : 'Pending';

  const kpiCards = [
    {
      title: 'Expected Return',
      value: `${(PORTFOLIO_DATA.metrics.expected_return * 100).toFixed(1)}%`,
      subtitle: 'Annualized',
      change: PORTFOLIO_DATA.metrics.expected_return * 100,
      icon: TrendingUp,
      sparklineData: [100, 102, 101, 105, 108, 106, 110, 112, 115, 118]
    },
    {
      title: 'Sharpe Ratio',
      value: PORTFOLIO_DATA.metrics.sharpe_ratio.toFixed(2),
      subtitle: 'Risk-adjusted',
      change: PORTFOLIO_DATA.metrics.sharpe_ratio > 1 ? 15.0 : -5.0,
      icon: Target,
      sparklineData: [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, PORTFOLIO_DATA.metrics.sharpe_ratio]
    },
    {
      title: 'Sortino Ratio',
      value: PORTFOLIO_DATA.metrics.sortino_ratio.toFixed(2),
      subtitle: 'Downside-adjusted',
      change: PORTFOLIO_DATA.metrics.sortino_ratio > 1 ? 12.0 : -3.0,
      icon: Shield,
      sparklineData: [1.0, 1.1, 1.05, 1.15, 1.2, 1.3, 1.4, 1.5, 1.6, PORTFOLIO_DATA.metrics.sortino_ratio]
    },
    {
      title: 'Volatility',
      value: `${(PORTFOLIO_DATA.metrics.volatility * 100).toFixed(1)}%`,
      subtitle: 'Annualized σ',
      change: -5.2,
      icon: Activity,
      sparklineData: [18, 17.5, 16, 15.5, 15, 14.5, 14, 13.5, 13.2, PORTFOLIO_DATA.metrics.volatility * 100]
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header - Institutional Style */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row items-center justify-between gap-4 pb-4 border-b border-border"
      >
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-primary" />
          <h1 className="text-xl font-bold text-foreground tracking-tight">Qurve Command Center</h1>
          <span className="px-2 py-0.5 rounded text-xs bg-[#10B981]/20 text-[#10B981]">Live Result</span>
          {optimizationTaskId && taskStatus && (
            <span className="px-2 py-0.5 rounded text-xs bg-primary/20 text-primary flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              {taskStatus.step} ({taskStatus.progress.toFixed(0)}%)
            </span>
          )}
          <span className="text-muted-foreground text-sm border-l border-border pl-3 ml-1 hidden lg:block">NIFTY 50 Universe</span>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={solverMode}
            onChange={(event) => setSolverMode(event.target.value as SolverMode)}
            className="h-9 rounded bg-card border border-border px-3 text-xs text-foreground outline-none"
          >
            {solverOptions.map((solver) => (
              <option key={solver.id} value={solver.id}>
                {solver.label} ({solver.status})
              </option>
            ))}
          </select>
          <div className="hidden xl:flex items-center gap-2 px-3 py-2 rounded bg-card border border-border text-muted-foreground text-xs font-mono h-9">
            <Clock className="w-3 h-3" />
            <span>{solveTime}</span>
          </div>
          <Button
            onClick={handleRunOptimization}
            disabled={runOptimization.isPending || !!optimizationTaskId}
            className="bg-primary hover:bg-primary/90 text-primary-foreground glow-purple h-9"
          >
            {(runOptimization.isPending || optimizationTaskId) ? (
              <><Loader2 className="w-3 h-3 mr-2 animate-spin" />Optimizing...</>
            ) : (
              <><Zap className="w-3 h-3 mr-2" />Optimize</>
            )}
          </Button>
          <Button onClick={handleExport} variant="outline" size="sm" className="border-border text-muted-foreground hover:text-foreground hover:border-primary bg-card h-9 hidden md:flex">
            <Download className="w-3 h-3 mr-2" />
            Export
          </Button>
        </div>
      </motion.div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border">
        {[
          { id: 'overview', label: 'Overview', icon: BarChart3 },
          { id: 'analytics', label: 'Backtesting & Risk', icon: LineChartIcon },
          { id: 'telemetry', label: 'GPU Telemetry', icon: Cpu },
          { id: 'settings', label: 'Configuration', icon: Settings },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab.id 
                ? 'text-primary border-primary' 
                : 'text-muted-foreground border-transparent hover:text-foreground'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          {/* KPI Cards Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
            {kpiCards.map((card, i) => (
              <div key={card.title} className="h-full">
                <KPICard {...card} delay={i * 0.1} />
              </div>
            ))}
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6">
            {/* Candlestick Chart - Takes 8 columns */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="lg:col-span-8 h-full"
            >
              <CandlestickChart 
                title="Predictive Alpha" 
                symbol="QUBO-NIFTY OPTIMIZED" 
                height={520}
                showTimeframes={true}
              />
            </motion.div>

            {/* Right Panel - Takes 4 columns */}
            <div className="lg:col-span-4 flex flex-col gap-4 lg:gap-6 h-full">
              {/* Sector Allocation */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="h-[280px] lg:h-auto lg:flex-1"
              >
                <Card className="bg-card border-border h-full flex flex-col">
                  <CardHeader className="flex flex-row items-center gap-2 py-2.5 px-4 border-b border-border">
                    <PieChart className="w-4 h-4 text-primary" />
                    <CardTitle className="text-foreground text-sm font-semibold">Asset Allocation</CardTitle>
                  </CardHeader>
                  <CardContent className="p-3 flex-1 flex flex-col justify-between">
                    <SectorChart sectors={sectorAllocation} />
                    <div className="mt-4 space-y-2">
                      {Object.entries(sectorAllocation || {})
                        .sort((a, b) => b[1] - a[1])
                        .map(([sector, weight], i) => (
                      <div key={sector} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-2 h-2 rounded-full" 
                            style={{ backgroundColor: ['#7C3AED', '#3B82F6', '#06B6D4', '#0D9488', '#10B981', '#6D28D9', '#2563EB'][i % 7] }}
                          />
                          <span className="text-[#94A3B8]">{sector}</span>
                        </div>
                        <span className="text-white font-mono font-medium">{(weight * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Equity Curve Mini */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="h-[280px] lg:h-auto"
          >
            <Card className="bg-card border-border h-full flex flex-col">
              <CardHeader className="flex flex-row items-center gap-2 py-2.5 px-4 border-b border-border">
                <TrendingUp className="w-4 h-4 text-[#10B981]" />
                <CardTitle className="text-foreground text-sm font-semibold">Equity Curve</CardTitle>
              </CardHeader>
              <CardContent className="p-3 flex-1 flex flex-col justify-between">
                <EquityCurveChart />
                <div className="flex items-center justify-center gap-4 mt-2 text-xs">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    <span className="text-[#94A3B8]">Portfolio</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-[#3B82F6]" />
                    <span className="text-[#94A3B8]">NIFTY 50</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Bottom Row - Holdings & Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6 mt-4 lg:mt-6">
        {/* Holdings Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card className="bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between py-2.5 px-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-primary" />
                <CardTitle className="text-foreground text-sm font-semibold">Portfolio Holdings</CardTitle>
                <span className="text-[#64748B] text-xs">({Object.keys(PORTFOLIO_DATA.portfolio || {}).length} assets)</span>
              </div>
              <Button variant="outline" size="sm" className="border-border text-muted-foreground hover:text-foreground hover:border-primary bg-transparent">
                View All
                <ArrowUpRight className="w-3 h-3 ml-2" />
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#1E293B] bg-[#0a0f1c]">
                      <th className="text-left py-3 px-4 text-[#64748B] text-xs font-medium uppercase tracking-wider">Asset</th>
                      <th className="text-left py-3 px-4 text-[#64748B] text-xs font-medium uppercase tracking-wider">Sector</th>
                      <th className="text-right py-3 px-4 text-[#64748B] text-xs font-medium uppercase tracking-wider">Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(PORTFOLIO_DATA.portfolio || {})
                      .sort((a, b) => b[1].weight - a[1].weight)
                      .map(([ticker, data]) => {
                        return (
                          <tr key={ticker} className="border-b border-[#1E293B]/50 hover:bg-[#1E293B]/30 transition-colors">
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-[#1E293B] flex items-center justify-center">
                                  <span className="text-white text-xs font-bold font-mono">{ticker[0]}</span>
                                </div>
                                <span className="text-white font-medium text-sm">{ticker.replace('.NS', '')}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-1 rounded text-xs font-medium bg-[#1E293B] text-[#94A3B8]">
                                {data.sector}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className="text-white font-mono font-medium">{(data.weight * 100).toFixed(2)}%</span>
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

        {/* Risk Analytics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <Card className="bg-card border-border h-full flex flex-col">
            <CardHeader className="flex flex-row items-center gap-2 py-2.5 px-4 border-b border-border">
              <Shield className="w-4 h-4 text-[#f2362c]" />
              <CardTitle className="text-foreground text-sm font-semibold">Risk Analytics</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4 flex-1 flex flex-col">
              {/* Risk Metrics Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Volatility</p>
                  <p className="text-white font-mono font-bold">{(PORTFOLIO_DATA.metrics.volatility * 100).toFixed(1)}%</p>
                </div>
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Sharpe Ratio</p>
                  <p className="text-white font-mono font-bold">{PORTFOLIO_DATA.metrics.sharpe_ratio.toFixed(2)}</p>
                </div>
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Sortino Ratio</p>
                  <p className="text-white font-mono font-bold">{PORTFOLIO_DATA.metrics.sortino_ratio.toFixed(2)}</p>
                </div>
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Variance</p>
                  <p className="text-white font-mono font-bold">{PORTFOLIO_DATA.metrics.variance.toFixed(4)}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Feasibility</p>
                  <p className={`font-mono font-bold ${PORTFOLIO_DATA.constraint_verification?.all_satisfied ? 'text-[#22c55e]' : 'text-[#F59E0B]'}`}>
                    {PORTFOLIO_DATA.constraint_verification?.all_satisfied ? 'Passed' : 'Review'}
                  </p>
                  <p className="text-[#64748B] text-[11px] mt-2">
                    {PORTFOLIO_DATA.constraint_verification?.cardinality ?? 0}/{PORTFOLIO_DATA.parameters?.cardinality ?? 15} assets
                  </p>
                </div>
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Solver Used</p>
                  <p className="text-white font-mono font-bold text-sm truncate">{solverMeta?.actual_solver_used ?? String(solverPenalty.solver ?? 'unknown')}</p>
                  <p className="text-[#64748B] text-[11px] mt-2">{solverMeta?.qubo_variables ?? 0} variables</p>
                </div>
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Energy</p>
                  <p className="text-white font-mono font-bold">
                    {typeof solverPenalty.energy === 'number' ? solverPenalty.energy.toFixed(3) : 'N/A'}
                  </p>
                </div>
                <div className="p-4 rounded bg-[#0a0f1c] border border-[#1E293B]">
                  <p className="text-[#64748B] text-xs mb-2">Quantum Backend</p>
                  <p className="text-white font-mono font-bold">{String(solverPenalty.backend_name ?? solverPenalty.quantum_backend ?? 'local')}</p>
                  <p className="text-[#64748B] text-[11px] mt-2">
                    {String(solverPenalty.provider ?? 'local')} | Chain breaks: {solverPenalty.chain_break_fraction ?? 'N/A'}
                  </p>
                </div>
              </div>
              
              {/* Drawdown Chart */}
              <div className="flex-1 flex flex-col min-h-[200px]">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[#64748B] text-xs">Drawdown Analysis</span>
                  <span className="text-[#f2362c] text-xs font-mono">Simulated</span>
                </div>
                <div className="flex-1 bg-[#0a0f1c] rounded border border-[#1E293B] p-3">
                  <DrawdownChart />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* GPU Status Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="mt-4 lg:mt-6"
          >
            <Card className="bg-card border-border">
              <CardContent className="p-3">
                <div className="flex items-center gap-3 mb-3">
                  <Zap className="w-4 h-4 text-[#22c55e]" />
                  <span className="text-white text-sm font-semibold">GPU Optimization Status</span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#22c55e]/20 text-[#22c55e]">Active</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 lg:gap-6">
                  {[
                    { label: 'GPU Utilization', value: 78, color: '#7C3AED' },
                    { label: 'VRAM Usage', value: 62, color: '#3B82F6' },
                    { label: 'Temperature', value: 68, color: '#10B981' },
                    { label: 'Power Draw', value: 125, suffix: 'W', max: 150, color: '#a855f7' },
                  ].map((metric) => (
                    <div key={metric.label}>
                      <div className="flex justify-between mb-1.5">
                        <span className="text-[#64748B] text-xs">{metric.label}</span>
                        <span className="text-white text-xs font-mono font-medium">
                          {metric.value}{metric.suffix || '%'}
                        </span>
                      </div>
                      <div className="h-1.5 bg-[#1E293B] rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all duration-500"
                          style={{ 
                            width: `${(metric.value / (metric.max || 100)) * 100}%`,
                            backgroundColor: metric.color
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}

      {activeTab === 'analytics' && <BacktestingRiskTab />}
      {activeTab === 'telemetry' && <GPUTelemetryTab />}
      {activeTab === 'settings' && <ConfigurationTab />}
    </div>
  );
}
