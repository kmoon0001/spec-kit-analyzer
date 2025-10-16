import { useEffect, useRef, useState } from 'react';

import { getConfig, getNormalizedApiBaseUrl } from '../../../lib/config';
import { createExponentialBackoff } from '../../../lib/network/backoff';
import { useAppStore } from '../../../store/useAppStore';

const MAX_MESSAGES = 100;
const textDecoder = typeof TextDecoder !== 'undefined' ? new TextDecoder() : null;

export type LogEntry = {
  id: string;
  message: string;
  level: string;
  logger?: string;
  timestamp?: string;
  raw?: unknown;
};

const buildLogStreamUrl = (token: string) => {
  const runtimeConfig = getConfig();
  const baseUrl = getNormalizedApiBaseUrl(runtimeConfig).replace(/^http/i, 'ws');
  const url = new URL(`${baseUrl}/ws/logs`);
  url.searchParams.set('token', token);
  return url.toString();
};

const decodePayload = async (data: MessageEvent['data']): Promise<string | null> => {
  if (typeof data === 'string') {
    return data;
  }

  if (data instanceof Blob) {
    try {
      return await data.text();
    } catch {
      return null;
    }
  }

  if (data instanceof ArrayBuffer) {
    return textDecoder ? textDecoder.decode(data) : null;
  }

  if (ArrayBuffer.isView(data)) {
    return textDecoder ? textDecoder.decode(data.buffer) : null;
  }

  return null;
};

const normalizeLogEntry = (payload: unknown, fallbackMessage: string): LogEntry | null => {
  if (payload && typeof payload === 'object') {
    const maybeType = (payload as { type?: string }).type;
    if (maybeType === 'heartbeat') {
      return null;
    }

    const logger = (payload as { logger?: string }).logger;
    const timestamp = (payload as { timestamp?: string }).timestamp;
    const rawMessage = (payload as { message?: unknown }).message;
    const level = ((payload as { level?: string }).level ?? 'info').toLowerCase();

    let resolvedMessage: string;
    if (typeof rawMessage === 'string') {
      resolvedMessage = rawMessage;
    } else if (rawMessage !== undefined) {
      try {
        resolvedMessage = JSON.stringify(rawMessage);
      } catch {
        resolvedMessage = String(rawMessage);
      }
    } else {
      try {
        resolvedMessage = JSON.stringify(payload);
      } catch {
        resolvedMessage = fallbackMessage;
      }
    }

    return {
      id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
      message: resolvedMessage,
      level,
      logger,
      timestamp,
      raw: payload,
    };
  }

  return {
    id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
    message: typeof payload === 'string' ? payload : fallbackMessage,
    level: 'info',
  };
};

export const useLogStream = () => {
  const token = useAppStore((state) => state.auth.token);
  const [messages, setMessages] = useState<LogEntry[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const cleanupTimer = () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const cleanupSocket = () => {
      if (socketRef.current) {
        try {
          socketRef.current.close();
        } catch (error) {
          console.warn('Failed to close log stream socket', error);
        }
      }
      socketRef.current = null;
    };

    if (!token) {
      setIsConnected(false);
      setMessages([]);
      setConnectionError('Authentication required to view logs');
      cleanupTimer();
      cleanupSocket();
      return () => {
        cleanupTimer();
        cleanupSocket();
      };
    }

    let disposed = false;
    const backoff = createExponentialBackoff({ initialDelayMs: 750, maxDelayMs: 15000 });

    const scheduleReconnect = () => {
      if (disposed) {
        return;
      }
      const delay = backoff.next();
      reconnectTimerRef.current = window.setTimeout(connect, delay);
    };

    const handleMessage = async (data: MessageEvent['data']) => {
      if (disposed) {
        return;
      }

      const decoded = await decodePayload(data);
      if (decoded === null) {
        return;
      }

      let parsed: unknown = decoded;
      try {
        parsed = JSON.parse(decoded);
      } catch {
        // non-JSON payload, treat as plain text
      }

      const entry = normalizeLogEntry(parsed, decoded);
      if (!entry) {
        return;
      }

      setMessages((prev) => [...prev.slice(-(MAX_MESSAGES - 1)), entry]);
    };

    const connect = () => {
      if (disposed) {
        return;
      }

      cleanupTimer();
      cleanupSocket();

      const socket = new WebSocket(buildLogStreamUrl(token));
      socketRef.current = socket;

      socket.onopen = () => {
        backoff.reset();
        setIsConnected(true);
        setConnectionError(null);
        setMessages([]);
      };

      socket.onmessage = (event) => {
        void handleMessage(event.data);
      };

      socket.onerror = () => {
        setConnectionError('Log stream connection error');
      };

      socket.onclose = () => {
        setIsConnected(false);
        if (disposed) {
          return;
        }
        setConnectionError('Log stream disconnected, attempting to reconnect...');
        scheduleReconnect();
      };
    };

    connect();

    return () => {
      disposed = true;
      cleanupTimer();
      cleanupSocket();
      setIsConnected(false);
    };
  }, [token]);

  const clear = () => setMessages([]);

  return { messages, connectionError, isConnected, clear };
};
