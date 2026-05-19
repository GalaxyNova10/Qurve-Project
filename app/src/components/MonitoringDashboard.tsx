import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Zap, Cpu } from 'lucide-react';

interface SystemOverview {
  system_health: string;
  active_executions: number;
  total_executions: number;
  success_rate: number;
  avg_latency_ms: number;
  throughput_per_min: number;
  fallback_frequency: number;
  timeout_count: number;
  cloud_active_tasks: number;
  memory_usage_mb: number;
  last_updated: number;
}

interface SolverData {
  status: string;
  avg_latency_ms: number;
  total_executions: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  fallback_count: number;
  cloud_usage_percentage: number;
}

interface CloudData {
  active_aws_tasks: number;
  cloud_queue_latency_ms: number;
  cloud_execution_latency_ms: number;
  aws_region_usage: Record<string, number>;
  task_state_distribution: Record<string, number>;
  estimated_cloud_cost: number;
  primary_region: string;
}

interface ExecutionEvent {
  timestamp: number;
  event_type: string;
  solver: string;
  execution_mode: string;
  correlation_id: string;
  latency_ms?: number;
  cloud_task_arn?: string;
  error_message?: string;
}

interface MonitoringResponse {
  overview: SystemOverview;
  solvers: Record<string, SolverData>;
  cloud: CloudData;
  recent_events: ExecutionEvent[];
}

const MonitoringDashboard: React.FC = () => {
  const [data, setData] = useState<MonitoringResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMonitoringData = async () => {
      try {
        const response = await fetch('/api/v1/monitoring/overview');
        const overview = await response.json();

        const solversResponse = await fetch('/api/v1/monitoring/solvers');
        const solvers = await solversResponse.json();

        const cloudResponse = await fetch('/api/v1/monitoring/cloud');
        const cloud = await cloudResponse.json();

        const eventsResponse = await fetch('/api/v1/monitoring/recent-events?limit=50');
        const events = await eventsResponse.json();

        setData({
          overview,
          solvers: solvers.solvers,
          cloud,
          recent_events: events.events
        });
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch monitoring data');
      } finally {
        setLoading(false);
      }
    };

    fetchMonitoringData();
    const interval = setInterval(fetchMonitoringData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  
  const getHealthBadgeVariant = (health: string) => {
    switch (health) {
      case 'healthy': return 'default';
      case 'degraded': return 'secondary';
      case 'unstable': return 'outline';
      case 'critical': return 'destructive';
      default: return 'outline';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'started': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'timeout': return 'text-orange-600';
      case 'fallback': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading monitoring data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">No monitoring data available</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight text-white">Operational Dashboard</h1>
          <p className="text-sm text-slate-400">Real-time AWS Braket & Local Optimization Telemetry</p>
        </div>
        <Badge variant={getHealthBadgeVariant(data.overview.system_health)} className="px-4 py-1 text-sm font-semibold">
          {data.overview.system_health.toUpperCase()}
        </Badge>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.active_executions}</div>
            <p className="text-xs text-muted-foreground">
              Total: {data.overview.total_executions}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.success_rate.toFixed(1)}%</div>
            <Progress value={data.overview.success_rate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatLatency(data.overview.avg_latency_ms)}</div>
            <p className="text-xs text-muted-foreground">
              Throughput: {data.overview.throughput_per_min.toFixed(1)}/min
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fallback Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.fallback_frequency.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Timeouts: {data.overview.timeout_count}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cloud Execution Panel */}
        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm overflow-hidden">
          <CardHeader className="border-b border-slate-800 bg-cyan-500/5">
            <CardTitle className="flex items-center gap-2 text-cyan-400">
              <Zap className="w-4 h-4" />
              Cloud Execution (AWS Braket)
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-1">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">Active AWS Tasks</div>
                <div className="text-3xl font-bold text-white tabular-nums">{data.cloud.active_aws_tasks}</div>
              </div>
              <div className="space-y-1 text-right">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">Primary Region</div>
                <div className="text-lg font-semibold text-slate-300">{data.cloud.primary_region}</div>
              </div>
              <div className="space-y-1">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">Queue Latency</div>
                <div className="text-xl font-semibold text-cyan-500 tabular-nums">{formatLatency(data.cloud.cloud_queue_latency_ms)}</div>
              </div>
              <div className="space-y-1 text-right">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider">Execution Latency</div>
                <div className="text-xl font-semibold text-cyan-500 tabular-nums">{formatLatency(data.cloud.cloud_execution_latency_ms)}</div>
              </div>
            </div>
            
            <div className="mt-8 space-y-4">
              <div className="flex items-center justify-between text-[10px] text-slate-500 uppercase tracking-wider">
                <span>Task State Distribution</span>
                <span>Real-time AWS Status</span>
              </div>
              <div className="flex gap-1.5 h-3">
                {Object.entries(data.cloud.task_state_distribution).map(([state, count]) => {
                  const colors: Record<string, string> = {
                    'CREATED': 'bg-slate-700',
                    'QUEUED': 'bg-blue-500',
                    'RUNNING': 'bg-cyan-500',
                    'COMPLETED': 'bg-green-500',
                    'FAILED': 'bg-red-500',
                    'CANCELLED': 'bg-orange-500'
                  };
                  const total = Object.values(data.cloud.task_state_distribution).reduce((a, b) => a + b, 0);
                  const width = total > 0 ? (count / total) * 100 : 0;
                  return width > 0 ? (
                    <div 
                      key={state} 
                      className={`${colors[state] || 'bg-slate-400'} h-full rounded-full transition-all duration-500`}
                      style={{ width: `${width}%` }}
                      title={`${state}: ${count} tasks`}
                    />
                  ) : null;
                })}
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {Object.entries(data.cloud.task_state_distribution).map(([state, count]) => (
                  <div key={state} className="flex items-center gap-1.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${
                      state === 'RUNNING' ? 'bg-cyan-500 shadow-[0_0_5px_rgba(6,182,212,0.8)]' : 
                      state === 'COMPLETED' ? 'bg-green-500' : 
                      state === 'FAILED' ? 'bg-red-500' : 'bg-slate-600'
                    }`} />
                    <span className="text-[10px] text-slate-400 uppercase">{state}</span>
                    <span className="text-[10px] font-bold text-slate-300">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Local Execution Panel */}
        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm overflow-hidden">
          <CardHeader className="border-b border-slate-800 bg-slate-500/5">
            <CardTitle className="flex items-center gap-2 text-slate-400">
              <Cpu className="w-4 h-4" />
              Local Execution (Fallback & Simulation)
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-1">
                <div className="text-xs text-slate-500 uppercase">Fallback Freq</div>
                <div className="text-3xl font-bold text-orange-500">{data.overview.fallback_frequency.toFixed(1)}%</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-slate-500 uppercase">Throughput</div>
                <div className="text-xl font-semibold text-white">{data.overview.throughput_per_min.toFixed(1)}/min</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-slate-500 uppercase">Avg Local Latency</div>
                <div className="text-xl font-semibold text-slate-400">{formatLatency(data.overview.avg_latency_ms)}</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-slate-500 uppercase">Success Rate</div>
                <div className="text-xl font-semibold text-green-500">{data.overview.success_rate.toFixed(1)}%</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Solver Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Solver Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Solver</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Executions</TableHead>
                <TableHead>Success Rate</TableHead>
                <TableHead>Avg Latency</TableHead>
                <TableHead>Fallbacks</TableHead>
                <TableHead>Cloud Usage</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(data.solvers).map(([solver, metrics]) => (
                <TableRow key={solver}>
                  <TableCell className="font-medium">{solver}</TableCell>
                  <TableCell>
                    <Badge variant={getHealthBadgeVariant(metrics.status)}>
                      {metrics.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{metrics.total_executions}</TableCell>
                  <TableCell>{metrics.success_rate.toFixed(1)}%</TableCell>
                  <TableCell>{formatLatency(metrics.avg_latency_ms)}</TableCell>
                  <TableCell>{metrics.fallback_count}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Progress value={metrics.cloud_usage_percentage} className="w-16" />
                      <span className="text-sm">{metrics.cloud_usage_percentage.toFixed(0)}%</span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Recent Events */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Execution Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.recent_events.map((event, index) => (
              <div key={index} className="flex flex-col p-3 border border-slate-800 rounded bg-slate-900/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`text-xs font-bold px-2 py-0.5 rounded bg-slate-950 border border-slate-800 ${getEventTypeColor(event.event_type)}`}>
                      {event.event_type.toUpperCase()}
                    </div>
                    <div className="text-sm font-medium text-white">{event.solver}</div>
                    <Badge variant="outline" className="text-[10px] bg-slate-950 text-slate-500">
                      {event.execution_mode.toUpperCase()}
                    </Badge>
                    {event.cloud_task_arn && (
                      <Badge className="bg-cyan-500/10 text-cyan-500 border-cyan-500/20 text-[10px]">CLOUD</Badge>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-slate-500 font-mono">
                      {formatTimestamp(event.timestamp)}
                    </div>
                  </div>
                </div>
                {event.cloud_task_arn && (
                  <div className="mt-2 text-[10px] font-mono text-cyan-700 truncate bg-slate-950 p-1 rounded border border-slate-800/50">
                    ARN: {event.cloud_task_arn}
                  </div>
                )}
                {event.error_message && (
                  <div className="mt-2 text-xs text-red-400 italic">
                    Error: {event.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Info */}
      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-medium">Memory Usage</div>
              <div>{data.overview.memory_usage_mb.toFixed(1)} MB</div>
            </div>
            <div>
              <div className="font-medium">Last Updated</div>
              <div>{new Date(data.overview.last_updated * 1000).toLocaleString()}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MonitoringDashboard;
