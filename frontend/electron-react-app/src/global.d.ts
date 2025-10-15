export {};

declare global {
  interface DesktopEnvironment {
    isDev: boolean;
    apiBaseUrl: string;
  }

  interface DesktopDiagnosticPayload {
    type?: string;
    message?: string;
    stack?: string;
    severity?: 'info' | 'warning' | 'error' | 'critical';
    source?: string;
    context?: Record<string, unknown>;
    timestamp?: number;
  }

  interface DesktopTaskResult {
    [key: string]: unknown;
  }

  interface DesktopTaskError {
    message?: string;
    stack?: string;
    name?: string;
    [key: string]: unknown;
  }

  interface DesktopTaskSummary {
    id: string;
    type: string;
    status: string;
    progress?: number;
    statusMessage?: string;
    createdAt?: number;
    startedAt?: number;
    completedAt?: number;
    error?: DesktopTaskError | null;
    result?: DesktopTaskResult | null;
    meta?: Record<string, unknown> | null;
  }

  interface DesktopTelemetryCpuSample {
    percent: number;
    normalizedPercent: number;
    user: number;
    system: number;
    totalMs: number;
    elapsedMs: number;
    cores: number;
  }

  interface DesktopTelemetryMemorySample {
    rss: number;
    heapTotal: number;
    heapUsed: number;
    external: number;
    arrayBuffers: number;
    details?: Record<string, number> | null;
  }

  interface DesktopTelemetryEventLoopSample {
    mean: number;
    max: number;
    min: number;
    stddev: number;
    p50: number;
    p90: number;
    p99: number;
  }

  interface DesktopTelemetrySystemSample {
    loadavg: number[];
    totalMem: number | null;
    freeMem: number | null;
    uptime: number | null;
  }

  interface DesktopTelemetryWorkerSample {
    jobId: string;
    threadId: number | null;
    type: string;
    status: string;
    progress: number;
    runtimeMs: number;
    eventLoopUtilization: number | null;
  }

  interface DesktopTelemetrySnapshot {
    timestamp: number;
    queueSize: number;
    activeCount: number;
    concurrency: number;
    cpu: DesktopTelemetryCpuSample;
    memory: DesktopTelemetryMemorySample;
    eventLoop: DesktopTelemetryEventLoopSample | null;
    system: DesktopTelemetrySystemSample;
    workers: DesktopTelemetryWorkerSample[];
    jobs: DesktopTaskSummary[];
  }

  interface DesktopTaskEventPayload {
    jobId: string;
    job?: DesktopTaskSummary;
    level?: string;
    message?: string;
    [key: string]: unknown;
  }

  interface DesktopTaskEventMap {
    queued: DesktopTaskEventPayload;
    started: DesktopTaskEventPayload;
    progress: DesktopTaskEventPayload;
    completed: DesktopTaskEventPayload;
    failed: DesktopTaskEventPayload;
    cancelled: DesktopTaskEventPayload;
    log: DesktopTaskEventPayload;
    telemetry: DesktopTelemetrySnapshot;
  }

  type DesktopTaskEventName = keyof DesktopTaskEventMap;

  interface DesktopTaskStartOptions {
    type: string;
    payload: unknown;
    jobId?: string;
    metadata?: Record<string, unknown>;
    timeoutMs?: number;
  }

  interface DesktopTasksApi {
    startTask: (request: DesktopTaskStartOptions) => Promise<{ jobId: string }>;
    startAnalysis: (
      payload: Record<string, unknown>,
      options?: { metadata?: Record<string, unknown>; timeoutMs?: number; jobId?: string },
    ) => Promise<{ jobId: string }>;
    cancel: (jobId: string, reason?: string) => Promise<{ ok: boolean }>;
    list: () => Promise<{ jobs: DesktopTaskSummary[] }>;
    get: (jobId: string) => Promise<{ job: DesktopTaskSummary | null }>;
    on: <T extends DesktopTaskEventName>(eventName: T, listener: (payload: DesktopTaskEventMap[T]) => void) => () => void;
  }

  interface DesktopApi {
    getEnvironment: () => Promise<DesktopEnvironment>;
    openExternal: (url: string) => void;
    platform: NodeJS.Platform;
    tasks: DesktopTasksApi;
    onDiagnostic?: (listener: (payload: DesktopDiagnosticPayload) => void) => () => void;
  }

  interface Window {
    desktopApi?: DesktopApi;
  }
}
