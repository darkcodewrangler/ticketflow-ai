# TicketFlow AI - Client Application Development Guide

## Overview

This document provides a comprehensive guide for building a modern React client application for TicketFlow AI, an intelligent ticket management system with AI-powered automation. The client should leverage modern tools including **shadcn/ui**, **Zustand** for state management, and **TanStack React Query** for data fetching.

## Application Architecture

### Core Features

- **Ticket Management**: Create, view, update, and track support tickets
- **Real-time Updates**: WebSocket integration for live agent processing updates
- **AI Agent Monitoring**: Track AI workflow execution and confidence scores
- **Knowledge Base**: Browse and search knowledge articles
- **Analytics Dashboard**: Performance metrics and insights
- **Search & Discovery**: Semantic search across tickets and knowledge base
- **Settings Management**: Configure system settings and integrations

### Technology Stack

- **Framework**: React 18+ with TypeScript
- **UI Components**: shadcn/ui (Radix UI + Tailwind CSS)
- **State Management**: Zustand
- **Data Fetching**: TanStack React Query v5
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Forms**: React Hook Form + Zod validation
- **WebSocket**: Native WebSocket API or Socket.io client
- **Charts**: Recharts or Chart.js
- **Date Handling**: date-fns

## API Integration

### Base Configuration

```typescript
// api/config.ts
export const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://localhost:8000";
export const WS_URL = process.env.REACT_APP_WS_URL || "ws://localhost:8000/ws";
```

### API Endpoints

#### Tickets API

- **POST** `/api/tickets/` - Create new ticket
- **GET** `/api/tickets/` - List tickets (with pagination, filters)
- **GET** `/api/tickets/{id}` - Get specific ticket
- **PUT** `/api/tickets/{id}` - Update ticket
- **GET** `/api/tickets/recent` - Get recent tickets

#### Agent Processing API

- **POST** `/api/agent/process` - Process ticket with AI agent
- **GET** `/api/agent/status` - Get agent status and queue info

#### Knowledge Base API

- **POST** `/api/kb/articles` - Create article
- **GET** `/api/kb/articles` - List articles
- **GET** `/api/kb/articles/{id}` - Get specific article
- **POST** `/api/kb/upload` - Upload file for processing
- **POST** `/api/kb/crawl-url` - Process URL content
- **GET** `/api/kb/processing-status/task_id={task_id}` - Check processing status

#### Search API

- **GET** `/api/search/tickets` - Search tickets
- **GET** `/api/search/knowledge-base` - Search knowledge base
- **GET** `/api/search/unified` - Unified search across all content

#### Analytics API

- **GET** `/api/analytics/dashboard` - Dashboard metrics
- **GET** `/api/analytics/performance/daily` - Daily performance data
- **GET** `/api/analytics/performance/summary` - Performance summary
- **GET** `/api/analytics/categories` - Category breakdown
- **GET** `/api/analytics/stats` - Basic statistics

#### Integrations API

- **POST** `/api/integrations/webhook` - Receive external tickets
- **POST** `/api/integrations/webhook/batch` - Batch webhook processing

#### WebSocket Events

- **connection_established** - Initial connection
- **agent_update** - AI agent processing updates
- **ticket_created** - New ticket notifications
- **metrics_update** - Real-time metrics updates

## Data Models & Types

### Core Types

```typescript
// types/ticket.ts
export interface Ticket {
  id: number;
  title: string;
  description: string;
  category: string;
  priority: "low" | "medium" | "high" | "urgent";
  status: "new" | "processing" | "resolved" | "escalated" | "closed";
  user_id: string;
  user_email: string;
  user_type: string;
  resolution: string;
  resolved_by: string;
  resolution_type: "automated" | "human" | "escalated";
  agent_confidence: number;
  processing_duration_ms: number;
  similar_cases_found: number;
  kb_articles_used: number;
  workflow_steps: WorkflowStep[];
  ticket_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
}

export interface TicketCreateRequest {
  title: string;
  description: string;
  category: string;
  priority?: "low" | "medium" | "high" | "urgent";
  user_id?: string;
  user_email?: string;
  user_type?: string;
  ticket_metadata?: Record<string, any>;
}

export interface WorkflowStep {
  step_name: string;
  step_type: string;
  started_at: string;
  completed_at?: string;
  duration_ms: number;
  status: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  error_message: string;
}
```

```typescript
// types/knowledge-base.ts
export interface KnowledgeBaseArticle {
  id: number;
  title: string;
  content: string;
  summary: string;
  category: string;
  tags: string[];
  source_url: string;
  source_type: "manual" | "crawled" | "imported";
  author: string;
  view_count: number;
  helpful_votes: number;
  unhelpful_votes: number;
  usage_in_resolutions: number;
  helpfulness_score: number;
  created_at: string;
  updated_at: string;
  last_accessed?: string;
}

export interface KnowledgeBaseCreateRequest {
  title: string;
  content: string;
  summary?: string;
  category: string;
  tags?: string[];
  source_url?: string;
  source_type?: string;
  author?: string;
}
```

```typescript
// types/analytics.ts
export interface DashboardMetrics {
  tickets_today: number;
  tickets_auto_resolved_today: number;
  currently_processing: number;
  pending_tickets: number;
  avg_confidence: number;
  avg_processing_time_ms: number;
  avg_resolution_hours: number;
  automation_rate: number;
  resolution_rate: number;
  customer_satisfaction_avg: number;
  estimated_time_saved_hours: number;
  estimated_cost_saved: number;
  category_breakdown: Record<string, number>;
  priority_breakdown: Record<string, number>;
}

export interface PerformanceMetrics {
  id: number;
  metric_date: string;
  metric_hour?: number;
  tickets_processed: number;
  tickets_auto_resolved: number;
  tickets_escalated: number;
  avg_confidence_score: number;
  avg_processing_time_ms: number;
  avg_resolution_time_hours: number;
  customer_satisfaction_avg: number;
  resolution_accuracy_rate: number;
  category_breakdown: Record<string, any>;
  priority_breakdown: Record<string, any>;
  estimated_time_saved_hours: number;
  estimated_cost_saved: number;
  created_at: string;
  updated_at: string;
}
```

```typescript
// types/websocket.ts
export interface WebSocketMessage {
  type:
    | "connection_established"
    | "agent_update"
    | "ticket_created"
    | "metrics_update"
    | "pong";
  timestamp: number;
  [key: string]: any;
}

export interface AgentUpdateMessage extends WebSocketMessage {
  type: "agent_update";
  ticket_id: number;
  step: string;
  message: string;
  data: Record<string, any>;
}

export interface TicketCreatedMessage extends WebSocketMessage {
  type: "ticket_created";
  ticket: Ticket;
}

export interface MetricsUpdateMessage extends WebSocketMessage {
  type: "metrics_update";
  metrics: DashboardMetrics;
}
```

## State Management with Zustand

### Ticket Store

```typescript
// stores/ticketStore.ts
import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { Ticket, TicketCreateRequest } from "../types/ticket";

interface TicketState {
  tickets: Ticket[];
  selectedTicket: Ticket | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    status?: string;
    category?: string;
    priority?: string;
    search?: string;
  };

  // Actions
  setTickets: (tickets: Ticket[]) => void;
  addTicket: (ticket: Ticket) => void;
  updateTicket: (id: number, updates: Partial<Ticket>) => void;
  setSelectedTicket: (ticket: Ticket | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<TicketState["filters"]>) => void;
  clearFilters: () => void;
}

export const useTicketStore = create<TicketState>()(
  devtools((set, get) => ({
    tickets: [],
    selectedTicket: null,
    isLoading: false,
    error: null,
    filters: {},

    setTickets: (tickets) => set({ tickets }),
    addTicket: (ticket) =>
      set((state) => ({
        tickets: [ticket, ...state.tickets],
      })),
    updateTicket: (id, updates) =>
      set((state) => ({
        tickets: state.tickets.map((ticket) =>
          ticket.id === id ? { ...ticket, ...updates } : ticket
        ),
        selectedTicket:
          state.selectedTicket?.id === id
            ? { ...state.selectedTicket, ...updates }
            : state.selectedTicket,
      })),
    setSelectedTicket: (ticket) => set({ selectedTicket: ticket }),
    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error }),
    setFilters: (filters) =>
      set((state) => ({
        filters: { ...state.filters, ...filters },
      })),
    clearFilters: () => set({ filters: {} }),
  }))
);
```

### WebSocket Store

```typescript
// stores/websocketStore.ts
import { create } from "zustand";
import { WebSocketMessage, AgentUpdateMessage } from "../types/websocket";

interface WebSocketState {
  isConnected: boolean;
  messages: WebSocketMessage[];
  agentUpdates: Record<number, AgentUpdateMessage[]>; // ticket_id -> updates

  // Actions
  setConnected: (connected: boolean) => void;
  addMessage: (message: WebSocketMessage) => void;
  addAgentUpdate: (update: AgentUpdateMessage) => void;
  clearMessages: () => void;
}

export const useWebSocketStore = create<WebSocketState>()((set, get) => ({
  isConnected: false,
  messages: [],
  agentUpdates: {},

  setConnected: (isConnected) => set({ isConnected }),
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages.slice(-99), message], // Keep last 100 messages
    })),
  addAgentUpdate: (update) =>
    set((state) => ({
      agentUpdates: {
        ...state.agentUpdates,
        [update.ticket_id]: [
          ...(state.agentUpdates[update.ticket_id] || []),
          update,
        ],
      },
    })),
  clearMessages: () => set({ messages: [], agentUpdates: {} }),
}));
```

## TanStack React Query Setup

### Query Client Configuration

```typescript
// lib/queryClient.ts
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        if (error?.status === 404) return false;
        return failureCount < 3;
      },
    },
    mutations: {
      retry: 1,
    },
  },
});
```

### API Hooks

```typescript
// hooks/useTickets.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ticket, TicketCreateRequest } from "../types/ticket";
import { ticketApi } from "../api/tickets";
import { useTicketStore } from "../stores/ticketStore";

export const useTickets = (filters?: Record<string, any>) => {
  return useQuery({
    queryKey: ["tickets", filters],
    queryFn: () => ticketApi.getTickets(filters),
    select: (data) => data.tickets || data,
  });
};

export const useTicket = (id: number) => {
  return useQuery({
    queryKey: ["ticket", id],
    queryFn: () => ticketApi.getTicket(id),
    enabled: !!id,
  });
};

export const useCreateTicket = () => {
  const queryClient = useQueryClient();
  const addTicket = useTicketStore((state) => state.addTicket);

  return useMutation({
    mutationFn: (data: TicketCreateRequest) => ticketApi.createTicket(data),
    onSuccess: (newTicket) => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      addTicket(newTicket);
    },
  });
};

export const useProcessTicket = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticketId: number) => ticketApi.processTicket(ticketId),
    onSuccess: (_, ticketId) => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });
};
```

```typescript
// hooks/useAnalytics.ts
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../api/analytics";

export const useDashboardMetrics = () => {
  return useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: analyticsApi.getDashboardMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const usePerformanceMetrics = (days: number = 7) => {
  return useQuery({
    queryKey: ["analytics", "performance", days],
    queryFn: () => analyticsApi.getPerformanceMetrics(days),
  });
};
```

## Component Structure

### Layout Components

```typescript
// components/layout/AppLayout.tsx
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { WebSocketProvider } from "../providers/WebSocketProvider";

export function AppLayout() {
  return (
    <WebSocketProvider>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-auto p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </WebSocketProvider>
  );
}
```

### Ticket Components

```typescript
// components/tickets/TicketList.tsx
import { useState } from "react";
import { useTickets } from "../../hooks/useTickets";
import { useTicketStore } from "../../stores/ticketStore";
import { TicketCard } from "./TicketCard";
import { TicketFilters } from "./TicketFilters";
import { Button } from "../ui/button";
import { Plus } from "lucide-react";

export function TicketList() {
  const { filters } = useTicketStore();
  const { data: tickets, isLoading, error } = useTickets(filters);

  if (isLoading) return <div>Loading tickets...</div>;
  if (error) return <div>Error loading tickets</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Tickets</h1>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Ticket
        </Button>
      </div>

      <TicketFilters />

      <div className="grid gap-4">
        {tickets?.map((ticket) => (
          <TicketCard key={ticket.id} ticket={ticket} />
        ))}
      </div>
    </div>
  );
}
```

```typescript
// components/tickets/TicketCard.tsx
import { Badge } from "../ui/badge";
import { Card, CardContent, CardHeader } from "../ui/card";
import { Ticket } from "../../types/ticket";
import { formatDistanceToNow } from "date-fns";

interface TicketCardProps {
  ticket: Ticket;
}

export function TicketCard({ ticket }: TicketCardProps) {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent":
        return "destructive";
      case "high":
        return "destructive";
      case "medium":
        return "default";
      case "low":
        return "secondary";
      default:
        return "default";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "new":
        return "default";
      case "processing":
        return "default";
      case "resolved":
        return "default";
      case "escalated":
        return "destructive";
      case "closed":
        return "secondary";
      default:
        return "default";
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <h3 className="font-semibold line-clamp-1">{ticket.title}</h3>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {ticket.description}
            </p>
          </div>
          <div className="flex gap-2">
            <Badge variant={getPriorityColor(ticket.priority)}>
              {ticket.priority}
            </Badge>
            <Badge variant={getStatusColor(ticket.status)}>
              {ticket.status}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex justify-between items-center text-sm text-muted-foreground">
          <span>
            #{ticket.id} • {ticket.category}
          </span>
          <span>
            {formatDistanceToNow(new Date(ticket.created_at), {
              addSuffix: true,
            })}
          </span>
        </div>
        {ticket.agent_confidence > 0 && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs">AI Confidence:</span>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${ticket.agent_confidence * 100}%` }}
              />
            </div>
            <span className="text-xs">
              {Math.round(ticket.agent_confidence * 100)}%
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### Form Components

```typescript
// components/tickets/TicketForm.tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../ui/form";
import { useCreateTicket } from "../../hooks/useTickets";

const ticketSchema = z.object({
  title: z.string().min(1, "Title is required").max(500),
  description: z.string().min(1, "Description is required"),
  category: z.string().min(1, "Category is required"),
  priority: z.enum(["low", "medium", "high", "urgent"]).default("medium"),
  user_email: z.string().email().optional().or(z.literal("")),
  user_id: z.string().optional(),
});

type TicketFormData = z.infer<typeof ticketSchema>;

export function TicketForm({ onSuccess }: { onSuccess?: () => void }) {
  const createTicket = useCreateTicket();

  const form = useForm<TicketFormData>({
    resolver: zodResolver(ticketSchema),
    defaultValues: {
      title: "",
      description: "",
      category: "",
      priority: "medium",
      user_email: "",
      user_id: "",
    },
  });

  const onSubmit = async (data: TicketFormData) => {
    try {
      await createTicket.mutateAsync(data);
      form.reset();
      onSuccess?.();
    } catch (error) {
      console.error("Failed to create ticket:", error);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title</FormLabel>
              <FormControl>
                <Input
                  placeholder="Brief description of the issue"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Detailed description of the issue"
                  className="min-h-[120px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="category"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Category</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="technical">Technical</SelectItem>
                    <SelectItem value="billing">Billing</SelectItem>
                    <SelectItem value="account">Account</SelectItem>
                    <SelectItem value="general">General</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="priority"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Priority</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="user_email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>User Email (Optional)</FormLabel>
              <FormControl>
                <Input type="email" placeholder="user@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => form.reset()}>
            Reset
          </Button>
          <Button type="submit" disabled={createTicket.isPending}>
            {createTicket.isPending ? "Creating..." : "Create Ticket"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

### Real-time Components

```typescript
// components/agent/AgentProcessingView.tsx
import { useEffect } from "react";
import { useWebSocketStore } from "../../stores/websocketStore";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { CheckCircle, Clock, AlertCircle } from "lucide-react";

interface AgentProcessingViewProps {
  ticketId: number;
}

export function AgentProcessingView({ ticketId }: AgentProcessingViewProps) {
  const { agentUpdates } = useWebSocketStore();
  const updates = agentUpdates[ticketId] || [];

  const getStepIcon = (step: string) => {
    switch (step) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-blue-500" />;
    }
  };

  const getStepProgress = () => {
    const steps = [
      "ingest",
      "search_similar",
      "search_kb",
      "analyze",
      "decide",
      "execute",
      "finalize",
    ];
    const completedSteps = updates.filter((u) => steps.includes(u.step)).length;
    return (completedSteps / steps.length) * 100;
  };

  if (updates.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            No agent processing updates yet
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          AI Agent Processing
          <Badge variant="outline">Ticket #{ticketId}</Badge>
        </CardTitle>
        <Progress value={getStepProgress()} className="w-full" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {updates.map((update, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 rounded-lg bg-muted/50"
            >
              {getStepIcon(update.step)}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium capitalize">
                    {update.step.replace("_", " ")}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(update.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {update.message}
                </p>
                {update.data && Object.keys(update.data).length > 0 && (
                  <div className="mt-2 text-xs">
                    {update.data.confidence && (
                      <span className="inline-flex items-center gap-1">
                        Confidence: {Math.round(update.data.confidence * 100)}%
                      </span>
                    )}
                    {update.data.count && (
                      <span className="inline-flex items-center gap-1 ml-3">
                        Found: {update.data.count} items
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

### Analytics Dashboard

```typescript
// components/analytics/DashboardMetrics.tsx
import { useDashboardMetrics } from "../../hooks/useAnalytics";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { TrendingUp, Clock, CheckCircle, AlertTriangle } from "lucide-react";

export function DashboardMetrics() {
  const { data: metrics, isLoading } = useDashboardMetrics();

  if (isLoading) return <div>Loading metrics...</div>;
  if (!metrics) return <div>No metrics available</div>;

  const metricCards = [
    {
      title: "Tickets Today",
      value: metrics.tickets_today,
      icon: TrendingUp,
      description: "New tickets created",
    },
    {
      title: "Auto-Resolved",
      value: metrics.tickets_auto_resolved_today,
      icon: CheckCircle,
      description: "Resolved by AI agent",
    },
    {
      title: "Processing",
      value: metrics.currently_processing,
      icon: Clock,
      description: "Currently being processed",
    },
    {
      title: "Pending",
      value: metrics.pending_tickets,
      icon: AlertTriangle,
      description: "Awaiting processing",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {metricCards.map((metric) => {
        const Icon = metric.icon;
        return (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <p className="text-xs text-muted-foreground">
                {metric.description}
              </p>
            </CardContent>
          </Card>
        );
      })}

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Performance Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">
                Automation Rate
              </div>
              <div className="text-2xl font-bold">
                {Math.round(metrics.automation_rate * 100)}%
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">
                Avg Confidence
              </div>
              <div className="text-2xl font-bold">
                {Math.round(metrics.avg_confidence * 100)}%
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">
                Avg Processing Time
              </div>
              <div className="text-2xl font-bold">
                {Math.round(metrics.avg_processing_time_ms / 1000)}s
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">
                Customer Satisfaction
              </div>
              <div className="text-2xl font-bold">
                {metrics.customer_satisfaction_avg.toFixed(1)}/5
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

## WebSocket Integration

```typescript
// providers/WebSocketProvider.tsx
import { createContext, useContext, useEffect, useRef } from "react";
import { useWebSocketStore } from "../stores/websocketStore";
import { useTicketStore } from "../stores/ticketStore";
import { WS_URL } from "../api/config";
import {
  WebSocketMessage,
  AgentUpdateMessage,
  TicketCreatedMessage,
} from "../types/websocket";

const WebSocketContext = createContext<WebSocket | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const wsRef = useRef<WebSocket | null>(null);
  const { setConnected, addMessage, addAgentUpdate } = useWebSocketStore();
  const { addTicket } = useTicketStore();

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("WebSocket connected");
          setConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            addMessage(message);

            // Handle specific message types
            switch (message.type) {
              case "agent_update":
                addAgentUpdate(message as AgentUpdateMessage);
                break;
              case "ticket_created":
                const ticketMessage = message as TicketCreatedMessage;
                addTicket(ticketMessage.ticket);
                break;
              case "metrics_update":
                // Could trigger analytics refresh
                break;
            }
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        ws.onclose = () => {
          console.log("WebSocket disconnected");
          setConnected(false);
          // Attempt to reconnect after 3 seconds
          setTimeout(connect, 3000);
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
        };
      } catch (error) {
        console.error("Failed to connect WebSocket:", error);
        setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <WebSocketContext.Provider value={wsRef.current}>
      {children}
    </WebSocketContext.Provider>
  );
}

export const useWebSocket = () => {
  return useContext(WebSocketContext);
};
```

## Routing Structure

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { queryClient } from "./lib/queryClient";
import { AppLayout } from "./components/layout/AppLayout";
import { TicketList } from "./components/tickets/TicketList";
import { TicketDetail } from "./components/tickets/TicketDetail";
import { KnowledgeBase } from "./components/knowledge-base/KnowledgeBase";
import { Analytics } from "./components/analytics/Analytics";
import { Settings } from "./components/settings/Settings";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/tickets" replace />} />
            <Route path="tickets" element={<TicketList />} />
            <Route path="tickets/:id" element={<TicketDetail />} />
            <Route path="knowledge-base" element={<KnowledgeBase />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
```

## Implementation Checklist

### Phase 1: Core Setup

- [ ] Initialize React project with TypeScript
- [ ] Install and configure shadcn/ui components
- [ ] Set up Tailwind CSS
- [ ] Configure TanStack React Query
- [ ] Set up Zustand stores
- [ ] Create basic routing structure

### Phase 2: Ticket Management

- [ ] Implement ticket list view with filtering
- [ ] Create ticket detail view
- [ ] Build ticket creation form
- [ ] Add ticket update functionality
- [ ] Implement search functionality

### Phase 3: Real-time Features

- [ ] Set up WebSocket connection
- [ ] Implement agent processing view
- [ ] Add real-time ticket updates
- [ ] Create notification system

### Phase 4: Knowledge Base

- [ ] Build knowledge base article list
- [ ] Create article detail view
- [ ] Implement article creation/editing
- [ ] Add file upload functionality
- [ ] Implement URL processing

### Phase 5: Analytics & Reporting

- [ ] Create dashboard metrics view
- [ ] Implement performance charts
- [ ] Add category/priority breakdowns
- [ ] Build export functionality

### Phase 6: Settings & Configuration

- [ ] Create settings management interface
- [ ] Implement integration configurations
- [ ] Add user preferences
- [ ] Build API key management

### Phase 7: Polish & Optimization

- [ ] Add loading states and error handling
- [ ] Implement responsive design
- [ ] Add accessibility features
- [ ] Optimize performance
- [ ] Add comprehensive testing

## Key Features to Highlight

1. **AI-Powered Intelligence**: Real-time agent processing with confidence scores
2. **Semantic Search**: Vector-based search across tickets and knowledge base
3. **Real-time Updates**: WebSocket integration for live processing updates
4. **Modern UI**: Clean, accessible interface with shadcn/ui components
5. **Performance**: Optimized data fetching with React Query caching
6. **Scalability**: Modular architecture with proper state management

This comprehensive guide provides everything needed to build a modern, feature-rich client application for TicketFlow AI, leveraging the latest React ecosystem tools and best practices.
