import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp } from 'lucide-react';

// Generate mock historical data
const generateChartData = () => {
  const dates = [];
  const niftyData = [];
  const qurveData = [];
  
  let niftyValue = 100;
  let qurveValue = 100;
  
  for (let i = 0; i < 252; i++) {
    const date = new Date();
    date.setDate(date.getDate() - (252 - i));
    dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    
    // NIFTY 50 simulation
    const niftyReturn = Math.sin(i * 0.23) * 0.008 + Math.cos(i * 0.07) * 0.003;
    niftyValue *= (1 + niftyReturn);
    niftyData.push(niftyValue);
    
    // Qurve portfolio simulation (outperforming)
    const qurveReturn = Math.sin(i * 0.21 + 0.4) * 0.007 + Math.cos(i * 0.09) * 0.003;
    qurveValue *= (1 + qurveReturn * 1.15); // 15% outperformance
    qurveData.push(qurveValue);
  }
  
  return { dates, niftyData, qurveData };
};

const PortfolioChart = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [timeRange, setTimeRange] = useState('1Y');
  const [hoverData, setHoverData] = useState<{x: number, y: number, nifty: number, qurve: number} | null>(null);
  
  const { dates, niftyData, qurveData } = generateChartData();
  void dates; // Suppress unused variable warning
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);
    
    // Chart dimensions
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = rect.width - padding.left - padding.right;
    const chartHeight = rect.height - padding.top - padding.bottom;
    
    // Find min/max for scaling
    const allData = [...niftyData, ...qurveData];
    const minValue = Math.min(...allData) * 0.95;
    const maxValue = Math.max(...allData) * 1.05;
    
    // Helper functions
    const getX = (index: number) => padding.left + (index / (dates.length - 1)) * chartWidth;
    const getY = (value: number) => padding.top + chartHeight - ((value - minValue) / (maxValue - minValue)) * chartHeight;
    
    // Draw grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartWidth, y);
      ctx.stroke();
      
      // Y-axis labels
      const value = maxValue - ((maxValue - minValue) / 5) * i;
      ctx.fillStyle = '#64748B';
      ctx.font = '11px Urbanist';
      ctx.textAlign = 'right';
      ctx.fillText(value.toFixed(0), padding.left - 10, y + 4);
    }
    
    // Draw X-axis labels
    const labelInterval = Math.floor(dates.length / 6);
    for (let i = 0; i < dates.length; i += labelInterval) {
      const x = getX(i);
      ctx.fillStyle = '#64748B';
      ctx.font = '11px Urbanist';
      ctx.textAlign = 'center';
      ctx.fillText(dates[i], x, rect.height - 15);
    }
    
    // Draw NIFTY 50 line
    ctx.strokeStyle = '#64748B';
    ctx.lineWidth = 2;
    ctx.beginPath();
    niftyData.forEach((value, i) => {
      const x = getX(i);
      const y = getY(value);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Draw Qurve portfolio line with gradient
    const gradient = ctx.createLinearGradient(0, padding.top, 0, rect.height - padding.bottom);
    gradient.addColorStop(0, '#7C3AED');
    gradient.addColorStop(1, '#06B6D4');
    
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 3;
    ctx.beginPath();
    qurveData.forEach((value, i) => {
      const x = getX(i);
      const y = getY(value);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Fill area under Qurve line
    ctx.fillStyle = 'rgba(124, 58, 237, 0.1)';
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(qurveData[0]));
    qurveData.forEach((value, i) => {
      ctx.lineTo(getX(i), getY(value));
    });
    ctx.lineTo(getX(qurveData.length - 1), padding.top + chartHeight);
    ctx.lineTo(getX(0), padding.top + chartHeight);
    ctx.closePath();
    ctx.fill();
    
    // Draw hover line
    if (hoverData) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(hoverData.x, padding.top);
      ctx.lineTo(hoverData.x, padding.top + chartHeight);
      ctx.stroke();
      ctx.setLineDash([]);
      
      // Draw points
      const niftyY = getY(hoverData.nifty);
      const qurveY = getY(hoverData.qurve);
      
      ctx.fillStyle = '#64748B';
      ctx.beginPath();
      ctx.arc(hoverData.x, niftyY, 5, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.fillStyle = '#7C3AED';
      ctx.beginPath();
      ctx.arc(hoverData.x, qurveY, 6, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [dates, niftyData, qurveData, hoverData]);
  
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const padding = { left: 60, right: 20 };
    const chartWidth = rect.width - padding.left - padding.right;
    
    const relativeX = x - padding.left;
    const index = Math.round((relativeX / chartWidth) * (dates.length - 1));
    
    if (index >= 0 && index < dates.length) {
      setHoverData({
        x,
        y: e.clientY - rect.top,
        nifty: niftyData[index],
        qurve: qurveData[index]
      });
    }
  };
  
  const handleMouseLeave = () => {
    setHoverData(null);
  };
  
  const timeRanges = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];
  
  const qurveReturn = ((qurveData[qurveData.length - 1] - qurveData[0]) / qurveData[0]) * 100;
  const niftyReturn = ((niftyData[niftyData.length - 1] - niftyData[0]) / niftyData[0]) * 100;
  
  return (
    <Card className="glass-card gradient-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Portfolio Performance
            </CardTitle>
            <p className="text-sm text-[#64748B] mt-1">
              Qurve Optimized vs NIFTY 50 Benchmark
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {timeRanges.map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeRange(range)}
                className={`text-xs ${
                  timeRange === range 
                    ? 'bg-primary text-primary-foreground glow-purple' 
                    : 'bg-transparent border-[#1E293B] text-[#94A3B8] hover:text-white'
                }`}
              >
                {range}
              </Button>
            ))}
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex items-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-[#7C3AED] to-[#06B6D4]"></div>
            <span className="text-sm text-white font-medium">Qurve Portfolio</span>
            <Badge className="badge-green ml-2">
              +{qurveReturn.toFixed(2)}%
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#64748B]"></div>
            <span className="text-sm text-[#94A3B8]">NIFTY 50</span>
            <Badge className="bg-[#1E293B] text-[#94A3B8] ml-2">
              +{niftyReturn.toFixed(2)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-4">
        <div className="relative">
          <canvas
            ref={canvasRef}
            className="w-full h-[300px] cursor-crosshair"
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          />
          
          {/* Hover tooltip */}
          {hoverData && (
            <div 
              className="absolute bg-card border border-border rounded-lg p-3 shadow-xl pointer-events-none"
              style={{
                left: hoverData.x + 10,
                top: hoverData.y - 50,
                transform: hoverData.x > 300 ? 'translateX(-110%)' : 'none'
              }}
            >
              <div className="text-xs text-[#94A3B8] mb-1">Portfolio Value</div>
              <div className="text-sm font-bold text-primary">
                Qurve: {hoverData.qurve.toFixed(2)}
              </div>
              <div className="text-sm text-[#64748B]">
                NIFTY: {hoverData.nifty.toFixed(2)}
              </div>
            </div>
          )}
        </div>
        
        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-[#1E293B]/50">
          <div>
            <p className="text-xs text-[#64748B]">Alpha</p>
            <p className="text-lg font-bold text-[#10B981]">+4.23%</p>
          </div>
          <div>
            <p className="text-xs text-[#64748B]">Beta</p>
            <p className="text-lg font-bold text-white">0.92</p>
          </div>
          <div>
            <p className="text-xs text-[#64748B]">Max Drawdown</p>
            <p className="text-lg font-bold text-[#EF4444]">-12.4%</p>
          </div>
          <div>
            <p className="text-xs text-[#64748B]">Information Ratio</p>
            <p className="text-lg font-bold text-primary">1.45</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PortfolioChart;
