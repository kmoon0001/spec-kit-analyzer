const { parentPort, workerData } = require('node:worker_threads');
const { Blob } = require('node:buffer');
const fs = require('node:fs/promises');
const path = require('node:path');

const sleep = (ms, signal) =>
  new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'));
      return;
    }
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(timer);
        reject(new DOMException('Aborted', 'AbortError'));
      },
      { once: true },
    );
  });

const serializeError = (error) => ({
  message: error?.message ?? String(error),
  stack: error?.stack,
  name: error?.name,
  cause: error?.cause ?? null,
});

const post = (type, data) => parentPort.postMessage({ type, data });

const createExponentialDelay = ({ initialDelayMs = 500, multiplier = 2, maxDelayMs = 8000 } = {}) => {
  let attempt = 0;
  return () => {
    const delay = Math.min(initialDelayMs * multiplier ** attempt, maxDelayMs);
    attempt += 1;
    return delay + Math.random() * Math.min(delay * 0.25, 1000);
  };
};

const createRequestSignal = (timeoutMs, ...signals) => {
  const validSignals = signals.filter((signal) => Boolean(signal));
  let timeoutId = null;

  if (typeof timeoutMs === 'number' && timeoutMs > 0) {
    const timeoutController = new AbortController();
    timeoutId = setTimeout(() => timeoutController.abort(), timeoutMs);
    validSignals.push(timeoutController.signal);
  }

  if (validSignals.length === 0) {
    return { signal: undefined, dispose: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    } };
  }

  if (validSignals.length === 1) {
    return { signal: validSignals[0], dispose: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    } };
  }

  const composite = new AbortController();
  const abort = () => composite.abort();

  for (const signal of validSignals) {
    if (signal.aborted) {
      composite.abort();
      break;
    }
    signal.addEventListener('abort', abort, { once: true });
  }

  return {
    signal: composite.signal,
    dispose: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    },
  };
};

const createRetryNotifier = (stage, metaProvider) => (attempt, delay, error) => {
  const seconds = Math.max(1, Math.round(delay / 1000));
  const extraMeta = typeof metaProvider === 'function' ? metaProvider() : metaProvider;
  post('progress', {
    statusMessage: `${stage} retry ${attempt} in ${seconds}s`,
    meta: {
      stage,
      retryAttempt: attempt,
      retryDelayMs: delay,
      error: serializeError(error),
      ...extraMeta,
    },
  });
};

const { payload, metadata } = workerData;
const controller = new AbortController();
const { apiBaseUrl, token, pollIntervalMs = 1500, timeoutMs = 15 * 60 * 1000, uploadTimeoutMs = 4 * 60 * 1000, statusTimeoutMs = 15000 } = metadata ?? {};

let cancelled = false;

parentPort.on('message', (message) => {
  if (message?.type === 'cancel') {
    cancelled = true;
    controller.abort();
    post('progress', { statusMessage: 'Cancellation requested by user' });
  }
});

const readFileBuffer = async () => {
  if (payload.fileBuffer) {
    return Buffer.from(payload.fileBuffer);
  }
  if (payload.filePath) {
    const resolved = path.resolve(payload.filePath);
    return fs.readFile(resolved);
  }
  throw new Error('No file content provided');
};

const buildFormData = async () => {
  const buffer = await readFileBuffer();
  const formData = new FormData();
  const fileName = payload.fileName ?? 'document.bin';
  formData.append('file', new Blob([buffer]), fileName);
  formData.append('discipline', payload.discipline ?? 'pt');
  formData.append('analysis_mode', payload.analysisMode ?? 'rubric');
  formData.append('strictness', payload.strictness ?? 'standard');
  return formData;
};

const fetchJson = async (url, options = {}, retryOptions = {}) => {
  const method = typeof options.method === 'string' ? options.method.toUpperCase() : 'GET';
  const defaultRetryable = ['GET', 'HEAD', 'OPTIONS'].includes(method);
  const maxRetries = typeof retryOptions.maxRetries === 'number' ? retryOptions.maxRetries : defaultRetryable ? 3 : 0;
  const retryStatuses = new Set([408, 425, 429, ...(retryOptions.retryOnStatuses ?? [])]);
  const allowNetworkRetry = retryOptions.retryNetworkErrors ?? defaultRetryable;
  const nextDelay = createExponentialDelay({
    initialDelayMs: retryOptions.initialDelayMs ?? 500,
    maxDelayMs: retryOptions.maxDelayMs ?? 8000,
  });

  let lastError;
  for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
    const { signal, dispose } = createRequestSignal(retryOptions.timeoutMs, controller.signal, options.signal);

    try {
      const response = await fetch(url, { ...options, signal });

      if (!response.ok) {
        const text = await response.text();
        const error = new Error(`Request failed with status ${response.status}`);
        error.status = response.status;
        error.body = text;

        const shouldRetryResponse =
          attempt < maxRetries &&
          (response.status >= 500 ||
            retryStatuses.has(response.status) ||
            (retryOptions.retryOnClientErrors && response.status >= 400 && response.status < 500));

        if (!shouldRetryResponse) {
          dispose();
          throw error;
        }

        lastError = error;
        const delay = nextDelay();
        retryOptions.onRetry?.(attempt + 1, delay, error);
        dispose();
        await sleep(delay, controller.signal);
        continue;
      }

      if (retryOptions.expectJson === false) {
        dispose();
        return response;
      }

      const contentType = response.headers.get('content-type');
      if (contentType && !contentType.includes('application/json')) {
        dispose();
        return response.text();
      }

      dispose();
      return response.json();
    } catch (error) {
      if (error?.name === 'AbortError') {
        dispose();
        throw error;
      }

      const status = error?.status;
      const isNetworkError = status === undefined;
      const shouldRetry =
        attempt < maxRetries &&
        ((isNetworkError && allowNetworkRetry) ||
          (typeof status === 'number' && status >= 500) ||
          (typeof status === 'number' && retryStatuses.has(status)) ||
          (retryOptions.retryOnClientErrors &&
            typeof status === 'number' &&
            status >= 400 &&
            status < 500));

      if (!shouldRetry) {
        dispose();
        throw error;
      }

      lastError = error;
      const delay = nextDelay();
      retryOptions.onRetry?.(attempt + 1, delay, error);
      dispose();
      await sleep(delay, controller.signal);
    }
  }

  throw lastError ?? new Error('Request failed after retries');
};

const buildHeaders = () => {
  const result = { Accept: 'application/json' };
  if (token) {
    result.Authorization = `Bearer ${token}`;
  }
  return result;
};

const normalizeProgress = (value) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0;
  }
  if (value <= 1) {
    return Math.round(value * 100);
  }
  if (value > 100) {
    return 100;
  }
  return value;
};

const run = async () => {
  try {
    if (!apiBaseUrl) {
      throw new Error('API base URL missing');
    }

    post('progress', { progress: 2, statusMessage: 'Preparing analysis job' });

    const formData = await buildFormData();

    post('progress', { progress: 10, statusMessage: 'Uploading document' });

    const startResponse = await fetchJson(
      `${apiBaseUrl}/analysis/analyze`,
      {
        method: 'POST',
        body: formData,
        headers: buildHeaders(),
        signal: controller.signal,
      },
      {
        maxRetries: 0,
        timeoutMs: uploadTimeoutMs,
      },
    );

    const taskId = startResponse?.task_id;
    if (!taskId) {
      throw new Error('API did not return task_id');
    }

    post('progress', { progress: 15, statusMessage: 'Analysis started', meta: { taskId } });

    const startedAt = Date.now();
    let lastProgress = 0;

    while (!cancelled) {
      if (Date.now() - startedAt > timeoutMs) {
        throw new Error('Analysis timed out');
      }

      await sleep(pollIntervalMs, controller.signal);

      const statusData = await fetchJson(
        `${apiBaseUrl}/analysis/status/${taskId}`,
        {
          method: 'GET',
          headers: buildHeaders(),
          signal: controller.signal,
        },
        {
          maxRetries: 1,
          retryOnStatuses: [404, 409],
          timeoutMs: statusTimeoutMs,
          onRetry: createRetryNotifier('Analysis status', () => ({ taskId })),
        },
      );

      const status = statusData?.status ?? 'processing';
      let progress = normalizeProgress(statusData?.progress);

      // Only prevent backwards progress if we have meaningful progress from backend
      if (progress > 0 && progress < lastProgress) {
        progress = lastProgress;
      } else if (progress > lastProgress) {
        lastProgress = progress;
      }

      const statusMessage = statusData?.status_message ?? `Status: ${status}`;

      post('progress', {
        progress,
        statusMessage,
        meta: { status, taskId, raw: statusData },
      });

      if (status === 'failed') {
        const errorMessage = statusData?.error ?? 'Analysis failed';
        throw new Error(errorMessage);
      }

      if (status === 'completed') {
        post('result', {
          progress: 100,
          statusMessage: 'Analysis completed',
          result: {
            taskId,
            status: statusData.status,
            statusMessage: statusData.status_message,
            progress: normalizeProgress(statusData.progress),
            analysis: statusData.analysis,
            reportHtml: statusData.report_html,
            raw: statusData,
          },
        });
        return;
      }
    }
  } catch (error) {
    if (cancelled || error?.name === 'AbortError') {
      post('cancelled', { statusMessage: 'Analysis cancelled by user' });
      return;
    }
    post('error', {
      statusMessage: error?.message ?? 'Analysis failed',
      error: serializeError(error),
    });
  }
};

run();
