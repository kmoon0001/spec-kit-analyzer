const { app, BrowserWindow, ipcMain, shell, nativeTheme } = require('electron');
const path = require('node:path');
const { taskManager } = require('./tasks');

const isDev = process.env.ELECTRON_IS_DEV === '1' || !app.isPackaged;
const defaultApiBaseUrl = process.env.COMPLIANCE_API_URL || 'http://127.0.0.1:8100';

process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = 'true';

let mainWindow;

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

const safeSerialize = (value) => {
  if (value === undefined) {
    return undefined;
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    try {
      return String(value);
    } catch {
      return undefined;
    }
  }
};

const broadcastDiagnostic = (payload) => {
  const message = {
    timestamp: Date.now(),
    ...payload,
  };
  const windows = BrowserWindow.getAllWindows();
  windows.forEach((win) => {
    if (!win.isDestroyed()) {
      win.webContents.send(DIAGNOSTIC_CHANNEL, message);
    }
  });
};

const emitDiagnostic = ({ type, message, severity = 'error', stack, context }) => {
  const normalizedContext =
    context && typeof context === 'object' ? context : context === undefined ? undefined : { value: context };

  broadcastDiagnostic({
    type,
    message,
    severity,
    stack,
    source: 'main-process',
    context: normalizedContext,
  });
};

const broadcastTaskEvent = (channel, payload) => {
  const windows = BrowserWindow.getAllWindows();
  windows.forEach((win) => {
    if (!win.isDestroyed()) {
      win.webContents.send(channel, payload);
    }
  });
};

const registerDiagnosticHandlers = () => {
  process.on('uncaughtException', (error) => {
    console.error('[main][uncaughtException]', error);
    emitDiagnostic({
      type: 'uncaught-exception',
      message: error?.message ?? 'Uncaught exception',
      stack: error?.stack,
      context: {
        name: error?.name,
      },
    });
  });

  process.on('unhandledRejection', (reason) => {
    console.error('[main][unhandledRejection]', reason);
    const message =
      reason instanceof Error
        ? reason.message
        : typeof reason === 'string'
          ? reason
          : 'Unhandled promise rejection';
    const stack = reason instanceof Error ? reason.stack : undefined;

    emitDiagnostic({
      type: 'unhandled-rejection',
      message,
      stack,
      context: {
        reason: safeSerialize(reason),
      },
    });
  });

  app.on('child-process-gone', (_event, details) => {
    emitDiagnostic({
      type: 'child-process-gone',
      severity: 'critical',
      message: `Child process ${details?.type ?? 'unknown'} exited (${details?.reason ?? 'unknown'})`,
      context: details,
    });
  });
};

const setupTaskEventForwarding = () => {
  taskManager.on('queued', (event) => broadcastTaskEvent(TASK_EVENT_CHANNELS.queued, event));
  taskManager.on('started', (event) => broadcastTaskEvent(TASK_EVENT_CHANNELS.started, event));
  taskManager.on('progress', (event) => broadcastTaskEvent(TASK_EVENT_CHANNELS.progress, event));
  taskManager.on('completed', (event) => broadcastTaskEvent(TASK_EVENT_CHANNELS.completed, event));
  taskManager.on('failed', (event) => broadcastTaskEvent(TASK_EVENT_CHANNELS.failed, event));
  taskManager.on('cancelled', (event) => broadcastTaskEvent(TASK_EVENT_CHANNELS.cancelled, event));
  taskManager.on('log', (event) => broadcastTaskEvent(TASK_EVENT_CHANNELS.log, event));
  taskManager.on('telemetry', (payload) => broadcastTaskEvent(TASK_EVENT_CHANNELS.telemetry, payload));
};

const registerTaskIpcHandlers = () => {
  ipcMain.handle('tasks/start', (_event, request) => {
    const { type, payload, jobId, metadata: metadataFromRenderer, timeoutMs } = request ?? {};
    if (!type) {
      throw new Error('Task type is required');
    }
    const metadata = {
      apiBaseUrl: metadataFromRenderer?.apiBaseUrl ?? defaultApiBaseUrl,
      token: metadataFromRenderer?.token ?? null,
      pollIntervalMs: metadataFromRenderer?.pollIntervalMs ?? 1500,
      timeoutMs: metadataFromRenderer?.timeoutMs ?? timeoutMs ?? 15 * 60 * 1000,
      origin: 'renderer',
    };

    const jobIdCreated = taskManager.startTask({
      type,
      payload,
      jobId,
      metadata,
      timeoutMs: metadata.timeoutMs,
    });
    return { jobId: jobIdCreated };
  });

  ipcMain.handle('tasks/cancel', (_event, request) => {
    const { jobId, reason } = request ?? {};
    if (!jobId) {
      return { ok: false, error: 'jobId is required' };
    }
    const ok = taskManager.cancel(jobId, reason);
    return { ok };
  });

  ipcMain.handle('tasks/list', () => ({ jobs: taskManager.listJobs() }));
  ipcMain.handle('tasks/get', (_event, request) => {
    const { jobId } = request ?? {};
    if (!jobId) {
      return { job: null };
    }
    return { job: taskManager.getJob(jobId) };
  });
};

const createMainWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1280,
    minHeight: 768,
    show: false,
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#0f172a' : '#f8fafc',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      devTools: isDev,
    },
  });

  mainWindow.once('ready-to-show', () => mainWindow.show());

  const rendererUrl = process.env.ELECTRON_RENDERER_URL || 'http://localhost:3001';

  if (isDev) {
    mainWindow.loadURL(rendererUrl);
  } else {
    const indexFile = path.join(__dirname, '..', 'build', 'index.html');
    mainWindow.loadFile(indexFile);
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.webContents.on('render-process-gone', (_event, details) => {
    emitDiagnostic({
      type: 'renderer-process-gone',
      severity: 'critical',
      message: `Renderer process exited (${details?.reason ?? 'unknown'})`,
      context: details,
    });
  });

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL, isMainFrame) => {
    emitDiagnostic({
      type: 'renderer-load-failed',
      severity: 'warning',
      message: `Renderer failed to load (${errorCode}): ${errorDescription}`,
      context: {
        errorCode,
        errorDescription,
        validatedURL,
        isMainFrame,
      },
    });
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
};

const setupAppEvents = () => {
  const gotLock = app.requestSingleInstanceLock();
  if (!gotLock) {
    app.quit();
    return;
  }

  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore();
      }
      mainWindow.focus();
    }
  });

  app.on('ready', () => {
    createMainWindow();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('before-quit', () => {
    taskManager.dispose();
  });
};

const registerIpcHandlers = () => {
  ipcMain.handle('app/get-environment', () => ({
    isDev,
    apiBaseUrl: defaultApiBaseUrl,
  }));

  ipcMain.on('app/open-external', (_event, url) => {
    if (typeof url === 'string') {
      shell.openExternal(url);
    }
  });
};

registerDiagnosticHandlers();
setupTaskEventForwarding();
setupAppEvents();
registerIpcHandlers();
registerTaskIpcHandlers();
