const { EventEmitter } = require('node:events');
const { Worker } = require('node:worker_threads');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const perfHooks = require('node:perf_hooks');

const { performance } = perfHooks;
const monitorEventLoopDelay = typeof perfHooks.monitorEventLoopDelay === 'function' ? perfHooks.monitorEventLoopDelay : null;

const DEFAULT_TERMINATE_TIMEOUT_MS = 5_000;
const DEFAULT_TELEMETRY_INTERVAL_MS = 1_000;

class TaskManager extends EventEmitter {
  #telemetryTimer = null;
  #eventLoopDelayMonitor = null;
  #lastCpuUsage = null;
  #lastCpuTimestamp = null;
  #emittingTelemetry = false;
  #disposed = false;

  constructor(options = {}) {
    super();
    const cpuCount = os.cpus()?.length ?? 4;
    this.concurrency = Math.max(1, options.concurrency ?? Math.min(cpuCount - 1, 4));
    this.telemetryIntervalMs = Math.max(250, options.telemetryIntervalMs ?? DEFAULT_TELEMETRY_INTERVAL_MS);
    this.workerRegistry = new Map();
    this.jobs = new Map();
    this.queue = [];
    this.active = new Map();
    this.#initTelemetry();
  }

  #initTelemetry() {
    this.#lastCpuUsage = process.cpuUsage();
    this.#lastCpuTimestamp = performance.now();

    if (monitorEventLoopDelay) {
      try {
        this.#eventLoopDelayMonitor = monitorEventLoopDelay({ resolution: 20 });
        this.#eventLoopDelayMonitor.enable();
      } catch (error) {
        this.emit('log', {
          level: 'warn',
          message: 'Failed to initialize event loop delay monitor',
          meta: { error: error?.message },
        });
        this.#eventLoopDelayMonitor = null;
      }
    }

    this.#telemetryTimer = setInterval(() => {
      void this.#emitTelemetry();
    }, this.telemetryIntervalMs);

    if (typeof this.#telemetryTimer.unref === 'function') {
      this.#telemetryTimer.unref();
    }
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
      meta: job.meta,
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
      meta: null,
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
    }, DEFAULT_TERMINATE_TIMEOUT_MS);
    if (typeof active.timeoutHandle.unref === 'function') {
      active.timeoutHandle.unref();
    }
    this.emit('cancelling', { jobId, job });
    return true;
  }

  dispose() {
    this.#disposed = true;
    if (this.#telemetryTimer) {
      clearInterval(this.#telemetryTimer);
      this.#telemetryTimer = null;
    }
    if (this.#eventLoopDelayMonitor) {
      try {
        this.#eventLoopDelayMonitor.disable();
      } catch (error) {
        this.emit('log', {
          level: 'debug',
          message: 'Failed to disable event loop monitor',
          meta: { error: error?.message },
        });
      }
      this.#eventLoopDelayMonitor = null;
    }
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
      eventLoopUtilization: worker?.performance?.eventLoopUtilization
        ? worker.performance.eventLoopUtilization()
        : null,
    };
    this.active.set(job.id, activeRecord);

    job.status = 'running';
    job.startedAt = activeRecord.startedAt;
    job.statusMessage = 'Running';
    this.emit('started', { jobId: job.id, job });

    if (job.timeoutMs) {
      activeRecord.timeoutHandle = setTimeout(() => {
        this.cancel(job.id, 'Timed out');
      }, job.timeoutMs);
      if (typeof activeRecord.timeoutHandle.unref === 'function') {
        activeRecord.timeoutHandle.unref();
      }
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

  async #emitTelemetry() {
    if (this.#emittingTelemetry || this.#disposed) {
      return;
    }

    this.#emittingTelemetry = true;
    try {
      const now = performance.now();
      const cpuUsage = process.cpuUsage();
      const prevUsage = this.#lastCpuUsage;
      const prevTimestamp = this.#lastCpuTimestamp;
      const cpuDiffUser = prevUsage ? cpuUsage.user - prevUsage.user : 0;
      const cpuDiffSystem = prevUsage ? cpuUsage.system - prevUsage.system : 0;
      const elapsedMs = prevTimestamp ? Math.max(now - prevTimestamp, 1) : this.telemetryIntervalMs;
      const totalCpuMs = (cpuDiffUser + cpuDiffSystem) / 1_000;
      const cores = os.cpus()?.length ?? 1;
      const cpuPercent = elapsedMs > 0 ? Math.min(cores * 100, (totalCpuMs / elapsedMs) * 100) : 0;
      const normalizedCpuPercent = cores > 0 ? cpuPercent / cores : cpuPercent;

      this.#lastCpuUsage = cpuUsage;
      this.#lastCpuTimestamp = now;

      const memoryUsage = process.memoryUsage();
      let processMemoryInfo = null;
      if (typeof process.getProcessMemoryInfo === 'function') {
        try {
          processMemoryInfo = await process.getProcessMemoryInfo();
        } catch (error) {
          this.emit('log', {
            level: 'debug',
            message: 'getProcessMemoryInfo failed',
            meta: { error: error?.message },
          });
        }
      }

      let eventLoopMetrics = null;
      if (this.#eventLoopDelayMonitor) {
        const histogram = this.#eventLoopDelayMonitor;
        eventLoopMetrics = {
          mean: histogram.mean / 1e6,
          max: histogram.max / 1e6,
          min: histogram.min / 1e6,
          stddev: histogram.stddev / 1e6,
          p50: histogram.percentile(50) / 1e6,
          p90: histogram.percentile(90) / 1e6,
          p99: histogram.percentile(99) / 1e6,
        };
        histogram.reset();
      }

      const workers = [];
      for (const [jobId, record] of this.active.entries()) {
        const job = this.jobs.get(jobId);
        let workerEventLoopUtilization = null;
        if (record.worker?.performance?.eventLoopUtilization) {
          try {
            const metrics = record.worker.performance.eventLoopUtilization(record.eventLoopUtilization ?? undefined);
            record.eventLoopUtilization = metrics;
            workerEventLoopUtilization = metrics?.utilization ?? null;
          } catch (error) {
            this.emit('log', {
              level: 'debug',
              message: 'Failed to read worker eventLoopUtilization',
              meta: { jobId, error: error?.message },
            });
          }
        }
        workers.push({
          jobId,
          threadId: record.worker?.threadId ?? null,
          type: job?.type ?? 'unknown',
          status: job?.status ?? 'unknown',
          progress: job?.progress ?? 0,
          runtimeMs: job?.startedAt ? Date.now() - job.startedAt : 0,
          eventLoopUtilization: workerEventLoopUtilization,
        });
      }

      const payload = {
        timestamp: Date.now(),
        queueSize: this.queue.length,
        activeCount: this.active.size,
        concurrency: this.concurrency,
        cpu: {
          percent: Number(cpuPercent.toFixed(2)),
          normalizedPercent: Number(normalizedCpuPercent.toFixed(2)),
          user: cpuUsage.user,
          system: cpuUsage.system,
          totalMs: totalCpuMs,
          elapsedMs,
          cores,
        },
        memory: {
          rss: memoryUsage.rss,
          heapTotal: memoryUsage.heapTotal,
          heapUsed: memoryUsage.heapUsed,
          external: memoryUsage.external,
          arrayBuffers: memoryUsage.arrayBuffers,
          details: processMemoryInfo,
        },
        eventLoop: eventLoopMetrics,
        system: {
          loadavg: typeof os.loadavg === 'function' ? os.loadavg() : [],
          totalMem: typeof os.totalmem === 'function' ? os.totalmem() : null,
          freeMem: typeof os.freemem === 'function' ? os.freemem() : null,
          uptime: typeof os.uptime === 'function' ? os.uptime() : null,
        },
        workers,
        jobs: this.listJobs(),
      };

      this.emit('telemetry', payload);
    } finally {
      this.#emittingTelemetry = false;
    }
  }
}

module.exports = {
  TaskManager,
};
