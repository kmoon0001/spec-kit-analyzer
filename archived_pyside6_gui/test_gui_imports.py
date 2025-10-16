#!/usr/bin/env python3
"""Test individual GUI imports to find the slow one."""

import time

print("Testing GUI imports individually...")

imports_to_test = [
    "from src.config import get_settings",
    "from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog",
    "from src.gui.dialogs.change_password_dialog import ChangePasswordDialog",
    "from src.gui.dialogs.chat_dialog import ChatDialog",
    "from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker",
    "from src.gui.workers.folder_analysis_starter_worker import FolderAnalysisStarterWorker",
]

for import_stmt in imports_to_test:
    try:
        start = time.time()
        exec(import_stmt)
        duration = time.time() - start
        print(f"✅ {import_stmt:<70} {duration:.2f}s")
    except Exception as e:
        print(f"❌ {import_stmt:<70} ERROR: {e}")
