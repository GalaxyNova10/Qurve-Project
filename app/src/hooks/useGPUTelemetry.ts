/// <reference types="vite/client" />

/**
 * WebSocket hook for real-time GPU telemetry.
 * Connects to ws://localhost:8000/ws/gpu-telemetry
 * Replaces all Math.random() + setInterval fake GPU data.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { GPUMetrics } from '../types/portfolio';

interface UseGPUTelemetryReturn {
  metrics: GPUMetrics | null;
  isConnected: boolean;
  error: string | null;
  history: GPUMetrics[];
  reconnect: () => void;
}

const getWsUrl = () => {
  const configured = import.meta.env.VITE_WS_BASE_URL;
  if (configured) return configured;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // Backend runs on port 8000, frontend on different port
  return `${protocol}//localhost:8000/ws/gpu-telemetry`;
};
const MAX_HISTORY = 60; // Keep 60 seconds of history
const RECONNECT_DELAY = 3000; // Reconnect after 3s

export function useGPUTelemetry(): UseGPUTelemetryReturn {
  const [metrics, setMetrics] = useState<GPUMetrics | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<GPUMetrics[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const ws = new WebSocket(getWsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        setError(null);
        console.log('[WS] GPU telemetry connected');
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setIsConnected(false);
        console.log('[WS] GPU telemetry disconnected');
        
        // Auto-reconnect
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) {
            console.log('[WS] Attempting reconnect...');
            connect();
          }
        }, RECONNECT_DELAY);
      };

      ws.onerror = (evt) => {
        if (!mountedRef.current) return;
        setError('WebSocket connection failed — is the backend running?');
        console.error('[WS] GPU telemetry error:', evt);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data) as GPUMetrics;
          setMetrics(data);
          setHistory(prev => {
            const next = [...prev, data];
            return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
          });
        } catch (e) {
          console.error('[WS] Failed to parse GPU metrics:', e);
        }
      };
    } catch (e) {
      setError(`Failed to connect: ${e}`);
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }
    connect();
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { metrics, isConnected, error, history, reconnect };
}
