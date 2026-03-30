/** WebSocket hook for live execution monitoring. */

import { useEffect, useRef, useCallback, useState } from 'react';

interface WSMessage {
  action: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export function useWebSocket(executionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WSMessage | null>(null);

  useEffect(() => {
    if (!executionId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/executions/${executionId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      // Subscribe to all events
      ws.send(JSON.stringify({ action: 'subscribe_all' }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        setLastEvent(msg);
      } catch { /* ignore parse errors */ }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [executionId]);

  const send = useCallback((action: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, data }));
    }
  }, []);

  return { connected, lastEvent, send };
}
