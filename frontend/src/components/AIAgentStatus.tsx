import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Bot,
  Cpu,
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle,
  Zap,
  Database,
  Network,
  RefreshCw,
  Settings,
  Play,
  Eye,
  Pause,
} from "lucide-react";
import { useAppContext } from "@/contexts/AppContext";
import { cn } from "@/lib/utils";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { api } from "@/services/api";
import { DashboardMetrics } from "@/types";
import { useDashboardMetrics } from "@/hooks";

interface AgentMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_workflows: number;
  queue_size: number;
  success_rate: number;
  avg_processing_time_ms: number;
  uptime: number;
  last_heartbeat: string;
}

interface AIAgentStatusProps {
  showControls?: boolean;
  compact?: boolean;
  className?: string;
}

// Mock agent metrics
const mockMetrics: AgentMetrics = {
  cpu_usage: 45,
  memory_usage: 62,
  uptime: 99.8,
  last_heartbeat: new Date().toISOString(),
  active_workflows: 3,
  queue_size: 7,
  success_rate: 0.94,
  avg_processing_time_ms: 2300,
};

export const AIAgentStatus: React.FC<AIAgentStatusProps> = ({
  showControls = true,
  compact = false,
  className = "",
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { connectionStatus, connectWebSocket, disconnectWebSocket } =
    useAppContext();
  const { data: apiMetrics, error } = useDashboardMetrics();
  const metrics = apiMetrics || mockMetrics;
  // Simulate real-time metrics updates
  // useEffect(() => {
  //   const interval = setInterval(() => {
  //     setMetrics((prev) => ({
  //       ...prev,
  //       cpu_usage: Math.max(
  //         20,
  //         Math.min(80, prev.cpu_usage + (Math.random() - 0.5) * 10)
  //       ),
  //       memory_usage: Math.max(
  //         40,
  //         Math.min(90, prev.memory_usage + (Math.random() - 0.5) * 5)
  //       ),
  //       active_workflows: Math.max(
  //         0,
  //         Math.min(
  //           10,
  //           prev.active_workflows + Math.floor((Math.random() - 0.5) * 3)
  //         )
  //       ),
  //       queue_size: Math.max(
  //         0,
  //         Math.min(20, prev.queue_size + Math.floor((Math.random() - 0.5) * 4))
  //       ),
  //       last_heartbeat: new Date().toISOString(),
  //     }));
  //   }, 5000);

  //   return () => clearInterval(interval);
  // }, []);

  const handleRefreshMetrics = async () => {
    setIsRefreshing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsRefreshing(false);
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case "connected":
        return "text-green-600 bg-green-50 border-green-200";
      case "connecting":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "error":
        return "text-red-600 bg-red-50 border-red-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getHealthStatus = () => {
    if (connectionStatus !== "connected") return "offline";
    if (metrics?.cpu_usage > 80 || metrics?.memory_usage > 85) return "warning";
    return "healthy";
  };

  const healthStatus = getHealthStatus();

  if (compact) {
    return (
      <Card className={cn("w-full", className)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "w-10 h-10 rounded-full border-2 flex items-center justify-center",
                  connectionStatus === "connected"
                    ? "border-green-500 bg-green-50"
                    : "border-gray-300 bg-gray-50"
                )}
              >
                <Bot
                  className={cn(
                    "w-5 h-5",
                    connectionStatus === "connected"
                      ? "text-green-600"
                      : "text-gray-400"
                  )}
                />
              </div>
              <div>
                <h3 className="font-medium">AI Agent</h3>
                <p className="text-sm text-gray-600">
                  {connectionStatus === "connected" ? "Online" : "Offline"}
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className="text-sm font-medium">
                {metrics.active_workflows} active
              </p>
              <p className="text-xs text-gray-500">
                {metrics.queue_size} queued
              </p>
            </div>
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
            {/* <Bot className="w-5 h-5 text-blue-600" /> */}
            {/* AI Agent Status */}
          </CardTitle>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className={getStatusColor()}>
              {connectionStatus}
            </Badge>
            {showControls && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshMetrics}
                disabled={isRefreshing}
              >
                <RefreshCw
                  className={cn("w-4 h-4", isRefreshing && "animate-spin")}
                />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Health Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div
              className={cn(
                "w-12 h-12 rounded-full border-2 flex items-center justify-center mx-auto mb-2",
                healthStatus === "healthy"
                  ? "border-green-500 bg-green-50"
                  : healthStatus === "warning"
                  ? "border-yellow-500 bg-yellow-50"
                  : "border-red-500 bg-red-50"
              )}
            >
              <Activity
                className={cn(
                  "w-6 h-6",
                  healthStatus === "healthy"
                    ? "text-green-600"
                    : healthStatus === "warning"
                    ? "text-yellow-600"
                    : "text-red-600"
                )}
              />
            </div>
            <p className="text-sm font-medium">Health</p>
            <p className="text-xs text-gray-600 capitalize">{healthStatus}</p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-blue-500 bg-blue-50 flex items-center justify-center mx-auto mb-2">
              <Zap className="w-6 h-6 text-blue-600" />
            </div>
            <p className="text-sm font-medium">Active</p>
            <p className="text-xs text-gray-600">
              {metrics.currently_processing} workflows
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-purple-500 bg-purple-50 flex items-center justify-center mx-auto mb-2">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
            <p className="text-sm font-medium">Queue</p>
            <p className="text-xs text-gray-600">
              {metrics.pending_tickets} pending
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-green-500 bg-green-50 flex items-center justify-center mx-auto mb-2">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-sm font-medium">Success</p>
            <p className="text-xs text-gray-600">
              {(
                (metrics.tickets_auto_resolved_today / metrics.tickets_today ||
                  0) * 100
              ).toFixed(0)}
              %
            </p>
          </div>
        </div>

        {/* Resource Usage */}
        {/* <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium flex items-center gap-2">
                <Cpu className="w-4 h-4 text-gray-500" />
                CPU Usage
              </span>
              <span className="text-sm text-gray-600">
                {metrics.cpu_usage.toFixed(0)}%
              </span>
            </div>
            <Progress
              value={metrics.cpu_usage}
              className={cn("h-2", metrics.cpu_usage > 80 && "bg-red-100")}
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium flex items-center gap-2">
                <Database className="w-4 h-4 text-gray-500" />
                Memory Usage
              </span>
              <span className="text-sm text-gray-600">
                {metrics.memory_usage.toFixed(0)}%
              </span>
            </div>
            <Progress
              value={metrics.memory_usage}
              className={cn("h-2", metrics.memory_usage > 85 && "bg-red-100")}
            />
          </div>
        </div> */}

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm font-medium text-gray-700">
              Avg Processing Time
            </p>
            <p className="text-lg font-bold text-blue-600">
              {metrics.avg_processing_time_ms / 1000}s
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700">Uptime</p>
            <p className="text-lg font-bold text-green-600">
              {metrics.uptime || 94}%
            </p>
          </div>
        </div>

        {/* Agent Controls */}
        {showControls && (
          <div className="flex items-center gap-2 pt-4 border-t">
            {connectionStatus === "connected" ? (
              <Button variant="outline" size="sm" onClick={disconnectWebSocket}>
                <Pause className="w-4 h-4 mr-1" />
                Disconnect
              </Button>
            ) : (
              <Button variant="outline" size="sm" onClick={connectWebSocket}>
                <Play className="w-4 h-4 mr-1" />
                Connect
              </Button>
            )}

            <Button variant="outline" size="sm" asChild>
              <Link to="/settings">
                <Settings className="w-4 h-4 mr-1" />
                Configure
              </Link>
            </Button>

            <Button variant="outline" size="sm" asChild>
              <Link to="/processing">
                <Eye className="w-4 h-4 mr-1" />
                Monitor
              </Link>
            </Button>
          </div>
        )}

        {/* Last Heartbeat */}
        <div className="text-xs text-gray-500 pt-2 border-t">
          Last heartbeat:{" "}
          {formatDistanceToNow(new Date(metrics.last_heartbeat || new Date()), {
            addSuffix: true,
          })}
        </div>
      </CardContent>
    </Card>
  );
};
