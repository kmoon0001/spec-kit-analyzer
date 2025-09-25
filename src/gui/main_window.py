import os
import sys
import requests
import urllib.parse
import webbrowser
import jwt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QMainWindow, QStatusBar, QMenuBar, 
    QFileDialog, QSplitter, QTextEdit, QHBoxLayout, QListWidget, QListWidgetItem, 
    QComboBox, QLabel, QGroupBox, QProgressBar, QCheckBox, QPushButton, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, QUrl
from PyQt6.QtGui import QTextDocument

# Dialogs
from .dialogs.rubric_manager_dialog import RubricManagerDialog
from .dialogs.login_dialog import LoginDialog
from .dialogs.change_password_dialog import ChangePasswordDialog
from .dialogs.chat_dialog import ChatDialog

# Workers
from .workers.analysis_starter_worker import AnalysisStarterWorker
from .workers.analysis_worker import AnalysisWorker
from .workers.folder_analysis_worker import FolderAnalysisWorker
from .workers.ai_loader_worker import AILoaderWorker
from .workers.dashboard_worker import DashboardWorker

# Widgets
from .widgets.dashboard_widget import DashboardWidget

API_URL = "http://127.0.0.1:8000"

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.access_token = None
        self.username = None
        self.is_admin = False
        self._current_file_path = None
        self._current_folder_path = None
        self.analyzer_service = None
        self.thread = None
        self.worker = None

        self.init_base_ui()
        self.load_ai_models()
        self.show_login_dialog()

    def init_base_ui(self):
        self.setWindowTitle('Therapy Compliance Analyzer')
        self.setGeometry(100, 100, 1200, 800)

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu('File')
        self.file_menu.addAction('Logout', self.logout)
        self.file_menu.addSeparator()
        self.file_menu.addAction('Exit', self.close)
        self.tools_menu = self.menu_bar.addMenu('Tools')
        self.tools_menu.addAction('Manage Rubrics', self.manage_rubrics)
        self.tools_menu.addAction('Change Password', self.show_change_password_dialog)
        self.theme_menu = self.menu_bar.addMenu('Theme')
        self.theme_menu.addAction('Light', self.set_light_theme)
        self.theme_menu.addAction('Dark', self.set_dark_theme)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')

        self.ai_status_label = QLabel("Loading AI models...")
        self.status_bar.addPermanentWidget(self.ai_status_label)
        self.user_status_label = QLabel("")
        self.status_bar.addPermanentWidget(self.user_status_label)

        self.progress_bar = QProgressBar(self.status_bar)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def show_login_dialog(self):
        self.hide()
        dialog = LoginDialog(self)
        if dialog.exec():
            username, password = dialog.get_credentials()
            try:
                response = requests.post(f"{API_URL}/auth/token", data={"username": username, "password": password})
                response.raise_for_status()
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.username = username
                
                decoded_token = jwt.decode(self.access_token, options={"verify_signature": False})
                self.is_admin = decoded_token.get('is_admin', False)

                self.user_status_label.setText(f"Logged in as: {self.username}")
                self.status_bar.showMessage("Login successful.")
                self.load_main_ui()
                self.show()
            except (requests.exceptions.RequestException, jwt.exceptions.DecodeError) as e:
                QMessageBox.critical(self, "Login Failed", f"Failed to authenticate: {e}")
                self.close()
        else:
            self.close()

    def logout(self):
        self.access_token = None
        self.username = None
        self.is_admin = False
        self.user_status_label.setText("")
        self.setCentralWidget(None)
        self.show_login_dialog()

    def load_main_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        analysis_tab = self._create_analysis_tab()
        self.tabs.addTab(analysis_tab, "Analysis")

        self.dashboard_widget = DashboardWidget()
        self.tabs.addTab(self.dashboard_widget, "Dashboard")

        self.dashboard_widget.refresh_requested.connect(self.load_dashboard_data)

        if self.is_admin:
            self.admin_menu = self.menu_bar.addMenu("Admin")
            self.admin_menu.addAction("Open Admin Dashboard", self.open_admin_dashboard)

        self.load_dashboard_data()

        theme = self.load_theme_setting()
        self.apply_stylesheet(theme)

    def open_admin_dashboard(self):
        webbrowser.open(f"{API_URL}/admin/dashboard?token={self.access_token}")

    def _create_analysis_tab(self) -> QWidget:
        analysis_widget = QWidget()
        main_layout = QVBoxLayout(analysis_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout()
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)

        self.upload_button = QPushButton('Upload Document')
        self.upload_button.clicked.connect(self.open_file_dialog)
        controls_layout.addWidget(self.upload_button)

        self.clear_button = QPushButton('Clear Display')
        self.clear_button.clicked.connect(self.clear_display)
        controls_layout.addWidget(self.clear_button)

        controls_layout.addStretch()

        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        self.run_analysis_button.setEnabled(False)
        controls_layout.addWidget(self.run_analysis_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        document_group = QGroupBox("Document")
        document_layout = QVBoxLayout()
        document_group.setLayout(document_layout)
        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText("Upload a document to see its content here.")
        self.document_display_area.setReadOnly(True)
        document_layout.addWidget(self.document_display_area)
        splitter.addWidget(document_group)

        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        self.analysis_results_area = QTextEdit()
        self.analysis_results_area.setPlaceholderText("Analysis results will appear here.")
        self.analysis_results_area.setReadOnly(True)
        self.analysis_results_area.setOpenExternalLinks(False)
        self.analysis_results_area.anchorClicked.connect(self.handle_anchor_click)
        results_layout.addWidget(self.analysis_results_area)
        splitter.addWidget(results_group)

        return analysis_widget

    def handle_anchor_click(self, url: QUrl):
        if url.scheme() == 'highlight':
            self.handle_text_highlight_request(url)
        elif url.scheme() == 'chat':
            self.handle_chat_request(url)

    def handle_text_highlight_request(self, url: QUrl):
        combined_payload = urllib.parse.unquote(url.path())
        parts = combined_payload.split('|||')
        context_snippet = parts[0]
        text_to_highlight = parts[1] if len(parts) > 1 else context_snippet

        doc = self.document_display_area.document()
        context_cursor = doc.find(context_snippet, 0, QTextDocument.FindFlag.FindCaseSensitively)

        if not context_cursor.isNull():
            inner_cursor = doc.find(text_to_highlight, context_cursor.selectionStart(), QTextDocument.FindFlag.FindCaseSensitively)
            if not inner_cursor.isNull() and inner_cursor.selectionEnd() <= context_cursor.selectionEnd():
                self.document_display_area.setTextCursor(inner_cursor)
                self.tabs.setCurrentIndex(0)
                self.document_display_area.setFocus()
                return

        cursor = self.document_display_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.document_display_area.setTextCursor(cursor)
        if self.document_display_area.find(text_to_highlight, QTextDocument.FindFlag.FindCaseSensitively):
            self.tabs.setCurrentIndex(0)
            self.document_display_area.setFocus()
        else:
            self.status_bar.showMessage(f"Could not find text: '{text_to_highlight}'", 5000)

    def handle_chat_request(self, url: QUrl):
        initial_context = urllib.parse.unquote(url.path())
        chat_dialog = ChatDialog(initial_context, self.access_token, self)
        chat_dialog.exec()

    def show_change_password_dialog(self):
        dialog = ChangePasswordDialog(self)
        if dialog.exec():
            current_password, new_password = dialog.get_passwords()
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                payload = {"current_password": current_password, "new_password": new_password}
                response = requests.post(f"{API_URL}/auth/users/change-password", json=payload, headers=headers)
                response.raise_for_status()
                QMessageBox.information(self, "Success", "Password changed successfully.")
            except requests.exceptions.RequestException as e:
                detail = e.response.json().get('detail', str(e)) if e.response else str(e)
                QMessageBox.critical(self, "Error", f"Failed to change password: {detail}")

    def load_dashboard_data(self):
        self.status_bar.showMessage("Refreshing dashboard data...")
        self.thread = QThread()
        self.worker = DashboardWorker(self.access_token)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_dashboard_data_loaded)
        self.worker.error.connect(lambda msg: self.status_bar.showMessage(f"Dashboard Error: {msg}"))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_dashboard_data_loaded(self, data):
        self.dashboard_widget.update_dashboard(data)
        self.status_bar.showMessage("Dashboard updated.", 3000)

    def run_analysis(self):
        if not self._current_file_path:
            return

        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.run_analysis_button.setEnabled(False)
        self.status_bar.showMessage("Starting analysis...")

        self.thread = QThread()
        self.worker = AnalysisStarterWorker(self._current_file_path, {}, self.access_token)
        self.worker.moveToThread(self.thread)
        self.worker.success.connect(self.handle_analysis_started)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def handle_analysis_started(self, task_id: str):
        self.status_bar.showMessage(f"Analysis in progress... (Task ID: {task_id})")
        self.run_analysis_threaded(task_id)

    def run_analysis_threaded(self, task_id: str):
        self.thread = QThread()
        self.worker = AnalysisWorker(task_id)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_analysis_success)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_analysis_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_analysis_progress(self, progress):
        self.progress_bar.setValue(progress)

    def on_analysis_success(self, result):
        self.progress_bar.hide()
        self.analysis_results_area.setText(result)
        self.status_bar.showMessage("Analysis complete.")
        self.run_analysis_button.setEnabled(True)

    def on_analysis_error(self, error_message):
        self.progress_bar.hide()
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.status_bar.showMessage("Backend analysis failed.")
        self.run_analysis_button.setEnabled(True)

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Document', '', 'All Files (*.*)')
        if file_name:
            self._current_file_path = file_name
            self.status_bar.showMessage(f"Loaded document: {os.path.basename(file_name)}")
            self.run_analysis_button.setEnabled(True)
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.document_display_area.setText(f.read())
            except (IOError, UnicodeDecodeError) as e:
                self.document_display_area.setText(f"Could not display preview for: {file_name}\n{e}")

    def clear_display(self):
        self.document_display_area.clear()
        self.analysis_results_area.clear()
        self._current_file_path = None
        self.run_analysis_button.setEnabled(False)
        self.status_bar.showMessage("Display cleared.")

    def load_ai_models(self):
        self.thread = QThread()
        self.worker = AILoaderWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_ai_loaded)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_ai_loaded(self, analyzer_service, is_healthy, status_message):
        self.analyzer_service = analyzer_service
        self.ai_status_label.setText(status_message)
        self.ai_status_label.setStyleSheet("color: green;" if is_healthy else "color: red;")

    def apply_stylesheet(self, theme="dark"):
        if theme == "light":
            self.setStyleSheet(self.get_light_theme_stylesheet())
        else:
            self.setStyleSheet(self.get_dark_theme_stylesheet())

    def save_theme_setting(self, theme):
        with open("theme.cfg", "w") as f:
            f.write(theme)

    def load_theme_setting(self):
        try:
            with open("theme.cfg", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "dark"

    def set_light_theme(self):
        self.apply_stylesheet("light")
        self.save_theme_setting("light")

    def set_dark_theme(self):
        self.apply_stylesheet("dark")
        self.save_theme_setting("dark")

    @staticmethod
    def get_light_theme_stylesheet():
        return """
            QMainWindow { background-color: #f0f0f0; color: #000000; }
            QGroupBox { background-color: #ffffff; color: #000000; border: 1px solid #d0d0d0; border-radius: 5px; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; background-color: #ffffff; }
            QLabel { color: #000000; }
            QPushButton { background-color: #e0e0e0; color: #000000; border: 1px solid #c0c0c0; padding: 5px; border-radius: 3px; }
            QPushButton:hover { background-color: #d0d0d0; }
            QPushButton:pressed { background-color: #c0c0c0; }
            QTextEdit, QListWidget, QComboBox { background-color: #ffffff; color: #000000; border: 1px solid #d0d0d0; border-radius: 5px; }
            QMenuBar { background-color: #f0f0f0; color: #000000; }
            QMenuBar::item:selected { background-color: #d0d0d0; }
            QMenu { background-color: #f0f0f0; color: #000000; }
            QMenu::item:selected { background-color: #d0d0d0; }
            QStatusBar { background-color: #f0f0f0; color: #000000; }
        """

    @staticmethod
    def get_dark_theme_stylesheet():
        return """
            QMainWindow { background-color: #2b2b2b; color: #f0f0f0; }
            QGroupBox { border: 1px solid #444; border-radius: 5px; margin-top: 10px; font-weight: bold; color: #f0f0f0; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
            QPushButton { background-color: #007acc; color: white; border: none; padding: 10px; border-radius: 5px; box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1); }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #003c6a; }
            QTextEdit, QListWidget, QComboBox { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; border-radius: 5px; padding: 5px; }
            QStatusBar { background-color: #007acc; color: white; }
            QLabel { color: #f0f0f0; }
        """
