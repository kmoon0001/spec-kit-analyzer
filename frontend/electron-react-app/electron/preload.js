const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desktopApi', {
  getEnvironment: () => ipcRenderer.invoke('app/get-environment'),
  openExternal: (url) => ipcRenderer.send('app/open-external', url),
  platform: process.platform,
});
