import { useEffect, useRef, useState, useCallback } from 'react';
import { 
  createChart, 
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  type IChartApi, 
  type CandlestickData, 
  type HistogramData,
  type LineData,
  type ISeriesApi,
  LineStyle,
} from 'lightweight-charts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useBiLSTMWithIndicators } from '@/hooks/usePortfolioData';
import { ChevronDown, BarChart3 } from 'lucide-react';

interface CandlestickChartProps {
  title?: string;
  symbol?: string;
  height?: number;
  showTimeframes?: boolean;
}

const TIME_RANGES = [
  { label: '1D', days: 1 },
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1Y', days: 252 },
  { label: 'ALL', days: 1260 },
];

const INDICATOR_PRESETS = [
  { id: 'sma', label: 'SMA 20/50', overlays: ['sma20', 'sma50'] },
  { id: 'ema', label: 'EMA 9/21', overlays: ['ema9', 'ema21'] },
  { id: 'bb', label: 'Bollinger', overlays: ['bb_upper', 'bb_mid', 'bb_lower'] },
  { id: 'vwap', label: 'VWAP', overlays: ['vwap'] },
  { id: 'supertrend', label: 'Supertrend', overlays: ['supertrend'] },
  { id: 'rsi', label: 'RSI(14)', overlays: [] },
  { id: 'macd', label: 'MACD', overlays: [] },
];

const OVERLAY_COLORS: Record<string, string> = {
  sma20: '#7C3AED',
  sma50: '#3B82F6',
  ema9: '#06B6D4',
  ema21: '#A855F7',
  bb_upper: 'rgba(59,130,246,0.3)',
  bb_mid: 'rgba(59,130,246,0.6)',
  bb_lower: 'rgba(59,130,246,0.3)',
  vwap: '#10B981',
  supertrend: '#EF4444',
};

export function CandlestickChart({ 
  title = 'Predictive Alpha', 
  symbol = 'QURVE-NIFTY OPTIMIZED', 
  height = 400,
  showTimeframes = true,
}: CandlestickChartProps) {
  const mainChartRef = useRef<HTMLDivElement>(null);
  const rsiChartRef = useRef<HTMLDivElement>(null);
  const macdChartRef = useRef<HTMLDivElement>(null);
  const chartApiRef = useRef<IChartApi | null>(null);
  const rsiApiRef = useRef<IChartApi | null>(null);
  const macdApiRef = useRef<IChartApi | null>(null);

  const [hoverData, setHoverData] = useState<CandlestickData | null>(null);
  const [selectedRange, setSelectedRange] = useState('1Y');
  const [activeIndicators, setActiveIndicators] = useState<Set<string>>(new Set(['sma']));
  const [showIndicatorMenu, setShowIndicatorMenu] = useState(false);

  const days = TIME_RANGES.find(r => r.label === selectedRange)?.days || 252;
  const { data: apiResponse, isLoading } = useBiLSTMWithIndicators(symbol, days);

  const showRSI = activeIndicators.has('rsi');
  const showMACD = activeIndicators.has('macd');

  const toggleIndicator = useCallback((id: string) => {
    setActiveIndicators(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  // Build charts
  useEffect(() => {
    if (!mainChartRef.current || isLoading || !apiResponse?.data?.length) return;

    const rawData = apiResponse.data;
    const indicators = apiResponse.indicators || {};

    // ── MAIN CHART ──
    const chart = createChart(mainChartRef.current, {
      layout: { background: { color: '#0B0E14' }, textColor: '#94A3B8', fontFamily: "'JetBrains Mono', monospace" },
      grid: { vertLines: { color: 'rgba(255, 255, 255, 0.05)' }, horzLines: { color: 'rgba(255, 255, 255, 0.05)' } },
      crosshair: {
        mode: 1,
        vertLine: { color: '#7C3AED', width: 1, style: 2, labelBackgroundColor: '#7C3AED' },
        horzLine: { color: '#7C3AED', width: 1, style: 2, labelBackgroundColor: '#7C3AED' },
      },
      rightPriceScale: { borderColor: 'rgba(255, 255, 255, 0.08)', scaleMargins: { top: 0.05, bottom: 0.2 } },
      timeScale: { borderColor: 'rgba(255, 255, 255, 0.08)', timeVisible: days <= 7, secondsVisible: false },
      handleScroll: { vertTouchDrag: false },
    });
    chartApiRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10B981', downColor: '#EF4444',
      borderUpColor: '#10B981', borderDownColor: '#EF4444',
      wickUpColor: '#10B981', wickDownColor: '#EF4444',
    });

    const candleData: CandlestickData[] = rawData.map((d: any) => ({
      time: d.time, open: d.open, high: d.high, low: d.low, close: d.close,
    }));
    candleSeries.setData(candleData);

    // Volume
    const volSeries = chart.addSeries(HistogramSeries, {
      color: '#10B981', priceFormat: { type: 'volume' }, priceScaleId: 'vol',
    });
    volSeries.priceScale().applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });
    const volumeData: HistogramData[] = rawData.map((d: any) => ({
      time: d.time, value: d.volume,
      color: d.predicted ? 'rgba(124,58,237,0.4)' : d.close >= d.open ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.35)',
    }));
    volSeries.setData(volumeData);

    // ── OVERLAY INDICATORS ──
    const overlaySeries: ISeriesApi<any>[] = [];
    for (const preset of INDICATOR_PRESETS) {
      if (!activeIndicators.has(preset.id)) continue;
      for (const key of preset.overlays) {
        const values = indicators[key];
        if (!values) continue;
        const color = OVERLAY_COLORS[key] || '#94A3B8';
        const isSuper = key === 'supertrend';
        const isBB = key.startsWith('bb_');
        const series = chart.addSeries(LineSeries, {
          color, lineWidth: isBB ? 1 : 2,
          lineStyle: isBB && key !== 'bb_mid' ? LineStyle.Dashed : LineStyle.Solid,
          crosshairMarkerVisible: false, priceLineVisible: false, lastValueVisible: false,
        });
        const lineData: LineData[] = [];
        for (let i = 0; i < rawData.length && i < values.length; i++) {
          if (values[i] !== null && values[i] !== undefined) {
            if (isSuper) {
              (series as any).applyOptions?.({
                color: (indicators.supertrend_direction?.[i] ?? 1) === 1 ? '#10B981' : '#EF4444',
              });
            }
            lineData.push({ time: rawData[i].time, value: values[i] });
          }
        }
        series.setData(lineData);
        overlaySeries.push(series);
      }
    }

    // Crosshair
    chart.subscribeCrosshairMove((param) => {
      if (param.time && param.point) {
        const data = param.seriesData.get(candleSeries) as CandlestickData;
        if (data) setHoverData(data);
      }
    });
    chart.timeScale().fitContent();

    // ── RSI CHART ──
    let rsiChart: IChartApi | null = null;
    if (showRSI && rsiChartRef.current && indicators.rsi) {
      rsiChart = createChart(rsiChartRef.current, {
        layout: { background: { color: '#0B0E14' }, textColor: '#94A3B8', fontFamily: "'JetBrains Mono', monospace" },
        grid: { vertLines: { color: 'rgba(255, 255, 255, 0.05)' }, horzLines: { color: 'rgba(255, 255, 255, 0.05)' } },
        rightPriceScale: { borderColor: 'rgba(255, 255, 255, 0.08)', scaleMargins: { top: 0.1, bottom: 0.1 } },
        timeScale: { visible: !showMACD, borderColor: 'rgba(255, 255, 255, 0.08)' },
        crosshair: { mode: 1, vertLine: { color: '#7C3AED', width: 1, style: 2, labelBackgroundColor: '#7C3AED' }, horzLine: { color: '#7C3AED', width: 1, style: 2, labelBackgroundColor: '#7C3AED' } },
        handleScroll: { vertTouchDrag: false },
      });
      rsiApiRef.current = rsiChart;
      const rsiLine = rsiChart.addSeries(LineSeries, { color: '#A78BFA', lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
      const rsiData: LineData[] = [];
      for (let i = 0; i < rawData.length && i < indicators.rsi.length; i++) {
        if (indicators.rsi[i] !== null) rsiData.push({ time: rawData[i].time, value: indicators.rsi[i] });
      }
      rsiLine.setData(rsiData);
      // 70/30 lines
      const ob = rsiChart.addSeries(LineSeries, { color: 'rgba(239,68,68,0.3)', lineWidth: 1, lineStyle: LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      const os = rsiChart.addSeries(LineSeries, { color: 'rgba(16,185,129,0.3)', lineWidth: 1, lineStyle: LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      ob.setData(rsiData.map(d => ({ time: d.time, value: 70 })));
      os.setData(rsiData.map(d => ({ time: d.time, value: 30 })));
      rsiChart.timeScale().fitContent();
    }

    // ── MACD CHART ──
    let macdChart: IChartApi | null = null;
    if (showMACD && macdChartRef.current && indicators.macd_line) {
      macdChart = createChart(macdChartRef.current, {
        layout: { background: { color: '#0B0E14' }, textColor: '#94A3B8', fontFamily: "'JetBrains Mono', monospace" },
        grid: { vertLines: { color: 'rgba(255, 255, 255, 0.05)' }, horzLines: { color: 'rgba(255, 255, 255, 0.05)' } },
        rightPriceScale: { borderColor: 'rgba(255, 255, 255, 0.08)', scaleMargins: { top: 0.1, bottom: 0.1 } },
        timeScale: { borderColor: 'rgba(255, 255, 255, 0.08)' },
        crosshair: { mode: 1, vertLine: { color: '#7C3AED', width: 1, style: 2, labelBackgroundColor: '#7C3AED' }, horzLine: { color: '#7C3AED', width: 1, style: 2, labelBackgroundColor: '#7C3AED' } },
        handleScroll: { vertTouchDrag: false },
      });
      macdApiRef.current = macdChart;
      const macdLine = macdChart.addSeries(LineSeries, { color: '#3B82F6', lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
      const signalLine = macdChart.addSeries(LineSeries, { color: '#06B6D4', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
      const histSeries = macdChart.addSeries(HistogramSeries, { priceScaleId: '', priceLineVisible: false, lastValueVisible: false });

      const ml: LineData[] = [], sl: LineData[] = [], hl: HistogramData[] = [];
      for (let i = 0; i < rawData.length; i++) {
        const t = rawData[i].time;
        if (indicators.macd_line[i] !== null) ml.push({ time: t, value: indicators.macd_line[i] });
        if (indicators.macd_signal[i] !== null) sl.push({ time: t, value: indicators.macd_signal[i] });
        if (indicators.macd_histogram[i] !== null) hl.push({ time: t, value: indicators.macd_histogram[i], color: indicators.macd_histogram[i] >= 0 ? 'rgba(16,185,129,0.6)' : 'rgba(239,68,68,0.6)' });
      }
      macdLine.setData(ml); signalLine.setData(sl); histSeries.setData(hl);
      macdChart.timeScale().fitContent();
    }

    // Resize handler
    const handleResize = () => {
      if (mainChartRef.current) chart.applyOptions({ width: mainChartRef.current.clientWidth, height });
      if (rsiChart && rsiChartRef.current) rsiChart.applyOptions({ width: rsiChartRef.current.clientWidth, height: 120 });
      if (macdChart && macdChartRef.current) macdChart.applyOptions({ width: macdChartRef.current.clientWidth, height: 120 });
    };
    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      rsiChart?.remove();
      macdChart?.remove();
    };
  }, [height, apiResponse, isLoading, activeIndicators, days, showRSI, showMACD]);

  const currentPrice = hoverData?.close || 0;
  const priceChange = hoverData ? hoverData.close - hoverData.open : 0;
  const priceChangePct = hoverData ? ((priceChange / hoverData.open) * 100) : 0;
  const isPositive = priceChange >= 0;

  return (
    <Card className="bg-card border-border overflow-hidden">
      {/* ── HEADER ── */}
      <CardHeader className="py-2 px-4 border-b border-border">
        <div className="flex items-center justify-between flex-wrap gap-2">
          {/* Left: Title + OHLC */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              <CardTitle className="text-foreground text-sm font-semibold tracking-wide">{title}</CardTitle>
              <span className="text-muted-foreground text-xs">{symbol}</span>
            </div>
            {hoverData && (
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="text-muted-foreground">O:<span className="text-foreground ml-1">{hoverData.open.toFixed(2)}</span></span>
                <span className="text-muted-foreground">H:<span className="text-foreground ml-1">{hoverData.high.toFixed(2)}</span></span>
                <span className="text-muted-foreground">L:<span className="text-foreground ml-1">{hoverData.low.toFixed(2)}</span></span>
                <span className="text-muted-foreground">C:<span className={isPositive ? 'text-[#10B981] ml-1' : 'text-[#EF4444] ml-1'}>{currentPrice.toFixed(2)}</span></span>
                <span className={isPositive ? 'text-[#10B981]' : 'text-[#EF4444]'}>
                  {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{priceChangePct.toFixed(2)}%)
                </span>
              </div>
            )}
          </div>

          {/* Right: Timeframes + Indicators */}
          <div className="flex items-center gap-2">
            {showTimeframes && TIME_RANGES.map(r => (
              <button key={r.label} onClick={() => setSelectedRange(r.label)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                  selectedRange === r.label ? 'bg-primary text-primary-foreground glow-purple' : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }`}
              >{r.label}</button>
            ))}
            <div className="relative">
              <button onClick={() => setShowIndicatorMenu(!showIndicatorMenu)}
                className="flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-all border border-border"
              >Indicators <ChevronDown className="w-3 h-3" /></button>
              {showIndicatorMenu && (
                <div className="absolute right-0 top-8 z-50 bg-card border border-border rounded-lg shadow-xl py-1 min-w-[180px]">
                  {INDICATOR_PRESETS.map(p => (
                    <button key={p.id} onClick={() => toggleIndicator(p.id)}
                      className="flex items-center justify-between w-full px-3 py-2 text-xs hover:bg-muted transition-colors"
                    >
                      <span className="text-foreground">{p.label}</span>
                      <span className={`w-3 h-3 rounded-sm border ${activeIndicators.has(p.id) ? 'bg-primary border-primary' : 'border-border'}`} />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardHeader>

      {/* ── CHARTS ── */}
      <CardContent className="p-0">
        {isLoading ? (
          <div className="flex items-center justify-center" style={{ height }}>
            <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : (
          <>
            <div ref={mainChartRef} style={{ height: `${height}px` }} />
            {showRSI && <div className="border-t border-border">
              <div className="px-3 py-1 text-[10px] text-muted-foreground font-mono bg-[#0B0E14]">RSI(14)</div>
              <div ref={rsiChartRef} style={{ height: '120px' }} />
            </div>}
            {showMACD && <div className="border-t border-border">
              <div className="px-3 py-1 text-[10px] text-muted-foreground font-mono bg-[#0B0E14]">MACD(12,26,9)</div>
              <div ref={macdChartRef} style={{ height: '120px' }} />
            </div>}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default CandlestickChart;
