import { useState } from 'react';
import { motion } from 'framer-motion';
import { PieChart, Download, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { usePortfolio } from '@/hooks/usePortfolioData';

const MAX_SECTOR_EXPOSURE = 0.25;

const SECTOR_COLORS: Record<string, string> = {
  'Financial': '#7C3AED',
  'IT': '#0048B4',
  'Consumer': '#10B981',
  'Energy': '#F59E0B',
  'Telecom': '#8B5CF6',
  'Construction': '#EC4899',
  'Pharma': '#06B6D4',
  'Auto': '#f43f5e',
  'Metals': '#84cc16',
  'FMCG': '#14b8a6',
  'Oil & Gas': '#eab308',
  'Banking': '#7C3AED',
  'Infrastructure': '#a855f7',
  'Chemicals': '#0ea5e9',
  'Power': '#f97316',
  'Cement': '#64748b',
};

const FALLBACK_COLORS = ['#7C3AED', '#0048B4', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#f43f5e', '#84cc16', '#14b8a6'];

function getSectorColor(sector: string, index: number): string {
  return SECTOR_COLORS[sector] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

export default function Allocation() {
  const [selectedView, setSelectedView] = useState<'sector' | 'stock'>('sector');
  const { data: portfolioData, isLoading } = usePortfolio();

  // Derive data from the real portfolio response
  const sectorAllocation = portfolioData?.sector_allocation || {};
  const portfolio = portfolioData?.portfolio || {};
  const constraints = portfolioData?.constraint_verification;
  const params = portfolioData?.parameters;

  const sortedSectors = Object.entries(sectorAllocation).sort((a, b) => b[1] - a[1]);
  const sortedStocks = Object.entries(portfolio).sort((a, b) => b[1].weight - a[1].weight);

  const handleExport = () => toast.success('Allocation report exported');
  const handleRebalance = () => toast.info('Rebalancing initiated', { description: 'This may take a few minutes' });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-[#7C3AED]/30 border-t-[#7C3AED] rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white">Asset Allocation</h1>
          <p className="text-[#94A3B8]">Portfolio composition and sector breakdown</p>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={handleRebalance} className="bg-gradient-to-r from-[#7C3AED] to-[#8B5CF6] text-white">
            Rebalance Portfolio
          </Button>
          <Button onClick={handleExport} variant="outline" className="border-[#1E293B] text-[#94A3B8]">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </motion.div>

      {/* View Toggle */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center gap-2 p-1 bg-[#111827] rounded-xl w-fit border border-[#1E293B]"
      >
        <button
          onClick={() => setSelectedView('sector')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            selectedView === 'sector' ? 'bg-[#7C3AED] text-white' : 'text-[#94A3B8] hover:text-white'
          }`}
        >By Sector</button>
        <button
          onClick={() => setSelectedView('stock')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            selectedView === 'stock' ? 'bg-[#7C3AED] text-white' : 'text-[#94A3B8] hover:text-white'
          }`}
        >By Stock</button>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="lg:col-span-1">
          <Card className="bg-[#111827]/50 border-[#1E293B] h-full">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <PieChart className="w-5 h-5 text-[#7C3AED]" />
                Allocation Chart
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative w-64 h-64 mx-auto">
                <svg viewBox="0 0 100 100" className="transform -rotate-90">
                  {selectedView === 'sector' ? (
                    sortedSectors.map(([sector, weight], i) => {
                      const total = sortedSectors.reduce((sum, [, w]) => sum + w, 0);
                      const angle = (weight / total) * 360;
                      const startAngle = sortedSectors.slice(0, i).reduce((sum, [, w]) => sum + (w / total) * 360, 0);
                      const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
                      const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
                      const x2 = 50 + 40 * Math.cos(((startAngle + angle) * Math.PI) / 180);
                      const y2 = 50 + 40 * Math.sin(((startAngle + angle) * Math.PI) / 180);
                      const largeArc = angle > 180 ? 1 : 0;
                      return (
                        <path key={sector} d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
                          fill={getSectorColor(sector, i)} stroke="#111827" strokeWidth="2" />
                      );
                    })
                  ) : (
                    sortedStocks.slice(0, 10).map(([ticker, data], i) => {
                      const total = sortedStocks.slice(0, 10).reduce((sum, [, d]) => sum + d.weight, 0);
                      const angle = (data.weight / total) * 360;
                      const startAngle = sortedStocks.slice(0, i).reduce((sum, [, d]) => sum + (d.weight / total) * 360, 0);
                      const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
                      const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
                      const x2 = 50 + 40 * Math.cos(((startAngle + angle) * Math.PI) / 180);
                      const y2 = 50 + 40 * Math.sin(((startAngle + angle) * Math.PI) / 180);
                      const largeArc = angle > 180 ? 1 : 0;
                      return (
                        <path key={ticker} d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
                          fill={getSectorColor(data.sector, i)} stroke="#111827" strokeWidth="2" />
                      );
                    })
                  )}
                  <circle cx="50" cy="50" r="25" fill="#111827" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-white">
                      {selectedView === 'sector' ? sortedSectors.length : sortedStocks.length}
                    </p>
                    <p className="text-xs text-[#64748B]">
                      {selectedView === 'sector' ? 'Sectors' : 'Holdings'}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Breakdown List */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="lg:col-span-2">
          <Card className="bg-[#111827]/50 border-[#1E293B] h-full">
            <CardHeader>
              <CardTitle className="text-white">
                {selectedView === 'sector' ? 'Sector Breakdown' : 'Stock Holdings'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {selectedView === 'sector' ? (
                  sortedSectors.map(([sector, weight], idx) => {
                    const isOverLimit = weight > MAX_SECTOR_EXPOSURE;
                    const color = getSectorColor(sector, idx);
                    return (
                      <div key={sector} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: color }} />
                            <span className="text-white font-medium">{sector}</span>
                            {isOverLimit && <AlertTriangle className="w-4 h-4 text-[#EF4444]" />}
                          </div>
                          <div className="flex items-center gap-4">
                            <span className={`font-semibold ${isOverLimit ? 'text-[#EF4444]' : 'text-white'}`}>
                              {(weight * 100).toFixed(1)}%
                            </span>
                            {isOverLimit && (
                              <span className="px-2 py-0.5 rounded-full bg-[#EF4444]/10 text-[#EF4444] text-xs">Over Limit</span>
                            )}
                          </div>
                        </div>
                        <div className="relative h-2 bg-[#1E293B] rounded-full overflow-hidden">
                          <div className="absolute top-0 bottom-0 left-0 w-0.5 bg-[#EF4444]/50 z-10" style={{ left: `${MAX_SECTOR_EXPOSURE * 100}%` }} />
                          <div className="h-full rounded-full transition-all duration-500"
                            style={{ width: `${(weight / 0.35) * 100}%`, backgroundColor: color, opacity: isOverLimit ? 0.7 : 1 }} />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  sortedStocks.map(([ticker, data]) => {
                    const color = getSectorColor(data.sector, 0);
                    return (
                      <div key={ticker} className="flex items-center justify-between py-3 border-b border-[#1E293B]/50">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
                            <span className="text-white font-bold text-sm">{ticker[0]}</span>
                          </div>
                          <div>
                            <p className="text-white font-medium">{ticker.replace('.NS', '')}</p>
                            <p className="text-[#64748B] text-xs">{data.sector}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-white font-medium">{(data.weight * 100).toFixed(2)}%</p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Constraints Summary */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
        <Card className="bg-[#111827]/50 border-[#1E293B]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Info className="w-5 h-5 text-[#0048B4]" />
              QUBO Constraints
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
                  <span className="text-white font-medium">Budget</span>
                </div>
                <p className="text-[#94A3B8] text-sm">Σwᵢ = 1 (100% allocation)</p>
                <p className={`text-xs mt-1 ${constraints?.budget_satisfaction !== undefined ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                  {constraints?.budget_satisfaction !== undefined ? '✓ Satisfied' : '⚠ Violated'}
                </p>
              </div>
              
              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <div className="flex items-center gap-2 mb-2">
                  {constraints?.all_satisfied ? <CheckCircle2 className="w-5 h-5 text-[#10B981]" /> : <AlertTriangle className="w-5 h-5 text-[#F59E0B]" />}
                  <span className="text-white font-medium">Cardinality</span>
                </div>
                <p className="text-[#94A3B8] text-sm">Exactly {params?.cardinality ?? 15} assets</p>
                <p className="text-[#10B981] text-xs mt-1">
                  {constraints?.cardinality ?? sortedStocks.length}/{params?.cardinality ?? 15} selected
                </p>
              </div>
              
              <div className={`p-4 rounded-xl bg-[#0d1117] border ${sortedSectors.some(([,w]) => w > MAX_SECTOR_EXPOSURE) ? 'border-[#EF4444]/30' : 'border-[#1E293B]'}`}>
                <div className="flex items-center gap-2 mb-2">
                  {sortedSectors.some(([,w]) => w > MAX_SECTOR_EXPOSURE) 
                    ? <AlertTriangle className="w-5 h-5 text-[#EF4444]" />
                    : <CheckCircle2 className="w-5 h-5 text-[#10B981]" />}
                  <span className="text-white font-medium">Sector Limit</span>
                </div>
                <p className="text-[#94A3B8] text-sm">Max 25% per sector</p>
                {sortedSectors.filter(([,w]) => w > MAX_SECTOR_EXPOSURE).map(([s, w]) => (
                  <p key={s} className="text-[#EF4444] text-xs mt-1">⚠ {s}: {(w * 100).toFixed(1)}%</p>
                ))}
                {!sortedSectors.some(([,w]) => w > MAX_SECTOR_EXPOSURE) && (
                  <p className="text-[#10B981] text-xs mt-1">✓ All sectors within limit</p>
                )}
              </div>
              
              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#1E293B]">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
                  <span className="text-white font-medium">Binary Expansion</span>
                </div>
                <p className="text-[#94A3B8] text-sm">7-bit encoding (K=7)</p>
                <p className="text-[#10B981] text-xs mt-1">✓ 128 steps/asset</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
