export {};

declare global {
  interface DesktopEnvironment {
    isDev: boolean;
    apiBaseUrl: string;
  }

  type DesktopTaskEventName = 'queued' | 'started' | 'progress' | 'completed' | 'failed' | 'cancelled' | 'log';

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
    meta?: Record<string, unknown>;
  }

  interface DesktopTaskEventPayload {
    jobId: string;
    job: DesktopTaskSummary;
    level?: string;
    message?: string;
    [key: string]: unknown;
  }

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
    on: (eventName: DesktopTaskEventName, listener: (payload: DesktopTaskEventPayload) => void) => () => void;
  }

  interface DesktopApi {
    getEnvironment: () => Promise<DesktopEnvironment>;
    openExternal: (url: string) => void;
    platform: NodeJS.Platform;
    tasks: DesktopTasksApi;
  }

  interface Window {
    desktopApi: DesktopApi;
  }
}
