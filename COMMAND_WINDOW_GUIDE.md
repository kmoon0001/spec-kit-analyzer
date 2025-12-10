# Command window guidance

Use a standard terminal window so project scripts and virtual environments behave consistently across platforms:

- **Linux/macOS:** use your default Terminal app (bash/zsh). From the repo root, run `source venv_test/bin/activate` (or your preferred venv) before commands like `pytest` or `python start_backend.py`.
- **Windows:** use **PowerShell** (recommended) or **Command Prompt**. Activate the venv with `./venv_test/Scripts/Activate.ps1` (PowerShell) or `venv_test\\Scripts\\activate.bat` (cmd) from the project root before running scripts.
- Always run commands from the repository root so relative paths match examples in `README.md`, `TESTING_INSTALLATION_STEPS.md`, and other guides.
- If using an IDE terminal, ensure it opens in the repo root and respects the active virtual environment for consistent dependency resolution and coverage measurement.

Following these defaults keeps tooling and path resolution aligned with the documented test commands and startup scripts.
