import { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { WorkflowVisualizer } from "@/components/WorkflowVisualizer";
import { 
  Bot, 
  Play, 
  Pause, 
  RotateCcw, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Zap,
  Brain,
  Search,
  FileText,
  Send,
  Filter,
  Eye
} from "lucide-react";
import { WorkflowResponse, WorkflowStep } from "@/types";
import { useAppContext } from "@/contexts/AppContext";
import { formatDistanceToNow } from "date-fns";

// Move static data outside component to prevent recreation
const stepIcons = {
  ticket_analysis: Brain,
  knowledge_search: Search,
  similar_cases: FileText,
  solution_generation: Zap,
  confidence_check: CheckCircle,
  external_action: Send
};

const stepLabels = {
  ticket_analysis: "Ticket Analysis",
  knowledge_search: "Knowledge Search",
  similar_cases: "Similar Cases",
  solution_generation: "Solution Generation",
  confidence_check: "Confidence Check",
  external_action: "External Action"
};

// Mock workflow data - moved outside to prevent recreation
const initialMockWorkflows: WorkflowResponse[] = [
  {
    workflow_id: "wf_001",
    ticket_id: 1,
    status: "processing",
    steps: [
      {
        step: "ticket_analysis",
        status: "completed",
        message: "Analyzed ticket content and extracted key information",
        timestamp: "2024-01-15T10:30:00Z",
        duration_ms: 1200,
        data: { confidence: 0.95, category: "Integration", priority: "high" }
      },
      {
        step: "knowledge_search",
        status: "completed",
        message: "Found 3 relevant knowledge base articles",
        timestamp: "2024-01-15T10:30:05Z",
        duration_ms: 2800,
        data: { articles_found: 3, relevance_score: 0.87 }
      },
      {
        step: "similar_cases",
        status: "processing",
        message: "Searching for similar resolved cases...",
        timestamp: "2024-01-15T10:30:08Z",
        data: { cases_analyzed: 15, similarity_threshold: 0.8 }
      },
      {
        step: "solution_generation",
        status: "pending",
        message: "Waiting to generate solution",
        timestamp: "2024-01-15T10:30:08Z"
      },
      {
        step: "confidence_check",
        status: "pending",
        message: "Waiting for confidence validation",
        timestamp: "2024-01-15T10:30:08Z"
      }
    ]
  },
  {
    workflow_id: "wf_002",
    ticket_id: 5,
    status: "completed",
    steps: [
      {
        step: "ticket_analysis",
        status: "completed",
        message: "Analyzed mobile app crash reports",
        timestamp: "2024-01-15T09:15:00Z",
        duration_ms: 1500,
        data: { confidence: 0.88, category: "Mobile", priority: "high" }
      },
      {
        step: "knowledge_search",
        status: "completed",
        message: "Found relevant crash debugging guides",
        timestamp: "2024-01-15T09:15:03Z",
        duration_ms: 2200,
        data: { articles_found: 2, relevance_score: 0.92 }
      },
      {
        step: "similar_cases",
        status: "completed",
        message: "Found 2 similar resolved crash issues",
        timestamp: "2024-01-15T09:15:06Z",
        duration_ms: 3100,
        data: { cases_found: 2, avg_similarity: 0.85 }
      },
      {
        step: "solution_generation",
        status: "completed",
        message: "Generated solution based on similar cases",
        timestamp: "2024-01-15T09:15:10Z",
        duration_ms: 4200,
        data: { solution_confidence: 0.91 }
      },
      {
        step: "confidence_check",
        status: "completed",
        message: "Solution meets confidence threshold (91%)",
        timestamp: "2024-01-15T09:15:15Z",
        duration_ms: 800,
        data: { final_confidence: 0.91, threshold: 0.85 }
      }
    ]
  },
  {
    workflow_id: "wf_003",
    ticket_id: 8,
    status: "processing",
    steps: [
      {
        step: "ticket_analysis",
        status: "completed",
        message: "Analyzed database performance issue",
        timestamp: "2024-01-15T11:00:00Z",
        duration_ms: 1800,
        data: { confidence: 0.82, category: "Performance", priority: "medium" }
      },
      {
        step: "knowledge_search",
        status: "processing",
        message: "Searching knowledge base for performance solutions...",
        timestamp: "2024-01-15T11:00:05Z",
        data: { search_query: "database performance optimization" }
      },
      {
        step: "similar_cases",
        status: "pending",
        message: "Waiting to analyze similar cases",
        timestamp: "2024-01-15T11:00:05Z"
      },
      {
        step: "solution_generation",
        status: "pending",
        message: "Waiting to generate solution",
        timestamp: "2024-01-15T11:00:05Z"
      },
      {
        step: "confidence_check",
        status: "pending",
        message: "Waiting for confidence validation",
        timestamp: "2024-01-15T11:00:05Z"
      }
    ]
  }
];

export default function LiveProcessing() {
  const [workflows, setWorkflows] = useState<WorkflowResponse[]>(initialMockWorkflows);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(initialMockWorkflows[0]?.workflow_id || null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);
  
  const { connectionStatus } = useAppContext();

  // Memoize selected workflow data
  const selectedWorkflowData = useMemo(() => 
    workflows.find(w => w.workflow_id === selectedWorkflow),
    [workflows, selectedWorkflow]
  );

  // Memoize filtered workflows
  const filteredWorkflows = useMemo(() => 
    workflows.filter(w => filterStatus === 'all' || w.status === filterStatus),
    [workflows, filterStatus]
  );

  // Memoize utility functions
  const getStepProgress = useCallback((steps: WorkflowStep[]) => {
    const completed = steps.filter(s => s.status === 'completed').length;
    return (completed / steps.length) * 100;
  }, []);

  const getWorkflowStatusColor = useCallback((status: WorkflowResponse['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  }, []);

  // Memoize toggle auto-refresh handler
  const toggleAutoRefresh = useCallback(() => {
    setAutoRefresh(prev => !prev);
  }, []);

  const handleStepClick = useCallback((step: WorkflowStep) => {
    setSelectedStep(step);
  }, []);

  // Simulate real-time updates with proper cleanup
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setWorkflows(prev => prev.map(workflow => {
        if (workflow.status === 'processing') {
          const processingStepIndex = workflow.steps.findIndex(s => s.status === 'processing');
          if (processingStepIndex !== -1) {
            // Randomly complete the processing step
            if (Math.random() > 0.7) {
              const updatedSteps = [...workflow.steps];
              updatedSteps[processingStepIndex] = {
                ...updatedSteps[processingStepIndex],
                status: 'completed',
                message: `${stepLabels[updatedSteps[processingStepIndex].step as keyof typeof stepLabels]} completed successfully`,
                duration_ms: Math.floor(Math.random() * 3000) + 1000
              };
              
              // Start next step if available
              if (processingStepIndex + 1 < updatedSteps.length) {
                updatedSteps[processingStepIndex + 1] = {
                  ...updatedSteps[processingStepIndex + 1],
                  status: 'processing',
                  message: `Processing ${stepLabels[updatedSteps[processingStepIndex + 1].step as keyof typeof stepLabels]}...`,
                  timestamp: new Date().toISOString()
                };
              } else {
                // Workflow completed
                return {
                  ...workflow,
                  status: 'completed' as const,
                  steps: updatedSteps
                };
              }
              
              return {
                ...workflow,
                steps: updatedSteps
              };
            }
          }
        }
        return workflow;
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Processing</h1>
          <p className="text-gray-600 mt-1">
            Monitor AI agent workflows in real-time
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => setFilterStatus(filterStatus === 'processing' ? 'all' : 'processing')}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            {filterStatus === 'processing' ? 'Show All' : 'Active Only'}
          </Button>
          
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={toggleAutoRefresh}
            className="flex items-center gap-2"
          >
            {autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {autoRefresh ? 'Pause' : 'Resume'} Auto-refresh
          </Button>
          
          <Button variant="outline" className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Connection Status */}
      {connectionStatus !== 'connected' && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertCircle className="w-5 h-5 text-yellow-600" />
            <div>
              <p className="text-sm font-medium text-yellow-800">
                Real-time updates unavailable
              </p>
              <p className="text-xs text-yellow-700">
                Connect to the AI agent system to see live processing updates
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Workflow Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Workflows</p>
                <p className="text-2xl font-bold">{workflows.length}</p>
              </div>
              <Bot className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Processing</p>
                <p className="text-2xl font-bold text-blue-600">
                  {workflows.filter(w => w.status === 'processing').length}
                </p>
              </div>
              <Clock className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-green-600">
                  {workflows.filter(w => w.status === 'completed').length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Failed</p>
                <p className="text-2xl font-bold text-red-600">
                  {workflows.filter(w => w.status === 'failed').length}
                </p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflow List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-blue-600" />
                Workflows ({filteredWorkflows.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[600px]">
                <div className="space-y-2 p-4">
                  {filteredWorkflows.map((workflow) => (
                    <div
                      key={workflow.workflow_id}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedWorkflow === workflow.workflow_id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedWorkflow(workflow.workflow_id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm">
                          Ticket #{workflow.ticket_id}
                        </span>
                        <Badge className={getWorkflowStatusColor(workflow.status)}>
                          {workflow.status}
                        </Badge>
                      </div>
                      
                      <div className="space-y-2">
                        <Progress value={getStepProgress(workflow.steps)} className="h-2" />
                        <div className="flex justify-between text-xs text-gray-600">
                          <span>
                            {workflow.steps.filter(s => s.status === 'completed').length} / {workflow.steps.length} steps
                          </span>
                          <span>
                            {formatDistanceToNow(new Date(workflow.steps[0].timestamp), { addSuffix: true })}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Workflow Details */}
        <div className="lg:col-span-2">
          {selectedWorkflowData ? (
            <WorkflowVisualizer
              workflow={selectedWorkflowData}
              onStepClick={handleStepClick}
              showDetails={true}
            />
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-[600px]">
                <div className="text-center text-gray-500">
                  <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">No workflow selected</p>
                  <p className="text-sm">Select a workflow from the list to view details</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Step Details Modal/Panel */}
      {selectedStep && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-blue-600" />
                Step Details: {stepLabels[selectedStep.step as keyof typeof stepLabels]}
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setSelectedStep(null)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-2">Step Information</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <Badge variant="outline">{selectedStep.status}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Started:</span>
                    <span>{formatDistanceToNow(new Date(selectedStep.timestamp), { addSuffix: true })}</span>
                  </div>
                  {selectedStep.duration_ms && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Duration:</span>
                      <span>{(selectedStep.duration_ms / 1000).toFixed(1)}s</span>
                    </div>
                  )}
                </div>
              </div>
              
              {selectedStep.data && (
                <div>
                  <h4 className="font-medium mb-2">Step Data</h4>
                  <div className="space-y-2 text-sm">
                    {Object.entries(selectedStep.data).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-600">{key}:</span>
                        <span className="font-medium">
                          {typeof value === 'number' && key.includes('score') 
                            ? `${(value * 100).toFixed(0)}%`
                            : String(value)
                          }
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-4 p-3 bg-white rounded border">
              <p className="text-sm text-gray-700">{selectedStep.message}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}