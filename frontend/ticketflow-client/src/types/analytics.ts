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