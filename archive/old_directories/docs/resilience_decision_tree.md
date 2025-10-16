# Runtime Resilience Decision Tree

## Connectivity & API Reachability
- **Verify service endpoint**: Confirm the Electron handshake exposes the expected `apiBaseUrl` (`npm run env:print`), and compare with the FastAPI `settings.api_base_url`.
- **CORS & protocol guard**: When the renderer runs from `file://`/`app://`, hit `GET /healthz`; a 308/404 implies the backend is enforcing HTTP-only origins—update `settings.ALLOWED_ORIGINS` and TLS configuration accordingly.
- **Decision node – backend unreachable**
  1. Inspect local firewall/VPN/proxy rules; whitelist the configured port (defaults to `8100`).
  2. Tail FastAPI logs (`poetry run uvicorn ... --reload`) for `Address already in use`; recycle the service to clear stale sockets.
  3. For packaged Electron builds, assert `desktopApi.getEnvironment()` returns the runtime port.
- **Detection instrumentation**: the Status Bar `Network` chip should flip to `offline`/`degraded` with a descriptive tooltip; `useNetworkStore` now records diagnostics whenever connectivity status changes.
- **Code pattern** (`frontend/electron-react-app/src/lib/api/client.ts`):

```ts
apiClient.interceptors.response.use(
  (response) => {
    useNetworkStore.getState().setStatus('online');
    return response;
  },
  async (error) => {
    if (shouldRetry(error, config, maxRetries)) {
      const delay = retryState.backoff.next();
      useNetworkStore.getState().setStatus('degraded', `Retrying in ${delay}ms`);
      await waitFor(delay, config.signal);
      return apiClient(config);
    }
    useNetworkStore.getState().setStatus('offline', deriveMessage(error));
    return Promise.reject(error);
  }
);
```

## WebSocket & Log Streaming
- **Single connection audit**: `useLogStream` keeps one socket per token, resets backoff after successful open, and cleans handlers on unmount.
- **Decision node – silent console**
  1. Confirm `/ws/logs` query string includes the bearer token; a 1008 close means JWT verification failed.
  2. If the backend drops immediately, inspect FastAPI logs for permission errors—`WebSocketLogHandler` now runs in the API event loop.
  3. Renderer console should render `[HH:MM][LEVEL logger] message`; parsing failures fall back to the raw payload.
- **Heartbeat monitor**: backend emits `{ "type": "heartbeat" }`; the hook discards these so the UI does not flood.
- **Code pattern** (`useLogStream.ts`):

```ts
const backoff = createExponentialBackoff({ initialDelayMs: 750, maxDelayMs: 15_000 });
const scheduleReconnect = () => {
  const delay = backoff.next();
  reconnectTimerRef.current = window.setTimeout(connect, delay);
};
```

## Worker Threads & Task Polling
- **Upload stage**: `analysisWorker.js` wraps uploads with `createRequestSignal` and `uploadTimeoutMs` (4 min default) so stalled transfers abort cleanly.
- **Status polling**: retries transient `404/409` once, emits structured retry telemetry, and caps total runtime via `timeoutMs`.
- **Decision node – stuck polling**
  1. Inspect worker telemetry logs for `retryAttempt`; continuous retries imply the backend queue is idle—query `/analysis/status/{taskId}` manually.
  2. If `timeoutMs` expires, reset the task via `/analysis/analyze` and review `analysis_task_registry` for orphaned metadata.
- **Code pattern** (`electron/workers/analysisWorker.js`):

```js
const statusData = await fetchJson(statusUrl, init, {
  maxRetries: 1,
  retryOnStatuses: [404, 409],
  timeoutMs: statusTimeoutMs,
  onRetry: createRetryNotifier('Analysis status', () => ({ taskId })),
});
```

## Renderer & Desktop Diagnostics
- **Global guards** (`frontend/electron-react-app/src/lib/monitoring/globalErrors.ts`): traps window errors and unhandled rejections, pushing them into `useDiagnosticsStore`.
- **Desktop bridge** (`frontend/electron-react-app/src/lib/monitoring/desktopDiagnostics.ts`): `initializeDesktopDiagnosticsBridge()` subscribes to `desktopApi.onDiagnostic` so uncaught main-process errors, renderer crashes, and worker exits surface in the renderer alerts feed.
- **Main-process coverage** (`frontend/electron-react-app/electron/main.js`): `registerDiagnosticHandlers()` captures `uncaughtException`, `unhandledRejection`, `child-process-gone`, and renderer load failures, broadcasting enriched diagnostics over `app:diagnostic` IPC.
- **UI surface**: the Status Bar `Alerts` chip now reflects diagnostics count; hovering shows the most recent stack trace. Clearing the store resets the badge without muting future alerts.
- **Code pattern** (`initializeDesktopDiagnosticsBridge`):

```ts
const unsubscribe = api.onDiagnostic((payload) => {
  pushEvent({
    source: 'process',
    severity: normalizeSeverity(payload.severity),
    message: payload.message ?? payload.type ?? 'Desktop diagnostic',
    stack: payload.stack,
    context: { origin: payload.source ?? 'main-process', ...payload.context },
  });
});
```

## Resource Governance & Large Documents
- Route heavy analysis through worker threads (`analysisWorker.js`) so the renderer remains responsive.
- Stream or chunk large uploads via `fetchJson` + `FormData`; enforce size checks in `src/api/routers/analysis.py` and reject 0-byte/oversized payloads early.
- Use virtualization (`react-window`/list slicing) for >50-page renderers; memoize derived data in mission-control dashboards to prevent cascade re-renders.
- Monitor CPU/RAM via the telemetry snapshot from the Electron main process; throttle background polls if `cpuPercent > 85` or memory pressure exceeds 80%.

## Secure Disposal & Compliance
- Queue follow-up to purge temporary buffers once analysis completes; ensure worker threads `fs.readFile` buffers are zeroed or dropped promptly.
- Before exporting PDFs, confirm PHI redaction pathways in `PDFExportService` and tighten file permissions in packaging scripts.
- Maintain HIPAA-aligned audit trails: diagnostics events include timestamps, severity, and origin for centralized logging.

## Regression Safety & "Unknown Unknowns"
- **Testing cadence**:
  1. Backend: extend `tests/test_api_analysis.py` to cover strictness propagation, file-size validation, and task-registry cancellation. Mock `transformers` if unavailable.
  2. Frontend: add RTL coverage for `useLogStream` reconnects and network store diagnostics; stage Playwright chaos tests to simulate WebSocket drops and slow networks.
  3. Desktop: scripted worker harness to replay large-document workloads, verifying retry telemetry and IPC health.
- **Instrumentation**: enable verbose Structlog + WebSocket log streaming during load tests; correlate with renderer diagnostics feed to capture silent failures.
- **Code review checklist**:
  - Flag any new network call without timeout/backoff.
  - Verify cleanup of timers/event listeners in hooks and workers.
  - Ensure every IPC entry point validates payload shape and abort signals.
- **Runtime assertions**: prefer defensive guards like `if (!token) throw new Error('Authentication required');` in async flows to expose misconfigurations early.
- **Operational drills**: rehearse network partition, backend crash, and worker OOM scenarios; validate that retry telemetry, diagnostics alerts, and user-facing messaging remain responsive.
