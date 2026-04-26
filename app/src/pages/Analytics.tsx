import { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, AlertTriangle, Download, Filter, Target } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';

const deterministicJitter = (seed: number, amplitude: number) => Math.sin(seed * 12.9898) * amplitude;

// Generate dynamic data based on time range
const generateRiskMetrics = (timeRange: string) => {
  const multipliers: Record<string, number> = {
    '1M': 0.3,
    '3M': 0.5,
    '6M': 0.7,
    '1Y': 1.0,
    '2Y': 1.3,
    'ALL': 1.5,
  };
  const m = multipliers[timeRange] || 1.0;
  
  return {
    var: { 
      daily: `${(2.34 * m).toFixed(2)}%`, 
      weekly: `${(5.67 * m).toFixed(2)}%`, 
      monthly: `${(12.45 * m).toFixed(2)}%` 
    },
    cvar: { 
      daily: `${(3.12 * m).toFixed(2)}%`, 
      weekly: `${(7.89 * m).toFixed(2)}%`, 
      monthly: `${(15.23 * m).toFixed(2)}%` 
    },
    beta: 0.92 + deterministicJitter(m, 0.05 * m),
    alpha: 0.0423 * m,
    trackingError: 0.0345 * Math.sqrt(m),
    informationRatio: 1.45 * Math.sqrt(m),
    treynorRatio: 0.89 * m,
    jensenAlpha: 0.0389 * m,
  };
};

const generateDrawdownData = (timeRange: string) => {
  const months: Record<string, number> = {
    '1M': 1,
    '3M': 3,
    '6M': 6,
    '1Y': 12,
    '2Y': 24,
    'ALL': 36,
  };
  const numMonths = months[timeRange] || 12;
  const data = [];
  const now = new Date();
  
  for (let i = numMonths - 1; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const phase = (i + 1) / Math.max(numMonths, 1);
    const value = -(4 + Math.abs(Math.sin((i + 1) * 1.7)) * 11) * (1 - phase * 0.5);
    data.push({
      date: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`,
      value: parseFloat(value.toFixed(1)),
    });
  }
  return data;
};

const generateCorrelationMatrix = (timeRange: string) => {
  const variance = timeRange === '1M' ? 0.05 : timeRange === 'ALL' ? 0.02 : 0.03;
  const base = [
    ['', 'QUBO', 'NIFTY', 'SENSEX', 'BANKNIFTY'],
    ['QUBO', '1.00', (0.89 + deterministicJitter(1, variance)).toFixed(2), (0.87 + deterministicJitter(2, variance)).toFixed(2), (0.92 + deterministicJitter(3, variance)).toFixed(2)],
    ['NIFTY', '', '1.00', '0.98', '0.95'],
    ['SENSEX', '', '', '1.00', '0.93'],
    ['BANKNIFTY', '', '', '', '1.00'],
  ];
  // Fill symmetric values
  for (let i = 2; i <= 4; i++) {
    base[i][1] = base[1][i];
  }
  base[3][2] = base[2][3];
  base[4][2] = base[2][4];
  base[4][3] = base[3][4];
  return base;
};

const generateFactorExposure = (timeRange: string) => {
  const volatility = timeRange === '1M' ? 0.3 : timeRange === 'ALL' ? 0.1 : 0.2;
  return [
    { factor: 'Market', exposure: 0.92 + deterministicJitter(4, volatility), tStat: 15.23 + deterministicJitter(5, 1) },
    { factor: 'Size', exposure: 0.34 + deterministicJitter(6, volatility), tStat: 4.56 + deterministicJitter(7, 0.5) },
    { factor: 'Value', exposure: -0.12 + deterministicJitter(8, volatility), tStat: -2.34 + deterministicJitter(9, 0.5) },
    { factor: 'Momentum', exposure: 0.45 + deterministicJitter(10, volatility), tStat: 6.78 + deterministicJitter(11, 0.75) },
    { factor: 'Quality', exposure: 0.23 + deterministicJitter(12, volatility), tStat: 3.45 + deterministicJitter(13, 0.5) },
    { factor: 'Volatility', exposure: -0.56 + deterministicJitter(14, volatility), tStat: -8.90 + deterministicJitter(15, 1) },
  ];
};

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('1Y');
  
  // Generate data based on selected time range
  const riskMetrics = generateRiskMetrics(timeRange);
  const drawdownData = generateDrawdownData(timeRange);
  const correlationMatrix = generateCorrelationMatrix(timeRange);
  const factorExposure = generateFactorExposure(timeRange);

  const handleExport = () => {
    toast.success(`Analytics report exported for ${timeRange} period`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
          <p className="text-[#94A3B8]">Deep dive into portfolio analytics and risk metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="border-[#1E293B] text-[#94A3B8]">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
          <Button onClick={handleExport} variant="outline" className="border-[#1E293B] text-[#94A3B8]">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </motion.div>

      {/* Time Range */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center gap-2"
      >
        {['1M', '3M', '6M', '1Y', '2Y', 'ALL'].map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              timeRange === range
                ? 'bg-gradient-to-r from-[#FF6200] to-[#FF8533] text-white'
                : 'bg-[#111827] border border-[#1E293B] text-[#94A3B8] hover:text-white'
            }`}
          >
            {range}
          </button>
        ))}
      </motion.div>

      {/* Risk Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-[#111827]/50 border-[#1E293B]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#F59E0B]" />
              Risk Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <p className="text-[#64748B] text-xs mb-1">Value at Risk (95%)</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Daily</span>
                    <span className="text-[#EF4444] font-mono">{riskMetrics.var.daily}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Weekly</span>
                    <span className="text-[#EF4444] font-mono">{riskMetrics.var.weekly}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Monthly</span>
                    <span className="text-[#EF4444] font-mono">{riskMetrics.var.monthly}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <p className="text-[#64748B] text-xs mb-1">Conditional VaR</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Daily</span>
                    <span className="text-[#EF4444] font-mono">{riskMetrics.cvar.daily}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Weekly</span>
                    <span className="text-[#EF4444] font-mono">{riskMetrics.cvar.weekly}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Monthly</span>
                    <span className="text-[#EF4444] font-mono">{riskMetrics.cvar.monthly}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <p className="text-[#64748B] text-xs mb-1">Risk Ratios</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Beta</span>
                    <span className="text-white font-mono">{riskMetrics.beta}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Alpha</span>
                    <span className="text-[#10B981] font-mono">+{(riskMetrics.alpha * 100).toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Tracking Error</span>
                    <span className="text-white font-mono">{(riskMetrics.trackingError * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <p className="text-[#64748B] text-xs mb-1">Performance Ratios</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Info Ratio</span>
                    <span className="text-[#10B981] font-mono">{riskMetrics.informationRatio}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Treynor</span>
                    <span className="text-white font-mono">{riskMetrics.treynorRatio}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#94A3B8]">Jensen Alpha</span>
                    <span className="text-[#10B981] font-mono">+{(riskMetrics.jensenAlpha * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Drawdown Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-[#111827]/50 border-[#1E293B]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#EF4444]" />
              Drawdown Analysis
            </CardTitle>
            <p className="text-sm text-[#64748B]">Portfolio drawdown over time</p>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-end gap-2">
              {drawdownData.map((d, i) => (
                <div key={i} className="flex-1 flex flex-col items-center">
                  <div 
                    className="w-full bg-gradient-to-t from-[#EF4444] to-[#F59E0B] rounded-t"
                    style={{ height: `${Math.abs(d.value) * 15}px` }}
                  />
                  <span className="text-[#64748B] text-xs mt-2">{d.date.split('-')[1]}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-4 pt-4 border-t border-[#1E293B]">
              <div>
                <p className="text-[#64748B] text-xs">Max Drawdown</p>
                <p className="text-[#EF4444] text-xl font-bold">
                  {Math.min(...drawdownData.map(d => d.value)).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-[#64748B] text-xs">Avg Drawdown</p>
                <p className="text-[#F59E0B] text-xl font-bold">
                  {(drawdownData.reduce((sum, d) => sum + d.value, 0) / drawdownData.length).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-[#64748B] text-xs">Data Points</p>
                <p className="text-white text-xl font-bold">{drawdownData.length}</p>
              </div>
              <div>
                <p className="text-[#64748B] text-xs">Period</p>
                <p className="text-[#10B981] text-xl font-bold">{timeRange}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Factor Exposure & Correlation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Factor Exposure */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-[#111827]/50 border-[#1E293B]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-[#0048B4]" />
                Factor Exposure
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {factorExposure.map((factor) => (
                  <div key={factor.factor}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white text-sm">{factor.factor}</span>
                      <div className="flex items-center gap-4">
                        <span className={`font-mono text-sm ${factor.exposure >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                          {factor.exposure >= 0 ? '+' : ''}{factor.exposure.toFixed(2)}
                        </span>
                        <span className="text-[#64748B] text-xs">t={factor.tStat.toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="h-2 bg-[#1E293B] rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${
                          factor.exposure >= 0 ? 'bg-[#10B981]' : 'bg-[#EF4444]'
                        }`}
                        style={{ 
                          width: `${Math.abs(factor.exposure) * 50}%`,
                          marginLeft: factor.exposure < 0 ? 'auto' : '0',
                          marginRight: factor.exposure >= 0 ? 'auto' : '0',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Correlation Matrix */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="bg-[#111827]/50 border-[#1E293B]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-[#FF6200]" />
                Correlation Matrix
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <tbody>
                    {correlationMatrix.map((row, i) => (
                      <tr key={i} className={i === 0 ? '' : 'border-t border-[#1E293B]/50'}>
                        {row.map((cell, j) => {
                          const value = parseFloat(cell);
                          const isHeader = i === 0 || j === 0;
                          const isDiagonal = i === j && i > 0;
                          
                          return (
                            <td 
                              key={j} 
                              className={`p-3 text-center ${
                                isHeader 
                                  ? 'text-[#94A3B8] font-medium' 
                                  : isDiagonal 
                                    ? 'text-white font-bold'
                                    : ''
                              }`}
                            >
                              {!isHeader && !isNaN(value) ? (
                                <span className={`font-mono ${
                                  value > 0.9 ? 'text-[#10B981]' :
                                  value > 0.7 ? 'text-[#F59E0B]' :
                                  'text-[#94A3B8]'
                                }`}>
                                  {cell}
                                </span>
                              ) : (
                                cell
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
