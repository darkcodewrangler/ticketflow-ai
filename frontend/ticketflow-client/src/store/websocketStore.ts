import { create } from 'zustand';
import { WebSocketMessage, DashboardMetrics } from '../types';
import { WS_URL } from '../api';

interface WebSocketState {
  socket: WebSocket | null;
  connected: boolean;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  reconnectInterval: number;
  lastMessage: WebSocketMessage | null;
  agentStatus: string;
  processingTicketId: number | null;
  
  // Actions
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: any) => void;
  setAgentStatus: (status: string) => void;
  setProcessingTicketId: (ticketId: number | null) => void;
  
  // Message handlers
  onMessage: (callback: (message: WebSocketMessage) => void) => void;
  onAgentUpdate: (callback: (data: any) => void) => void;
  onTicketCreated: (callback: (ticket: any) => void) => void;
  onMetricsUpdate: (callback: (metrics: DashboardMetrics) => void) => void;
}

export const useWebSocketStore = create<WebSocketState>((set, get) => {
  let messageCallbacks: ((message: WebSocketMessage) => void)[] = [];
  let agentUpdateCallbacks: ((data: any) => void)[] = [];
  let ticketCreatedCallbacks: ((ticket: any) => void)[] = [];
  let metricsUpdateCallbacks: ((metrics: DashboardMetrics) => void)[] = [];
  
  const handleMessage = (event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      set({ lastMessage: message });
      
      // Call all registered message callbacks
      messageCallbacks.forEach(callback => callback(message));
      
      // Handle specific message types
      switch (message.type) {
        case 'agent_update':
          set({ 
            agentStatus: message.data.status,
            processingTicketId: message.data.ticket_id || null
          });
          agentUpdateCallbacks.forEach(callback => callback(message.data));
          break;
          
        case 'ticket_created':
          ticketCreatedCallbacks.forEach(callback => callback(message.data));
          break;
          
        case 'metrics_update':
          metricsUpdateCallbacks.forEach(callback => callback(message.data));
          break;
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };
  
  const handleOpen = () => {
    console.log('WebSocket connected');
    set({ connected: true, reconnectAttempts: 0 });
  };
  
  const handleClose = () => {
    console.log('WebSocket disconnected');
    set({ connected: false });
    
    const { reconnectAttempts, maxReconnectAttempts, reconnectInterval } = get();
    
    if (reconnectAttempts < maxReconnectAttempts) {
      setTimeout(() => {
        console.log(`Attempting to reconnect... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
        set({ reconnectAttempts: reconnectAttempts + 1 });
        get().connect();
      }, reconnectInterval);
    }
  };
  
  const handleError = (error: Event) => {
    console.error('WebSocket error:', error);
  };
  
  return {
    socket: null,
    connected: false,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectInterval: 3000,
    lastMessage: null,
    agentStatus: 'idle',
    processingTicketId: null,
    
    connect: () => {
      const { socket } = get();
      
      if (socket && socket.readyState === WebSocket.OPEN) {
        return;
      }
      
      try {
        const newSocket = new WebSocket(WS_URL);
        
        newSocket.onopen = handleOpen;
        newSocket.onmessage = handleMessage;
        newSocket.onclose = handleClose;
        newSocket.onerror = handleError;
        
        set({ socket: newSocket });
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
      }
    },
    
    disconnect: () => {
      const { socket } = get();
      
      if (socket) {
        socket.close();
        set({ socket: null, connected: false });
      }
    },
    
    sendMessage: (message) => {
      const { socket, connected } = get();
      
      if (socket && connected) {
        socket.send(JSON.stringify(message));
      } else {
        console.warn('WebSocket not connected. Cannot send message.');
      }
    },
    
    setAgentStatus: (status) => set({ agentStatus: status }),
    setProcessingTicketId: (ticketId) => set({ processingTicketId: ticketId }),
    
    onMessage: (callback) => {
      messageCallbacks.push(callback);
    },
    
    onAgentUpdate: (callback) => {
      agentUpdateCallbacks.push(callback);
    },
    
    onTicketCreated: (callback) => {
      ticketCreatedCallbacks.push(callback);
    },
    
    onMetricsUpdate: (callback) => {
      metricsUpdateCallbacks.push(callback);
    }
  };
});