export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: 'new' | 'processing' | 'resolved' | 'escalated';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: string;
  customer_email: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolution: string | null;
  agent_confidence: number | null;
  metadata: Record<string, any>;
}

export interface TicketCreateRequest {
  title: string;
  description: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  customer_email: string;
  metadata?: Record<string, any>;
  auto_process?: boolean;
}

export interface TicketFilters {
  status?: string[];
  priority?: string[];
  category?: string[];
  searchQuery?: string;
  dateRange?: { start: Date; end: Date };
}

export interface WorkflowStep {
  step: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message: string;
  data?: Record<string, any>;
  timestamp: string;
  duration_ms?: number;
}

export interface WorkflowResponse {
  workflow_id: string;
  ticket_id: number;
  status: 'started' | 'processing' | 'completed' | 'failed';
  steps: WorkflowStep[];
}

export interface DashboardMetrics {
  total_tickets: number;
  auto_resolved: number;
  avg_resolution_time_hours: number;
  success_rate: number;
  tickets_today: number;
  processing_time_avg_ms: number;
}

export interface ActivityItem {
  id: string;
  type: 'ticket_created' | 'agent_update' | 'resolution' | 'escalation';
  message: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface WebSocketMessage {
  type: 'connection_established' | 'agent_update' | 'ticket_created' | 'metrics_update' | 'pong';
  message?: string;
  ticket_id?: number;
  step?: string;
  data?: Record<string, any>;
  timestamp: number;
  ticket?: Ticket;
  metrics?: DashboardMetrics;
}

export interface ClientMessage {
  type: 'ping' | 'subscribe';
  subscription?: string;
}

export interface SimilarCase {
  id: number;
  title: string;
  similarity_score: number;
  resolution: string;
}

export interface KBArticle {
  id: number;
  title: string;
  content: string;
  category: string;
  tags: string[];
  relevance_score?: number;
  content_preview?: string;
}

export interface AIAnalysis {
  confidence: number;
  recommended_action: string;
  reasoning: string;
  risk_assessment: string;
}

export interface AgentConfig {
  auto_resolve_threshold: number;
  enable_external_actions: boolean;
  max_similar_cases: number;
  kb_search_limit: number;
}

export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// New Settings Interfaces

export interface SlackChannelConfig {
  channelId: string;
  channelName: string;
  enabled: boolean;
}

export interface SlackSettings {
  enabled: boolean;
  botToken: string;
  signingSecret: string;
  channels: {
    escalated: SlackChannelConfig;
    general: SlackChannelConfig;
    agentUpdates: SlackChannelConfig;
    resolutions: SlackChannelConfig;
    alerts: SlackChannelConfig;
  };
  notificationSettings: {
    includeTicketDetails: boolean;
    mentionUsers: boolean;
    useThreads: boolean;
    quietHours: {
      enabled: boolean;
      startTime: string;
      endTime: string;
      timezone: string;
    };
  };
}

export interface EmailTemplate {
  enabled: boolean;
  subject: string;
  template: 'default' | 'custom';
  customTemplate?: string;
  recipients?: string[];
  sendOnlyOnCompletion?: boolean;
}

export interface ResendSettings {
  enabled: boolean;
  apiKey: string;
  fromEmail: string;
  fromName: string;
  replyToEmail: string;
  templates: {
    ticketCreated: EmailTemplate;
    ticketResolved: EmailTemplate;
    ticketEscalated: EmailTemplate & { recipients: string[] };
    processingUpdate: EmailTemplate & { sendOnlyOnCompletion: boolean };
  };
  advanced: {
    maxEmailsPerHour: number;
    maxEmailsPerDay: number;
    retryAttempts: number;
    retryDelay: number;
    trackOpens: boolean;
    trackClicks: boolean;
    suppressionList: string[];
    quietHours: {
      enabled: boolean;
      startTime: string;
      endTime: string;
      timezone: string;
    };
  };
}

export interface GeneralSettings {
  companyName: string;
  supportEmail: string;
  timezone: string;
  dateFormat: string;
  language: string;
}

export interface AgentSettings {
  autoResolveThreshold: number;
  enableExternalActions: boolean;
  maxSimilarCases: number;
  kbSearchLimit: number;
  confidenceThreshold: number;
  escalationThreshold: number;
  processingTimeout: number;
}

export interface WebhookSettings {
  enabled: boolean;
  endpoints: Array<{
    id: string;
    name: string;
    url: string;
    events: string[];
    headers: Record<string, string>;
    enabled: boolean;
  }>;
}

export interface SecuritySettings {
  twoFactorAuth: boolean;
  sessionTimeout: number;
  ipWhitelist: string[];
  auditLogging: boolean;
}

export interface NotificationSettings {
  emailNotifications: boolean;
  slackNotifications: boolean;
  webhookNotifications: boolean;
  notifyOnResolution: boolean;
  notifyOnEscalation: boolean;
  notifyOnFailure: boolean;
}

export interface AppSettings {
  general: GeneralSettings;
  agent: AgentSettings;
  slack: SlackSettings;
  resend: ResendSettings;
  webhooks: WebhookSettings;
  security: SecuritySettings;
  notifications: NotificationSettings;
}