import { create } from 'zustand';

export type DiagnosticSeverity = 'info' | 'warning' | 'error' | 'critical';

export type DiagnosticSource = 'window-error' | 'unhandled-rejection' | 'manual' | 'network' | 'process';

export interface DiagnosticEvent {
  id: string;
  message: string;
  timestamp: number;
  severity: DiagnosticSeverity;
  source: DiagnosticSource;
  stack?: string;
  context?: Record<string, unknown>;
}

interface DiagnosticsState {
  events: DiagnosticEvent[];
  lastEvent: DiagnosticEvent | null;
  pushEvent: (event: Omit<DiagnosticEvent, 'id' | 'timestamp'> & Partial<Pick<DiagnosticEvent, 'timestamp'>>) => void;
  acknowledge: (id: string) => void;
  clear: () => void;
}

const createEventId = () => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;

export const useDiagnosticsStore = create<DiagnosticsState>((set) => ({
  events: [],
  lastEvent: null,
  pushEvent: (event) =>
    set((state) => {
      const timestamp = event.timestamp ?? Date.now();
      const nextEvent: DiagnosticEvent = {
        id: createEventId(),
        timestamp,
        severity: event.severity,
        source: event.source,
        message: event.message,
        stack: event.stack,
        context: event.context,
      };
      const nextEvents = [...state.events.slice(-49), nextEvent];
      return {
        events: nextEvents,
        lastEvent: nextEvent,
      };
    }),
  acknowledge: (id) =>
    set((state) => {
      const filtered = state.events.filter((event) => event.id !== id);
      const lastEvent = state.lastEvent && state.lastEvent.id === id ? filtered.at(-1) ?? null : state.lastEvent;
      return {
        events: filtered,
        lastEvent,
      };
    }),
  clear: () => set({ events: [], lastEvent: null }),
}));
