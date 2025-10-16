#!/usr/bin/env node
const os = require('node:os');
const { setTimeout: delay } = require('node:timers/promises');
const { createTaskManager } = require('./index');

const DEFAULTS = {
  jobs: 12,
  concurrency: Math.max(1, (os.cpus()?.length ?? 4) - 1),
  durationMs: 5_000,
  steps: 25,
  cancelRate: 5,
  timeoutRate: 4,
  telemetryIntervalMs: 750,
};

const parseArgs = () => {
  const options = { ...DEFAULTS };
  for (const arg of process.argv.slice(2)) {
    if (!arg.startsWith('--')) {
      continue;
    }
    const [rawKey, rawValue] = arg.slice(2).split('=');
    const value = rawValue ?? '';
    const key = rawKey.trim();
    switch (key) {
      case 'jobs':
        options.jobs = Number(value) > 0 ? Number(value) : options.jobs;
        break;
      case 'concurrency':
        options.concurrency = Number(value) > 0 ? Number(value) : options.concurrency;
        break;
      case 'duration':
      case 'durationMs':
        options.durationMs = Number(value) > 0 ? Number(value) : options.durationMs;
        break;
      case 'steps':
        options.steps = Number(value) > 0 ? Number(value) : options.steps;
        break;
      case 'cancelRate':
      case 'cancel-rate':
        options.cancelRate = Number(value) >= 0 ? Number(value) : options.cancelRate;
        break;
      case 'timeoutRate':
      case 'timeout-rate':
        options.timeoutRate = Number(value) >= 0 ? Number(value) : options.timeoutRate;
        break;
      case 'telemetry':
      case 'telemetryIntervalMs':
        options.telemetryIntervalMs = Number(value) >= 250 ? Number(value) : options.telemetryIntervalMs;
        break;
      default:
        break;
    }
  }
  return options;
};

const formatPercent = (value) => `${value.toFixed(1)}%`;

const buildJobPlan = (index, options) => {
  const jitter = Math.max(250, Math.round(options.durationMs * 0.35));
  const durationMs = Math.max(750, options.durationMs + Math.round(Math.random() * jitter - jitter / 2));
  const steps = Math.max(10, options.steps + Math.round(Math.random() * 6 - 3));
  const plan = {
    index,
    durationMs,
    steps,
    timeoutMs: null,
    cancelAfterMs: null,
    expect: 'complete',
  };

  if (options.timeoutRate > 0 && (index + 1) % options.timeoutRate === 0) {
    plan.timeoutMs = Math.max(500, Math.round(durationMs * 0.6));
    plan.expect = 'timeout';
  } else if (options.cancelRate > 0 && (index + 1) % options.cancelRate === 0) {
    plan.cancelAfterMs = Math.max(400, Math.round(durationMs * 0.4));
    plan.expect = 'cancel';
  }

  return plan;
};

const run = async () => {
  const options = parseArgs();
  const manager = createTaskManager({ concurrency: options.concurrency, telemetryIntervalMs: options.telemetryIntervalMs });
  const jobRecords = new Map();
  const jobPromises = [];
  const stats = {
    completed: 0,
    failed: 0,
    cancelled: 0,
    timedOut: 0,
    mismatched: 0,
    started: 0,
  };
  let lastTelemetry = null;

  manager.on('telemetry', (snapshot) => {
    lastTelemetry = snapshot;
  });

  const resolveJob = (jobId, outcome) => {
    const record = jobRecords.get(jobId);
    if (!record) {
      return;
    }
    record.outcome = outcome;
    record.resolve();
  };

  manager.on('started', ({ jobId }) => {
    const record = jobRecords.get(jobId);
    if (record) {
      record.startedAt = Date.now();
      stats.started += 1;
    }
  });

  manager.on('completed', ({ jobId, job }) => {
    stats.completed += 1;
    const record = jobRecords.get(jobId);
    if (record && record.plan.expect !== 'complete') {
      stats.mismatched += 1;
    }
    resolveJob(jobId, { status: 'completed', job });
  });

  manager.on('failed', ({ jobId, job }) => {
    stats.failed += 1;
    const record = jobRecords.get(jobId);
    if (record && record.plan.expect === 'timeout' && typeof job?.statusMessage === 'string' && job.statusMessage.toLowerCase().includes('timed')) {
      stats.timedOut += 1;
    } else if (record && record.plan.expect !== 'complete') {
      stats.mismatched += 1;
    }
    resolveJob(jobId, { status: 'failed', job });
  });

  manager.on('cancelled', ({ jobId, job }) => {
    stats.cancelled += 1;
    const record = jobRecords.get(jobId);
    if (record?.plan.expect === 'timeout' && typeof job?.statusMessage === 'string' && job.statusMessage.toLowerCase().includes('timed')) {
      stats.timedOut += 1;
    } else if (record?.plan.expect !== 'cancel') {
      stats.mismatched += 1;
    }
    resolveJob(jobId, { status: 'cancelled', job });
  });

  const jobs = Array.from({ length: options.jobs }, (_value, index) => buildJobPlan(index, options));

  console.log(`
[stress] launching ${jobs.length} jobs (concurrency=${options.concurrency})`);

  for (const plan of jobs) {
    const record = {
      plan,
      createdAt: Date.now(),
      startedAt: null,
      outcome: null,
      resolve: () => {},
    };

    const completionPromise = new Promise((resolve) => {
      record.resolve = resolve;
    });

    jobPromises.push(completionPromise);

    const jobId = manager.startTask({
      type: 'mock',
      payload: { durationMs: plan.durationMs, steps: plan.steps },
      metadata: { origin: 'stress-harness', expected: plan.expect },
      timeoutMs: plan.timeoutMs ?? undefined,
    });

    jobRecords.set(jobId, record);

    if (plan.cancelAfterMs !== null) {
      setTimeout(() => {
        manager.cancel(jobId, 'Harness cancellation');
      }, plan.cancelAfterMs).unref();
    }

    await delay(50);
  }

  const telemetryLog = setInterval(() => {
    if (!lastTelemetry) {
      return;
    }
    const cpu = formatPercent(lastTelemetry.cpu.normalizedPercent ?? lastTelemetry.cpu.percent ?? 0);
    const rssMb = Math.round((lastTelemetry.memory.rss ?? 0) / 1024 / 1024);
    console.log(
      `[telemetry] active=${lastTelemetry.activeCount}/${lastTelemetry.concurrency} queued=${lastTelemetry.queueSize} cpu=${cpu} rss=${rssMb}MB loop-p99=${lastTelemetry.eventLoop ? lastTelemetry.eventLoop.p99.toFixed(1) : 'n/a'}ms`,
    );
  }, 2_000);
  telemetryLog.unref();

  await Promise.all(jobPromises);

  clearInterval(telemetryLog);
  manager.dispose();

  console.log('
[stress] results');
  console.table([
    { metric: 'completed', value: stats.completed },
    { metric: 'cancelled', value: stats.cancelled },
    { metric: 'timedOut', value: stats.timedOut },
    { metric: 'failed', value: stats.failed },
    { metric: 'mismatched expectations', value: stats.mismatched },
  ]);

  if (stats.mismatched > 0 || stats.failed > stats.timedOut) {
    console.warn('[stress] mismatches detected. Investigate worker handling.');
    process.exitCode = 1;
  }
};

if (require.main === module) {
  run().catch((error) => {
    console.error('[stress] harness crashed', error);
    process.exitCode = 1;
  });
}
