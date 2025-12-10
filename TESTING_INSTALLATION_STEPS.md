# Testing & Coverage Installation Guide

These steps install the dependencies needed to run the backend test suite and measure coverage locally. Commands assume Python 3.12 and a clean virtual environment.

## 1) Prepare a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
```

## 2) Install Required Dependencies
The core suite relies on FastAPI/Starlette, HTTPX, and Pydantic. Install everything with:
```bash
python -m pip install -r requirements.txt
python -m pip install "fastapi>=0.110" "starlette>=0.37" "httpx>=0.27" "pydantic-settings>=2.2"
```
If PDF export tests are needed, add optional extras:
```bash
python -m pip install "reportlab>=4" "pypdf2>=3"
```

## 3) Run the Full Coverage Suite
```bash
pytest --cov=src --cov-report=term-missing
```
This command runs every unit test, prints missing-line details, and writes coverage data to `.coverage`.

## 4) Safe Subset When Dependencies Are Limited
If network access blocks installs, you can still run the pure-Python tests that avoid external services:
```bash
pytest --noconftest \
  tests/unit/test_utils_portable.py \
  tests/unit/test_logging_and_prompts.py \
  tests/unit/test_config_validator_rules.py \
  tests/unit/test_mock_api_offline.py \
  tests/unit/test_type_safety_result.py
```
These exercise text utilities, logging setup, config validation, offline mock API flows, and the type-safety helpers without requiring FastAPI or database drivers.

## 5) Troubleshooting
- **Import errors for FastAPI/Starlette/HTTPX**: Re-run the installation commands in Step 2 inside the active virtual environment.
- **Coverage below target**: Enable missing plugins (e.g., `pytest-asyncio`) by installing `pip install pytest-asyncio` after Step 2 and re-run coverage.
- **Slow installs behind a proxy**: Set `HTTPS_PROXY`/`HTTP_PROXY` environment variables before running pip.
- **`nvidia-cufile-cu12` not found on Windows**: Install the CPU-only PyTorch wheels before the rest of the requirements to avoid unavailable CUDA dependencies:
  ```powershell
  python -m pip install --upgrade pip
  python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.8.0+cpu"
  python -m pip install -r requirements.txt
  ```
  The CPU wheels satisfy the `torch` requirement without pulling the missing `nvidia-cufile-cu12` package.
