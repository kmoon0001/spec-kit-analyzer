## 2025-10-14T18:24Z - Scaffold Upgrade
- Replaced CRA starter with TypeScript-ready structure and modular layout scaffolding.
- Introduced Electron secure main/preload processes and npm scripts.
- Added query/state infrastructure, theme tokens, and placeholder routes for PySide parity.
\n## 2025-10-14T18:45Z - Layout Parity Scaffolding
- Implemented mission-control layout, calibrated cards, and PySide-equivalent tabs in React.
- Added reusable UI primitives (Card, Button, StatusChip) with clinical theme tokens.
- Replicated status strips, metrics, and placeholders for analysis, dashboard, settings, and mission control.
## 2025-10-14T19:05Z - Analysis Workflow Port
- Added React Query workflow for uploading documents, polling /analysis/status, and rendering compliance summaries.
- Wired rubric dropdown to FastAPI /rubrics endpoint and mirrored strictness controls.
- Implemented progress, findings preview, and report viewer parity with PySide handlers.
