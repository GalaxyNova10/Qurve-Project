import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface SectorAllocation {
  [key: string]: number;
}

interface SectorBreakdownProps {
  sectors: SectorAllocation;
}

const MAX_SECTOR_EXPOSURE = 0.25; // 25% max

const sectorColors: { [key: string]: string } = {
  'Financial': '#7C3AED',
  'IT': '#0048B4',
  'Consumer': '#10B981',
  'Energy': '#F59E0B',
  'Telecom': '#8B5CF6',
  'Construction': '#EC4899',
  'Pharma': '#06B6D4',
  'Auto': '#84CC16',
  'Metals': '#6366F1',
  'Cement': '#14B8A6',
  'Diversified': '#F97316',
  'Mining': '#64748B',
  'Utilities': '#22D3EE',
  'Healthcare': '#FB7185',
  'Infrastructure': '#A3E635',
  'Chemicals': '#C084FC'
};

const SectorBreakdown = ({ sectors }: SectorBreakdownProps) => {
  const [hoveredSector, setHoveredSector] = useState<string | null>(null);
  
  const sortedSectors = Object.entries(sectors)
    .sort((a, b) => b[1] - a[1]);
  
  const totalAllocation = sortedSectors.reduce((sum, [, weight]) => sum + weight, 0);
  
  return (
    <Card className="glass-card gradient-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-white text-lg flex items-center gap-2">
          <PieChart className="w-5 h-5 text-[#8B5CF6]" />
          Sector Breakdown
        </CardTitle>
        <p className="text-sm text-[#64748B]">
          Regulatory Constraint: Max 25% per sector
        </p>
      </CardHeader>
      
      <CardContent>
        {/* Horizontal Bar Chart */}
        <div className="space-y-3">
          {sortedSectors.map(([sector, weight]) => {
            const percentage = (weight / totalAllocation) * 100;
            const isOverLimit = weight > MAX_SECTOR_EXPOSURE;
            const color = sectorColors[sector] || '#94A3B8';
            const isHovered = hoveredSector === sector;
            
            return (
              <div 
                key={sector}
                className="group"
                onMouseEnter={() => setHoveredSector(sector)}
                onMouseLeave={() => setHoveredSector(null)}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-sm text-white font-medium">{sector}</span>
                    {isOverLimit && (
                      <AlertTriangle className="w-4 h-4 text-[#EF4444]" />
                    )}
                    {!isOverLimit && weight > 0.15 && (
                      <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${
                      isOverLimit ? 'text-[#EF4444]' : 'text-white'
                    }`}>
                      {(weight * 100).toFixed(1)}%
                    </span>
                    {isOverLimit && (
                      <Badge className="badge-red text-xs">
                        Over Limit
                      </Badge>
                    )}
                  </div>
                </div>
                
                <div className="relative h-2 bg-[#1E293B] rounded-full overflow-hidden">
                  {/* Limit marker */}
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-[#EF4444]/50 z-10"
                    style={{ left: `${(MAX_SECTOR_EXPOSURE / totalAllocation) * 100}%` }}
                  />
                  
                  {/* Bar */}
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ 
                      width: `${percentage}%`,
                      background: `linear-gradient(90deg, ${color}, ${color}80)`,
                      opacity: isHovered ? 1 : 0.85
                    }}
                  />
                </div>
                
                {/* Hover tooltip */}
                {isHovered && (
                  <div className="mt-2 p-2 bg-[#0a0f1c] border border-[#1E293B] rounded-lg text-xs">
                    <div className="flex justify-between gap-4">
                      <span className="text-[#94A3B8]">Allocation:</span>
                      <span className="text-white font-mono">{(weight * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-[#94A3B8]">Limit:</span>
                      <span className="text-white font-mono">{(MAX_SECTOR_EXPOSURE * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-[#94A3B8]">Headroom:</span>
                      <span className={`font-mono ${
                        isOverLimit ? 'text-[#EF4444]' : 'text-[#10B981]'
                      }`}>
                        {((MAX_SECTOR_EXPOSURE - weight) * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Summary */}
        <div className="mt-6 pt-4 border-t border-[#1E293B]/50">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-white">
                {sortedSectors.length}
              </p>
              <p className="text-xs text-[#64748B]">Sectors</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-[#10B981]">
                {sortedSectors.filter(([, w]) => w <= MAX_SECTOR_EXPOSURE).length}
              </p>
              <p className="text-xs text-[#64748B]">Compliant</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-[#EF4444]">
                {sortedSectors.filter(([, w]) => w > MAX_SECTOR_EXPOSURE).length}
              </p>
              <p className="text-xs text-[#64748B]">Violations</p>
            </div>
          </div>
        </div>
        
        {/* Constraint Info */}
        <div className="mt-4 p-3 bg-[#0048B4]/10 border border-[#0048B4]/20 rounded-lg">
          <p className="text-xs text-[#94A3B8]">
            <span className="text-[#0048B4] font-semibold">Qurve Constraint:</span>
            {' '}Sector exposure encoded as quadratic penalty term with slack variables
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default SectorBreakdown;
