import { useState, useCallback, useEffect, useRef } from 'react';
import { WebSocketMessage, ClientMessage, ConnectionStatus } from '@/types';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = ({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5
}: UseWebSocketOptions) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();
  const isConnectingRef = useRef(false);
  
  // Use refs for callbacks to prevent dependency changes from causing reconnections
  const onMessageRef = useRef(onMessage);
  const onConnectRef = useRef(onConnect);
  const onDisconnectRef = useRef(onDisconnect);
  const onErrorRef = useRef(onError);
  
  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);
  
  useEffect(() => {
    onConnectRef.current = onConnect;
  }, [onConnect]);
  
  useEffect(() => {
    onDisconnectRef.current = onDisconnect;
  }, [onDisconnect]);
  
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = undefined;
    }
  }, []);

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current || socket?.readyState === WebSocket.OPEN) {
      return;
    }

    isConnectingRef.current = true;
    setConnectionStatus('connecting');
    cleanup();
    
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        isConnectingRef.current = false;
        setConnectionStatus('connected');
        setSocket(ws);
        setReconnectAttempts(0);
        onConnectRef.current?.();

        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessageRef.current?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        isConnectingRef.current = false;
        setConnectionStatus('disconnected');
        setSocket(null);
        onDisconnectRef.current?.();
        cleanup();

        // Attempt reconnection only if we haven't exceeded max attempts
        if (reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        isConnectingRef.current = false;
        setConnectionStatus('error');
        onErrorRef.current?.(error);
      };

      setSocket(ws);

    } catch (error) {
      isConnectingRef.current = false;
      setConnectionStatus('error');
      console.error('WebSocket connection failed:', error);
    }
  }, [url, reconnectAttempts, maxReconnectAttempts, reconnectInterval, socket, cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
    isConnectingRef.current = false;
    
    if (socket) {
      socket.close();
      setSocket(null);
    }
    setConnectionStatus('disconnected');
    setReconnectAttempts(0);
  }, [socket, cleanup]);

  const sendMessage = useCallback((message: ClientMessage) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  }, [socket]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
      if (socket) {
        socket.close();
      }
    };
  }, [cleanup, socket]);

  return {
    socket,
    connectionStatus,
    lastMessage,
    reconnectAttempts,
    connect,
    disconnect,
    sendMessage
  };
};