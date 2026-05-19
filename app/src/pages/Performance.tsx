import { motion } from 'framer-motion';
import { TrendingUp, Download, Filter, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from '@/components/ui/tooltip';
import { Info } from 'lucide-react';
import { CandlestickChart } from '@/components/CandlestickChart';
import { usePortfolio } from '@/hooks/usePortfolioData';

export default function Performance() {
  const { data: portfolio } = usePortfolio();
  
  const m = portfolio?.metrics;
  const metrics = m ? [
    { label: 'Total Return', value: `${(m.expected_return * 100).toFixed(2)}%`, change: '+8.2%', positive: m.expected_return >= 0 },
    { label: 'Volatility', value: `${(m.volatility * 100).toFixed(2)}%`, change: '-2.3%', positive: true },
    { label: 'Sharpe Ratio', value: m.sharpe_ratio.toFixed(3), change: '+0.45', positive: m.sharpe_ratio > 1.0 },
    { label: 'Sortino Ratio', value: m.sortino_ratio.toFixed(3), change: '+0.32', positive: m.sortino_ratio > 1.0 },
    { label: 'Variance', value: `${(m.variance * 10000).toFixed(2)} bps`, change: '-12 bps', positive: true },
    { label: 'Alpha', value: '4.23%', change: '+1.8%', positive: true },
    { label: 'Beta', value: '0.92', change: '-0.08', positive: true },
    { label: 'Information Ratio', value: '1.45', change: '+0.32', positive: true },
  ] : [
    { label: 'Total Return', value: '-', change: '-', positive: true },
    { label: 'Volatility', value: '-', change: '-', positive: true },
    { label: 'Sharpe Ratio', value: '-', change: '-', positive: true },
    { label: 'Sortino Ratio', value: '-', change: '-', positive: true },
  ];

  const handleExport = () => {
    toast.success('Performance report exported');
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
          <h1 className="text-3xl font-bold text-white">Performance</h1>
          <p className="text-[#94A3B8]">Detailed portfolio performance analysis</p>
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

      {/* Metrics Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3"
      >
        {metrics.map((metric, i) => (
          <TooltipProvider key={i}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Card className="bg-[#111827]/50 border-[#1E293B] hover:border-primary/30 transition-all cursor-help">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[#94A3B8] text-xs uppercase tracking-wider">{metric.label}</p>
                      <Info className="w-3 h-3 text-[#64748B]" />
                    </div>
                    <p className="text-xl font-bold text-white mb-1">{metric.value}</p>
                    <div className={`flex items-center gap-1 text-xs ${metric.positive ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {metric.positive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      <span>{metric.change}</span>
                    </div>
                  </CardContent>
                </Card>
              </TooltipTrigger>
              <TooltipContent className="bg-[#1e293b] border-[#334155] text-white text-[10px] max-w-[200px]">
                {metric.label === 'Total Return' && "Overall return on investment since inception."}
                {metric.label === 'Volatility' && "Measurement of the dispersion of returns. Lower indicates more stability."}
                {metric.label === 'Sharpe Ratio' && "Reward-to-volatility ratio. Above 1.0 is a typical threshold for success."}
                {metric.label === 'Sortino Ratio' && "Similar to Sharpe, but only considers harmful downside volatility."}
                {metric.label === 'Variance' && "The expectation of the squared deviation of a random variable from its mean."}
                {metric.label === 'Alpha' && "Active return on an investment, gauges performance against a market index."}
                {metric.label === 'Beta' && "Relative volatility of an investment compared to the overall market."}
                {metric.label === 'Information Ratio' && "Consistency of active returns, measuring the manager's ability to generate excess returns."}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* TradingView Candlestick Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-6 h-full"
        >
          <CandlestickChart
            title="Performance Chart"
            symbol="QURVE-NIFTY OPTIMIZED"
            height={420}
            showTimeframes={true}
          />
        </motion.div>

      {/* Rolling Performance */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="lg:col-span-6 flex-1 flex flex-col"
      >
        <Card className="bg-[#111827]/50 border-[#1E293B] flex-1 flex flex-col">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Rolling Performance
            </CardTitle>
            <p className="text-sm text-[#64748B]">Returns over different time periods</p>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#1E293B]">
                    <th className="text-left py-3 text-[#94A3B8] text-xs font-medium uppercase">Period</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">Qurve</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">NIFTY 50</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">Alpha</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { period: '1 Month', qurve: '+3.24%', nifty: '+2.18%', alpha: '+1.06%' },
                    { period: '3 Months', qurve: '+8.67%', nifty: '+5.42%', alpha: '+3.25%' },
                    { period: '6 Months', qurve: '+14.23%', nifty: '+9.87%', alpha: '+4.36%' },
                    { period: '1 Year', qurve: '+24.56%', nifty: '+16.34%', alpha: '+8.22%' },
                    { period: 'YTD', qurve: '+18.92%', nifty: '+12.45%', alpha: '+6.47%' },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-[#1E293B]/50">
                      <td className="py-3 text-white">{row.period}</td>
                      <td className="py-3 text-right text-[#10B981]">{row.qurve}</td>
                      <td className="py-3 text-right text-[#94A3B8]">{row.nifty}</td>
                      <td className="py-3 text-right text-primary font-medium">{row.alpha}</td>
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
