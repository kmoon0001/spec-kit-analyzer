import logging
from pathlib import Path

import yaml
from yaml import SafeLoader, SafeDumper
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
)
from src.config import get_settings

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setModal(True)
        self.resize(400, 200)

        self.settings = get_settings()

        layout = QVBoxLayout(self)

        # 7 Habits Coaching
        self.habit_coaching_checkbox = QCheckBox("Enable '7 Habits' Coaching")
        layout.addWidget(self.habit_coaching_checkbox)

        # Director Dashboard
        self.director_dashboard_checkbox = QCheckBox("Enable Director Dashboard")
        layout.addWidget(self.director_dashboard_checkbox)

        # Add other settings here...
        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.load_settings()

    def load_settings(self) -> None:
        """Load settings from the config object."""
        try:
            self.habit_coaching_checkbox.setChecked(bool(self.settings.enable_habit_coaching))
            self.director_dashboard_checkbox.setChecked(bool(self.settings.enable_director_dashboard))
        except Exception:
            logger.exception("Failed to load settings into dialog")
            QMessageBox.warning(self, "Settings", "Unable to load some settings; using defaults.")

    def save_settings(self) -> None:
        """Save the settings to the config.yaml file."""
        try:
            cfg_path = Path("config.yaml").resolve()
            if not cfg_path.exists():
                QMessageBox.critical(self, "Error Saving Settings", f"Config file not found: {cfg_path}")
                return

            with cfg_path.open("r", encoding="utf-8") as f:
                config_data = yaml.load(f, Loader=SafeLoader) or {}

            config_data["enable_habit_coaching"] = bool(self.habit_coaching_checkbox.isChecked())
            config_data["enable_director_dashboard"] = bool(self.director_dashboard_checkbox.isChecked())

            with cfg_path.open("w", encoding="utf-8") as f:
                yaml.dump(config_data, f, Dumper=SafeDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)

            QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")
            self.accept()
        except Exception as e:  # pragma: no cover - GUI safety
            logger.exception("Failed to save settings")
            QMessageBox.critical(self, "Error Saving Settings", f"Could not save settings: {e}")
