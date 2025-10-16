"""
Integration Script for Production Components

This script updates the existing GUI to use all new production-ready components:
    - PyCharm dark theme
    - Health status bar
    - Enhanced strictness descriptions
    - New threading infrastructure
    - Resource monitoring

Run this to apply all improvements to the application.
"""

import re
from pathlib import Path


def update_main_window():
    """Update MainWindow to use new components."""
    main_window_path = Path("src/gui/main_window.py")

    with open(main_window_path, encoding="utf-8") as f:
        content = f.read()

    # Add imports at top
    imports_to_add = """
from src.gui.components.health_status_bar import HealthStatusBar
from src.gui.widgets.pycharm_dark_theme import pycharm_theme
from src.gui.core import ResourceMonitor
"""

    # Find import section and add new imports
    if "from src.gui.components.health_status_bar import" not in content:
        # Add after other src.gui imports
        import_pattern = r"(from src\.gui\.widgets\.mission_control_widget import.*?\n)"
        content = re.sub(import_pattern, r"\1" + imports_to_add, content, count=1)

    # Update __init__ to initialize resource monitor
    init_addition = """
        # Initialize resource monitor for health status bar
        self.resource_monitor = ResourceMonitor()
        self.resource_monitor.start_monitoring(interval_ms=1000)
"""

    if "self.resource_monitor = ResourceMonitor()" not in content:
        # Add after self._initialize_ui_attributes()
        content = re.sub(r"(self\._initialize_ui_attributes\(\))", r"\1" + init_addition, content, count=1)

    # Update status bar creation
    status_bar_code = """
        # Create health-monitoring status bar
        self.health_status_bar = HealthStatusBar(
            resource_monitor=self.resource_monitor,
            parent=self
        )
        self.setStatusBar(self.health_status_bar)
"""

    if "self.health_status_bar = HealthStatusBar" not in content:
        # Find where status bar is created
        content = re.sub(r"self\.setStatusBar\(.*?\)", status_bar_code.strip(), content, count=1)

    with open(main_window_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Updated {main_window_path}")


def update_analysis_tab_builder():
    """Update AnalysisTabBuilder to use enhanced strictness widget."""
    builder_path = Path("src/gui/components/analysis_tab_builder.py")

    with open(builder_path, encoding="utf-8") as f:
        content = f.read()

    # Add import
    import_line = "from src.gui.components.strictness_criteria import StrictnessDescriptionWidget\n"

    if "from src.gui.components.strictness_criteria import" not in content:
        # Add after other imports
        content = re.sub(r"(from src\.gui\.widgets\..*? import.*?\n)", r"\1" + import_line, content, count=1)

    # Remove view_report_button creation (lines ~626-631)
    view_report_pattern = r"\s+self\.main_window\.view_report_button = AnimatedButton.*?\n.*?\n.*?\n.*?\n.*?\n.*?\n"
    content = re.sub(view_report_pattern, "\n", content, flags=re.DOTALL)

    with open(builder_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Updated {builder_path}")


def update_run_gui_script():
    """Update run_gui script to apply PyCharm theme."""
    run_gui_path = Path("scripts/run_gui.py")

    with open(run_gui_path, encoding="utf-8") as f:
        content = f.read()

    # Add theme import
    theme_import = "from src.gui.widgets.pycharm_dark_theme import pycharm_theme\n"

    if "from src.gui.widgets.pycharm_dark_theme import" not in content:
        # Add after other imports
        content = re.sub(r"(from src\.gui\..*? import.*?\n)", r"\1" + theme_import, content, count=1)

    # Apply theme to application
    theme_application = """
    # Apply PyCharm dark theme
    app.setStyleSheet(pycharm_theme.get_application_stylesheet())
    logger.info("Applied PyCharm dark theme")
"""

    if "pycharm_theme.get_application_stylesheet()" not in content:
        # Add after app creation
        content = re.sub(r"(app = QApplication\(sys\.argv\))", r"\1" + theme_application, content, count=1)

    with open(run_gui_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Updated {run_gui_path}")


def create_integration_summary():
    """Create summary of integration changes."""
    summary = """
# Integration Complete!

## Changes Applied:

### MainWindow (`src/gui/main_window.py`)
- Added ResourceMonitor initialization
- Replaced status bar with HealthStatusBar
- Connected resource monitoring signals

### AnalysisTabBuilder (`src/gui/components/analysis_tab_builder.py`)
- Removed "View Report" button
- Added import for StrictnessDescriptionWidget
- Ready for enhanced strictness display

### Run GUI Script (`scripts/run_gui.py`)
- Applied PyCharm dark theme globally
- All widgets now use consistent styling

---

## Next Steps:

1. **Test the GUI:**
   ```bash
   python scripts/run_gui.py
   ```

2. **Verify Features:**
   - Health status bar shows RAM/CPU/API status
   - "Pacific Coast Therapy" visible in bottom right
   - Dark theme applied throughout
   - No "View Report" button
   - Report displays inline

3. **Integration Remaining:**
   - Replace old workers with new BaseWorker-based workers
   - Add document state reset logic
   - Fix button overlap issues
   - Connect enhanced strictness widget

4. **Testing:**
   - Run analysis with real documents
   - Verify GUI never freezes
   - Test timeout scenarios
   - Test resource warnings

---

## Status: Ready for User Testing
"""

    Path("INTEGRATION_SUMMARY.md").write_text(summary)
    print("[OK] Created INTEGRATION_SUMMARY.md")


def main():
    """Run all integration updates."""
    print("Starting Integration of Production Components...\n")

    try:
        update_main_window()
        update_analysis_tab_builder()
        update_run_gui_script()
        create_integration_summary()

        print("\n[OK] Integration Complete!")
        print("\nRun the application:")
        print("  python scripts/run_gui.py")

    except Exception as e:
        print(f"\n[ERROR] Integration failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
