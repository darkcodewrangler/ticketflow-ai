import { Ticket } from './ticket';
import { DashboardMetrics } from './analytics';

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