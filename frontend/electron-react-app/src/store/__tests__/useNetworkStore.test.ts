import { act } from "@testing-library/react";

import { useDiagnosticsStore } from "../useDiagnosticsStore";
import { useNetworkStore } from "../useNetworkStore";

describe("useNetworkStore", () => {
  beforeEach(() => {
    useDiagnosticsStore.getState().clear();
    useNetworkStore.setState(() => ({
      status: "idle",
      pendingRequests: 0,
      lastError: null,
      lastUpdated: Date.now(),
    }));
  });

  it("pushes diagnostics when transitioning offline and back online", () => {
    act(() => {
      useNetworkStore.getState().setStatus("offline", "Network unreachable");
    });

    const offlineEvent = useDiagnosticsStore.getState().lastEvent;
    expect(offlineEvent?.severity).toBe("error");
    expect(offlineEvent?.message).toBe("Network unreachable");
    expect(offlineEvent?.context).toMatchObject({ status: "offline" });

    act(() => {
      useNetworkStore.getState().setStatus("offline");
    });

    expect(useDiagnosticsStore.getState().events).toHaveLength(1);

    act(() => {
      useNetworkStore.getState().setStatus("online");
    });

    const restoredEvent = useDiagnosticsStore.getState().lastEvent;
    expect(restoredEvent?.severity).toBe("info");
    expect(restoredEvent?.message).toBe("Network connection restored");
    expect(restoredEvent?.context).toMatchObject({ previousStatus: "offline" });
  });

  it("tracks pending request counts safely", () => {
    act(() => {
      useNetworkStore.getState().trackRequestStart();
      useNetworkStore.getState().trackRequestStart();
      useNetworkStore.getState().trackRequestEnd();
    });

    expect(useNetworkStore.getState().pendingRequests).toBe(1);

    act(() => {
      useNetworkStore.getState().trackRequestEnd();
      useNetworkStore.getState().trackRequestEnd();
    });

    expect(useNetworkStore.getState().pendingRequests).toBe(0);
  });
});
