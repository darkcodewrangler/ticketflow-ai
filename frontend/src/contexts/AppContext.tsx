import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  ReactNode,
  useCallback,
  useMemo,
} from "react";
import {
  DashboardMetrics,
  ActivityItem,
  ConnectionStatus,
  WebSocketMessage,
} from "@/types";
import { useWebSocket } from "@/hooks/useWebSocket";
import { api } from "@/services/api";
import { showSuccess, showError } from "@/utils/toast";

interface AppState {
  // Connection state
  connectionStatus: ConnectionStatus;

  // Real-time data
  liveUpdates: ActivityItem[];
  metrics: DashboardMetrics | null;

  // UI state
  sidebarCollapsed: boolean;
  currentPage: string;

  // Loading states
  metricsLoading: boolean;
}

interface AppContextType extends AppState {
  // Actions
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  addLiveUpdate: (update: ActivityItem) => void;
  updateMetrics: (metrics: Partial<DashboardMetrics>) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCurrentPage: (page: string) => void;
  refreshMetrics: () => Promise<void>;
}

type AppAction =
  | { type: "SET_CONNECTION_STATUS"; payload: ConnectionStatus }
  | { type: "ADD_LIVE_UPDATE"; payload: ActivityItem }
  | { type: "UPDATE_METRICS"; payload: Partial<DashboardMetrics> }
  | { type: "SET_METRICS"; payload: DashboardMetrics }
  | { type: "SET_SIDEBAR_COLLAPSED"; payload: boolean }
  | { type: "SET_CURRENT_PAGE"; payload: string }
  | { type: "SET_METRICS_LOADING"; payload: boolean };

const initialState: AppState = {
  connectionStatus: "disconnected",
  liveUpdates: [],
  metrics: null,
  sidebarCollapsed: false,
  currentPage: "dashboard",
  metricsLoading: false,
};

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case "SET_CONNECTION_STATUS":
      return { ...state, connectionStatus: action.payload };
    case "ADD_LIVE_UPDATE":
      return {
        ...state,
        liveUpdates: [action.payload, ...state.liveUpdates].slice(0, 50), // Keep last 50 updates
      };
    case "UPDATE_METRICS":
      return {
        ...state,
        metrics: state.metrics ? { ...state.metrics, ...action.payload } : null,
      };
    case "SET_METRICS":
      return { ...state, metrics: action.payload };
    case "SET_SIDEBAR_COLLAPSED":
      return { ...state, sidebarCollapsed: action.payload };
    case "SET_CURRENT_PAGE":
      return { ...state, currentPage: action.payload };
    case "SET_METRICS_LOADING":
      return { ...state, metricsLoading: action.payload };
    default:
      return state;
  }
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
};

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Memoize WebSocket message handler to prevent recreating on every render
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case "connection_established":
        showSuccess("Connected to TicketFlow AI");
        break;
      case "agent_update":
        if (message.ticket_id && message.step && message.message) {
          const update: ActivityItem = {
            id: `${message.ticket_id}-${message.step}-${Date.now()}`,
            type: "agent_update",
            message: `Ticket #${message.ticket_id}: ${message.message}`,
            timestamp: new Date().toISOString(),
            metadata: {
              ticket_id: message.ticket_id,
              step: message.step,
              data: message.data,
            },
          };
          dispatch({ type: "ADD_LIVE_UPDATE", payload: update });
        }
        break;
      case "ticket_created":
        if (message.ticket) {
          const update: ActivityItem = {
            id: `ticket-created-${message.ticket.id}-${Date.now()}`,
            type: "ticket_created",
            message: `New ticket created: ${message.ticket.title}`,
            timestamp: new Date().toISOString(),
            metadata: { ticket: message.ticket },
          };
          dispatch({ type: "ADD_LIVE_UPDATE", payload: update });
        }
        break;
      case "metrics_update":
        if (message.metrics) {
          dispatch({ type: "UPDATE_METRICS", payload: message.metrics });
        }
        break;
    }
  }, []);

  // Memoize WebSocket event handlers
  const handleConnect = useCallback(() => {
    dispatch({ type: "SET_CONNECTION_STATUS", payload: "connected" });
  }, []);

  const handleDisconnect = useCallback(() => {
    dispatch({ type: "SET_CONNECTION_STATUS", payload: "disconnected" });
  }, []);

  const handleError = useCallback(() => {
    dispatch({ type: "SET_CONNECTION_STATUS", payload: "error" });
    showError("WebSocket connection error");
  }, []);

  // Use WebSocket hook with memoized handlers
  const {
    connectionStatus,
    connect: connectWS,
    disconnect: disconnectWS,
  } = useWebSocket({
    url: import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws",
    onMessage: handleWebSocketMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
  });

  // Memoize refresh metrics function
  const refreshMetrics = useCallback(async () => {
    dispatch({ type: "SET_METRICS_LOADING", payload: true });
    try {
      const response = await api.getDashboardMetrics();
      if (response.success) {
        dispatch({ type: "SET_METRICS", payload: response.data });
      }
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
      showError("Failed to load dashboard metrics");
    } finally {
      dispatch({ type: "SET_METRICS_LOADING", payload: false });
    }
  }, []);

  // Load initial metrics only once
  useEffect(() => {
    let mounted = true;

    const loadInitialMetrics = async () => {
      if (mounted) {
        await refreshMetrics();
      }
    };

    loadInitialMetrics();

    return () => {
      mounted = false;
    };
  }, []); // Empty dependency array - only run once

  // Update connection status from WebSocket hook only when it changes
  useEffect(() => {
    dispatch({ type: "SET_CONNECTION_STATUS", payload: connectionStatus });
  }, [connectionStatus]);

  // Memoize action functions to prevent unnecessary re-renders
  const addLiveUpdate = useCallback((update: ActivityItem) => {
    dispatch({ type: "ADD_LIVE_UPDATE", payload: update });
  }, []);

  const updateMetrics = useCallback((metrics: Partial<DashboardMetrics>) => {
    dispatch({ type: "UPDATE_METRICS", payload: metrics });
  }, []);

  const setSidebarCollapsed = useCallback((collapsed: boolean) => {
    dispatch({ type: "SET_SIDEBAR_COLLAPSED", payload: collapsed });
  }, []);

  const setCurrentPage = useCallback((page: string) => {
    dispatch({ type: "SET_CURRENT_PAGE", payload: page });
  }, []);

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo<AppContextType>(
    () => ({
      ...state,
      connectWebSocket: connectWS,
      disconnectWebSocket: disconnectWS,
      addLiveUpdate,
      updateMetrics,
      setSidebarCollapsed,
      setCurrentPage,
      refreshMetrics,
    }),
    [
      state,
      connectWS,
      disconnectWS,
      addLiveUpdate,
      updateMetrics,
      setSidebarCollapsed,
      setCurrentPage,
      refreshMetrics,
    ]
  );

  return (
    <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>
  );
};
