import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, ArrowUpDown, TrendingUp, TrendingDown, Download } from 'lucide-react';

interface Portfolio {
  [key: string]: {
    weight: number;
    sector: string;
  };
}

interface HoldingsTableProps {
  portfolio: Portfolio;
}

type SortKey = 'ticker' | 'weight' | 'sector';
type SortOrder = 'asc' | 'desc';

// Mock price data
const mockPrices: { [key: string]: { price: number; change: number; pe: number } } = {
  'RELIANCE.NS': { price: 2456.80, change: 1.25, pe: 22.5 },
  'TCS.NS': { price: 3890.50, change: -0.45, pe: 28.3 },
  'HDFCBANK.NS': { price: 1523.60, change: 0.89, pe: 18.7 },
  'INFY.NS': { price: 1456.30, change: 1.12, pe: 24.1 },
  'ICICIBANK.NS': { price: 987.45, change: 2.34, pe: 16.8 },
  'HINDUNILVR.NS': { price: 2345.90, change: -0.23, pe: 32.4 },
  'ITC.NS': { price: 423.80, change: 0.67, pe: 25.6 },
  'SBIN.NS': { price: 678.90, change: 1.89, pe: 12.3 },
  'BHARTIARTL.NS': { price: 892.30, change: -0.78, pe: 21.5 },
  'KOTAKBANK.NS': { price: 1756.40, change: 0.45, pe: 19.8 },
  'LT.NS': { price: 3123.50, change: 1.67, pe: 26.4 },
  'HCLTECH.NS': { price: 1234.60, change: -0.34, pe: 22.1 },
  'BAJFINANCE.NS': { price: 6789.20, change: 2.12, pe: 28.9 },
  'SUNPHARMA.NS': { price: 1123.40, change: 0.56, pe: 24.7 },
  'AXISBANK.NS': { price: 945.70, change: 1.23, pe: 15.6 },
};

const HoldingsTable = ({ portfolio }: HoldingsTableProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('weight');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  
  // Get unique sectors
  const sectors = [...new Set(Object.values(portfolio).map(p => p.sector))];
  
  // Filter and sort holdings
  let holdings = Object.entries(portfolio)
    .map(([ticker, data]) => ({
      ticker,
      ...data,
      ...mockPrices[ticker] || { price: 0, change: 0, pe: 0 }
    }))
    .filter(holding => {
      const matchesSearch = holding.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           holding.sector.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSector = !selectedSector || holding.sector === selectedSector;
      return matchesSearch && matchesSector;
    });
  
  // Sort
  holdings.sort((a, b) => {
    let comparison = 0;
    switch (sortKey) {
      case 'ticker':
        comparison = a.ticker.localeCompare(b.ticker);
        break;
      case 'weight':
        comparison = a.weight - b.weight;
        break;
      case 'sector':
        comparison = a.sector.localeCompare(b.sector);
        break;
    }
    return sortOrder === 'asc' ? comparison : -comparison;
  });
  
  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };
  
  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return <ArrowUpDown className="w-4 h-4 text-[#64748B]" />;
    return sortOrder === 'asc' 
      ? <TrendingUp className="w-4 h-4 text-primary" />
      : <TrendingDown className="w-4 h-4 text-primary" />;
  };
  
  return (
    <Card className="glass-card gradient-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Portfolio Holdings
            </CardTitle>
            <p className="text-sm text-[#64748B]">
              {holdings.length} assets selected by Qurve optimizer
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
              <Input
                type="text"
                placeholder="Search holdings..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-48 pl-10 bg-[#0a0f1c] border-[#1E293B] text-white text-sm focus:border-primary/50"
              />
            </div>
            
            {/* Sector Filter */}
            <select
              value={selectedSector || ''}
              onChange={(e) => setSelectedSector(e.target.value || null)}
              className="px-3 py-2 bg-[#0a0f1c] border border-[#1E293B] rounded-lg text-sm text-white focus:outline-none focus:border-primary/50"
            >
              <option value="">All Sectors</option>
              {sectors.map(sector => (
                <option key={sector} value={sector}>{sector}</option>
              ))}
            </select>
            
            {/* Export */}
            <Button variant="outline" size="sm" className="border-[#1E293B] text-[#94A3B8] hover:text-white hover:bg-muted">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-[#1E293B] hover:bg-transparent">
                <TableHead className="text-[#94A3B8]">
                  <button 
                    onClick={() => toggleSort('ticker')}
                    className="flex items-center gap-2"
                  >
                    Symbol
                    <SortIcon column="ticker" />
                  </button>
                </TableHead>
                <TableHead className="text-[#94A3B8]">Sector</TableHead>
                <TableHead className="text-[#94A3B8] text-right">
                  <button 
                    onClick={() => toggleSort('weight')}
                    className="flex items-center gap-2 ml-auto"
                  >
                    Weight
                    <SortIcon column="weight" />
                  </button>
                </TableHead>
                <TableHead className="text-[#94A3B8] text-right">Price (₹)</TableHead>
                <TableHead className="text-[#94A3B8] text-right">24h Change</TableHead>
                <TableHead className="text-[#94A3B8] text-right">P/E Ratio</TableHead>
                <TableHead className="text-[#94A3B8] text-right">Allocation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {holdings.map((holding) => (
                <TableRow 
                  key={holding.ticker}
                  className="border-[#1E293B]/50 hover:bg-primary/5"
                >
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                        <span className="text-xs font-bold text-white">
                          {holding.ticker.charAt(0)}
                        </span>
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          {holding.ticker.replace('.NS', '')}
                        </p>
                        <p className="text-xs text-[#64748B]">NSE</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className="bg-primary/10 text-primary border border-primary/20">
                      {holding.sector}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="font-semibold text-white">
                      {(holding.weight * 100).toFixed(2)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right text-white">
                    ₹{holding.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={`flex items-center justify-end gap-1 ${
                      holding.change >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                    }`}>
                      {holding.change >= 0 ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                      {Math.abs(holding.change).toFixed(2)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right text-white">
                    {holding.pe.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-2 bg-[#1E293B] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-primary to-secondary"
                          style={{ width: `${holding.weight * 500}%` }}
                        />
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        
        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#1E293B]/50">
          <p className="text-sm text-[#64748B]">
            Showing {holdings.length} of {Object.keys(portfolio).length} assets
          </p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="border-[#1E293B] text-[#94A3B8]" disabled>
              Previous
            </Button>
            <Button variant="outline" size="sm" className="border-[#1E293B] text-[#94A3B8]" disabled>
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default HoldingsTable;
