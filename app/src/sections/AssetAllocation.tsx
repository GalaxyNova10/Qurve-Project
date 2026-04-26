import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart } from 'lucide-react';

interface Portfolio {
  [key: string]: {
    weight: number;
    sector: string;
  };
}

interface AssetAllocationProps {
  portfolio: Portfolio;
}

const AssetAllocation = ({ portfolio }: AssetAllocationProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredSegment, setHoveredSegment] = useState<number | null>(null);
  
  // Sort by weight and get top holdings
  const sortedHoldings = Object.entries(portfolio)
    .sort((a, b) => b[1].weight - a[1].weight)
    .slice(0, 8);
  
  const totalWeight = sortedHoldings.reduce((sum, [, data]) => sum + data.weight, 0);
  
  // Colors for segments
  const colors = [
    '#FF6200', '#0048B4', '#10B981', '#8B5CF6',
    '#F59E0B', '#EC4899', '#06B6D4', '#84CC16'
  ];
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    ctx.clearRect(0, 0, rect.width, rect.height);
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const radius = Math.min(centerX, centerY) - 20;
    const innerRadius = radius * 0.6;
    
    let currentAngle = -Math.PI / 2;
    
    sortedHoldings.forEach(([, data], index) => {
      const sliceAngle = (data.weight / totalWeight) * 2 * Math.PI;
      const endAngle = currentAngle + sliceAngle;
      
      // Draw segment
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, currentAngle, endAngle);
      ctx.arc(centerX, centerY, innerRadius, endAngle, currentAngle, true);
      ctx.closePath();
      
      const isHovered = hoveredSegment === index;
      ctx.fillStyle = colors[index % colors.length];
      ctx.globalAlpha = isHovered ? 1 : 0.85;
      ctx.fill();
      
      // Border
      ctx.strokeStyle = '#111827';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // Glow effect on hover
      if (isHovered) {
        ctx.shadowColor = colors[index % colors.length];
        ctx.shadowBlur = 20;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }
      
      ctx.globalAlpha = 1;
      currentAngle = endAngle;
    });
    
    // Center text
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 20px Urbanist';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${sortedHoldings.length}`, centerX, centerY - 10);
    
    ctx.fillStyle = '#94A3B8';
    ctx.font = '12px Urbanist';
    ctx.fillText('Holdings', centerX, centerY + 10);
  }, [sortedHoldings, totalWeight, hoveredSegment]);
  
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    const dx = x - centerX;
    const dy = y - centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const radius = Math.min(centerX, centerY) - 20;
    const innerRadius = radius * 0.6;
    
    if (distance >= innerRadius && distance <= radius) {
      let angle = Math.atan2(dy, dx) + Math.PI / 2;
      if (angle < 0) angle += 2 * Math.PI;
      
      let currentAngle = 0;
      for (let i = 0; i < sortedHoldings.length; i++) {
        const [, data] = sortedHoldings[i];
        const sliceAngle = (data.weight / totalWeight) * 2 * Math.PI;
        
        if (angle >= currentAngle && angle < currentAngle + sliceAngle) {
          setHoveredSegment(i);
          return;
        }
        currentAngle += sliceAngle;
      }
    }
    
    setHoveredSegment(null);
  };
  
  return (
    <Card className="glass-card gradient-border h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-white text-lg flex items-center gap-2">
          <PieChart className="w-5 h-5 text-[#0048B4]" />
          Asset Allocation
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="relative">
          <canvas
            ref={canvasRef}
            className="w-full h-[200px] cursor-pointer"
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setHoveredSegment(null)}
          />
          
          {hoveredSegment !== null && (
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
              <p className="text-lg font-bold text-white">
                {(sortedHoldings[hoveredSegment][1].weight * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-[#94A3B8]">
                {sortedHoldings[hoveredSegment][0].replace('.NS', '')}
              </p>
            </div>
          )}
        </div>
        
        {/* Holdings List */}
        <div className="mt-4 space-y-2 max-h-[180px] overflow-y-auto">
          {sortedHoldings.map(([ticker, data], index) => (
            <div 
              key={ticker}
              className={`flex items-center justify-between p-2 rounded-lg transition-all ${
                hoveredSegment === index 
                  ? 'bg-[#FF6200]/10' 
                  : 'hover:bg-[#1E293B]/50'
              }`}
              onMouseEnter={() => setHoveredSegment(index)}
              onMouseLeave={() => setHoveredSegment(null)}
            >
              <div className="flex items-center gap-3">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <div>
                  <p className="text-sm font-medium text-white">
                    {ticker.replace('.NS', '')}
                  </p>
                  <p className="text-xs text-[#64748B]">{data.sector}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-white">
                  {(data.weight * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default AssetAllocation;
