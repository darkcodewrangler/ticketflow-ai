import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { 
  Brain, 
  Search, 
  FileText, 
  Zap, 
  CheckCircle, 
  Clock,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  Eye,
  ChevronRight
} from "lucide-react";
import { WorkflowStep, WorkflowResponse } from "@/types";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

interface WorkflowVisualizerProps {
  workflow: WorkflowResponse;
  onStepClick?: (step: WorkflowStep) => void;
  showDetails?: boolean;
  compact?: boolean;
  className?: string;
}

const stepIcons = {
  ticket_analysis: Brain,
  knowledge_search: Search,
  similar_cases: FileText,
  solution_generation: Zap,
  confidence_check: CheckCircle,
  external_action: ChevronRight
};

const stepLabels = {
  ticket_analysis: "Ticket Analysis",
  knowledge_search: "Knowledge Search", 
  similar_cases: "Similar Cases",
  solution_generation: "Solution Generation",
  confidence_check: "Confidence Check",
  external_action: "External Action"
};

const stepDescriptions = {
  ticket_analysis: "Analyzing ticket content and extracting key information",
  knowledge_search: "Searching knowledge base for relevant articles",
  similar_cases: "Finding similar resolved cases for reference",
  solution_generation: "Generating solution based on analysis",
  confidence_check: "Validating solution confidence score",
  external_action: "Performing external API calls or actions"
};

export const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  workflow,
  onStepClick,
  showDetails = true,
  compact = false,
  className = ""
}) => {
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);
  const [isPlaying, setIsPlaying] = useState(workflow.status === 'processing');

  const getStepStatus = (step: WorkflowStep) => {
    switch (step.status) {
      case 'completed':
        return { color: 'text-green-600', bgColor: 'bg-green-50', borderColor: 'border-green-200' };
      case 'processing':
        return { color: 'text-blue-600', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' };
      case 'failed':
        return { color: 'text-red-600', bgColor: 'bg-red-50', borderColor: 'border-red-200' };
      default:
        return { color: 'text-gray-400', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' };
    }
  };

  const getWorkflowProgress = () => {
    const completedSteps = workflow.steps.filter(s => s.status === 'completed').length;
    return (completedSteps / workflow.steps.length) * 100;
  };

  const getCurrentStep = () => {
    return workflow.steps.find(s => s.status === 'processing') || 
           workflow.steps[workflow.steps.filter(s => s.status === 'completed').length];
  };

  const handleStepClick = (step: WorkflowStep) => {
    setSelectedStep(step);
    onStepClick?.(step);
  };

  if (compact) {
    return (
      <Card className={cn("w-full", className)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={
                workflow.status === 'completed' ? 'border-green-200 text-green-800' :
                workflow.status === 'processing' ? 'border-blue-200 text-blue-800' :
                workflow.status === 'failed' ? 'border-red-200 text-red-800' :
                'border-gray-200 text-gray-800'
              }>
                {workflow.status}
              </Badge>
              <span className="text-sm font-medium">Ticket #{workflow.ticket_id}</span>
            </div>
            <span className="text-xs text-gray-500">
              {workflow.steps.filter(s => s.status === 'completed').length} / {workflow.steps.length}
            </span>
          </div>
          
          <Progress value={getWorkflowProgress()} className="h-2 mb-2" />
          
          <div className="flex items-center gap-2">
            {workflow.steps.map((step, index) => {
              const StepIcon = stepIcons[step.step as keyof typeof stepIcons] || Clock;
              const status = getStepStatus(step);
              
              return (
                <div
                  key={`${step.step}-${index}`}
                  className={cn(
                    "w-6 h-6 rounded-full border-2 flex items-center justify-center",
                    status.borderColor,
                    status.bgColor
                  )}
                  title={stepLabels[step.step as keyof typeof stepLabels]}
                >
                  <StepIcon className={cn("w-3 h-3", status.color)} />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            Workflow: Ticket #{workflow.ticket_id}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={
              workflow.status === 'completed' ? 'border-green-200 text-green-800 bg-green-50' :
              workflow.status === 'processing' ? 'border-blue-200 text-blue-800 bg-blue-50' :
              workflow.status === 'failed' ? 'border-red-200 text-red-800 bg-red-50' :
              'border-gray-200 text-gray-800 bg-gray-50'
            }>
              {workflow.status}
            </Badge>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">
              Progress: {workflow.steps.filter(s => s.status === 'completed').length} of {workflow.steps.length} steps
            </span>
            <span className="text-sm font-medium">
              {getWorkflowProgress().toFixed(0)}%
            </span>
          </div>
          <Progress value={getWorkflowProgress()} className="h-3" />
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {workflow.steps.map((step, index) => {
            const StepIcon = stepIcons[step.step as keyof typeof stepIcons] || Clock;
            const status = getStepStatus(step);
            const isLast = index === workflow.steps.length - 1;
            const isSelected = selectedStep?.step === step.step;
            
            return (
              <div key={`${step.step}-${index}`} className="relative">
                {/* Timeline line */}
                {!isLast && (
                  <div className="absolute left-6 top-12 w-0.5 h-16 bg-gray-200"></div>
                )}
                
                <div 
                  className={cn(
                    "flex items-start gap-4 p-3 rounded-lg cursor-pointer transition-all",
                    isSelected && "bg-blue-50 border border-blue-200",
                    !isSelected && "hover:bg-gray-50"
                  )}
                  onClick={() => handleStepClick(step)}
                >
                  {/* Step icon */}
                  <div className={cn(
                    "flex items-center justify-center w-12 h-12 rounded-full border-2",
                    status.borderColor,
                    status.bgColor,
                    step.status === 'processing' && "animate-pulse"
                  )}>
                    <StepIcon className={cn("w-5 h-5", status.color)} />
                  </div>
                  
                  {/* Step content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900">
                        {stepLabels[step.step as keyof typeof stepLabels] || step.step}
                      </h3>
                      <Badge variant="outline" className={cn(
                        "text-xs",
                        step.status === 'completed' && "border-green-200 text-green-800",
                        step.status === 'processing' && "border-blue-200 text-blue-800",
                        step.status === 'failed' && "border-red-200 text-red-800",
                        step.status === 'pending' && "border-gray-200 text-gray-600"
                      )}>
                        {step.status}
                      </Badge>
                      {step.status === 'processing' && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-2">
                      {step.message}
                    </p>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>
                        {formatDistanceToNow(new Date(step.timestamp), { addSuffix: true })}
                      </span>
                      {step.duration_ms && (
                        <span>
                          Duration: {(step.duration_ms / 1000).toFixed(1)}s
                        </span>
                      )}
                    </div>
                    
                    {/* Step data */}
                    {showDetails && step.data && Object.keys(step.data).length > 0 && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Step Data:</h4>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {Object.entries(step.data).map(([key, value]) => (
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
                  
                  {/* Step actions */}
                  <div className="flex flex-col gap-1">
                    <Button variant="ghost" size="sm" onClick={(e) => {
                      e.stopPropagation();
                      handleStepClick(step);
                    }}>
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Workflow Controls */}
        {workflow.status === 'processing' && (
          <div className="mt-6 pt-4 border-t">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPlaying(!isPlaying)}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  {isPlaying ? 'Pause' : 'Resume'}
                </Button>
                <Button variant="outline" size="sm">
                  <RotateCcw className="w-4 h-4 mr-1" />
                  Restart
                </Button>
              </div>
              
              <div className="text-sm text-gray-600">
                Current: {getCurrentStep()?.step && stepLabels[getCurrentStep()!.step as keyof typeof stepLabels]}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};