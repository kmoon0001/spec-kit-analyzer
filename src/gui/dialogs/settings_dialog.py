import yaml
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
)
from src.config import get_settings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
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

    def load_settings(self):
        """Load settings from the config object."""
        self.habit_coaching_checkbox.setChecked(self.settings.enable_habit_coaching)
        self.director_dashboard_checkbox.setChecked(
            self.settings.enable_director_dashboard
        )

    def save_settings(self):
        """Save the settings to the config.yaml file."""
        try:
            with open("config.yaml", "r") as f:
                config_data = yaml.safe_load(f)

            config_data["enable_habit_coaching"] = self.habit_coaching_checkbox.isChecked()
            config_data[
                "enable_director_dashboard"
            ] = self.director_dashboard_checkbox.isChecked()

            with open("config.yaml", "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            QMessageBox.information(
                self, "Settings Saved", "Your settings have been saved successfully."
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Error Saving Settings", f"Could not save settings: {e}"
            )
