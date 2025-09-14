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