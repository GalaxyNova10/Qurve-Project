import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Shield, 
  Users, 
  BarChart3, 
  Cloud, 
  Zap, 
  Activity,
  Settings,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  RefreshCw
} from 'lucide-react';

interface UserStats {
  totalUsers: number;
  activeUsers: number;
  userTypes: Record<string, number>;
  sessionStats: {
    totalSessions: number;
    activeSessions: number;
    expiredSessions: number;
  };
}

interface ExecutionStats {
  totalRequests: number;
  totalExecutions: number;
  statusDistribution: Record<string, number>;
  modeDistribution: Record<string, number>;
  successRate: number;
  averageExecutionTime: number;
}

interface QuotaStats {
  totalQuotas: number;
  totalUsers: number;
  quotaTypeDistribution: Record<string, number>;
  totalUsage: number;
  totalLimit: number;
  utilizationRate: number;
  qpuTierDistribution: Record<string, number>;
}

interface GovernanceStats {
  environmentConfigs: Record<string, any>;
  rbacEnforcement: boolean;
  configurationLocking: boolean;
  auditTrailStats: {
    totalEvents: number;
    recentEvents: number;
    statusDistribution: Record<string, number>;
  };
}

interface CloudOversightData {
  cloudExecutionStats: {
    internalOnly: boolean;
    governanceControlled: boolean;
    auditTracked: boolean;
    quotaEnforced: boolean;
    executionStats: Record<string, any>;
  };
  qpuStatus: {
    qpuEnabled: boolean;
    deviceRegistryAvailable: boolean;
    hardwareGovernance: boolean;
  };
  costGovernance: {
    governanceEnforced: boolean;
    costTrackingActive: boolean;
  };
}

interface ReplayControlData {
  replaySystemStatus: {
    replayAvailable: boolean;
    replayIntegrity: boolean;
    replayIsolation: boolean;
  };
  recentReplayRequests: Array<{
    requestId: string;
    userId: string;
    timestamp: number;
    status: string;
  }>;
  replayAccessLogs: Array<{
    userId: string;
    accessType: string;
    timestamp: number;
    granted: boolean;
  }>;
}

const AdminOperationalConsole: React.FC = () => {
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [executionStats, setExecutionStats] = useState<ExecutionStats | null>(null);
  const [quotaStats, setQuotaStats] = useState<QuotaStats | null>(null);
  const [governanceStats, setGovernanceStats] = useState<GovernanceStats | null>(null);
  const [cloudOversight, setCloudOversight] = useState<CloudOversightData | null>(null);
  const [replayControls, setReplayControls] = useState<ReplayControlData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    loadDashboardData();
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all dashboard data in parallel
      const [
        userStatsResponse,
        executionStatsResponse,
        quotaStatsResponse,
        governanceStatsResponse,
        cloudOversightResponse,
        replayControlsResponse
      ] = await Promise.all([
        fetch('/api/v1/operator/dashboard'),
        fetch('/api/v1/operator/executions'),
        fetch('/api/v1/operator/quotas'),
        fetch('/api/v1/operator/governance'),
        fetch('/api/v1/operator/cloud_oversight'),
        fetch('/api/v1/operator/replay_controls')
      ]);

      // Parse responses
      const [
        userData,
        ,
        ,
        ,
        cloudData,
        replayData
      ] = await Promise.all([
        userStatsResponse.json(),
        executionStatsResponse.json(),
        quotaStatsResponse.json(),
        governanceStatsResponse.json(),
        cloudOversightResponse.json(),
        replayControlsResponse.json()
      ]);

      setUserStats(userData.dashboard_data.users);
      setExecutionStats(userData.dashboard_data.executions);
      setQuotaStats(userData.dashboard_data.quotas);
      setGovernanceStats(userData.dashboard_data.governance);
      setCloudOversight(cloudData);
      setReplayControls(replayData);
      setLastRefresh(new Date());

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
      case 'completed':
        return <Badge variant="default" className="bg-green-500">Healthy</Badge>;
      case 'warning':
      case 'pending':
        return <Badge variant="secondary" className="bg-yellow-500">Warning</Badge>;
      case 'error':
      case 'failed':
      case 'rejected':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };



  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="ml-2">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="w-8 h-8" />
            Admin Operational Console
          </h1>
          <p className="text-gray-600 mt-1">
            System governance, cloud oversight, and operational controls
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-500">
            Last refreshed: {lastRefresh.toLocaleTimeString()}
          </div>
          <Button onClick={loadDashboardData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userStats?.activeUsers || 0}</div>
            <p className="text-xs text-muted-foreground">
              Total: {userStats?.totalUsers || 0} users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Execution Success Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {executionStats?.successRate ? executionStats.successRate.toFixed(1) : '0'}%
            </div>
            <p className="text-xs text-muted-foreground">
              {executionStats?.totalExecutions || 0} executions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Quota Utilization</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {quotaStats?.utilizationRate ? quotaStats.utilizationRate.toFixed(1) : '0'}%
            </div>
            <p className="text-xs text-muted-foreground">
              {quotaStats?.totalUsage || 0}/{quotaStats?.totalLimit || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {governanceStats?.rbacEnforcement ? 'Healthy' : 'Warning'}
            </div>
            <p className="text-xs text-muted-foreground">
              All systems operational
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="governance" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="governance">Governance</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="executions">Executions</TabsTrigger>
          <TabsTrigger value="cloud">Cloud Oversight</TabsTrigger>
          <TabsTrigger value="replay">Replay Controls</TabsTrigger>
        </TabsList>

        {/* Governance Dashboard */}
        <TabsContent value="governance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Governance Controls
                </CardTitle>
                <CardDescription>
                  System governance status and controls
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>RBAC Enforcement</span>
                    {governanceStats?.rbacEnforcement ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Configuration Locking</span>
                    {governanceStats?.configurationLocking ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Environment Governance</span>
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Audit Trail Active</span>
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="w-5 h-5" />
                  Audit Trail Statistics
                </CardTitle>
                <CardDescription>
                  Recent audit activity and system events
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Events</span>
                    <span className="font-medium">
                      {governanceStats?.auditTrailStats.totalEvents || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recent Events (24h)</span>
                    <span className="font-medium">
                      {governanceStats?.auditTrailStats.recentEvents || 0}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm font-medium">Event Distribution</span>
                    {Object.entries(governanceStats?.auditTrailStats.statusDistribution || {}).map(([status, count]) => (
                      <div key={status} className="flex justify-between text-sm">
                        <span>{status}</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Users Dashboard */}
        <TabsContent value="users" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  User Statistics
                </CardTitle>
                <CardDescription>
                  User activity and session management
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-2xl font-bold">{userStats?.totalUsers || 0}</div>
                      <p className="text-xs text-muted-foreground">Total Users</p>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{userStats?.activeUsers || 0}</div>
                      <p className="text-xs text-muted-foreground">Active Users</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <span className="text-sm font-medium">User Types</span>
                    {Object.entries(userStats?.userTypes || {}).map(([type, count]) => (
                      <div key={type} className="flex justify-between text-sm">
                        <span>{type.replace('_', ' ').toUpperCase()}</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Session Statistics
                </CardTitle>
                <CardDescription>
                  Active and expired user sessions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <div className="text-2xl font-bold">
                        {userStats?.sessionStats.totalSessions || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">Total Sessions</p>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">
                        {userStats?.sessionStats.activeSessions || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">Active</p>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">
                        {userStats?.sessionStats.expiredSessions || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">Expired</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <span className="text-sm font-medium">Quota Utilization</span>
                    {quotaStats && (
                      <Progress 
                        value={quotaStats.utilizationRate} 
                        className="h-2"
                      />
                    )}
                    <div className="text-xs text-gray-500">
                      {quotaStats?.utilizationRate?.toFixed(1) || 0}% utilized
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Executions Dashboard */}
        <TabsContent value="executions" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Execution Statistics
                </CardTitle>
                <CardDescription>
                  Benchmark execution performance and status
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-2xl font-bold">
                        {executionStats?.totalRequests || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">Total Requests</p>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">
                        {executionStats?.totalExecutions || 0}
                      </div>
                      <p className="text-xs text-muted-foreground">Total Executions</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <span className="text-sm font-medium">Success Rate</span>
                    <Progress 
                      value={executionStats?.successRate || 0} 
                      className="h-2"
                    />
                    <div className="text-xs text-gray-500">
                      {executionStats?.successRate?.toFixed(1) || 0}% success rate
                    </div>
                  </div>
                  
                  <div className="text-sm">
                    <span className="font-medium">Avg Execution Time:</span>{' '}
                    {executionStats?.averageExecutionTime?.toFixed(0) || 0}ms
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Execution Distribution
                </CardTitle>
                <CardDescription>
                  Status and mode distribution
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <span className="text-sm font-medium">Status Distribution</span>
                    {Object.entries(executionStats?.statusDistribution || {}).map(([status, count]) => (
                      <div key={status} className="flex justify-between text-sm">
                        <span>{status.replace('_', ' ').toUpperCase()}</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="space-y-2">
                    <span className="text-sm font-medium">Mode Distribution</span>
                    {Object.entries(executionStats?.modeDistribution || {}).map(([mode, count]) => (
                      <div key={mode} className="flex justify-between text-sm">
                        <span>{mode.replace('_', ' ').toUpperCase()}</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Cloud Oversight Dashboard */}
        <TabsContent value="cloud" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cloud className="w-5 h-5" />
                  Cloud Execution Controls
                </CardTitle>
                <CardDescription>
                  Cloud execution governance and oversight
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Internal Only</span>
                    {cloudOversight?.cloudExecutionStats.internalOnly ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Governance Controlled</span>
                    {cloudOversight?.cloudExecutionStats.governanceControlled ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Audit Tracked</span>
                    {cloudOversight?.cloudExecutionStats.auditTracked ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Quota Enforced</span>
                    {cloudOversight?.cloudExecutionStats.quotaEnforced ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  QPU Status
                </CardTitle>
                <CardDescription>
                  QPU device status and governance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>QPU Enabled</span>
                    {cloudOversight?.qpuStatus.qpuEnabled ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-yellow-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Device Registry</span>
                    {cloudOversight?.qpuStatus.deviceRegistryAvailable ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Hardware Governance</span>
                    {cloudOversight?.qpuStatus.hardwareGovernance ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Cost Governance</span>
                    {cloudOversight?.costGovernance.governanceEnforced ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Replay Controls Dashboard */}
        <TabsContent value="replay" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Replay System Status
                </CardTitle>
                <CardDescription>
                  Replay system availability and integrity
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Replay Available</span>
                    {replayControls?.replaySystemStatus.replayAvailable ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Replay Integrity</span>
                    {replayControls?.replaySystemStatus.replayIntegrity ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Replay Isolation</span>
                    {replayControls?.replaySystemStatus.replayIsolation ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="w-5 h-5" />
                  Recent Replay Activity
                </CardTitle>
                <CardDescription>
                  Recent replay requests and access logs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <span className="text-sm font-medium">Recent Requests</span>
                    {replayControls?.recentReplayRequests.slice(0, 5).map((request, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span>{request.requestId.slice(0, 12)}...</span>
                        {getStatusBadge(request.status)}
                      </div>
                    ))}
                  </div>
                  
                  <div className="space-y-2">
                    <span className="text-sm font-medium">Access Logs</span>
                    {replayControls?.replayAccessLogs.slice(0, 5).map((log, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span>{log.userId.slice(0, 8)}...</span>
                        {log.granted ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminOperationalConsole;
