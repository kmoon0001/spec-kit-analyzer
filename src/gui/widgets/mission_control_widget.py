
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
)


class SettingsEditorWidget(QWidget):
    """A widget to dynamically edit application settings."""
    save_requested = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("🔧 Advanced Administration Settings")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #1d4ed8; margin-bottom: 15px;")
        layout.addWidget(header)
        
        # Create tabbed interface for different admin sections
        from PySide6.QtWidgets import QTabWidget
        admin_tabs = QTabWidget()
        admin_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #d1d5db;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #f1f5f9;
                border: 1px solid #d1d5db;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid white;
            }
        """)
        
        # System Configuration Tab
        system_tab = self._create_system_config_tab()
        admin_tabs.addTab(system_tab, "⚙️ System Config")
        
        # AI Model Settings Tab
        ai_tab = self._create_ai_settings_tab()
        admin_tabs.addTab(ai_tab, "🤖 AI Models")
        
        # Security Settings Tab
        security_tab = self._create_security_settings_tab()
        admin_tabs.addTab(security_tab, "🔒 Security")
        
        # Performance Tuning Tab
        performance_tab = self._create_performance_tab()
        admin_tabs.addTab(performance_tab, "⚡ Performance")
        
        layout.addWidget(admin_tabs)
        
        # Save button
        self.save_button = QPushButton("💾 Save All Settings")
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #047857;
            }
        """)
        layout.addWidget(self.save_button)
    
    def _create_system_config_tab(self) -> QWidget:
        """Create system configuration tab."""
        from PySide6.QtWidgets import QTextBrowser
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # System info display
        info_browser = QTextBrowser()
        info_browser.setStyleSheet("""
            QTextBrowser {
                background: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
            }
        """)
        
        # Generate realtime system info
        system_info = self._generate_realtime_system_info()
        info_browser.setHtml(system_info)
        
        # Set up timer for realtime updates
        from PySide6.QtCore import QTimer
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(lambda: info_browser.setHtml(self._generate_realtime_system_info()))
        self.system_timer.start(5000)  # Update every 5 seconds
        layout.addWidget(info_browser)
        
        return tab
    
    def _generate_realtime_system_info(self) -> str:
        """Generate realtime system information HTML."""
        import psutil
        import platform
        from datetime import datetime
        import os
        
        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get process info
            process = psutil.Process(os.getpid())
            app_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return f"""
            <h3 style='color: #1d4ed8;'>System Configuration - Live Status</h3>
            <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                <h4 style='color: #059669;'>Application Status</h4>
                <ul>
                    <li><strong>Version:</strong> 1.0.0</li>
                    <li><strong>Status:</strong> <span style='color: #059669;'>✅ Running</span></li>
                    <li><strong>Uptime:</strong> Active</li>
                    <li><strong>Last Update:</strong> {current_time}</li>
                </ul>
            </div>
            
            <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                <h4 style='color: #d97706;'>System Resources</h4>
                <ul>
                    <li><strong>CPU Usage:</strong> {cpu_percent:.1f}%</li>
                    <li><strong>System Memory:</strong> {memory.percent:.1f}% ({memory.used // 1024 // 1024:,} MB / {memory.total // 1024 // 1024:,} MB)</li>
                    <li><strong>App Memory:</strong> {app_memory:.1f} MB</li>
                    <li><strong>Disk Usage:</strong> {disk.percent:.1f}% ({disk.used // 1024 // 1024 // 1024:.1f} GB / {disk.total // 1024 // 1024 // 1024:.1f} GB)</li>
                </ul>
            </div>
            
            <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                <h4 style='color: #7c3aed;'>System Information</h4>
                <ul>
                    <li><strong>Platform:</strong> {platform.system()} {platform.release()}</li>
                    <li><strong>Architecture:</strong> {platform.machine()}</li>
                    <li><strong>Python:</strong> {platform.python_version()}</li>
                    <li><strong>Database:</strong> SQLite (Local)</li>
                </ul>
            </div>
            """
            
        except Exception as e:
            return f"""
            <h3 style='color: #1d4ed8;'>System Configuration</h3>
            <div style='background: #fee2e2; padding: 15px; border-radius: 6px; margin: 10px 0; border: 1px solid #dc2626;'>
                <h4 style='color: #dc2626;'>Error Loading System Info</h4>
                <p>Could not retrieve system metrics: {str(e)}</p>
                <p>Basic functionality remains available.</p>
            </div>
            """
    
    def _create_ai_settings_tab(self) -> QWidget:
        """Create AI model settings tab."""
        from PySide6.QtWidgets import QTextBrowser
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        ai_browser = QTextBrowser()
        ai_browser.setStyleSheet("""
            QTextBrowser {
                background: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
            }
        """)
        
        ai_info = """
        <h3 style='color: #1d4ed8;'>AI Model Configuration</h3>
        
        <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
            <h4 style='color: #7c3aed;'>Local Language Models</h4>
            <ul>
                <li><strong>Primary LLM:</strong> Phi-2 (2.7B parameters)</li>
                <li><strong>Backup LLM:</strong> Mistral-7B (quantized)</li>
                <li><strong>Embeddings:</strong> sentence-transformers/all-MiniLM-L6-v2</li>
                <li><strong>NER Model:</strong> BioBERT for medical entities</li>
            </ul>
        </div>
        
        <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
            <h4 style='color: #059669;'>Processing Settings</h4>
            <ul>
                <li><strong>Max Context Length:</strong> 2048 tokens</li>
                <li><strong>Temperature:</strong> 0.3 (conservative)</li>
                <li><strong>Batch Size:</strong> Adaptive based on memory</li>
                <li><strong>Timeout:</strong> 120 seconds per analysis</li>
            </ul>
        </div>
        
        <div style='background: #fef7ff; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #7c3aed;'>
            <h4 style='color: #7c3aed;'>Privacy Guarantee</h4>
            <p>All AI processing occurs locally. No data is transmitted to external servers.</p>
        </div>
        """
        
        ai_browser.setHtml(ai_info)
        layout.addWidget(ai_browser)
        
        return tab
    
    def _create_security_settings_tab(self) -> QWidget:
        """Create security settings tab."""
        from PySide6.QtWidgets import QTextBrowser
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        security_browser = QTextBrowser()
        security_browser.setStyleSheet("""
            QTextBrowser {
                background: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
            }
        """)
        
        security_info = """
        <h3 style='color: #1d4ed8;'>Security Configuration</h3>
        
        <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
            <h4 style='color: #dc2626;'>Authentication</h4>
            <ul>
                <li><strong>Password Policy:</strong> Min 8 chars, mixed case, numbers</li>
                <li><strong>Session Timeout:</strong> 30 minutes</li>
                <li><strong>JWT Expiration:</strong> 24 hours</li>
                <li><strong>Failed Login Limit:</strong> 5 attempts</li>
            </ul>
        </div>
        
        <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
            <h4 style='color: #059669;'>Data Protection</h4>
            <ul>
                <li><strong>PHI Scrubbing:</strong> Automatic detection and redaction</li>
                <li><strong>Database Encryption:</strong> AES-256 at rest</li>
                <li><strong>Audit Logging:</strong> All actions logged (no PHI)</li>
                <li><strong>Temp File Cleanup:</strong> Automatic after 24 hours</li>
            </ul>
        </div>
        
        <div style='background: #f0fdf4; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #059669;'>
            <h4 style='color: #059669;'>HIPAA Compliance</h4>
            <p>System designed for HIPAA compliance with local processing, encryption, and audit trails.</p>
        </div>
        """
        
        security_browser.setHtml(security_info)
        layout.addWidget(security_browser)
        
        return tab
    
    def _create_performance_tab(self) -> QWidget:
        """Create performance tuning tab."""
        from PySide6.QtWidgets import QTextBrowser
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        perf_browser = QTextBrowser()
        perf_browser.setStyleSheet("""
            QTextBrowser {
                background: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
            }
        """)
        
        perf_info = """
        <h3 style='color: #1d4ed8;'>Performance Optimization</h3>
        
        <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
            <h4 style='color: #d97706;'>Cache Management</h4>
            <ul>
                <li><strong>Embedding Cache:</strong> LRU with memory pressure monitoring</li>
                <li><strong>NER Cache:</strong> 1000 entries max</li>
                <li><strong>Document Cache:</strong> 500 entries max</li>
                <li><strong>LLM Response Cache:</strong> 200 entries max</li>
            </ul>
        </div>
        
        <div style='background: white; padding: 15px; border-radius: 6px; margin: 10px 0;'>
            <h4 style='color: #7c3aed;'>Processing Optimization</h4>
            <ul>
                <li><strong>Batch Processing:</strong> Enabled for multiple documents</li>
                <li><strong>Parallel Processing:</strong> CPU core utilization</li>
                <li><strong>Memory Management:</strong> Automatic cleanup at 80% usage</li>
                <li><strong>Model Loading:</strong> Lazy loading with caching</li>
            </ul>
        </div>
        
        <div style='background: #fffbeb; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #d97706;'>
            <h4 style='color: #d97706;'>Performance Monitoring</h4>
            <p>Real-time monitoring of memory usage, processing times, and system resources.</p>
        </div>
        """
        
        perf_browser.setHtml(perf_info)
        layout.addWidget(perf_browser)
        
        return tab

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
                group_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
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
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
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
            status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
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
        self.api_status_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.api_status_label, alignment=Qt.AlignmentFlag.AlignCenter)

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
