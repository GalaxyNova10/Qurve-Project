import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Clock, 
  Eye, 
  AlertTriangle, 
  CheckCircle, 
  BarChart3,
  GitBranch,
  Activity,
  Database,
  RefreshCw,
  Search
} from 'lucide-react';

interface TimelineEvent {
  eventId: string;
  timestamp: number;
  eventType: string;
  description: string;
  operatorId?: string;
  metadata?: any;
}

interface DivergenceAnalysis {
  correlationId: string;
  divergenceScore: number;
  divergenceType: string;
  divergenceDetails: {
    timingDivergence: number;
    resultDivergence: number;
    governanceDivergence: number;
  };
  affectedComponents: string[];
}

interface FallbackChain {
  correlationId: string;
  fallbackSteps: Array<{
    from: string;
    to: string;
    timestamp: number;
    reason: string;
    success: boolean;
  }>;
  totalFallbacks: number;
  finalResult: string;
}

interface ReplayArtifact {
  artifactId: string;
  correlationId: string;
  artifactType: string;
  reconstructedData: any;
  metadata: {
    reconstructedArtifact: boolean;
    notOperationalTruth: boolean;
    reconstructionTimestamp: number;
    integrityScore: number;
  };
}

const ReplayForensicInterface: React.FC = () => {
  const [correlationId, setCorrelationId] = useState('');
  const [timelineData, setTimelineData] = useState<TimelineEvent[]>([]);
  const [divergenceData, setDivergenceData] = useState<DivergenceAnalysis | null>(null);
  const [fallbackChainData, setFallbackChainData] = useState<FallbackChain | null>(null);
  const [replayArtifacts, setReplayArtifacts] = useState<ReplayArtifact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<ReplayArtifact | null>(null);

  useEffect(() => {
    if (correlationId) {
      loadReplayData(correlationId);
    }
  }, [correlationId]);

  const loadReplayData = async (id: string) => {
    setLoading(true);
    setError(null);

    try {
      // Load all replay data in parallel
      const [
        timelineResponse,
        divergenceResponse,
        fallbackResponse,
        artifactsResponse
      ] = await Promise.all([
        fetch(`/api/v1/forensic/timeline?correlation_id=${id}`),
        fetch(`/api/v1/forensic/divergence?correlation_id=${id}`),
        fetch(`/api/v1/forensic/fallback_chain?correlation_id=${id}`),
        fetch(`/api/v1/forensic/replay_artifacts?correlation_id=${id}`)
      ]);

      if (!timelineResponse.ok || !divergenceResponse.ok || 
          !fallbackResponse.ok || !artifactsResponse.ok) {
        throw new Error('Failed to load replay data');
      }

      const [
        timelineResult,
        divergenceResult,
        fallbackResult,
        artifactsResult
      ] = await Promise.all([
        timelineResponse.json(),
        divergenceResponse.json(),
        fallbackResponse.json(),
        artifactsResponse.json()
      ]);

      setTimelineData(timelineResult.timeline_data.events || []);
      setDivergenceData(divergenceResult.divergence_data);
      setFallbackChainData(fallbackResult.fallback_chain_data);
      setReplayArtifacts(artifactsResult.replay_artifacts || []);

    } catch (error) {
      console.error('Failed to load replay data:', error);
      setError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'execution_start':
      case 'governance_approval':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'fallback_transition':
      case 'divergence_detected':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'execution_complete':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case 'execution_failed':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getDivergenceColor = (score: number) => {
    if (score < 0.1) return 'text-green-600';
    if (score < 0.3) return 'text-yellow-600';
    if (score < 0.5) return 'text-orange-600';
    return 'text-red-600';
  };

  const getFallbackIcon = (success: boolean) => {
    return success ? 
      <CheckCircle className="w-4 h-4 text-green-500" /> :
      <AlertTriangle className="w-4 h-4 text-red-500" />;
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header with Warning */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Eye className="w-6 h-6" />
          <h1 className="text-3xl font-bold">Replay Forensic Interface</h1>
        </div>
        
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-yellow-800">
            <strong>IMPORTANT:</strong> This interface displays RECONSTRUCTED ARTIFACTS — NOT OPERATIONAL TRUTH.
            All data shown is from replay reconstruction and should not be used for operational decisions.
          </AlertDescription>
        </Alert>
      </div>

      {/* Search Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Replay Search
          </CardTitle>
          <CardDescription>
            Enter correlation ID to load replay forensic data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="correlationId">Correlation ID</Label>
              <Input
                id="correlationId"
                value={correlationId}
                onChange={(e) => setCorrelationId(e.target.value)}
                placeholder="Enter correlation ID (e.g., exec_1234567890)"
              />
            </div>
            <div className="flex items-end">
              <Button 
                onClick={() => correlationId && loadReplayData(correlationId)}
                disabled={!correlationId || loading}
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Search className="w-4 h-4 mr-2" />
                )}
                Load Replay Data
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {correlationId && !loading && (
        <Tabs defaultValue="timeline" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="divergence">Divergence</TabsTrigger>
            <TabsTrigger value="fallback">Fallback Chain</TabsTrigger>
            <TabsTrigger value="artifacts">Artifacts</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>

          {/* Timeline Visualization */}
          <TabsContent value="timeline" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Execution Timeline
                </CardTitle>
                <CardDescription>
                  Chronological events for correlation: {correlationId}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {timelineData.map((event, index) => (
                    <div key={event.eventId} className="flex items-start gap-4">
                      <div className="flex flex-col items-center">
                        {getEventIcon(event.eventType)}
                        {index < timelineData.length - 1 && (
                          <div className="w-0.5 h-16 bg-gray-300 mt-2" />
                        )}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {event.eventType.replace('_', ' ').toUpperCase()}
                          </Badge>
                          <span className="text-sm text-gray-500">
                            {formatTimestamp(event.timestamp)}
                          </span>
                        </div>
                        <p className="text-sm">{event.description}</p>
                        {event.operatorId && (
                          <p className="text-xs text-gray-500">
                            Operator: {event.operatorId}
                          </p>
                        )}
                        {event.metadata && (
                          <details className="text-xs">
                            <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                              View Metadata
                            </summary>
                            <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-auto">
                              {JSON.stringify(event.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Divergence Analysis */}
          <TabsContent value="divergence" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Divergence Analysis
                  </CardTitle>
                  <CardDescription>
                    Overall divergence metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {divergenceData && (
                    <div className="space-y-4">
                      <div className="text-center">
                        <div className={`text-4xl font-bold ${getDivergenceColor(divergenceData.divergenceScore)}`}>
                          {(divergenceData.divergenceScore * 100).toFixed(1)}%
                        </div>
                        <p className="text-sm text-gray-600">Divergence Score</p>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Divergence Type:</span>
                          <Badge variant="outline">
                            {divergenceData.divergenceType.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Timing Divergence:</span>
                          <span className={getDivergenceColor(divergenceData.divergenceDetails.timingDivergence)}>
                            {(divergenceData.divergenceDetails.timingDivergence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Result Divergence:</span>
                          <span className={getDivergenceColor(divergenceData.divergenceDetails.resultDivergence)}>
                            {(divergenceData.divergenceDetails.resultDivergence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Governance Divergence:</span>
                          <span className={getDivergenceColor(divergenceData.divergenceDetails.governanceDivergence)}>
                            {(divergenceData.divergenceDetails.governanceDivergence * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Affected Components
                  </CardTitle>
                  <CardDescription>
                    Components showing divergence
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {divergenceData && (
                    <div className="space-y-2">
                      {divergenceData.affectedComponents.map((component, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-yellow-500" />
                          <Badge variant="outline">{component}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Fallback Chain Visualization */}
          <TabsContent value="fallback" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  Fallback Chain Analysis
                </CardTitle>
                <CardDescription>
                  Fallback transitions and decisions
                </CardDescription>
              </CardHeader>
              <CardContent>
                {fallbackChainData && (
                  <div className="space-y-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {fallbackChainData.totalFallbacks}
                      </div>
                      <p className="text-sm text-gray-600">Total Fallbacks</p>
                    </div>
                    
                    <div className="space-y-3">
                      {fallbackChainData.fallbackSteps.map((step, index) => (
                        <div key={index} className="flex items-center gap-4">
                          <div className="flex flex-col items-center">
                            {getFallbackIcon(step.success)}
                            {index < fallbackChainData.fallbackSteps.length - 1 && (
                              <div className="w-0.5 h-12 bg-gray-300 mt-2" />
                            )}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">
                                {step.from} → {step.to}
                              </Badge>
                              <span className="text-sm text-gray-500">
                                {formatTimestamp(step.timestamp)}
                              </span>
                            </div>
                            <p className="text-sm">{step.reason}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="mt-4 p-4 bg-gray-50 rounded">
                      <p className="text-sm">
                        <strong>Final Result:</strong> {fallbackChainData.finalResult}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Replay Artifacts */}
          <TabsContent value="artifacts" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Replay Artifacts
                </CardTitle>
                <CardDescription>
                  Reconstructed execution artifacts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Warning Banner */}
                  <Alert className="border-red-200 bg-red-50">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription className="text-red-800">
                      <strong>RECONSTRUCTED ARTIFACT — NOT OPERATIONAL TRUTH</strong>
                      <br />
                      These are reconstructed artifacts from replay data and should not be used for operational decisions.
                    </AlertDescription>
                  </Alert>

                  {/* Artifact List */}
                  <div className="space-y-2">
                    {replayArtifacts.map((artifact, index) => (
                      <div key={index} className="border rounded p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">
                              {artifact.artifactType.toUpperCase()}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              {artifact.artifactId}
                            </span>
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setSelectedArtifact(artifact)}
                          >
                            View Details
                          </Button>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="font-medium">Integrity Score:</span>{' '}
                            <span className={
                              artifact.metadata.integrityScore > 0.9 ? 'text-green-600' :
                              artifact.metadata.integrityScore > 0.7 ? 'text-yellow-600' :
                              'text-red-600'
                            }>
                              {(artifact.metadata.integrityScore * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="font-medium">Reconstructed:</span>{' '}
                            {artifact.metadata.reconstructedArtifact ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Metadata */}
          <TabsContent value="metadata" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Replay Metadata
                </CardTitle>
                <CardDescription>
                  Comprehensive replay metadata and system information
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Replay Information</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <strong>Correlation ID:</strong> {correlationId}
                      </div>
                      <div>
                        <strong>Timeline Events:</strong> {timelineData.length}
                      </div>
                      <div>
                        <strong>Divergence Score:</strong>{' '}
                        {divergenceData ? `${(divergenceData.divergenceScore * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div>
                        <strong>Fallback Count:</strong>{' '}
                        {fallbackChainData ? fallbackChainData.totalFallbacks : 'N/A'}
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-2">System Status</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Replay System Available</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Timeline Reconstruction</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Divergence Analysis</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Fallback Chain Tracking</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Artifact Detail Modal */}
      {selectedArtifact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-auto">
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Artifact Details</h3>
                <Button 
                  variant="outline" 
                  onClick={() => setSelectedArtifact(null)}
                >
                  Close
                </Button>
              </div>
              
              <Alert className="border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-red-800">
                  <strong>RECONSTRUCTED ARTIFACT — NOT OPERATIONAL TRUTH</strong>
                </AlertDescription>
              </Alert>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Artifact Information</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><strong>ID:</strong> {selectedArtifact.artifactId}</div>
                    <div><strong>Type:</strong> {selectedArtifact.artifactType}</div>
                    <div><strong>Correlation ID:</strong> {selectedArtifact.correlationId}</div>
                    <div><strong>Integrity Score:</strong> {(selectedArtifact.metadata.integrityScore * 100).toFixed(1)}%</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium">Reconstructed Data</h4>
                  <pre className="p-4 bg-gray-50 rounded text-xs overflow-auto max-h-96">
                    {JSON.stringify(selectedArtifact.reconstructedData, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReplayForensicInterface;
