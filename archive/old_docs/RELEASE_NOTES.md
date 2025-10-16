## Release Notes

Date: 2025-10-13

Highlights:
- API and GUI stabilized; all tests and smoke checks pass.
- Authentication fixed and hardened; `/auth/token` works end-to-end.
- Rubrics API completed; seeded 3 initial entries for validation.
- File upload and analysis submit operational; task status polling reaches `completed`.
- Dev-only `/auth/dev-token` removed before release.
- Database initialization added at API startup to ensure tables exist.
- Optional dependencies made robust (FAISS, sentence-transformers, torch) with graceful fallbacks.
- Logging, WebSocket logs, and health checks verified.

Operational Notes:
- Ensure only one API instance on port 8001 to avoid bind conflicts.
- Use `scripts/dev_api_smoke.ps1` for quick end-to-end verification.
- Mocks disabled in `config.yaml` (`use_ai_mocks: false`).

Files Touched (selection):
- `src/api/main.py`: init DB on startup; router wiring; logs endpoint.
- `src/api/routers/auth.py`: hardened; removed dev token.
- `src/api/routers/rubric_router.py`: completed CRUD.
- `config.yaml`: `use_ai_mocks: false`.
- `scripts/dev_api_smoke.ps1`, `temp/dev_api_smoke.py`: smoke tests.
- `scripts/seed_rubrics.py`: seed sample rubrics.

Status: Ready for integration and manual QA.
