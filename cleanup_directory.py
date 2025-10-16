#!/usr/bin/env python3
"""
Directory Cleanup Script for Therapy Compliance Analyzer
Organizes the root directory by moving files to appropriate subdirectories.
"""

import os
import shutil
from pathlib import Path

def cleanup_directory():
    """Clean up the root directory by organizing files into subdirectories."""
    
    # Create cleanup directories
    cleanup_dirs = {
        'archive/old_docs': [
            'AGENTS.md', 'ALL_TODOS_COMPLETE.md', 'APPLICATION_READY_STATUS.md',
            'CLEANUP_PROGRESS_REPORT.md', 'CLEANUP_SUMMARY.md', 'CODE_CLEANUP_COMPLETION_REPORT.md',
            'CODE_QUALITY_FINAL_REPORT.md', 'COMPREHENSIVE_CODEBASE_REVIEW.md',
            'COMPREHENSIVE_DIAGNOSTIC_CHECKLIST.md', 'COMPREHENSIVE_IMPROVEMENTS_SUMMARY.md',
            'CRITICAL_TASKS_IMPLEMENTATION.md', 'DEBUG_COMPLETE_REPORT.md',
            'DEBUGGING_GUIDE.md', 'DEPLOYMENT_READY.md', 'E2E_TEST_RESULTS.md',
            'END_TO_END_TESTING_PLAN.md', 'FINAL_CODEBASE_STATUS.md',
            'FINAL_DEPLOYMENT_STATUS.md', 'FINAL_IMPLEMENTATION_REPORT.md',
            'FINAL_TYPE_ANNOTATION_SUMMARY.md', 'FRONTEND_TRANSITION_ANALYSIS.md',
            'GUI_REFACTORING_PLAN.md', 'IMMEDIATE_PRIORITIES_COMPLETION_REPORT.md',
            'IMPLEMENTATION_STATUS.md', 'INTEGRATION_SUMMARY.md',
            'LAUNCHER_GUIDE.md', 'LAUNCHER_README.md', 'MOCK_TEST_RUN.md',
            'MYPY_CLEANUP_FINAL.md', 'NEW_FEATURES_DOCUMENTATION.md',
            'NEXT_STEPS_BEST_PRACTICES.md', 'PERFORMANCE_UI_OPTIMIZATIONS.md',
            'PRODUCTION_ARCHITECTURE.md', 'PRODUCTION_DEPLOYMENT_CHECKLIST.md',
            'REFACTORING_COMPLETION_SUMMARY.md', 'REFACTORING_SUMMARY.md',
            'RELEASE_NOTES.md', 'TYPE_ANNOTATION_PROGRESS_UPDATE.md',
            'TYPE_ANNOTATION_PROGRESS.md'
        ],
        'archive/old_scripts': [
            'analyze_logs.py', 'comprehensive_code_quality_fix.py', 'consistency_check.py',
            'debug_api.py', 'debug_gui.py', 'debug_tools.py', 'diagnostic_startup.py',
            'final_cleanup.py', 'fix_blind_except.py', 'fix_critical_types.py',
            'integrate_production_components.py', 'integration_test.py', 'launch_gui.py',
            'minimal_api_start.py', 'monitor.py', 'quick_api_start.py', 'quick_start.py',
            'robust_startup.py', 'run_e2e_tests.py', 'run_validation.py',
            'simple_debug.py', 'simple_gui.py', 'simple_monitor.py',
            'simple_start_api.py', 'start_api.py', 'start_application.py',
            'start_electron_app.py', 'test_analysis_debug.py', 'test_api_startup.py',
            'verify_electron_setup.py'
        ],
        'archive/temp_files': [
            '__tmp_probe.py', 'sitecustomize.py', 'temp_api_err.log', 'temp_api_out.log',
            'temp_requirements.txt', 'npm-ver.err', 'npm-ver.log', 'Stop-Process',
            'List[pipeline]', 'license.dat', 'coverage.xml', 'test_report.pdf'
        ],
        'archive/old_configs': [
            'requirements-api.txt', 'requirements-dev.txt', 'requirements-original.txt',
            'requirements.lock'
        ],
        'archive/old_directories': [
            'archived_pyside6_gui', 'bin', 'config', 'data', 'database', 'docs',
            'examples', 'frontend', 'models', 'PySide6', 'pytest_asyncio',
            'scripts', 'temp', 'test', 'test_data', 'venv_fresh'
        ]
    }
    
    # Create archive directories
    for archive_dir in cleanup_dirs.keys():
        Path(archive_dir).mkdir(parents=True, exist_ok=True)
    
    # Move files
    moved_count = 0
    for target_dir, files in cleanup_dirs.items():
        for file_name in files:
            if Path(file_name).exists():
                try:
                    if Path(file_name).is_file():
                        shutil.move(file_name, f"{target_dir}/{file_name}")
                        moved_count += 1
                        print(f"Moved {file_name} to {target_dir}/")
                    elif Path(file_name).is_dir():
                        shutil.move(file_name, f"{target_dir}/{file_name}")
                        moved_count += 1
                        print(f"Moved directory {file_name} to {target_dir}/")
                except Exception as e:
                    print(f"Error moving {file_name}: {e}")
    
    print(f"\nCleanup complete! Moved {moved_count} items to archive directories.")
    print("\nRemaining important files in root:")
    
    # List remaining important files
    important_files = [
        'README.md', 'requirements.txt', 'config.yaml', 'pytest.ini',
        '.gitignore', '.env', '.ruff.toml', 'compliance.db'
    ]
    
    for file_name in important_files:
        if Path(file_name).exists():
            print(f"  ✓ {file_name}")
        else:
            print(f"  ✗ {file_name} (missing)")

if __name__ == "__main__":
    cleanup_directory()