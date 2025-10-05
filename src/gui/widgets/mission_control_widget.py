
from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextBrowser,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QScrollArea,
)


class SettingsEditorWidget(QWidget):
    """A widget to dynamically edit application settings."""
    save_requested = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.scroll_content = QWidget()
        self.form_layout = QFormLayout(self.scroll_content)
        scroll_area.setWidget(self.scroll_content)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self._on_save)
        layout.addWidget(self.save_button)

    def set_settings(self, settings: Dict[str, Any]) -> None:
        """Dynamically builds the form based on the settings dictionary."""
        # Clear old form
        while self.form_layout.count():
            self.form_layout.removeRow(0)

        self._build_form_recursively(settings)

    def _build_form_recursively(self, settings: Dict[str, Any], prefix="") -> None:
        for key, value in settings.items():
            full_key = f"{prefix}{key}"
            if isinstance(value, dict):
                group_label = QLabel(f"{key.replace('_', ' ').title()}")
                group_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.form_layout.addRow(group_label)
                self._build_form_recursively(value, f"{full_key}.")
            else:
                self._add_form_widget(full_key, value)

    def _add_form_widget(self, key: str, value: Any) -> None:
        label = QLabel(key.split('.')[-1].replace('_', ' ').title())
        widget: QWidget

        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(-1000000, 1000000)
            widget.setValue(value)
        elif isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-1000000, 1000000)
            widget.setValue(value)
        else:
            widget = QLineEdit(str(value))
        
        widget.setObjectName(key)
        self.form_layout.addRow(label, widget)

    def _on_save(self) -> None:
        """Collects data from the form and emits the save_requested signal."""
        new_settings = {}
        for i in range(self.form_layout.rowCount()):
            field = self.form_layout.itemAt(i, QFormLayout.FieldRole)
            if field and field.widget():
                widget = field.widget()
                key = widget.objectName()
                value: Any
                if isinstance(widget, QCheckBox):
                    value = widget.isChecked()
                elif isinstance(widget, QSpinBox):
                    value = widget.getValue()
                elif isinstance(widget, QDoubleSpinBox):
                    value = widget.getValue()
                elif isinstance(widget, QLineEdit):
                    value = widget.text()
                else:
                    continue
                
                # Reconstruct nested dictionary
                keys = key.split('.')
                d = new_settings
                for k in keys[:-1]:
                    d = d.setdefault(k, {})
                d[keys[-1]] = value

        self.save_requested.emit(new_settings)


class LogViewerWidget(QWidget):
    """A widget that displays log messages."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.log_browser = QTextBrowser()
        self.log_browser.setReadOnly(True)
        self.log_browser.setFontFamily("monospace")
        layout.addWidget(self.log_browser)

    def add_log_message(self, message: str) -> None:
        """Appends a new log message to the browser."""
        self.log_browser.append(message)


class TaskMonitorWidget(QWidget):
    """A widget that displays analysis tasks in a table."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["Task ID", "Filename", "Status", "Timestamp"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.task_table)

    def update_tasks(self, tasks: Dict[str, Dict[str, Any]]) -> None:
        """Updates the table with the latest task data."""
        self.task_table.setRowCount(0)
        sorted_tasks = sorted(tasks.items(), key=lambda item: item[1].get("timestamp", ""), reverse=True)

        for task_id, task_data in sorted_tasks:
            row_position = self.task_table.rowCount()
            self.task_table.insertRow(row_position)

            self.task_table.setItem(row_position, 0, QTableWidgetItem(task_id[:8] + "..."))
            self.task_table.setItem(row_position, 1, QTableWidgetItem(task_data.get("filename", "N/A")))
            self.task_table.setItem(row_position, 2, QTableWidgetItem(task_data.get("status", "N/A")))
            self.task_table.setItem(row_position, 3, QTableWidgetItem(str(task_data.get("timestamp", "N/A"))))


class MissionControlWidget(QWidget):
    """Mission control dashboard summarising compliance performance."""

    start_analysis_requested = Signal()
    review_document_requested = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update_overview(self, data: dict[str, Any]) -> None:
        if "ai_health" in data:
            self._update_ai_health_display(data["ai_health"])

    def update_api_status(self, status: str, color: str) -> None:
        """Updates the API status indicator."""
        self.api_status_label.setText(status)
        self.api_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def update_task_list(self, tasks: Dict[str, Dict[str, Any]]) -> None:
        """Passes task data to the task monitor widget."""
        self.task_monitor.update_tasks(tasks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header = QLabel("Mission Control")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)
        ai_health_frame = self._build_ai_health_frame()
        status_layout.addWidget(ai_health_frame, stretch=3)
        system_status_frame = self._build_system_status_frame()
        status_layout.addWidget(system_status_frame, stretch=1)
        layout.addLayout(status_layout)

        # New Task Monitor Frame
        task_monitor_frame = self._build_task_monitor_frame()
        layout.addWidget(task_monitor_frame, stretch=1)

        layout.addStretch(1)

    def _build_ai_health_frame(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("aiHealthFrame")
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(24)

        title = QLabel("AI Subsystem Status")
        title.setFont(QFont("Segoe UI", 11, QFont.Medium))
        layout.addWidget(title, 0, 0, 1, 4)

        self.ai_health_labels: Dict[str, QLabel] = {}
        components = {
            "llm_service": "LLM Service",
            "ner_service": "NER Service",
            "transformer_models": "Transformers",
            "vector_database": "Vector DB",
        }

        col = 0
        for key, name in components.items():
            name_label = QLabel(name)
            status_label = QLabel("Pending...")
            status_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.ai_health_labels[key] = status_label
            layout.addWidget(name_label, 1, col)
            layout.addWidget(status_label, 2, col)
            col += 1

        frame.setStyleSheet(
            "#aiHealthFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }"
        )
        return frame

    def _build_system_status_frame(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("systemStatusFrame")
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("API Status")
        title.setFont(QFont("Segoe UI", 11, QFont.Medium))
        layout.addWidget(title)

        self.api_status_label = QLabel("Pending...")
        self.api_status_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(self.api_status_label, alignment=Qt.AlignCenter)

        frame.setStyleSheet(
            "#systemStatusFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }"
        )
        return frame

    def _build_task_monitor_frame(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("taskMonitorFrame")
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Live Task Monitor")
        title.setFont(QFont("Segoe UI", 11, QFont.Medium))
        layout.addWidget(title)

        self.task_monitor = TaskMonitorWidget(self)
        layout.addWidget(self.task_monitor)

        frame.setStyleSheet(
            "#taskMonitorFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }"
        )
        return frame

    def _update_ai_health_display(self, health_data: Dict[str, Any]) -> None:
        for key, data in health_data.items():
            if key in self.ai_health_labels:
                status = data.get("status", "Unknown")
                label = self.ai_health_labels[key]
                label.setText(status)
                color = "#16a34a" if status.lower() == "healthy" else "#dc2626"
                label.setStyleSheet(f"color: {color}; font-weight: bold;")
