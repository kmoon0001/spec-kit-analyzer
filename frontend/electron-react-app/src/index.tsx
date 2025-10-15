import React from 'react';
import ReactDOM from 'react-dom/client';

import { App } from './app/App';
import { AppProviders } from './app/providers/AppProviders';
import { initializeDesktopDiagnosticsBridge } from './lib/monitoring/desktopDiagnostics';
import { initializeGlobalErrorHandlers } from './lib/monitoring/globalErrors';

initializeGlobalErrorHandlers();
initializeDesktopDiagnosticsBridge();

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element missing');
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </React.StrictMode>,
);
