import { create } from "zustand";
import { useDiagnosticsStore } from "./useDiagnosticsStore";

export type NetworkStatus = "idle" | "online" | "degraded" | "offline";

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
  status: "idle",
  pendingRequests: 0,
  lastError: null,
  lastUpdated: Date.now(),
  setStatus: (status: NetworkStatus, error: string | null = null) =>
    set((state) => {
      const statusChanged = state.status !== status;
      if (statusChanged) {
        const pushEvent = useDiagnosticsStore.getState().pushEvent;
        if (status === "online") {
          if (state.status !== "online") {
            pushEvent({
              source: "network",
              severity: "info",
              message: "Network connection restored",
              context: { previousStatus: state.status },
            });
          }
        } else {
          pushEvent({
            source: "network",
            severity: status === "offline" ? "error" : "warning",
            message: error ?? `Network status changed to ${status}`,
            context: { previousStatus: state.status, status, error },
          });
        }
      }

      return {
        status,
        lastError: error,
        lastUpdated: Date.now(),
      };
    }),
  trackRequestStart: () =>
    set((state) => ({
      pendingRequests: state.pendingRequests + 1,
    })),
  trackRequestEnd: () =>
    set((state) => ({
      pendingRequests:
        state.pendingRequests > 0 ? state.pendingRequests - 1 : 0,
      lastUpdated: Date.now(),
    })),
  clearError: () =>
    set({
      lastError: null,
      lastUpdated: Date.now(),
    }),
}));
