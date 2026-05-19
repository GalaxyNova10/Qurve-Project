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
  const [notifications] = useState<any[]>([]);

  const unreadCount = notifications.filter(n => n.unread).length;

  const handleExport = () => {
    toast.success('Report exported', { description: 'Portfolio report downloaded as PDF' });
  };

  return (
    <header className="h-16 bg-card/80 backdrop-blur-xl border-b border-border/50 flex items-center justify-between px-8 sticky top-0 z-40">
      {/* Search */}
      <div className="flex items-center gap-4 flex-1 max-w-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search assets, metrics, or settings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
          />
        </div>
        <Button variant="outline" size="icon" className="border-border text-muted-foreground hover:text-foreground">
          <Filter className="w-4 h-4" />
        </Button>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Date Display */}
        <div className="hidden lg:flex items-center gap-2 text-muted-foreground text-sm">
          <Calendar className="w-4 h-4" />
          <span>{new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
        </div>

        {/* Export Button */}
        <Button 
          variant="outline" 
          className="hidden sm:flex items-center gap-2 border-border text-muted-foreground hover:text-foreground hover:border-primary/50"
          onClick={handleExport}
        >
          <Download className="w-4 h-4" />
          <span>Export</span>
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="relative p-2.5 bg-background border border-border rounded-xl hover:border-primary/50 transition-colors">
              <Bell className="w-5 h-5 text-muted-foreground" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-primary rounded-full text-xs flex items-center justify-center text-white font-semibold glow-purple">
                  {unreadCount}
                </span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 bg-card border-border">
            <DropdownMenuLabel className="text-foreground">Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-border" />
            {notifications.map((notification) => (
              <DropdownMenuItem key={notification.id} className="p-3 cursor-pointer focus:bg-muted/50">
                <div className="flex gap-3">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${notification.unread ? 'bg-primary glow-purple' : 'bg-muted-foreground'}`} />
                  <div>
                    <p className="text-foreground text-sm font-medium">{notification.title}</p>
                    <p className="text-muted-foreground text-xs">{notification.message}</p>
                    <p className="text-muted-foreground/70 text-xs mt-1">{notification.time}</p>
                  </div>
                </div>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator className="bg-border" />
            <DropdownMenuItem className="justify-center text-primary cursor-pointer hover:bg-primary/10">
              View all notifications
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
