import { useEffect, useCallback, useMemo } from "react";
import { useAppContext } from "@/contexts/AppContext";
import { MetricCard } from "@/components/MetricCard";
import { ActivityFeed } from "@/components/ActivityFeed";
import { QuickActions } from "@/components/QuickActions";
import { NotificationCenter } from "@/components/NotificationCenter";
import { AIAgentStatus } from "@/components/AIAgentStatus";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/StatusBadge";
import { PriorityBadge } from "@/components/PriorityBadge";
import {
  RefreshCw,
  Plus,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertTriangle,
  Bot,
  Zap,
  Bell,
  Eye,
} from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "@/services/api";
import { useState } from "react";
import { Ticket } from "@/types";
// Import React Query hooks
import { useDashboardMetrics } from "@/hooks/useAnalytics";
import { useRecentTickets } from "@/hooks/useTickets";

// Mock recent tickets data - kept as backup
const mockRecentTickets = [
  {
    id: 1,
    title: "Email integration not working",
    status: "processing" as const,
    priority: "high" as const,
    category: "Integration",
    created_at: "2024-01-15T10:30:00Z",
    user_email: "user@company.com",
  },
  {
    id: 2,
    title: "Password reset functionality broken",
    status: "resolved" as const,
    priority: "medium" as const,
    category: "Authentication",
    created_at: "2024-01-15T09:15:00Z",
    user_email: "admin@company.com",
  },
  {
    id: 3,
    title: "Dashboard loading slowly",
    status: "new" as const,
    priority: "low" as const,
    category: "Performance",
    created_at: "2024-01-15T08:45:00Z",
    user_email: "support@company.com",
  },
  {
    id: 4,
    title: "Critical security vulnerability",
    status: "escalated" as const,
    priority: "urgent" as const,
    category: "Security",
    created_at: "2024-01-15T07:20:00Z",
    user_email: "security@company.com",
  },
];

export default function Dashboard() {
  const {
    metrics,
    liveUpdates,
    refreshMetrics,
    metricsLoading,
    connectionStatus,
    connectWebSocket,
  } = useAppContext();

  // React Query hooks for API data
  const {
    data: apiMetrics,
    isLoading: apiMetricsLoading,
    error: metricsError,
    refetch: refetchMetrics,
  } = useDashboardMetrics();

  const {
    data: recentTickets,
    isLoading: ticketsLoading,
    error: ticketsError,
    refetch: refetchTickets,
  } = useRecentTickets();

  // Use API data if available, fallback to context metrics or mock data
  const displayMetrics = apiMetrics || metrics;
  const displayRecentTickets = recentTickets || mockRecentTickets;
  const isLoadingMetrics = apiMetricsLoading || metricsLoading;

  // Connect to WebSocket only once when component mounts
  useEffect(() => {
    let mounted = true;

    if (connectionStatus === "disconnected" && mounted) {
      connectWebSocket();
    }

    return () => {
      mounted = false;
    };
  }, []); // Remove connectionStatus from dependencies to prevent reconnection loops

  // Memoize the refresh handler to prevent unnecessary re-renders
  const handleRefreshMetrics = useCallback(async () => {
    // Refetch both API data and context metrics
    await Promise.all([refetchMetrics(), refetchTickets(), refreshMetrics()]);
  }, [refetchMetrics, refetchTickets, refreshMetrics]);

  // Memoize metric card props to prevent unnecessary re-renders
  const metricCardProps = useMemo(
    () => [
      {
        title: "Total Tickets",
        value: displayMetrics?.all_tickets || 0,
        format: "number" as const,
        loading: isLoadingMetrics,
        change: {
          value: 12,
          direction: "up" as const,
          period: "last week",
        },
        status: "positive" as const,
      },
      {
        title: "Auto-Resolved",
        value: displayMetrics?.success_rate || 0,
        format: "percentage" as const,
        loading: isLoadingMetrics,
        change: {
          value: 0.05,
          direction: "up" as const,
          period: "last week",
        },
        status: "positive" as const,
      },
      {
        title: "Avg Resolution Time",
        value: displayMetrics?.avg_resolution_time_hours || 0,
        format: "duration" as const,
        loading: isLoadingMetrics,
        change: {
          value: 0.3,
          direction: "down" as const,
          period: "last week",
        },
        status: "negative" as const,
      },
      {
        title: "Today's Tickets",
        value: displayMetrics?.tickets_today || 0,
        format: "number" as const,
        loading: isLoadingMetrics,
        change: {
          value: 3,
          direction: "up" as const,
          period: "yesterday",
        },
        status: "positive" as const,
      },
    ],
    [displayMetrics, isLoadingMetrics]
  );
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            AI-powered support ticket automation system
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={handleRefreshMetrics}
            disabled={isLoadingMetrics}
            className="flex items-center gap-2"
          >
            <RefreshCw
              className={`w-4 h-4 ${isLoadingMetrics ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>

          <Link to="/tickets/new">
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              New Ticket
            </Button>
          </Link>
        </div>
      </div>

      {/* Connection Status Alert */}
      {connectionStatus !== "connected" && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-800">
                Real-time updates unavailable
              </p>
              <p className="text-xs text-yellow-700">
                {connectionStatus === "connecting"
                  ? "Connecting to TicketFlow AI..."
                  : "Unable to connect to the AI agent system"}
              </p>
            </div>
            {connectionStatus === "disconnected" && (
              <Button
                variant="outline"
                size="sm"
                onClick={connectWebSocket}
                className="border-yellow-300 text-yellow-700 hover:bg-yellow-100"
              >
                Retry Connection
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricCardProps.map((props, index) => (
          <MetricCard key={props.title} {...props} />
        ))}
      </div>

      {/* Quick Actions */}
      {/* <QuickActions maxActions={8} /> */}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Activity Feed */}
        <div className="lg:col-span-1 space-y-6">
          <ActivityFeed items={liveUpdates} />
          <AIAgentStatus compact />
        </div>

        {/* Right Column - Recent Tickets & Notifications */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Tickets */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-semibold">
                Recent Tickets
              </CardTitle>
              <Link to="/tickets">
                <Button variant="outline" size="sm">
                  <Eye className="w-4 h-4 mr-1" />
                  View All
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {displayRecentTickets.map((ticket) => (
                  <Link key={ticket.id} to={`/tickets/${ticket.id}`}>
                    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-medium text-gray-900">
                            #{ticket.id}
                          </span>
                          <h3 className="font-medium text-gray-900 truncate">
                            {ticket.title}
                          </h3>
                        </div>

                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <span>{ticket.category}</span>
                          <span>•</span>
                          <span>{ticket.user_email}</span>
                          <span>•</span>
                          <span>
                            {new Date(ticket.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <PriorityBadge priority={ticket.priority} />
                        <StatusBadge
                          status={ticket.status}
                          pulse={ticket.status === "processing"}
                        />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          {/* <NotificationCenter maxNotifications={5} /> */}
        </div>
      </div>

      {/* AI Agent Status - Full Width */}
      <AIAgentStatus showControls />
    </div>
  );
}
