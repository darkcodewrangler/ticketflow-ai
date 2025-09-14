import { 
  Ticket, 
  TicketCreateRequest, 
  TicketFilters, 
  WorkflowResponse, 
  DashboardMetrics, 
  APIResponse,
  AgentConfig,
  KBArticle,
  SlackSettings,
  ResendSettings,
  AppSettings,
  EmailTemplate
} from '@/types';

export class APIError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'APIError';
  }
}

class TicketFlowAPI {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new APIError(data.message || 'Request failed', response.status);
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Network error', 0);
    }
  }

  // Ticket operations
  async getTickets(filters?: TicketFilters): Promise<APIResponse<Ticket[]>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value && key !== 'dateRange') {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, String(v)));
          } else {
            params.append(key, String(value));
          }
        }
      });
    }
    return this.request(`/api/tickets?${params}`);
  }

  async getTicket(id: number): Promise<APIResponse<Ticket>> {
    return this.request(`/api/tickets/${id}`);
  }

  async createTicket(data: TicketCreateRequest): Promise<APIResponse<Ticket>> {
    return this.request('/api/tickets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTicket(id: number, data: Partial<Ticket>): Promise<APIResponse<Ticket>> {
    return this.request(`/api/tickets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTicket(id: number): Promise<APIResponse<void>> {
    return this.request(`/api/tickets/${id}`, {
      method: 'DELETE',
    });
  }

  // Agent operations
  async processTicket(ticketId: number, config?: AgentConfig): Promise<APIResponse<WorkflowResponse>> {
    return this.request('/api/agent/process', {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId, config }),
    });
  }

  async getWorkflowStatus(workflowId: string): Promise<APIResponse<WorkflowResponse>> {
    return this.request(`/api/agent/status/${workflowId}`);
  }

  async getWorkflow(workflowId: string): Promise<APIResponse<WorkflowResponse>> {
    return this.request(`/api/workflows/${workflowId}`);
  }

  async getTicketWorkflows(ticketId: number): Promise<APIResponse<WorkflowResponse[]>> {
    return this.request(`/api/workflows/ticket/${ticketId}`);
  }

  // Analytics operations
  async getDashboardMetrics(): Promise<APIResponse<DashboardMetrics>> {
    return this.request('/api/analytics/metrics');
  }

  async getPerformanceTrends(days: number): Promise<APIResponse<any[]>> {
    return this.request(`/api/analytics/daily-performance?days=${days}`);
  }

  async getPerformanceSummary(): Promise<APIResponse<any>> {
    return this.request('/api/analytics/performance-summary');
  }

  async getCategoryBreakdown(): Promise<APIResponse<any[]>> {
    return this.request('/api/analytics/category-breakdown');
  }

  // Knowledge Base operations
  async getKBArticles(): Promise<APIResponse<KBArticle[]>> {
    return this.request('/api/kb/articles');
  }

  async createKBArticle(data: Omit<KBArticle, 'id'>): Promise<APIResponse<KBArticle>> {
    return this.request('/api/kb/articles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async uploadKBFile(file: File, category: string, metadata?: Record<string, any>): Promise<APIResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    return this.request('/api/kb/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Remove Content-Type to let browser set it for FormData
    });
  }

  async crawlURL(url: string, category: string, maxDepth: number = 1, metadata?: Record<string, any>): Promise<APIResponse<any>> {
    return this.request('/api/kb/crawl-url', {
      method: 'POST',
      body: JSON.stringify({ url, category, max_depth: maxDepth, metadata }),
    });
  }

  // Search operations
  async searchTickets(query: string, limit: number = 10, category?: string): Promise<APIResponse<Ticket[]>> {
    const params = new URLSearchParams({ query, limit: limit.toString() });
    if (category) params.append('category', category);
    return this.request(`/api/search/tickets?${params}`);
  }

  async searchKB(query: string, limit: number = 10, category?: string): Promise<APIResponse<KBArticle[]>> {
    const params = new URLSearchParams({ query, limit: limit.toString() });
    if (category) params.append('category', category);
    return this.request(`/api/search/kb?${params}`);
  }

  async searchUnified(query: string, limit: number = 10): Promise<APIResponse<any>> {
    const params = new URLSearchParams({ query, limit: limit.toString() });
    return this.request(`/api/search/unified?${params}`);
  }

  // Settings operations
  async getSettings(): Promise<APIResponse<AppSettings>> {
    return this.request('/api/settings');
  }

  async updateSettings(settings: Partial<AppSettings>): Promise<APIResponse<void>> {
    return this.request('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Slack settings
  async getSlackSettings(): Promise<APIResponse<SlackSettings>> {
    return this.request('/api/settings/slack');
  }

  async updateSlackSettings(settings: SlackSettings): Promise<APIResponse<void>> {
    return this.request('/api/settings/slack', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async testSlackConnection(channelId: string): Promise<APIResponse<{ success: boolean; message: string }>> {
    return this.request('/api/settings/slack/test', {
      method: 'POST',
      body: JSON.stringify({ channelId }),
    });
  }

  async getSlackChannels(): Promise<APIResponse<Array<{ id: string; name: string }>>> {
    return this.request('/api/settings/slack/channels');
  }

  // Resend email settings
  async getResendSettings(): Promise<APIResponse<ResendSettings>> {
    return this.request('/api/settings/resend');
  }

  async updateResendSettings(settings: ResendSettings): Promise<APIResponse<void>> {
    return this.request('/api/settings/resend', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async testResendConfiguration(): Promise<APIResponse<{ success: boolean; message: string }>> {
    return this.request('/api/settings/resend/test', {
      method: 'POST',
    });
  }

  async getEmailTemplates(): Promise<APIResponse<EmailTemplate[]>> {
    return this.request('/api/settings/resend/templates');
  }

  async updateEmailTemplate(templateId: string, template: EmailTemplate): Promise<APIResponse<void>> {
    return this.request(`/api/settings/resend/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(template),
    });
  }

  async sendTestEmail(templateId: string, recipientEmail: string): Promise<APIResponse<{ success: boolean; message: string }>> {
    return this.request('/api/settings/resend/test-template', {
      method: 'POST',
      body: JSON.stringify({ templateId, recipientEmail }),
    });
  }
}

export const api = new TicketFlowAPI();