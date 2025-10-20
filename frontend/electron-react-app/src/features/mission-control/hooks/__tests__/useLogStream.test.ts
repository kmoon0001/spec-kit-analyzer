import { act, renderHook } from "@testing-library/react";

import { useLogStream } from "../useLogStream";
import { useAppStore } from "store/useAppStore";
import * as configModule from "lib/config";
import * as backoffModule from "lib/network/backoff";

let originalWebSocket: typeof WebSocket | undefined;

const mockNext = jest.fn(() => 1000);
const mockReset = jest.fn();

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  public url: string;
  public onopen: (() => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public close = jest.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
}

const getConfigMock = jest.spyOn(configModule, "getConfig");
const getNormalizedBaseMock = jest.spyOn(
  configModule,
  "getNormalizedApiBaseUrl",
);
const createBackoffMock = jest.spyOn(backoffModule, "createExponentialBackoff");

describe("useLogStream", () => {
  beforeAll(() => {
    originalWebSocket = global.WebSocket;
    Object.defineProperty(global, "WebSocket", {
      configurable: true,
      writable: true,
      value: MockWebSocket,
    });

    if (!global.crypto) {
      Object.defineProperty(global, "crypto", {
        configurable: true,
        writable: true,
        value: { randomUUID: jest.fn(() => "test-uuid") },
      });
    }
  });

  afterAll(() => {
    Object.defineProperty(global, "WebSocket", {
      configurable: true,
      writable: true,
      value: originalWebSocket,
    });
  });

  beforeEach(() => {
    MockWebSocket.instances.length = 0;
    mockReset.mockClear();
    mockNext.mockClear();

    getConfigMock.mockReturnValue({
      apiBaseUrl: "http://localhost:8100",
      isDesktop: false,
      isDev: false,
    });
    getNormalizedBaseMock.mockImplementation((config) => config.apiBaseUrl);
    createBackoffMock.mockReturnValue({ next: mockNext, reset: mockReset });

    act(() => {
      useAppStore.setState((state) => ({
        auth: { ...state.auth, token: null, username: null },
      }));
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns auth error state when token missing", () => {
    const { result } = renderHook(() => useLogStream());

    expect(result.current.isConnected).toBe(false);
    expect(result.current.messages).toHaveLength(0);
    expect(result.current.connectionError).toBe(
      "Authentication required to view logs",
    );
  });

  it("connects when token present and records messages", async () => {
    jest.useFakeTimers();
    act(() => {
      useAppStore.setState((state) => ({
        auth: { ...state.auth, token: "token-123", username: "tester" },
      }));
    });

    const { result, unmount } = renderHook(() => useLogStream());

    const socket = MockWebSocket.instances[0];
    expect(socket.url).toBe("ws://localhost:8100/ws/logs?token=token-123");

    await act(async () => {
      socket.onopen?.();
    });

    expect(mockReset).toHaveBeenCalledTimes(1);
    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionError).toBeNull();

    await act(async () => {
      await socket.onmessage?.({
        data: JSON.stringify({ message: "First", level: "INFO" }),
      } as MessageEvent);
      await socket.onmessage?.({
        data: JSON.stringify({ type: "heartbeat" }),
      } as MessageEvent);
      await socket.onmessage?.({ data: "Plain text payload" } as MessageEvent);
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].message).toBe("First");
    expect(result.current.messages[0].level).toBe("info");
    expect(result.current.messages[1].message).toBe("Plain text payload");

    unmount();
    expect(socket.close).toHaveBeenCalledTimes(1);
  });

  it("schedules reconnect with backoff on unexpected close", async () => {
    jest.useFakeTimers();
    const setTimeoutSpy = jest.spyOn(window, "setTimeout");

    act(() => {
      useAppStore.setState((state) => ({
        auth: { ...state.auth, token: "token-abc", username: "tester" },
      }));
    });

    const { result } = renderHook(() => useLogStream());
    const socket = MockWebSocket.instances[0];

    await act(async () => {
      socket.onopen?.();
    });

    await act(async () => {
      socket.onclose?.({} as CloseEvent);
    });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionError).toBe(
      "Log stream disconnected, attempting to reconnect...",
    );
    expect(mockNext).toHaveBeenCalledTimes(1);
    expect(setTimeoutSpy).toHaveBeenCalledTimes(1);

    const reconnectFn = setTimeoutSpy.mock.calls[0]?.[0] as () => void;
    act(() => {
      reconnectFn();
    });

    expect(MockWebSocket.instances).toHaveLength(2);

    setTimeoutSpy.mockRestore();
  });
});
