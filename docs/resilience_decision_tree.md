# Runtime Resilience Decision Tree

## Connectivity & API Reachability
- **Verify service endpoint**: Confirm Electron runtime `desktopApi` handshake delivered expected `apiBaseUrl` (`npm run env:print`).
- **CORS/protocol guard**:
  - If renderer served from `file://` or `app://`, hit `GET /healthz` to check for 308/404.
  - On mixed-content errors, ensure backend exposes TLS and update `settings.ALLOWED_ORIGINS`.
- **Decision node: backend unreachable**
  1. Check local firewall/VPN rules; whitelist configured port (default `8100`).
  2. Tail FastAPI logs via `uvicorn --reload` for `Address already in use`; restart service with clean socket.
  3. If Electron packaged build, confirm preload exposes `desktopApi.getEnvironment()`.
- **Detection instrumentation**:
  - `useNetworkStore` status should flip to `offline` with details. Inspect status bar ?Network? chip.
  - Run `curl -v http://127.0.0.1:8100/health` to ensure loopback accepts connections.
- **Code pattern**:

```ts
// src/lib/api/client.ts
apiClient.interceptors.response.use(
  (response) => {
    // Success: mark network healthy
  },
  async (error) => {
    // Retry recoverable statuses with exponential backoff
  }
);
```

## WebSocket & Log Streaming
- **Single connection audit**: `useLogStream` manages one socket and resets timers on token changes.
- **Decision node: log stream silent**
  1. Check `/ws/logs` authentication ? ensure bearer token appended.
  2. If backend closes with 1008, confirm JWT secret/algorithm matches Electron build.
  3. Inspect Mission Control console; structured payloads should show `[HH:MM][LEVEL logger] message`.
- **Heartbeat monitor**: Backend emits `{type: "heartbeat"}`; hook ignores without enqueueing.
- **Code pattern**:

```ts
const entry = normalizeLogEntry(parsed, decoded);
setMessages((prev) => [...prev.slice(-(MAX_MESSAGES - 1)), entry]);
```

## Worker Threads & Task Polling
- **Upload stage**: Worker enforces `uploadTimeoutMs` (defaults to 4 minutes) and respects cancellation via shared controller.
- **Status polling**
  - Retries transient 404/409 (task not yet registered) once before next poll.
  - Emits diagnostic `progress` message on retry to keep renderer telemetry alive.
- **Decision node: stuck polling**
  1. Inspect worker log for `retryAttempt` metadata; if continuous, backend queue likely stalled ? run `/analysis/status/{taskId}` manually.
  2. If timeout triggered, push task back into registry via `/analysis/analyze` and validate strictness path.
- **Code pattern**:

```js
const statusData = await fetchJson(url, init, {
  maxRetries: 1,
  retryOnStatuses: [404, 409],
  timeoutMs: statusTimeoutMs,
  onRetry: createRetryNotifier('Analysis status', () => ({ taskId })),
});
```

## Renderer Diagnostics & ?Unknown Unknowns?
- **Global guards**: `initializeGlobalErrorHandlers()` traps window errors and unhandled rejections, piping them to `useDiagnosticsStore`.
- **Status bar alerts**: New ?Alerts? chip surfaces outstanding crashes/hard failures; hover to review message/stack.
- **Memory/resource drift**
  - Use Mission Control telemetry to watch CPU/RAM under >50 page document runs.
  - For leaks, profile renderer heap snapshots after repeated uploads ? look for retained `ArrayBuffer` from file previews.
- **Testing checkpoints**
  1. `pytest tests/test_api_analysis.py -k strictness` once `transformers` dependency mocked.
  2. `npm run lint && npm run test -- --watch=false` to ensure hooks/components remain typed.
  3. Synthetic network chaos (drop packets / add latency) with `tnc` or `clumsy` to validate retry cadence.
- **Future hardening ideas**
  - Wire `useDiagnosticsStore` to desktop tray notifications via `desktopApi`.
  - Add Playwright smoke for reconnect flows (simulate `ws` drop via `page.route`).
  - Persist diagnostics queue to disk for post-mortem when renderer crashes.

## Secure Disposal & Compliance
- Ensure worker deletes temporary buffers when analysis completes (queue for follow-up).
- Review PDF export path for PHI redaction before writing to disk.
- Maintain HIPAA logging: tie diagnostics events to user/session identifiers in secure storage when enabling remote monitoring.
