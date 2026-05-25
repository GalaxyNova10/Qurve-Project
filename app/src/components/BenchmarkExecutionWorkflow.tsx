import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  User, 
  Shield, 
  Clock, 
  Zap, 
  Cloud, 
  Cpu, 
  CheckCircle, 
  AlertCircle,
  BarChart3,
  Settings
} from 'lucide-react';

interface BenchmarkRequest {
  benchmarkId: string;
  quboData: any;
  solverPreferences: string[];
  executionMode: 'local' | 'cloud_simulator' | 'cloud_qpu';
  shots: number;
}
interface ExecutionStatus {
  requestId: string;
  status: string;
  executionTimeMs?: number;
  governanceDecision?: string;
  fallbackChain?: string[];
  errorMessage?: string;
  executionOrigin?: 'local' | 'cloud' | 'fallback';
  fallbackTriggered?: boolean;
  taskArn?: string;
  deviceArn?: string;
  executionModeLabel?: string;
  scientific_comparability?: boolean;
  optimization_status?: string;
  repair_trace?: string[];
  parity_status?: string;
  scientific_gate?: {
    strict_ratio?: number;
    raw_ratio?: number;
    comparability_status?: string;
  };
  allocation_leakage_ratio?: number;
  repair_count?: number;
  topology_violation_ratio?: number;
}

interface UserQuotas {
  quotaType: string;
  currentUsage: number;
  limit: number;
  remaining: number;
  resetTime: number;
}

interface GovernanceStatus {
  cloudExecutionApproved: boolean;
  qpuExecutionApproved: boolean;
  costGovernancePassed: boolean;
  quotaEnforcementPassed: boolean;
}

const BenchmarkExecutionWorkflow: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [userQuotas, setUserQuotas] = useState<UserQuotas[]>([]);
  const [governanceStatus, setGovernanceStatus] = useState<GovernanceStatus | null>(null);

  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [benchmarkId, setBenchmarkId] = useState('');
  const [quboData, setQuboData] = useState('');
  const [selectedSolvers, setSelectedSolvers] = useState<string[]>(['dwave']);
  const [executionMode, setExecutionMode] = useState<'local' | 'cloud_simulator' | 'cloud_qpu'>('local');
  const [shots, setShots] = useState(100);

  useEffect(() => {
    // Check authentication and load user data
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      // Check if user is authenticated
      const sessionResponse = await fetch('/api/v1/auth/status');
      if (sessionResponse.ok) {
        const sessionData = await sessionResponse.json();
        setIsAuthenticated(true);
        setUserProfile(sessionData.user);
        await loadUserQuotas();
        await loadGovernanceStatus();
      }
    } catch (error) {
      console.error('Authentication check failed:', error);
    }
  };

  const loadUserQuotas = async () => {
    try {
      const response = await fetch('/api/v1/authenticated/user_quotas');
      if (response.ok) {
        const quotasData = await response.json();
        setUserQuotas(quotasData.quotas);
      }
    } catch (error) {
      console.error('Failed to load user quotas:', error);
    }
  };

  const loadGovernanceStatus = async () => {
    try {
      const response = await fetch('/api/v1/authenticated/governance_status');
      if (response.ok) {
        const governanceData = await response.json();
        setGovernanceStatus(governanceData);
      }
    } catch (error) {
      console.error('Failed to load governance status:', error);
    }
  };

  const handleSubmitBenchmark = async () => {
    if (!isAuthenticated) {
      setError('Please authenticate to submit benchmarks');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Parse QUBO data
      let parsedQuboData;
      try {
        parsedQuboData = JSON.parse(quboData);
      } catch (parseError) {
        throw new Error('Invalid QUBO data format');
      }

      const request: BenchmarkRequest = {
        benchmarkId,
        quboData: parsedQuboData,
        solverPreferences: selectedSolvers,
        executionMode,
        shots
      };

      const response = await fetch('/api/v1/authenticated/benchmark_submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error('Failed to submit benchmark');
      }

      const result = await response.json();

      
      // Start polling for execution status
      pollExecutionStatus(result.requestId);
      
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const pollExecutionStatus = async (requestId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/authenticated/benchmark_status?request_id=${requestId}`);
        if (response.ok) {
          const statusData = await response.json();
          setExecutionStatus(statusData);

          // Stop polling if execution is completed or failed
          if (statusData.status === 'completed' || statusData.status === 'failed') {
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Failed to poll execution status:', error);
      }
    }, 2000); // Poll every 2 seconds
  };

  const getExecutionStatusIcon = (statusObj: ExecutionStatus) => {
    const isSciFailure = 
      statusObj.scientific_comparability === false || 
      statusObj.parity_status === 'NON_COMPARABLE' || 
      statusObj.optimization_status === 'INFEASIBLE' ||
      statusObj.optimization_status === 'TOPOLOGY_UNSTABLE' ||
      (statusObj.scientific_gate?.strict_ratio ?? 0) <= 0 ||
      (statusObj.allocation_leakage_ratio ?? 0) > 0 ||
      (statusObj.repair_count ?? 0) > 0 ||
      (statusObj.topology_violation_ratio ?? 0) > 0;
    
    if (isSciFailure) {
      return <AlertCircle className="w-4 h-4 text-amber-500" />;
    }

    switch (statusObj.status) {
      case 'pending':
      case 'authenticating':
      case 'validating_quotas':
      case 'governance_checking':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'approved':
      case 'SUCCESS':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'rejected':
      case 'FAILED':
      case 'SCIENTIFIC_VIOLATION':
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'executing':
      case 'running':
        return <Zap className="w-4 h-4 text-cyan-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'queued':
        return <Clock className="w-4 h-4 text-blue-400 animate-pulse" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: ExecutionStatus) => {
    // Phase 7: Graded Frontend Scientific Truthfulness
    
    // 1. MANIFOLD_COLLAPSE (If strict_ratio is exactly 0)
    if ((status.scientific_gate?.strict_ratio ?? 0) <= 0 && status.status === 'completed') {
      return <Badge className="bg-red-600 hover:bg-red-700 text-white border-none shadow-[0_0_10px_rgba(220,38,38,0.5)]">MANIFOLD_COLLAPSE</Badge>;
    }
    
    // 2. TOPOLOGY_UNSTABLE (If any allocation leakage or repair happened)
    if ((status.allocation_leakage_ratio ?? 0) > 0 || (status.repair_count ?? 0) > 0 || (status.topology_violation_ratio ?? 0) > 0) {
      return <Badge className="bg-orange-600 hover:bg-orange-700 text-white border-none shadow-[0_0_10px_rgba(234,88,12,0.5)]">TOPOLOGY_UNSTABLE</Badge>;
    }

    // 3. FALLBACK_ONLY (If quantum failed and fell back to classical)
    if (status.fallbackTriggered || status.executionOrigin === 'fallback') {
      return <Badge className="bg-amber-500 hover:bg-amber-600 text-white border-none shadow-[0_0_10px_rgba(245,158,11,0.5)]">FALLBACK_ONLY</Badge>;
    }
    
    // 4. NUMERICAL_INSTABILITY
    if (status.status === 'failed' || status.status === 'rejected') {
      return <Badge variant="destructive">NUMERICAL_INSTABILITY</Badge>;
    }
    
    // 5. NON_COMPARABLE
    if (status.scientific_comparability === false || status.parity_status === 'NON_COMPARABLE' || status.optimization_status === 'INFEASIBLE') {
      return <Badge className="bg-gray-500 hover:bg-gray-600 text-white border-none">NON_COMPARABLE</Badge>;
    }
    
    // 6. PARTIALLY_FEASIBLE
    if ((status.scientific_gate?.strict_ratio ?? 0) > 0 && (status.scientific_gate?.strict_ratio ?? 0) < 1.0) {
      return <Badge className="bg-blue-500 hover:bg-blue-600 text-white border-none shadow-[0_0_10px_rgba(59,130,246,0.5)]">PARTIALLY_FEASIBLE</Badge>;
    }
    
    // 7. COMPARABLE (Fully valid)
    if ((status.scientific_gate?.strict_ratio ?? 0) === 1.0 || status.status === 'completed') {
      return <Badge className="bg-green-500 hover:bg-green-600 text-white border-none shadow-[0_0_10px_rgba(34,197,94,0.5)]">COMPARABLE</Badge>;
    }
    
    return <Badge variant="outline">{status.status.toUpperCase()}</Badge>;
  };

  const getExecutionModeIcon = (mode: string) => {
    switch (mode) {
      case 'local':
        return <Cpu className="w-4 h-4" />;
      case 'cloud_simulator':
        return <Cloud className="w-4 h-4" />;
      case 'cloud_qpu':
        return <Zap className="w-4 h-4" />;
      default:
        return <Cpu className="w-4 h-4" />;
    }
  };

  const getQuotaProgress = (quota: UserQuotas) => {
    const percentage = (quota.currentUsage / quota.limit) * 100;
    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>{quota.quotaType.replace('_', ' ').toUpperCase()}</span>
          <span>{quota.currentUsage}/{quota.limit}</span>
        </div>
        <Progress value={percentage} className="h-2" />
        <div className="text-xs text-gray-500">
          {quota.remaining} remaining
        </div>
      </div>
    );
  };

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto p-6">
        <Card className="max-w-md mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Authentication Required
            </CardTitle>
            <CardDescription>
              Please authenticate to access benchmark execution workflows
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => window.location.href = '/login'} className="w-full">
              Sign In
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* User Profile and Governance Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              User Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div><strong>Username:</strong> {userProfile?.username}</div>
              <div><strong>User Type:</strong> {userProfile?.userType}</div>
              <div><strong>Role:</strong> {userProfile?.operatorRole}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Governance Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant={governanceStatus?.cloudExecutionApproved ? "default" : "destructive"}>
                  Cloud Execution
                </Badge>
                {governanceStatus?.cloudExecutionApproved ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={governanceStatus?.qpuExecutionApproved ? "default" : "destructive"}>
                  QPU Execution
                </Badge>
                {governanceStatus?.qpuExecutionApproved ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={governanceStatus?.costGovernancePassed ? "default" : "destructive"}>
                  Cost Governance
                </Badge>
                {governanceStatus?.costGovernancePassed ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Quota Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {userQuotas.map((quota, index) => (
                <div key={index}>
                  {getQuotaProgress(quota)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Benchmark Submission Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Benchmark Submission
          </CardTitle>
          <CardDescription>
            Submit your QUBO benchmark for execution with governance-aware routing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="configuration" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="configuration">Configuration</TabsTrigger>
              <TabsTrigger value="execution">Execution</TabsTrigger>
              <TabsTrigger value="status">Status</TabsTrigger>
            </TabsList>

            <TabsContent value="configuration" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="benchmarkId">Benchmark ID</Label>
                  <Input
                    id="benchmarkId"
                    value={benchmarkId}
                    onChange={(e) => setBenchmarkId(e.target.value)}
                    placeholder="Enter benchmark identifier"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="shots">Number of Shots</Label>
                  <Input
                    id="shots"
                    type="number"
                    value={shots}
                    onChange={(e) => setShots(parseInt(e.target.value) || 100)}
                    min="1"
                    max="10000"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="quboData">QUBO Data (JSON)</Label>
                <Textarea
                  id="quboData"
                  value={quboData}
                  onChange={(e) => setQuboData(e.target.value)}
                  placeholder='{"Q": {"0,0": 1, "1,1": 1}, "offset": 0}'
                  rows={6}
                />
              </div>

              <div className="space-y-4">
                <Label>Solver Selection (Side-by-Side Comparison)</Label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {[
                    {
                      category: 'LOCAL EXECUTION',
                      solvers: [
                        { id: 'neal', label: 'Classical (Simulated Annealing)' },
                        { id: 'qiskit', label: 'Qiskit Local' },
                        { id: 'AWS_BRAKET_LOCAL', label: 'AWS Braket Local' }
                      ]
                    },
                    {
                      category: 'CLOUD EXECUTION',
                      solvers: [
                        { id: 'AWS_BRAKET_SV1', label: 'AWS Braket SV1' }
                      ]
                    },
                    {
                      category: 'HYBRID EXECUTION',
                      solvers: [
                        { id: 'dwave', label: 'D-Wave Hybrid' }
                      ]
                    }
                  ].map((cat) => (
                    <div key={cat.category} className="space-y-2">
                      <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{cat.category}</div>
                      <div className="space-y-2">
                        {cat.solvers.map((solver) => (
                          <div key={solver.id} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              id={solver.id}
                              checked={selectedSolvers.includes(solver.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedSolvers([...selectedSolvers, solver.id]);
                                } else {
                                  setSelectedSolvers(selectedSolvers.filter(s => s !== solver.id));
                                }
                              }}
                              className="accent-cyan-500"
                            />
                            <Label htmlFor={solver.id} className="text-xs text-slate-300">
                              {solver.label}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="execution" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="executionMode">Execution Mode</Label>
                <Select value={executionMode} onValueChange={(value: any) => setExecutionMode(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="local">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        Local Execution
                      </div>
                    </SelectItem>
                    <SelectItem value="cloud_simulator">
                      <div className="flex items-center gap-2">
                        <Cloud className="w-4 h-4" />
                        Cloud Simulator
                      </div>
                    </SelectItem>
                    <SelectItem value="cloud_qpu">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        Cloud QPU
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Execution Path</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        {getExecutionModeIcon(executionMode)}
                        <span className="font-medium">{executionMode.replace('_', ' ').toUpperCase()}</span>
                      </div>
                      <div className="text-sm text-gray-600">
                        {executionMode === 'local' && 'Execute on local solvers'}
                        {executionMode === 'cloud_simulator' && 'Execute on cloud simulators'}
                        {executionMode === 'cloud_qpu' && 'Execute on real QPU hardware'}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Governance Requirements</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {executionMode === 'cloud_simulator' && (
                        <>
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">Cloud execution approval</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">Cost governance check</span>
                          </div>
                        </>
                      )}
                      {executionMode === 'cloud_qpu' && (
                        <>
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">QPU execution approval</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">Cloud execution approval</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">Cost governance check</span>
                          </div>
                        </>
                      )}
                      {executionMode === 'local' && (
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span className="text-sm">No special requirements</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Button 
                onClick={handleSubmitBenchmark} 
                disabled={loading || !benchmarkId || !quboData}
                className="w-full"
              >
                {loading ? 'Submitting...' : 'Submit Benchmark'}
              </Button>
            </TabsContent>

            <TabsContent value="status" className="space-y-4">
              {executionStatus && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {getExecutionStatusIcon(executionStatus)}
                      Execution Status
                    </CardTitle>
                    <CardDescription>
                      Request ID: {executionStatus.requestId}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        {getStatusBadge(executionStatus)}
                        {executionStatus.executionTimeMs && (
                          <span className="text-sm text-gray-400 font-mono">
                            {executionStatus.executionTimeMs}ms
                          </span>
                        )}
                        {executionStatus.executionModeLabel && (
                          <Badge variant="outline" className="text-[10px] border-slate-700">
                            {executionStatus.executionModeLabel.toUpperCase()}
                          </Badge>
                        )}
                      </div>

                      {executionStatus.governanceDecision && (
                        <Alert>
                          <AlertDescription>
                            <strong>Governance Decision:</strong> {executionStatus.governanceDecision}
                          </AlertDescription>
                        </Alert>
                      )}

                      {executionStatus.taskArn && (
                        <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                          <Label className="text-[10px] text-slate-500 uppercase tracking-wider">AWS Task ARN</Label>
                          <div className="text-xs font-mono text-cyan-400 break-all">
                            {executionStatus.taskArn}
                          </div>
                        </div>
                      )}

                      {executionStatus.fallbackChain && executionStatus.fallbackChain.length > 0 && (
                        <div className="space-y-2">
                          <Label className="text-xs text-slate-400">Causal Lineage (Fallback Chain)</Label>
                          <div className="flex items-center gap-2 overflow-x-auto pb-1">
                            {executionStatus.fallbackChain.map((step, index, array) => (
                              <React.Fragment key={index}>
                                <Badge variant="secondary" className="bg-slate-800 text-slate-300 border-slate-700 whitespace-nowrap">
                                  {step}
                                </Badge>
                                {index < array.length - 1 && (
                                  <span className="text-slate-600 text-xs">→</span>
                                )}
                              </React.Fragment>
                            ))}
                          </div>
                        </div>
                      )}

                      {executionStatus.errorMessage && (
                        <Alert variant="destructive" className="bg-red-950/20 border-red-900/50">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription className="text-red-400">
                            {executionStatus.errorMessage}
                          </AlertDescription>
                        </Alert>
                      )}

                      {(() => {
                        if (executionStatus.status !== 'completed' && executionStatus.status !== 'SUCCESS' && executionStatus.status !== 'PARTIAL_SUCCESS' && executionStatus.status !== 'FAILED' && executionStatus.status !== 'FALLBACK' && executionStatus.status !== 'SCIENTIFIC_VIOLATION') return null;

                        const isTopologyInvalid = (executionStatus.allocation_leakage_ratio ?? 0) > 0 || (executionStatus.topology_violation_ratio ?? 0) > 0 || executionStatus.optimization_status === 'TOPOLOGY_UNSTABLE';
                        const isInfeasible = executionStatus.optimization_status === 'INFEASIBLE' || (executionStatus.scientific_gate?.strict_ratio ?? 0) <= 0;
                        const isNonComparable = executionStatus.scientific_comparability === false || executionStatus.parity_status === 'NON_COMPARABLE' || (executionStatus.repair_count ?? 0) > 0 || executionStatus.status === 'FAILED' || executionStatus.status === 'SCIENTIFIC_VIOLATION';

                        if (isTopologyInvalid) {
                          return (
                            <Alert variant="destructive" className="bg-red-950/30 border-red-900/50">
                              <AlertCircle className="h-4 w-4 text-red-500" />
                              <AlertDescription className="text-red-400 font-semibold">
                                TOPOLOGY_INVALID: Decode corruption detected. Normalization mutated topology or allocation leakage ratio &gt; 0.
                              </AlertDescription>
                            </Alert>
                          );
                        } else if (isInfeasible || isNonComparable) {
                          return (
                            <Alert variant="destructive" className="bg-orange-950/20 border-orange-900/50">
                              <AlertCircle className="h-4 w-4 text-orange-500" />
                              <AlertDescription className="text-orange-400 font-semibold">
                                Quantum execution completed but no scientifically valid feasible quantum states were discovered.
                              </AlertDescription>
                            </Alert>
                          );
                        }

                        return (
                          <Alert className="bg-green-950/20 border-green-900/50">
                            <AlertCircle className="h-4 w-4 text-green-500" />
                            <AlertDescription className="text-green-400 font-semibold">
                              COMPARABLE: Valid benchmark execution.
                            </AlertDescription>
                          </Alert>
                        );
                      })()}

                      {(() => {
                        const isSciFailure = 
                          executionStatus.scientific_comparability === false || 
                          executionStatus.parity_status === 'NON_COMPARABLE' || 
                          executionStatus.optimization_status === 'INFEASIBLE' ||
                          executionStatus.optimization_status === 'TOPOLOGY_UNSTABLE' ||
                          (executionStatus.scientific_gate?.strict_ratio ?? 0) <= 0 ||
                          (executionStatus.allocation_leakage_ratio ?? 0) > 0 ||
                          (executionStatus.repair_count ?? 0) > 0 ||
                          (executionStatus.topology_violation_ratio ?? 0) > 0 ||
                          executionStatus.status === 'FAILED' || 
                          executionStatus.status === 'SCIENTIFIC_VIOLATION';

                        return (executionStatus.status === 'completed' || executionStatus.status === 'SUCCESS' || executionStatus.status === 'PARTIAL_SUCCESS' || executionStatus.status === 'FALLBACK') && !isSciFailure && (
                        <div className="space-y-4">
                          <Label className="text-sm font-semibold text-slate-300">Operational Comparison Matrix</Label>
                          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950">
                            <table className="w-full text-xs text-left">
                              <thead className="bg-slate-900 text-slate-500 uppercase tracking-tighter">
                                <tr>
                                  <th className="px-3 py-2 font-medium">Solver</th>
                                  <th className="px-3 py-2 font-medium">Origin</th>
                                  <th className="px-3 py-2 font-medium">Infra Status</th>
                                  <th className="px-3 py-2 font-medium">Opt Status</th>
                                  <th className="px-3 py-2 font-medium">Sci Status</th>
                                  <th className="px-3 py-2 font-medium">Latency</th>
                                  <th className="px-3 py-2 font-medium">Task ARN</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-800">
                                <tr className="hover:bg-slate-900/50 transition-colors">
                                  <td className="px-3 py-3 font-mono text-cyan-400">
                                    {executionStatus.executionModeLabel || 'Unknown'}
                                  </td>
                                  <td className="px-3 py-3">
                                    <Badge className={executionStatus.executionOrigin === 'cloud' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-500/20 text-slate-400'}>
                                      {executionStatus.executionOrigin?.toUpperCase()}
                                    </Badge>
                                  </td>
                                  <td className="px-3 py-3">
                                    <span className="flex items-center gap-1">
                                      {['completed', 'SUCCESS', 'PARTIAL_SUCCESS', 'success', 'success_with_warnings'].includes(executionStatus.status) ? <CheckCircle className="w-3 h-3 text-green-500" /> : <AlertCircle className="w-3 h-3 text-red-500" />}
                                      {executionStatus.status.toUpperCase()}
                                    </span>
                                  </td>
                                  <td className="px-3 py-3">
                                    <span className="flex items-center gap-1">
                                      {executionStatus.optimization_status === 'decoded' || executionStatus.optimization_status === 'SUCCESS' ? <CheckCircle className="w-3 h-3 text-green-500" /> : <AlertCircle className="w-3 h-3 text-orange-500" />}
                                      {executionStatus.optimization_status?.toUpperCase() || 'UNKNOWN'}
                                    </span>
                                  </td>
                                  <td className="px-3 py-3">
                                    <span className="flex items-center gap-1">
                                      {(executionStatus.scientific_comparability as boolean | undefined) !== false ? <CheckCircle className="w-3 h-3 text-green-500" /> : <AlertCircle className="w-3 h-3 text-red-500" />}
                                      {(executionStatus.scientific_comparability as boolean | undefined) !== false ? 'COMPARABLE' : 'NON-COMPARABLE'}
                                    </span>
                                  </td>
                                  <td className="px-3 py-3 text-slate-400">
                                    {executionStatus.executionTimeMs}ms
                                  </td>
                                  <td className="px-3 py-3">
                                    {executionStatus.taskArn ? (
                                      <span className="text-[10px] font-mono text-slate-500 truncate block max-w-[150px]" title={executionStatus.taskArn}>
                                        {executionStatus.taskArn.split(':').pop()}
                                      </span>
                                    ) : '-'}
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                          
                          <div className="space-y-2">
                            <Label className="text-xs text-slate-500">Raw Telemetry Data</Label>
                            <div className="p-4 bg-slate-900 border border-slate-800 rounded-md">
                              <pre className="text-[10px] text-slate-400 font-mono overflow-auto max-h-[200px]">
                                {JSON.stringify(executionStatus, null, 2)}
                              </pre>
                            </div>
                          </div>
                          </div>
                        );
                      })()}
                    </div>
                  </CardContent>
                </Card>
              )}

              {!executionStatus && (
                <div className="text-center text-gray-500 py-8">
                  No execution in progress. Submit a benchmark to see status.
                </div>
              )}
            </TabsContent>
          </Tabs>

          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default BenchmarkExecutionWorkflow;
