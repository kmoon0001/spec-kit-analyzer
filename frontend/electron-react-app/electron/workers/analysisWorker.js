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

const { payload, metadata } = workerData;
const controller = new AbortController();
const { apiBaseUrl, token, pollIntervalMs = 1500, timeoutMs = 15 * 60 * 1000 } = metadata ?? {};

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

const fetchJson = async (url, options = {}) => {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    const error = new Error(`Request failed with status ${response.status}`);
    error.status = response.status;
    error.body = text;
    throw error;
  }
  return response.json();
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

    const startResponse = await fetchJson(`${apiBaseUrl}/analysis/analyze`, {
      method: 'POST',
      body: formData,
      headers: buildHeaders(),
      signal: controller.signal,
    });

    const taskId = startResponse?.task_id;
    if (!taskId) {
      throw new Error('API did not return task_id');
    }

    post('progress', { progress: 15, statusMessage: 'Analysis started', meta: { taskId } });

    const startedAt = Date.now();
    let lastProgress = 15;

    while (!cancelled) {
      if (Date.now() - startedAt > timeoutMs) {
        throw new Error('Analysis timed out');
      }

      await sleep(pollIntervalMs, controller.signal);

      const statusData = await fetchJson(`${apiBaseUrl}/analysis/status/${taskId}`, {
        method: 'GET',
        headers: buildHeaders(),
        signal: controller.signal,
      });

      const status = statusData?.status ?? 'processing';
      let progress = normalizeProgress(statusData?.progress);
      if (progress < lastProgress) {
        progress = lastProgress;
      } else {
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
