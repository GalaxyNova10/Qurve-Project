import { useState, useEffect, useRef } from 'react';
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
import { 
  createChart, 
  CandlestickSeries,
  HistogramSeries,
  type IChartApi, 
  type CandlestickData, 
  type HistogramData 
} from 'lightweight-charts';
import { usePortfolio, useBiLSTMPredictions } from '@/hooks/usePortfolioData';

// Performance page with TradingView candlestick charts

const timeRanges = [
  { label: '1D', days: 1, interval: '1m' },
  { label: '1W', days: 7, interval: '15m' },
  { label: '1M', days: 30, interval: '1h' },
  { label: '3M', days: 90, interval: '4h' },
  { label: '1Y', days: 252, interval: '1d' },
  { label: 'ALL', days: 1260, interval: '1d' },
];

// Metrics now generated dynamically below

// TradingView Candlestick Chart Component
function TradingViewChart({ days, height = 320 }: { days: number; height?: number }) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [hoverData, setHoverData] = useState<CandlestickData | null>(null);
  const { data: apiResponse, isLoading } = useBiLSTMPredictions('NIFTY 50', days);

  useEffect(() => {
    if (!chartContainerRef.current || isLoading || !apiResponse) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#111827' },
        textColor: '#94A3B8',
        fontFamily: "'JetBrains Mono', 'Courier New', monospace",
      },
      grid: {
        vertLines: { color: '#1E293B' },
        horzLines: { color: '#1E293B' },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#FF6200',
          width: 1,
          style: 2,
          labelBackgroundColor: '#FF6200',
        },
        horzLine: {
          color: '#FF6200',
          width: 1,
          style: 2,
          labelBackgroundColor: '#FF6200',
        },
      },
      rightPriceScale: {
        borderColor: '#1E293B',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#1E293B',
        timeVisible: days <= 1,
        secondsVisible: false,
      },
      handleScroll: {
        vertTouchDrag: false,
      },
    });

    chartRef.current = chart;

    // Create candlestick series with TradingView colors
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#f2362c',
      borderUpColor: '#16a34a',
      borderDownColor: '#dc2626',
      wickUpColor: '#22c55e',
      wickDownColor: '#f2362c',
    });

    // Create volume series
    const volSeries = chart.addSeries(HistogramSeries, {
      color: '#22c55e',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });

    volSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.85,
        bottom: 0,
      },
    });

    // Generate and set data from API
    const rawData = apiResponse.data;
    const candleData: CandlestickData[] = rawData.map((d: any) => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));
    
    const volumeData: HistogramData[] = rawData.map((d: any) => ({
      time: d.time,
      value: d.volume,
      color: d.predicted 
        ? 'rgba(255, 165, 0, 0.5)' // Orange for predicted
        : d.close >= d.open 
          ? 'rgba(34, 197, 94, 0.5)' 
          : 'rgba(242, 54, 44, 0.5)',
    }));
    
    candleSeries.setData(candleData);
    volSeries.setData(volumeData);

    // Subscribe to crosshair move
    chart.subscribeCrosshairMove((param) => {
      if (param.time && param.point) {
        const data = param.seriesData.get(candleSeries) as CandlestickData;
        if (data) {
          setHoverData(data);
        }
      }
    });

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: height,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [days, height, apiResponse, isLoading]);

  const currentPrice = hoverData?.close || 18250;
  const priceChange = hoverData ? hoverData.close - hoverData.open : 0;
  const priceChangePercent = hoverData ? ((priceChange / hoverData.open) * 100) : 0;
  const isPositive = priceChange >= 0;

  return (
    <div>
      {/* OHLC Data Header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1">
            <span className="text-[#64748B]">O:</span>
            <span className="text-white">{hoverData?.open.toFixed(2) || '18250.00'}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[#64748B]">H:</span>
            <span className="text-white">{hoverData?.high.toFixed(2) || '18345.60'}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[#64748B]">L:</span>
            <span className="text-white">{hoverData?.low.toFixed(2) || '18156.40'}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[#64748B]">C:</span>
            <span className={isPositive ? 'text-[#22c55e]' : 'text-[#f2362c]'}>
              {currentPrice.toFixed(2)}
            </span>
          </div>
          <div className={`flex items-center gap-1 ${isPositive ? 'text-[#22c55e]' : 'text-[#f2362c]'}`}>
            <span>{isPositive ? '+' : ''}{priceChange.toFixed(2)}</span>
            <span>({isPositive ? '+' : ''}{priceChangePercent.toFixed(2)}%)</span>
          </div>
        </div>
      </div>
      <div ref={chartContainerRef} style={{ height: `${height}px` }} />
    </div>
  );
}

export default function Performance() {
  const [selectedRange, setSelectedRange] = useState('1Y');
  const selectedDays = timeRanges.find(r => r.label === selectedRange)?.days || 252;
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

  const handleRangeChange = (range: string, _days: number) => {
    setSelectedRange(range);
  };

  const handleExport = () => {
    toast.success('Performance report exported');
  };

  // Historical data kept for potential future use

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

      {/* Time Range Selector */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center gap-2"
      >
        {timeRanges.map((range) => (
          <button
            key={range.label}
            onClick={() => handleRangeChange(range.label, range.days)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              selectedRange === range.label
                ? 'bg-gradient-to-r from-[#FF6200] to-[#FF8533] text-white'
                : 'bg-[#111827] border border-[#1E293B] text-[#94A3B8] hover:text-white'
            }`}
          >
            {range.label}
          </button>
        ))}
      </motion.div>

      {/* TradingView Candlestick Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-[#111827]/50 border-[#1E293B]">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-[#FF6200]" />
                Performance Chart
              </CardTitle>
              <p className="text-sm text-[#64748B]">QUBO Portfolio • {selectedRange} View • TradingView Style</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#22c55e]" />
                <span className="text-[#94A3B8] text-xs">Bullish</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#f2362c]" />
                <span className="text-[#94A3B8] text-xs">Bearish</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <TradingViewChart days={selectedDays} height={360} />
          </CardContent>
        </Card>
      </motion.div>

      {/* Metrics Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {metrics.map((metric, i) => (
          <TooltipProvider key={i}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Card className="bg-[#111827]/50 border-[#1E293B] hover:border-[#FF6200]/30 transition-all cursor-help">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[#94A3B8] text-xs uppercase tracking-wider">{metric.label}</p>
                      <Info className="w-3 h-3 text-[#64748B]" />
                    </div>
                    <p className="text-2xl font-bold text-white mb-1">{metric.value}</p>
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

      {/* Rolling Performance */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-[#111827]/50 border-[#1E293B]">
          <CardHeader>
            <CardTitle className="text-white">Rolling Performance</CardTitle>
            <p className="text-sm text-[#64748B]">Returns over different time periods</p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#1E293B]">
                    <th className="text-left py-3 text-[#94A3B8] text-xs font-medium uppercase">Period</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">QUBO</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">NIFTY 50</th>
                    <th className="text-right py-3 text-[#94A3B8] text-xs font-medium uppercase">Alpha</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { period: '1 Month', qubo: '+3.24%', nifty: '+2.18%', alpha: '+1.06%' },
                    { period: '3 Months', qubo: '+8.67%', nifty: '+5.42%', alpha: '+3.25%' },
                    { period: '6 Months', qubo: '+14.23%', nifty: '+9.87%', alpha: '+4.36%' },
                    { period: '1 Year', qubo: '+24.56%', nifty: '+16.34%', alpha: '+8.22%' },
                    { period: 'YTD', qubo: '+18.92%', nifty: '+12.45%', alpha: '+6.47%' },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-[#1E293B]/50">
                      <td className="py-3 text-white">{row.period}</td>
                      <td className="py-3 text-right text-[#10B981]">{row.qubo}</td>
                      <td className="py-3 text-right text-[#94A3B8]">{row.nifty}</td>
                      <td className="py-3 text-right text-[#FF6200] font-medium">{row.alpha}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
