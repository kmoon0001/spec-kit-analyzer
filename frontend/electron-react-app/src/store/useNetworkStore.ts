import { create } from 'zustand';

export type NetworkStatus = 'idle' | 'online' | 'degraded' | 'offline';

interface NetworkState {
  status: NetworkStatus;
  pendingRequests: number;
  lastError: string | null;
  lastUpdated: number;
  setStatus: (status: NetworkStatus, error?: string | null) => void;
  trackRequestStart: () => void;
  trackRequestEnd: () => void;
  clearError: () => void;
}

export const useNetworkStore = create<NetworkState>((set) => ({
  status: 'idle',
  pendingRequests: 0,
  lastError: null,
  lastUpdated: Date.now(),
  setStatus: (status, error = null) =>
    set({
      status,
      lastError: error,
      lastUpdated: Date.now(),
    }),
  trackRequestStart: () =>
    set((state) => ({
      pendingRequests: state.pendingRequests + 1,
    })),
  trackRequestEnd: () =>
    set((state) => ({
      pendingRequests: state.pendingRequests > 0 ? state.pendingRequests - 1 : 0,
      lastUpdated: Date.now(),
    })),
  clearError: () =>
    set({
      lastError: null,
      lastUpdated: Date.now(),
    }),
}));
