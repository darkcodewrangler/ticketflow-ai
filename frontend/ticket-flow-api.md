
# Project Overview

Build a modern, enterprise-grade frontend for **TicketFlow AI** - an intelligent support ticket automation system powered by TiDB's vector database capabilities. This application demonstrates real-world AI agent workflows with live processing visualization, making it perfect for technical demonstrations and production deployment.

**Core Value Proposition**: Automated ticket resolution using AI agents that search similar cases, analyze patterns, and execute appropriate actions - all visible in real-time.

## 🏗️ System Architecture Understanding

### Backend Capabilities Analysis
The TicketFlow AI system provides:

**Multi-Step AI Agent Workflow**:
1. **Ingest** - Ticket intake and initial processing
2. **Search Similar** - Vector similarity search for resolved cases
3. **Search KB** - Knowledge base article retrieval
4. **Analyze** - LLM-powered pattern analysis
5. **Decide** - Action selection based on confidence scores
6. **Execute** - Automated actions (Slack notifications, email, etc.)
7. **Finalize** - Workflow completion and metrics update

**Real-time Communication**:
- WebSocket manager for live updates
- Agent step-by-step progress broadcasting
- Metrics and notification streaming

**Data Management**:
- TiDB vector database with hybrid search
- Knowledge base with file upload (PDF, TXT, Markdown)
- URL crawling and content indexing
- Automated embedding generation

## 📊 Complete API Specification

### Core Endpoints

#### Ticket Management
```typescript
// Ticket Operations
POST /api/tickets
Content-Type: application/json
{
  "title": string,
  "description": string,
  "category": string,
  "priority": "low" | "medium" | "high" | "urgent",
  "customer_email": string,
  "metadata": object,
  "auto_process": boolean
}

Response: {
  "success": boolean,
  "message": string,
  "data": {
    "id": number,
    "title": string,
    "description": string,
    "status": "new" | "processing" | "resolved" | "escalated",
    "priority": string,
    "category": string,
    "customer_email": string,
    "created_at": string,
    "updated_at": string,
    "resolved_at": string | null,
    "resolution": string | null,
    "agent_confidence": number | null,
    "metadata": object
  }
}

GET /api/tickets
Query Parameters:
- status: string (optional)
- priority: string (optional)
- category: string (optional)
- limit: number (default: 50)
- offset: number (default: 0)

GET /api/tickets/{id}
PUT /api/tickets/{id}
DELETE /api/tickets/{id}
```

#### AI Agent Processing
```typescript
// Agent Workflow
POST /api/agent/process
{
  "ticket_id": number,
  "config": {
    "auto_resolve_threshold": number, // 0.0-1.0
    "enable_external_actions": boolean,
    "max_similar_cases": number,
    "kb_search_limit": number
  }
}

Response: {
  "success": boolean,
  "data": {
    "workflow_id": string,
    "ticket_id": number,
    "status": "started" | "processing" | "completed" | "failed",
    "steps": [
      {
        "step": string,
        "status": "pending" | "processing" | "completed" | "failed",
        "message": string,
        "data": object,
        "timestamp": string,
        "duration_ms": number
      }
    ]
  }
}

GET /api/agent/status/{workflow_id}
GET /api/workflows/{workflow_id}
GET /api/workflows/ticket/{ticket_id}
```

#### Knowledge Base Management
```typescript
// Knowledge Base Operations
POST /api/kb/articles
{
  "title": string,
  "content": string,
  "category": string,
  "tags": string[],
  "metadata": object
}

POST /api/kb/upload
Content-Type: multipart/form-data
- file: File (PDF, TXT, Markdown)
- category: string
- metadata: string (JSON)

POST /api/kb/crawl-url
{
  "url": string,
  "category": string,
  "max_depth": number,
  "metadata": object
}

GET /api/kb/articles
GET /api/kb/articles/{id}
GET /api/kb/processing-status/{job_id}
```

#### Search & Analytics
```typescript
// Unified Search
GET /api/search/tickets?query=string&limit=number&category=string
GET /api/search/kb?query=string&limit=number&category=string
GET /api/search/unified?query=string&limit=number

// Analytics Dashboard
GET /api/analytics/metrics
Response: {
  "total_tickets": number,
  "auto_resolved": number,
  "avg_resolution_time_hours": number,
  "success_rate": number,
  "tickets_today": number,
  "processing_time_avg_ms": number
}

GET /api/analytics/daily-performance?days=number
GET /api/analytics/performance-summary
GET /api/analytics/category-breakdown
```

#### Integration Webhooks
```typescript
// External Platform Integration
POST /api/integrations/webhook
{
  "platform": "zendesk" | "freshdesk" | "jira" | "servicenow" | "custom",
  "ticket_data": {
    "title": string,
    "description": string,
    "priority": string,
    "category": string,
    "customer_info": object,
    "platform_metadata": object
  },
  "auto_process": boolean
}

GET /api/integrations/webhook/health
```

### WebSocket Real-time Updates
```typescript
// WebSocket Connection
ws://localhost:8000/ws

// Message Types
type WebSocketMessage = 
  | { type: "connection_established", message: string, timestamp: number }
  | { type: "agent_update", ticket_id: number, step: string, message: string, data: object, timestamp: number }
  | { type: "ticket_created", ticket: object, timestamp: number }
  | { type: "metrics_update", metrics: object, timestamp: number }
  | { type: "pong" } // Response to ping

// Client Messages
type ClientMessage = 
  | { type: "ping" }
  | { type: "subscribe", subscription: string }
```

## 🎨 Design System & UI Requirements

### Visual Identity
- **Primary**: Professional blue (#2563EB) - enterprise software aesthetic
- **Secondary**: Clean grays (#F8FAFC, #64748B), success green (#10B981), warning amber (#F59E0B), error red (#EF4444)
- **Typography**: Inter or similar professional sans-serif
- **Style**: Modern enterprise dashboard - clean, trustworthy, data-rich

### Component Library Requirements

#### Status Indicators
```typescript
// Ticket Status Badge
interface StatusBadge {
  status: 'new' | 'processing' | 'resolved' | 'escalated';
  variant: 'default' | 'processing' | 'success' | 'warning';
  pulse?: boolean; // For processing states
}

// Priority Indicator
interface PriorityBadge {
  priority: 'low' | 'medium' | 'high' | 'urgent';
  color: 'gray' | 'blue' | 'yellow' | 'red';
}

// Agent Step Progress
interface StepIndicator {
  steps: Array<{
    name: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    duration?: number;
    data?: object;
  }>;
  currentStep: number;
}
```

#### Real-time Components
```typescript
// Live Activity Feed
interface ActivityFeed {
  items: Array<{
    id: string;
    type: 'ticket_created' | 'agent_update' | 'resolution' | 'escalation';
    message: string;
    timestamp: string;
    metadata?: object;
  }>;
  maxItems: number;
  autoScroll: boolean;
}

// Metrics Cards
interface MetricCard {
  title: string;
  value: number | string;
  change?: { value: number; direction: 'up' | 'down'; period: string };
  format: 'number' | 'percentage' | 'duration' | 'currency';
  status?: 'positive' | 'negative' | 'neutral';
}
```

## 📱 Required Pages & Features

### 1. Main Dashboard
**Layout**: Sidebar (20%) + Main Content (80%)

**Sidebar Components**:
- Company logo area
- Navigation: Dashboard, Tickets, Knowledge Base, Analytics, Settings
- Agent status indicator with pulse animation
- Quick stats card

**Main Content**:
```typescript
// Hero Metrics Row
const dashboardMetrics = [
  { title: "Total Tickets", value: metrics.total_tickets, format: "number" },
  { title: "Auto-Resolved", value: metrics.success_rate, format: "percentage" },
  { title: "Avg Resolution", value: metrics.avg_resolution_time_hours, format: "duration" },
  { title: "Today's Tickets", value: metrics.tickets_today, format: "number" }
];

// Real-time Activity Feed
<ActivityFeed 
  items={liveUpdates} 
  maxItems={50} 
  autoScroll={true}
/>

// Recent Tickets Table
<DataTable
  columns={[
    { key: "id", label: "ID", sortable: true },
    { key: "title", label: "Title", sortable: true },
    { key: "status", label: "Status", render: StatusBadge },
    { key: "priority", label: "Priority", render: PriorityBadge },
    { key: "created_at", label: "Created", format: "datetime" },
    { key: "actions", label: "Actions", render: ActionButtons }
  ]}
  data={recentTickets}
  pagination={true}
/>
```

### 2. Live Agent Processing View (Demo Centerpiece)
**This is your showcase feature for demonstrations**

**Layout**: Three-panel design
```typescript
// Left Panel - Ticket Details
interface TicketDetailsPanel {
  ticket: {
    id: number;
    title: string;
    description: string;
    priority: string;
    category: string;
    customer_email: string;
    metadata: object;
  };
  urgencyIndicator: 'low' | 'medium' | 'high' | 'critical';
}

// Center Panel - Agent Workflow
interface AgentWorkflowPanel {
  workflowId: string;
  currentStep: number;
  steps: Array<{
    name: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    message: string;
    data?: object;
    duration?: number;
  }>;
  overallProgress: number; // 0-100
  logs: Array<{
    timestamp: string;
    level: 'info' | 'success' | 'warning' | 'error';
    message: string;
    data?: object;
  }>;
}

// Right Panel - Results & Actions
interface ResultsPanel {
  similarCases: Array<{
    id: number;
    title: string;
    similarity_score: number;
    resolution: string;
  }>;
  kbArticles: Array<{
    id: number;
    title: string;
    relevance_score: number;
    content_preview: string;
  }>;
  aiAnalysis: {
    confidence: number;
    recommended_action: string;
    reasoning: string;
    risk_assessment: string;
  };
  actionButtons: {
    acceptResolution: boolean;
    requestManualReview: boolean;
    escalate: boolean;
  };
}
```

**Interactive Elements**:
- Live progress bar with step animations
- Expandable sections for each agent step
- Confidence score visualization (circular progress)
- Real-time log streaming
- Action buttons with confirmation dialogs

### 3. Ticket Management
```typescript
// Ticket List View
interface TicketListView {
  filters: {
    status: string[];
    priority: string[];
    category: string[];
    dateRange: { start: Date; end: Date };
    searchQuery: string;
  };
  sorting: {
    field: string;
    direction: 'asc' | 'desc';
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}

// Ticket Creation Form
interface TicketCreateForm {
  fields: {
    title: { value: string; validation: string[] };
    description: { value: string; validation: string[] };
    category: { value: string; options: string[] };
    priority: { value: string; options: string[] };
    customer_email: { value: string; validation: string[] };
    auto_process: { value: boolean; description: string };
  };
  onSubmit: (data: TicketCreateRequest) => Promise<void>;
  loading: boolean;
}
```

### 4. Knowledge Base Management
```typescript
// File Upload Interface
interface FileUploadComponent {
  acceptedTypes: ['.pdf', '.txt', '.md'];
  maxSize: number; // bytes
  multiple: boolean;
  onUpload: (files: File[]) => Promise<void>;
  progress: Array<{
    file: string;
    progress: number; // 0-100
    status: 'uploading' | 'processing' | 'completed' | 'failed';
  }>;
}

// URL Crawling Interface
interface URLCrawlComponent {
  url: string;
  maxDepth: number;
  category: string;
  onCrawl: (config: CrawlConfig) => Promise<void>;
  status: {
    jobId: string;
    progress: number;
    pagesFound: number;
    pagesProcessed: number;
    errors: string[];
  };
}

// Knowledge Base Search
interface KBSearchComponent {
  query: string;
  results: Array<{
    id: number;
    title: string;
    content_preview: string;
    relevance_score: number;
    category: string;
    tags: string[];
  }>;
  onSearch: (query: string) => Promise<void>;
  filters: {
    category: string[];
    tags: string[];
  };
}
```

### 5. Analytics Dashboard
```typescript
// Performance Metrics
interface AnalyticsDashboard {
  timeRange: '24h' | '7d' | '30d' | '90d';
  metrics: {
    totalTickets: number;
    autoResolved: number;
    avgResolutionTime: number;
    successRate: number;
    costSavings: number;
  };
  charts: {
    resolutionTrends: ChartData;
    categoryBreakdown: PieChartData;
    performanceOverTime: LineChartData;
    confidenceDistribution: HistogramData;
  };
}

// ROI Calculator
interface ROICalculator {
  inputs: {
    avgAgentSalary: number;
    avgResolutionTimeManual: number; // minutes
    avgResolutionTimeAI: number; // minutes
    ticketsPerMonth: number;
  };
  outputs: {
    timeSavedPerTicket: number;
    costSavedPerTicket: number;
    monthlySavings: number;
    annualSavings: number;
    roi: number; // percentage
  };
}
```

## 🛠️ Technical Implementation

### Technology Stack
```json
{
  "framework": "React 18 with TypeScript",
  "styling": "Shadcn and Tailwind CSS",
  "stateManagement": "React hooks + Zustand/Context API",
  "realTime": "WebSocket with reconnection logic",
  "charts": "Recharts",
  "icons": "Lucide React",
  "httpClient": "Fetch API with error handling",
  "forms": "React Hook Form with Zod validation",
  "routing": "React Router v6",
  "notifications": "React Hot Toast"
}
```

### State Management Architecture
```typescript
// Global App Context
interface AppContextType {
  // Connection state
  wsConnection: WebSocket | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  
  // Real-time data
  liveUpdates: ActivityItem[];
  metrics: DashboardMetrics;
  
  // UI state
  sidebarCollapsed: boolean;
  currentPage: string;
  notifications: Notification[];
  
  // Actions
  connectWebSocket: () => void;
  addNotification: (notification: Notification) => void;
  updateMetrics: (metrics: Partial<DashboardMetrics>) => void;
}

// Ticket Context
interface TicketContextType {
  tickets: Ticket[];
  currentTicket: Ticket | null;
  filters: TicketFilters;
  loading: boolean;
  
  // Actions
  fetchTickets: (filters?: TicketFilters) => Promise<void>;
  createTicket: (data: TicketCreateRequest) => Promise<Ticket>;
  updateTicket: (id: number, data: Partial<Ticket>) => Promise<void>;
  processTicket: (id: number, config?: AgentConfig) => Promise<void>;
}
```

### WebSocket Integration
```typescript
// WebSocket Hook
const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setConnectionStatus('connected');
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
      handleWebSocketMessage(message);
    };
    
    ws.onclose = () => {
      setConnectionStatus('disconnected');
      setSocket(null);
      // Implement reconnection logic
      setTimeout(connect, 3000);
    };
    
    ws.onerror = () => {
      setConnectionStatus('error');
    };
  }, [url]);
  
  const sendMessage = useCallback((message: ClientMessage) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  }, [socket]);
  
  return { socket, connectionStatus, lastMessage, connect, sendMessage };
};
```

### API Client Implementation
```typescript
// API Client with Error Handling
class TicketFlowAPI {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;
  
  constructor(baseURL: string) {
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
        if (value) params.append(key, String(value));
      });
    }
    return this.request(`/api/tickets?${params}`);
  }
  
  async createTicket(data: TicketCreateRequest): Promise<APIResponse<Ticket>> {
    return this.request('/api/tickets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  async processTicket(ticketId: number, config?: AgentConfig): Promise<APIResponse<WorkflowResponse>> {
    return this.request('/api/agent/process', {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId, config }),
    });
  }
  
  // Analytics operations
  async getDashboardMetrics(): Promise<APIResponse<DashboardMetrics>> {
    return this.request('/api/analytics/metrics');
  }
  
  async getPerformanceTrends(days: number): Promise<APIResponse<TrendData[]>> {
    return this.request(`/api/analytics/daily-performance?days=${days}`);
  }
}
```

## 🎭 UX & Interaction Design

### Loading States & Animations
```typescript
// Skeleton Components
const TicketCardSkeleton = () => (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
    <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
    <div className="h-3 bg-gray-200 rounded w-1/4"></div>
  </div>
);

// Progressive Loading
const AgentProcessingView = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [stepData, setStepData] = useState<StepData[]>([]);
  
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <StepIndicator
          key={step.name}
          step={step}
          active={index === currentStep}
          completed={index < currentStep}
          data={stepData[index]}
        />
      ))}
    </div>
  );
};
```

### Real-time Updates
```typescript
// Optimistic Updates
const useOptimisticTickets = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [pendingUpdates, setPendingUpdates] = useState<Map<number, Partial<Ticket>>>(new Map());
  
  const updateTicketOptimistically = (id: number, updates: Partial<Ticket>) => {
    // Update UI immediately
    setTickets(prev => prev.map(ticket => 
      ticket.id === id ? { ...ticket, ...updates } : ticket
    ));
    
    // Track pending update
    setPendingUpdates(prev => new Map(prev.set(id, updates)));
  };
  
  const confirmUpdate = (id: number, serverData: Ticket) => {
    // Replace optimistic update with server data
    setTickets(prev => prev.map(ticket => 
      ticket.id === id ? serverData : ticket
    ));
    
    // Remove from pending
    setPendingUpdates(prev => {
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
  };
  
  return { tickets, updateTicketOptimistically, confirmUpdate };
};
```

### Error Handling & Recovery
```typescript
// Error Boundary with Retry
const ErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const retry = () => {
    setHasError(false);
    setError(null);
  };
  
  if (hasError) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="text-red-500 mb-4">
          <AlertCircle size={48} />
        </div>
        <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
        <p className="text-gray-600 mb-4">{error?.message}</p>
        <button 
          onClick={retry}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Try Again
        </button>
      </div>
    );
  }
  
  return <>{children}</>;
};
```

## 🚀 Demo-Ready Features

### Live Processing Showcase
1. **Ticket Creation with Auto-Process**: Form that immediately triggers agent workflow
2. **Step-by-Step Visualization**: Real-time progress with expanding details
3. **Confidence Scoring**: Visual indicators of AI decision confidence
4. **Similar Case Discovery**: Show matching resolved tickets with similarity scores
5. **Knowledge Base Integration**: Display relevant articles found during processing
6. **Action Execution**: Live updates of external actions (Slack, email)

### Performance Metrics
1. **Real-time Dashboard**: Live updating metrics and charts
2. **ROI Calculator**: Interactive tool showing cost savings
3. **Success Rate Tracking**: Visual trends over time
4. **Processing Speed**: Average resolution time comparisons

### Integration Demonstrations
1. **Webhook Testing**: Live webhook endpoint for external platforms
2. **File Upload Processing**: Drag-and-drop with real-time indexing
3. **URL Crawling**: Live website content extraction
4. **Vector Search**: Interactive similarity search testing

## 📱 Responsive Design Requirements

### Breakpoints
- **Desktop**: 1024px+ (primary target)
- **Tablet**: 768px-1023px (secondary)
- **Mobile**: 320px-767px (basic support)

### Mobile Adaptations
- Collapsible sidebar becomes bottom navigation
- Stacked layout for agent processing view
- Simplified metrics cards
- Touch-optimized interactions

## 🔧 Development Guidelines

### Code Organization
```
src/
├── components/
│   ├── ui/           # Reusable UI components
│   ├── charts/       # Chart components
│   ├── forms/        # Form components
│   └── layout/       # Layout components
├── pages/            # Page components
├── hooks/            # Custom React hooks
├── services/         # API services
├── types/            # TypeScript definitions
├── utils/            # Utility functions
└── contexts/         # React contexts
```

### Performance Optimization
1. **Code Splitting**: Lazy load pages and heavy components
2. **Memoization**: Use React.memo for expensive renders
3. **Virtual Scrolling**: For large ticket lists
4. **WebSocket Throttling**: Limit update frequency
5. **Image Optimization**: Lazy loading and compression

### Testing Strategy
1. **Unit Tests**: Component logic and utilities
2. **Integration Tests**: API interactions
3. **E2E Tests**: Critical user flows
4. **WebSocket Testing**: Real-time functionality
5. **Performance Testing**: Load and stress testing

This comprehensive prompt provides everything needed to build a professional client application that showcases the full capabilities of the TicketFlow AI system. 