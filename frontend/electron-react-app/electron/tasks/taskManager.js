const { EventEmitter } = require('node:events');
const { Worker } = require('node:worker_threads');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

const DEFAULT_TERMINATE_TIMEOUT_MS = 5_000;

class TaskManager extends EventEmitter {
  constructor(options = {}) {
    super();
    const cpuCount = os.cpus()?.length ?? 4;
    this.concurrency = Math.max(1, options.concurrency ?? Math.min(cpuCount - 1, 4));
    this.workerRegistry = new Map();
    this.jobs = new Map();
    this.queue = [];
    this.active = new Map();
  }

  register(type, workerRelativePath) {
    const workerPath = path.isAbsolute(workerRelativePath)
      ? workerRelativePath
      : path.join(__dirname, '..', workerRelativePath);
    this.workerRegistry.set(type, workerPath);
  }

  listJobs() {
    return Array.from(this.jobs.values()).map((job) => ({
      id: job.id,
      type: job.type,
      status: job.status,
      progress: job.progress,
      statusMessage: job.statusMessage,
      createdAt: job.createdAt,
      startedAt: job.startedAt,
      completedAt: job.completedAt,
      error: job.error,
      result: job.result,
    }));
  }

  getJob(jobId) {
    return this.jobs.get(jobId) ?? null;
  }

  startTask({ type, payload, jobId: requestedId, metadata = {}, timeoutMs }) {
    if (!this.workerRegistry.has(type)) {
      throw new Error(`No worker registered for task type: ${type}`);
    }
    const jobId = requestedId ?? crypto.randomUUID();
    if (this.jobs.has(jobId)) {
      throw new Error(`Duplicate job id requested: ${jobId}`);
    }

    const job = {
      id: jobId,
      type,
      payload,
      metadata,
      status: 'queued',
      progress: 0,
      statusMessage: 'Queued',
      createdAt: Date.now(),
      timeoutMs: timeoutMs ?? null,
    };
    this.jobs.set(jobId, job);
    this.queue.push(job);
    this.emit('queued', { jobId, job });
    this.#drain();
    return jobId;
  }

  cancel(jobId, reason = 'Cancelled by user') {
    const job = this.jobs.get(jobId);
    if (!job) {
      return false;
    }
    if (job.status === 'queued') {
      this.queue = this.queue.filter((queued) => queued.id !== jobId);
      job.status = 'cancelled';
      job.statusMessage = reason;
      job.completedAt = Date.now();
      this.emit('cancelled', { jobId, job });
      return true;
    }
    const active = this.active.get(jobId);
    if (!active) {
      return false;
    }
    job.status = 'cancelling';
    job.statusMessage = reason;
    active.worker.postMessage({ type: 'cancel' });
    active.cancelRequested = true;
    if (active.timeoutHandle) {
      clearTimeout(active.timeoutHandle);
      active.timeoutHandle = null;
    }
    active.timeoutHandle = setTimeout(() => {
      if (this.active.has(jobId)) {
        active.worker.terminate();
      }
    }, DEFAULT_TERMINATE_TIMEOUT_MS).unref();
    this.emit('cancelling', { jobId, job });
    return true;
  }

  dispose() {
    for (const { worker } of this.active.values()) {
      worker.terminate();
    }
    this.queue = [];
    this.active.clear();
    this.jobs.clear();
  }

  #drain() {
    while (this.active.size < this.concurrency && this.queue.length > 0) {
      const job = this.queue.shift();
      if (!job) {
        break;
      }
      this.#spawn(job);
    }
  }

  #spawn(job) {
    const workerPath = this.workerRegistry.get(job.type);
    if (!workerPath) {
      throw new Error(`No worker registered for task type: ${job.type}`);
    }

    const worker = new Worker(workerPath, {
      workerData: {
        jobId: job.id,
        payload: job.payload,
        metadata: job.metadata,
        timeoutMs: job.timeoutMs,
      },
    });

    const activeRecord = {
      worker,
      startedAt: Date.now(),
      cancelRequested: false,
      timeoutHandle: null,
    };
    this.active.set(job.id, activeRecord);

    job.status = 'running';
    job.startedAt = activeRecord.startedAt;
    job.statusMessage = 'Running';
    this.emit('started', { jobId: job.id, job });

    if (job.timeoutMs) {
      activeRecord.timeoutHandle = setTimeout(() => {
        this.cancel(job.id, 'Timed out');
      }, job.timeoutMs).unref();
    }

    worker.on('message', (message) => {
      if (!message || typeof message !== 'object') {
        return;
      }
      const { type, data } = message;
      switch (type) {
        case 'progress': {
          const { progress = 0, statusMessage, meta } = data ?? {};
          job.progress = progress;
          if (statusMessage) {
            job.statusMessage = statusMessage;
          }
          if (meta) {
            job.meta = { ...(job.meta ?? {}), ...meta };
          }
          this.emit('progress', { jobId: job.id, job });
          break;
        }
        case 'log': {
          this.emit('log', { jobId: job.id, level: data?.level ?? 'info', message: data?.message, meta: data?.meta });
          break;
        }
        case 'result': {
          job.status = 'completed';
          job.progress = typeof data?.progress === 'number' ? data.progress : 1;
          job.statusMessage = data?.statusMessage ?? 'Completed';
          job.result = data?.result;
          job.completedAt = Date.now();
          this.#finalize(job.id);
          this.emit('completed', { jobId: job.id, job });
          break;
        }
        case 'error': {
          job.status = activeRecord.cancelRequested ? 'cancelled' : 'failed';
          job.statusMessage = data?.statusMessage ?? (activeRecord.cancelRequested ? 'Cancelled' : 'Failed');
          job.error = data?.error ?? null;
          job.completedAt = Date.now();
          this.#finalize(job.id);
          this.emit('failed', { jobId: job.id, job });
          break;
        }
        case 'cancelled': {
          job.status = 'cancelled';
          job.statusMessage = data?.statusMessage ?? 'Cancelled';
          job.completedAt = Date.now();
          this.#finalize(job.id);
          this.emit('cancelled', { jobId: job.id, job });
          break;
        }
        default:
          break;
      }
    });

    worker.on('error', (error) => {
      job.status = 'failed';
      job.statusMessage = error.message;
      job.error = { message: error.message, stack: error.stack };
      job.completedAt = Date.now();
      this.#finalize(job.id);
      this.emit('failed', { jobId: job.id, job });
    });

    worker.on('exit', (code) => {
      if (code !== 0 && job.status === 'running') {
        job.status = 'failed';
        job.statusMessage = `Worker exited with code ${code}`;
        job.error = { message: `Worker exited with code ${code}` };
        job.completedAt = Date.now();
        this.emit('failed', { jobId: job.id, job });
      }
      this.#finalize(job.id, { skipTerminate: true });
    });
  }

  #finalize(jobId, options = {}) {
    const activeRecord = this.active.get(jobId);
    if (activeRecord) {
      if (activeRecord.timeoutHandle) {
        clearTimeout(activeRecord.timeoutHandle);
      }
      this.active.delete(jobId);
    }
    if (!options.skipTerminate && activeRecord) {
      activeRecord.worker.terminate();
    }
    this.#drain();
  }
}

module.exports = {
  TaskManager,
};
