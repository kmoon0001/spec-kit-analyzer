# Repository Guidelines

## Project Structure & Module Organization
- `src/api` exposes FastAPI routers (analysis, preferences, health, admin) that the Electron frontend consumes. Core services live under `src/core`, while data access logic is in `src/database`.
- `frontend/electron-react-app` hosts the TypeScript React renderer and Electron shell. Feature folders (`features/analysis`, `features/settings`, etc.) mirror the PySide workflows for parity.
- `docs/` contains transition plans, API contracts, and operational runbooks. Use `docs/frontend_transition_log.md` to track parity milestones as we retire the PySide UI.
- Legacy PySide assets remain in `src/gui` until parity is confirmed; avoid modifying them unless you are fixing a regression.

## Build, Test, and Development Commands
- Backend: `poetry run uvicorn src.api.main:app --reload` (or `python start_api.py`) starts the FastAPI service. Run targeted tests with `pytest tests/test_api_analysis.py -k analyze`.
- Frontend: from `frontend/electron-react-app`, use `npm run start:electron` for local development and `npm run build` to produce the production bundle.
- Lint/format: `npm run lint` (frontend) and `ruff check .` / `ruff format .` (backend) keep the codebase consistent.

## Coding Style & Naming Conventions
- Prefer feature-based folders in React (`features/<domain>/components|hooks|api`). Write stateful logic in hooks and presentational logic in components.
- Backend modules follow snake_case file names and Pydantic/SQLAlchemy models live in `schemas.py` and `models.py`. Keep functions small, typed, and side-effect aware.
- Use descriptive names for React query keys and Zustand slices so client caching stays predictable.

## Testing Guidelines
- Extend `tests/test_api_analysis.py` when wiring new FastAPI routes, mirroring the request/response payloads used by Electron.
- For React, add lightweight RTL tests under `frontend/electron-react-app/src/**/__tests__` and integration flows once Playwright harnesses are in place.
- Validate WebSocket flows by scripting manual sessions (`useLogStream` relies on auth tokens and exponential backoff—capture that behaviour in docs/tests as it evolves).

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`) so changelog automation remains accurate. Include scope when touching both backend and frontend (e.g., `feat(frontend):`).
- PRs should link work-items, describe backend/frontend touchpoints, and note any follow-up TODOs left in code. Attach screenshots or recordings when UI changes are user visible.
- Before requesting review, run the relevant test suites and ensure docs (`docs/frontend_transition_plan.md`) reflect any parity or deprecation updates.
