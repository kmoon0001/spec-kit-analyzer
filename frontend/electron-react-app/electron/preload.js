const { contextBridge, ipcRenderer } = require('electron');

const TASK_EVENT_CHANNELS = {
  queued: 'tasks:queued',
  started: 'tasks:started',
  progress: 'tasks:progress',
  completed: 'tasks:completed',
  failed: 'tasks:failed',
  cancelled: 'tasks:cancelled',
  log: 'tasks:log',
  telemetry: 'tasks:telemetry',
};

const DIAGNOSTIC_CHANNEL = 'app:diagnostic';

const buildTaskEventHandler = (eventName, listener) => {
  const channel = TASK_EVENT_CHANNELS[eventName];
  if (!channel) {
    throw new Error(`Unsupported task event: ${eventName}`);
  }
  const handler = (_event, payload) => {
    listener(payload);
  };
  ipcRenderer.on(channel, handler);
  return () => {
    ipcRenderer.removeListener(channel, handler);
  };
};

const tasksApi = {
  startTask: (request) => ipcRenderer.invoke('tasks/start', request),
  startAnalysis: (payload, options = {}) =>
    ipcRenderer.invoke('tasks/start', {
      type: 'analysis',
      payload,
      metadata: options.metadata,
      timeoutMs: options.timeoutMs,
      jobId: options.jobId,
    }),
  cancel: (jobId, reason) => ipcRenderer.invoke('tasks/cancel', { jobId, reason }),
  list: () => ipcRenderer.invoke('tasks/list'),
  get: (jobId) => ipcRenderer.invoke('tasks/get', { jobId }),
  on: (eventName, listener) => buildTaskEventHandler(eventName, listener),
};

const secureStorageApi = {
  setSecureValue: (key, value) => ipcRenderer.invoke('secure-storage/set', key, value),
  getSecureValue: (key) => ipcRenderer.invoke('secure-storage/get', key),
  removeSecureValue: (key) => ipcRenderer.invoke('secure-storage/remove', key),
  clearSecureStorage: () => ipcRenderer.invoke('secure-storage/clear'),
};

contextBridge.exposeInMainWorld('desktopApi', {
  getEnvironment: () => ipcRenderer.invoke('app/get-environment'),
  openExternal: (url) => ipcRenderer.send('app/open-external', url),
  platform: process.platform,
  tasks: tasksApi,
  secureStorage: secureStorageApi,
  onDiagnostic: (listener) => {
    if (typeof listener !== 'function') {
      return () => {};
    }
    const handler = (_event, payload) => {
      listener(payload);
    };
    ipcRenderer.on(DIAGNOSTIC_CHANNEL, handler);
    return () => {
      ipcRenderer.removeListener(DIAGNOSTIC_CHANNEL, handler);
    };
  },
});
