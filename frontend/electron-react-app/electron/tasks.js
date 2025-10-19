// Task Manager for Electron
// Handles background tasks and API communication

const { EventEmitter } = require('events');
const axios = require('axios');

class TaskManager extends EventEmitter {
  constructor() {
    super();
    this.jobs = new Map();
    this.nextJobId = 1;
  }

  startTask({ type, payload, jobId, metadata, timeoutMs = 900000 }) {
    const id = jobId || `job-${this.nextJobId++}`;

    const job = {
      id,
      type,
      payload,
      metadata,
      status: 'queued',
      createdAt: Date.now(),
      timeoutMs,
    };

    this.jobs.set(id, job);
    this.emit('queued', { jobId: id, type, timestamp: Date.now() });

    // Start the task asynchronously
    this._executeTask(job);

    return id;
  }

  async _executeTask(job) {
    try {
      job.status = 'started';
      this.emit('started', { jobId: job.id, timestamp: Date.now() });

      const apiUrl = job.metadata?.apiBaseUrl || 'http://127.0.0.1:8001';
      const token = job.metadata?.token;

      // Make API call based on task type
      let endpoint = '/analysis/upload';
      if (job.type === 'analysis') {
        endpoint = '/analysis/upload';
      }

      const response = await axios.post(
        `${apiUrl}${endpoint}`,
        job.payload,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          timeout: job.timeoutMs,
        }
      );

      job.status = 'completed';
      job.result = response.data;
      this.emit('completed', {
        jobId: job.id,
        result: response.data,
        timestamp: Date.now()
      });

    } catch (error) {
      job.status = 'failed';
      job.error = error.message;
      this.emit('failed', {
        jobId: job.id,
        error: error.message,
        timestamp: Date.now()
      });
    }
  }

  cancel(jobId, reason = 'User cancelled') {
    const job = this.jobs.get(jobId);
    if (!job) return false;

    job.status = 'cancelled';
    job.cancelReason = reason;
    this.emit('cancelled', { jobId, reason, timestamp: Date.now() });
    return true;
  }

  getJob(jobId) {
    return this.jobs.get(jobId) || null;
  }

  listJobs() {
    return Array.from(this.jobs.values());
  }

  dispose() {
    this.jobs.clear();
    this.removeAllListeners();
  }
}

const taskManager = new TaskManager();

module.exports = { taskManager };
