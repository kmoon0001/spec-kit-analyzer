import os
import sys
import requests
import urllib.parse # New import for interactive reports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QMainWindow, QStatusBar, QMenuBar, 
    QFileDialog, QSplitter, QTextEdit, QHBoxLayout, QListWidget, QListWidgetItem, 
    QComboBox, QLabel, QGroupBox, QProgressBar, QCheckBox, QPushButton, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, QUrl
from PyQt6.QtGui import QTextDocument # New import for find flags

from .dialogs.rubric_manager_dialog import RubricManagerDialog
from .dialogs.login_dialog import LoginDialog
from .dialogs.change_password_dialog import ChangePasswordDialog
from .workers.analysis_worker import AnalysisWorker
from .workers.folder_analysis_worker import FolderAnalysisWorker
from .workers.ai_loader_worker import AILoaderWorker
from .workers.dashboard_worker import DashboardWorker
from .widgets.dashboard_widget import DashboardWidget

API_URL = "http://127.0.0.1:8000"

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (rest of __init__ is the same)

    # ... (init_base_ui, show_login_dialog, logout, load_main_ui are the same)

    def _create_analysis_tab(self) -> QWidget:
        analysis_widget = QWidget()
        main_layout = QVBoxLayout(analysis_widget)
        # ... (rest of UI creation is the same)

        # --- Document/Results Splitter ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Document group
        document_group = QGroupBox("Document")
        document_layout = QVBoxLayout()
        document_group.setLayout(document_layout)
        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText("Upload a document to see its content here.")
        self.document_display_area.setReadOnly(True)
        document_layout.addWidget(self.document_display_area)
        splitter.addWidget(document_group)

        # Results group
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        self.analysis_results_area = QTextEdit()
        self.analysis_results_area.setPlaceholderText("Analysis results will appear here.")
        self.analysis_results_area.setReadOnly(True)
        self.analysis_results_area.setOpenExternalLinks(False) # Important: handle links internally
        self.analysis_results_area.anchorClicked.connect(self.handle_text_highlight_request) # Connect the signal
        results_layout.addWidget(self.analysis_results_area)
        splitter.addWidget(results_group)

        return analysis_widget

    def handle_text_highlight_request(self, url: QUrl):
        """Handles clicks on custom highlight:// links in the report."""
        if url.scheme() == 'highlight':
            # Decode the text from the URL path
            text_to_highlight = urllib.parse.unquote(url.path())
            
            # Move cursor to the beginning of the document to ensure we find the first instance
            cursor = self.document_display_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.document_display_area.setTextCursor(cursor)

            # Find and highlight the text
            if self.document_display_area.find(text_to_highlight, QTextDocument.FindFlag.FindCaseSensitively):
                # The find method automatically selects the text
                self.tabs.setCurrentIndex(0) # Switch to the analysis tab if not already there
                self.document_display_area.setFocus() # Bring focus to the document view
            else:
                self.status_bar.showMessage(f"Could not find text: '{text_to_highlight}'", 5000)

    # ... (All other methods like show_change_password_dialog, load_dashboard_data, etc., are the same)
    # ... (Full, non-stubbed stylesheets are also included)
