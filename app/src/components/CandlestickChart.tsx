import { useEffect, useRef, useState } from 'react';
import { 
  createChart, 
  CandlestickSeries,
  HistogramSeries,
  type IChartApi, 
  type CandlestickData, 
  type HistogramData 
} from 'lightweight-charts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useBiLSTMPredictions } from '@/hooks/usePortfolioData';

interface CandlestickChartProps {
  title?: string;
  symbol?: string;
  height?: number;
}



export function CandlestickChart({ title = 'Price Chart', symbol = 'NIFTY 50', height = 400 }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [hoverData, setHoverData] = useState<CandlestickData | null>(null);
  
  const { data: apiResponse, isLoading } = useBiLSTMPredictions(symbol);

  useEffect(() => {
    if (!chartContainerRef.current || isLoading || !apiResponse) return;

    // Create chart with Bloomberg Terminal styling
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#161b22' },
        textColor: '#7d8590',
        fontFamily: "'Courier New', monospace",
      },
      grid: {
        vertLines: { color: '#21262d' },
        horzLines: { color: '#21262d' },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#ff6b35',
          width: 1,
          style: 2,
          labelBackgroundColor: '#ff6b35',
        },
        horzLine: {
          color: '#ff6b35',
          width: 1,
          style: 2,
          labelBackgroundColor: '#ff6b35',
        },
      },
      rightPriceScale: {
        borderColor: '#21262d',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#21262d',
        timeVisible: true,
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
  }, [height, apiResponse, isLoading]);

  const currentPrice = hoverData?.close || 2456.80;
  const priceChange = hoverData ? hoverData.close - hoverData.open : 12.50;
  const priceChangePercent = hoverData ? ((priceChange / hoverData.open) * 100) : 0.51;
  const isPositive = priceChange >= 0;

  return (
    <Card className="bg-terminal-card border-terminal-border overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between py-3 px-4 border-b border-terminal-border">
        <div className="flex items-center gap-4">
          <CardTitle className="text-terminal-text text-sm font-semibold tracking-wide">
            {title}
          </CardTitle>
          <span className="text-terminal-muted text-xs">{symbol}</span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-terminal-muted">O:</span>
            <span className="text-terminal-text">{hoverData?.open.toFixed(2) || '2456.80'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-terminal-muted">H:</span>
            <span className="text-terminal-text">{hoverData?.high.toFixed(2) || '2478.90'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-terminal-muted">L:</span>
            <span className="text-terminal-text">{hoverData?.low.toFixed(2) || '2434.50'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-terminal-muted">C:</span>
            <span className={isPositive ? 'text-tv-green' : 'text-tv-red'}>
              {currentPrice.toFixed(2)}
            </span>
          </div>
          <div className={`flex items-center gap-1 ${isPositive ? 'text-tv-green' : 'text-tv-red'}`}>
            <span>{isPositive ? '+' : ''}{priceChange.toFixed(2)}</span>
            <span>({isPositive ? '+' : ''}{priceChangePercent.toFixed(2)}%)</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div ref={chartContainerRef} style={{ height: `${height}px` }} />
      </CardContent>
    </Card>
  );
}

export default CandlestickChart;
