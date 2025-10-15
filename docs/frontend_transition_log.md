## 2025-10-15T19:45Z - Runtime Resilience & Diagnostics
- Added centralized axios retry/backoff pipeline with a network diagnostics store feeding the status bar.
- Parsed structured WebSocket logs, exposing level-aware messages and a clearable console in Mission Control.
- Hardened analysis worker polling with adaptive timeouts, retry telemetry, and cancellation-safe request signals.
- Registered global error/rejection traps and surfaced alert counts in the renderer to expose silent failures during heavy runs.

## 2025-10-15T16:10Z - Connectivity Hardening
- Unified FastAPI log streaming with authenticated WebSocket routing and broadened CORS support for Electron runtimes (localhost + app://).
- Patched analysis task scheduling to respect strictness, enforce upload validation, and run via the shared async registry.
- Normalized desktop/runtime API base URL negotiation so axios and workers follow the Electron main-process port.
- Added reusable exponential backoff helpers powering mission-control log streams and Node workers to avoid retry storms during outages.

## 2025-10-15T12:45Z - Resource Telemetry & Stress Harness
- Instrumented the Electron task manager with periodic CPU/memory/event loop telemetry and forwarded snapshots to renderer IPC.
- Added desktop telemetry hook + UI card to surface live worker health in Analysis Mission Control.
- Created worker-pool stress harness exercising cancellations, timeouts, and concurrency with the mock heavy worker.

## 2025-10-15T09:18Z - Desktop Task Orchestration
- Added worker-thread task manager with IPC wiring to offload analysis uploads/polling from the renderer.
- Exposed desktop task API via preload bridge for progress, cancellation, and error propagation.
- Refreshed analysis UI for responsive layout, live progress bars, and dark-mode safe styling while keeping PySide parity.

## 2025-10-14T18:24Z - Scaffold Upgrade
- Replaced CRA starter with TypeScript-ready structure and modular layout scaffolding.
- Introduced Electron secure main/preload processes and npm scripts.
- Added query/state infrastructure, theme tokens, and placeholder routes for PySide parity.

## 2025-10-14T18:45Z - Layout Parity Scaffolding
- Implemented mission-control layout, calibrated cards, and PySide-equivalent tabs in React.
- Added reusable UI primitives (Card, Button, StatusChip) with clinical theme tokens.
- Replicated status strips, metrics, and placeholders for analysis, dashboard, settings, and mission control.

## 2025-10-14T19:05Z - Analysis Workflow Port
- Added React Query workflow for uploading documents, polling /analysis/status, and rendering compliance summaries.
- Wired rubric dropdown to FastAPI /rubrics endpoint and mirrored strictness controls.
- Implemented progress, findings preview, and report viewer parity with PySide handlers.
