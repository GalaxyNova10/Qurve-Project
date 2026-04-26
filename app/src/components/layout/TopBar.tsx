import { useState } from 'react';
import { Search, Bell, Calendar, Download, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';

export default function TopBar() {
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications] = useState([
    { id: 1, title: 'Optimization Complete', message: 'QUBO solver converged in 847ms', time: '2 min ago', unread: true },
    { id: 2, title: 'Portfolio Rebalance', message: '15 assets selected', time: '1 hour ago', unread: true },
    { id: 3, title: 'GPU Temperature', message: 'Temperature normalized to 68°C', time: '3 hours ago', unread: false },
  ]);

  const unreadCount = notifications.filter(n => n.unread).length;

  const handleExport = () => {
    toast.success('Report exported', { description: 'Portfolio report downloaded as PDF' });
  };

  return (
    <header className="h-16 bg-[#0d1117]/80 backdrop-blur-xl border-b border-[#1E293B]/50 flex items-center justify-between px-8 sticky top-0 z-40">
      {/* Search */}
      <div className="flex items-center gap-4 flex-1 max-w-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
          <input
            type="text"
            placeholder="Search assets, metrics, or settings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#111827] border border-[#1E293B] rounded-xl text-sm text-white placeholder:text-[#64748B] focus:outline-none focus:border-[#FF6200]/50 transition-colors"
          />
        </div>
        <Button variant="outline" size="icon" className="border-[#1E293B] text-[#94A3B8] hover:text-white">
          <Filter className="w-4 h-4" />
        </Button>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Date Display */}
        <div className="hidden lg:flex items-center gap-2 text-[#94A3B8] text-sm">
          <Calendar className="w-4 h-4" />
          <span>{new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
        </div>

        {/* Export Button */}
        <Button 
          variant="outline" 
          className="hidden sm:flex items-center gap-2 border-[#1E293B] text-[#94A3B8] hover:text-white hover:border-[#FF6200]/50"
          onClick={handleExport}
        >
          <Download className="w-4 h-4" />
          <span>Export</span>
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="relative p-2.5 bg-[#111827] border border-[#1E293B] rounded-xl hover:border-[#FF6200]/50 transition-colors">
              <Bell className="w-5 h-5 text-[#94A3B8]" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#FF6200] rounded-full text-xs flex items-center justify-center text-white font-semibold">
                  {unreadCount}
                </span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 bg-[#111827] border-[#1E293B]">
            <DropdownMenuLabel className="text-white">Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-[#1E293B]" />
            {notifications.map((notification) => (
              <DropdownMenuItem key={notification.id} className="p-3 cursor-pointer focus:bg-[#1E293B]">
                <div className="flex gap-3">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${notification.unread ? 'bg-[#FF6200]' : 'bg-[#64748B]'}`} />
                  <div>
                    <p className="text-white text-sm font-medium">{notification.title}</p>
                    <p className="text-[#94A3B8] text-xs">{notification.message}</p>
                    <p className="text-[#64748B] text-xs mt-1">{notification.time}</p>
                  </div>
                </div>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator className="bg-[#1E293B]" />
            <DropdownMenuItem className="justify-center text-[#FF6200] cursor-pointer">
              View all notifications
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
