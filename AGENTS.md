# Repository Guidelines

## Project Structure & Module Organization
- `src/api` hosts FastAPI routers, dependency injection, and scheduled jobs for maintenance.
- `src/core` and `src/utils` implement document analysis, classifiers, and cross-cutting helpers shared by API and GUI.
- `src/gui` contains PyQt6 widgets while `src/resources` stores prompts and assets; sample artifacts for manual checks live in `data/`.
- Automated tests sit in `tests/` (`unit`, `integration`, `gui`, `_gui`, `_stability`) with reusable fixtures under `tests/test_data/`.

## Build, Test, and Development Commands
- `python -m venv venv && venv\Scripts\activate; pip install -r requirements.txt` prepares a clean environment with dependencies.
- `python run_api.py` runs the FastAPI backend; use `uvicorn src.api.main:app --reload` for hot-reload development.
- `python run_gui.py` boots the desktop shell against the local API instance.
- `pytest` executes the suite; narrow scope with `pytest tests/unit -m "not slow"` when iterating.
- `ruff check src tests` and `mypy src` must pass before you push.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indents, snake_case for functions, PascalCase for classes, UPPER_SNAKE for constants.
- Add type hints on new public functions and lean on `schemas.py` for shared DTOs.
- Place new FastAPI routes inside `src/api/routers` and GUI widgets inside `src/gui`; keep modules focused and injectable.
- Run `ruff` locally and accept its auto-fixes to avoid manual formatting drift.

## Testing Guidelines
- Reuse fixtures from `tests/conftest.py` and mirror production modules with matching tests (e.g., `src/core/foo.py` -> `tests/unit/core/test_foo.py`).
- Mark long-running suites with `@pytest.mark.slow` or `@pytest.mark.stability` so CI filters stay fast.
- GUI changes need `pytest-qt` assertions in `tests/gui` plus screenshots shared in the PR description, not the repo.
- Keep fixtures deterministic and refresh rubric samples in `tests/test_data/` whenever schemas change.

## Commit & Pull Request Guidelines
- Prefer Conventional Commit prefixes (`feat:`, `fix:`, `refactor:`) in imperative mood; keep subjects <=72 characters.
- Reference related issues with `Refs #123` and avoid bundling unrelated fixes.
- PRs should include a brief summary, verification notes (e.g., `Tests: pytest`), and UI evidence when visual output shifts.
- Document new configuration flags in `README.md` or inline `config.yaml` comments before requesting review.

## Configuration & Security Tips
- Store secrets in a local `.env`; never commit generated databases or patient-identifiable content.
- Mirror `config.yaml` adjustments in `src/config.py` defaults and flag migration implications early in the PR.
