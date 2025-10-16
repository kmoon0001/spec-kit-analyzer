const { parentPort, workerData } = require('node:worker_threads');

const post = (type, data) => parentPort.postMessage({ type, data });

const durationMs = workerData?.payload?.durationMs ?? 5_000;
const steps = workerData?.payload?.steps ?? 20;
let cancelled = false;

parentPort.on('message', (message) => {
  if (message?.type === 'cancel') {
    cancelled = true;
    post('cancelled', { statusMessage: 'Mock task cancelled' });
  }
});

(async () => {
  try {
    for (let i = 1; i <= steps; i += 1) {
      if (cancelled) {
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, durationMs / steps));
      post('progress', {
        progress: Math.round((i / steps) * 100),
        statusMessage: `Mock heavy work step ${i}/${steps}`,
      });
    }
    post('result', {
      progress: 100,
      statusMessage: 'Mock task completed',
      result: { message: 'Mock heavy task finished', startedAt: Date.now() - durationMs },
    });
  } catch (error) {
    post('error', {
      statusMessage: error?.message ?? 'Mock worker failed',
      error: { message: error?.message ?? 'Unknown error', stack: error?.stack },
    });
  }
})();
