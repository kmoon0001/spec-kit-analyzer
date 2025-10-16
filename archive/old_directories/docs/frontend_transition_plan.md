# Frontend Transition Plan

## PySide Feature Inventory
- Main shell: header, status bar, theme toggle, progress overlay (src\\gui\\main_window.py).
- Analysis tab: document upload/drag-drop, rubric selector, strictness presets, compliance toggles, report preview, chat integration (src\\gui\\components\\analysis_tab_builder.py).
- Dashboard tab: compliance metrics, refresh triggers (src\\gui\\components\\tab_builder.py).
- Mission Control: quick actions, document review workflow, log viewer (src\\gui\\widgets\\mission_control_widget.py).
- Settings: user preferences, analysis/report/performance toggles, admin settings editor with live system stats (src\\gui\\components\\settings_tab_builder.py).
- ViewModel: async workers for health checks, tasks, log streaming, rubrics, dashboard, meta analytics; orchestrates analysis lifecycle and updates UI state (src\\gui\\view_models\\main_view_model.py).
- Analysis handlers: start/repeat/stop flows, local worker threads, progress updates, report summary, dashboard updates (src\\gui\\handlers\\analysis_handlers.py).
- File handlers: selection, drag-drop, preview caching (see src\\gui\\handlers\\file_handlers.py).
- UI handlers: theme toggles, dialogs, mission control interactions (src\\gui\\handlers\\ui_handlers.py).
- Background workers: API polling, WebSocket logs, analysis execution (src\\gui\\workers).

## React/Electron Parity Goals
- Replicate tabbed layout with Header, StatusBar, left nav, mission control actions, status widgets.
- Provide drag-and-drop uploads, rubric dropdown, strictness presets, and start/stop analysis controls with real-time progress.
- Embed compliance summary, findings table, and interactive report viewer comparable to existing QTextBrowser outputs.
- Mirror dashboard analytics (scores, charts) and mission control widgets (task list, log stream, quick actions).
- Port settings editor with live system metrics (psutil-backed endpoint) and admin configuration editing.
- Maintain authentication flow, task tracking, WebSocket log streaming, and rubric/dashboard/meta-analytics loading.

## Transition Strategy
1. Harden Electron shell; add secure preload bridging and environment-aware loading.
2. Reboot React app with feature-driven structure, routing, state/query layers, shared design tokens (medical theme).
3. Implement shell layout (header/status/tabs) and stub screens mirroring PySide tabs.
4. Port Analysis workflow end-to-end (upload -> API -> results) with optimistic task updates.
5. Layer dashboard, mission control, settings, and log/task integrations; reuse backend endpoints.
6. Add frontend tests (RTL + Playwright) and align CI. Provide docs and scripts; mark PySide frontend as legacy once parity confirmed.

## Legacy PySide Frontend Decommissioning

- Maintain both frontends until the Electron workflow covers upload, rubric selection, strictness presets, report viewing, settings, and mission-control status parity.
- Track parity gaps in docs/frontend_transition_log.md and mirror resolved items in integration tests.
- Preserve PySide automation scripts for reference while redirecting new development toward the Electron bundle and FastAPI APIs.
- Coordinate with QA before removing PySide-specific database fixtures or GUI helpers.
- TODO: Confirm stakeholders sign off on feature parity, then archive the src/gui directory into docs/archive/ before deletion.
