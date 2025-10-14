import { useEffect, useRef, useState } from 'react';

import { getConfig } from '../../../lib/config';
import { useAppStore } from '../../../store/useAppStore';

export const useLogStream = () => {
  const token = useAppStore((state) => state.auth.token);
  const [messages, setMessages] = useState<string[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) {
      setConnectionError('Authentication required to view logs');
      socketRef.current?.close();
      socketRef.current = null;
      return () => undefined;
    }

    const config = getConfig();
    const baseUrl = config.apiBaseUrl.replace(/^http/i, 'ws');
    const url = new URL(`${baseUrl}/ws/logs`);
    url.searchParams.set('token', token);

    let reconnectAttempts = 0;
    let isActive = true;

    const connect = () => {
      // TODO: replace ad-hoc reconnect strategy with centralized WebSocket manager once mission control consolidates streams.
      try {
        const socket = new WebSocket(url.toString());
        socketRef.current = socket;

        socket.onopen = () => {
          reconnectAttempts = 0;
          setConnectionError(null);
          setMessages([]);
        };

        socket.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload?.message) {
              setMessages((prev) => [...prev.slice(-99), payload.message]);
              return;
            }
          } catch (error) {
            // Fall through to raw message handling below
          }
          setMessages((prev) => [...prev.slice(-99), event.data]);
        };

        socket.onerror = () => {
          setConnectionError('Log stream connection error');
        };

        socket.onclose = () => {
          socketRef.current = null;
          if (!isActive) {
            return;
          }
          setConnectionError('Log stream disconnected, attempting to reconnect...');
          reconnectAttempts += 1;
          const backoff = Math.min(1000 * 2 ** reconnectAttempts, 10000);
          window.setTimeout(connect, backoff);
        };
      } catch (error) {
        setConnectionError('Unable to establish log stream');
      }
    };

    connect();

    return () => {
      isActive = false;
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [token]);

  return { messages, connectionError };
};
