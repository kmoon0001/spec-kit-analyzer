# Python
from __future__ import annotations

# Standard library
from typing import Optional

# Third-party
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel,
    QListWidget, QTextEdit, QSplitter, QGridLayout, QCheckBox, QDateEdit
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal as Signal, QDate

# Matplotlib for analytics chart
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def _style_action_button(button: QPushButton, font_size: int = 11, bold: bool = True, height: int = 28, padding: str = "4px 10px"):
    try:
        f = QFont()
        f.setPointSize(font_size)
        f.setBold(bold)
        button.setFont(f)
        button.setMinimumHeight(height)
        button.setStyleSheet(f"text-align:center; padding:{padding};")
    except Exception:
        ...

class SetupTab(QWidget):
    """
    UI for the 'Setup & File Queue' tab.
    """
    open_file_requested = Signal()
    open_folder_requested = Signal()
    analyze_all_requested = Signal()
    cancel_batch_requested = Signal()
    remove_file_requested = Signal()
    clear_queue_requested = Signal()
    upload_rubric_requested = Signal()
    manage_rubrics_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        top_setup_layout = QHBoxLayout()

        # Rubric Panel
        rubric_panel = QGroupBox("Rubric")
        rubric_layout = QVBoxLayout(rubric_panel)
        row_rubric_btns = QHBoxLayout()
        self.btn_upload_rubric = QPushButton("Upload Rubric")
        self.btn_manage_rubrics = QPushButton("Manage Rubrics")
        for b in (self.btn_upload_rubric, self.btn_manage_rubrics):
            _style_action_button(b, font_size=11, bold=True, height=32, padding="6px 10px")
            row_rubric_btns.addWidget(b)
        row_rubric_btns.addStretch(1)
        self.btn_upload_rubric.clicked.connect(self.upload_rubric_requested)
        self.btn_manage_rubrics.clicked.connect(self.manage_rubrics_requested)
        rubric_layout.addLayout(row_rubric_btns)

        discipline_group = QGroupBox("Select Disciplines for Analysis")
        discipline_layout = QHBoxLayout(discipline_group)
        discipline_layout.setSpacing(15)
        self.chk_pt = QCheckBox("Physical Therapy")
        self.chk_ot = QCheckBox("Occupational Therapy")
        self.chk_slp = QCheckBox("Speech-Language Pathology")
        self.chk_all_disciplines = QCheckBox("All")
        self.chk_all_disciplines.setTristate(True)
        discipline_layout.addWidget(self.chk_pt)
        discipline_layout.addWidget(self.chk_ot)
        discipline_layout.addWidget(self.chk_slp)
        discipline_layout.addStretch(1)
        discipline_layout.addWidget(self.chk_all_disciplines)
        rubric_layout.addWidget(discipline_group)
        self.lbl_rubric_title = QLabel("(No rubric selected)")
        self.lbl_rubric_title.setWordWrap(True)
        rubric_layout.addWidget(self.lbl_rubric_title)
        top_setup_layout.addWidget(rubric_panel)

        # File Selection Panel
        report_panel = QGroupBox("File Selection")
        report_layout = QVBoxLayout(report_panel)
        row_report_btns = QHBoxLayout()
        self.btn_upload_report = QPushButton("Open File")
        self.btn_upload_folder = QPushButton("Open Folder")
        for b in (self.btn_upload_report, self.btn_upload_folder):
            _style_action_button(b, font_size=11, bold=True, height=32, padding="6px 10px")
            row_report_btns.addWidget(b)
        row_report_btns.addStretch(1)
        self.btn_upload_report.clicked.connect(self.open_file_requested)
        self.btn_upload_folder.clicked.connect(self.open_folder_requested)
        report_layout.addLayout(row_report_btns)
        self.lbl_report_name = QLabel("(No file selected for single analysis)")
        report_layout.addWidget(self.lbl_report_name)
        top_setup_layout.addWidget(report_panel)

        layout.addLayout(top_setup_layout)

        # File Queue Panel
        queue_group = QGroupBox("File Queue (for batch analysis)")
        queue_layout = QVBoxLayout(queue_group)
        queue_actions_layout = QHBoxLayout()
        self.btn_analyze_all = QPushButton("Analyze All in Queue")
        self.btn_cancel_batch = QPushButton("Cancel Batch")
        self.btn_remove_file = QPushButton("Remove Selected")
        self.btn_clear_all = QPushButton("Clear Queue")
        _style_action_button(self.btn_analyze_all, font_size=11, bold=True, height=32)
        _style_action_button(self.btn_cancel_batch, font_size=11, bold=True, height=32)
        _style_action_button(self.btn_remove_file, font_size=11, bold=True, height=32)
        _style_action_button(self.btn_clear_all, font_size=11, bold=True, height=32)
        queue_actions_layout.addWidget(self.btn_analyze_all)
        queue_actions_layout.addWidget(self.btn_cancel_batch)
        queue_actions_layout.addStretch(1)
        queue_actions_layout.addWidget(self.btn_remove_file)
        queue_actions_layout.addWidget(self.btn_clear_all)
        self.list_folder_files = QListWidget()
        queue_layout.addLayout(queue_actions_layout)
        queue_layout.addWidget(self.list_folder_files)

        self.btn_analyze_all.clicked.connect(self.analyze_all_requested)
        self.btn_cancel_batch.clicked.connect(self.cancel_batch_requested)
        self.btn_remove_file.clicked.connect(self.remove_file_requested)
        self.btn_clear_all.clicked.connect(self.clear_queue_requested)

        layout.addWidget(queue_group)

class ResultsTab(QWidget):
    """
    UI for the 'Analysis Results' tab.
    """
    anchor_clicked = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        results_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.txt_chat = QTextEdit()
        self.txt_chat.setPlaceholderText("Analysis summary will appear here.")
        self.txt_chat.setReadOnly(True)
        self.txt_chat.anchorClicked.connect(self.anchor_clicked)

        self.txt_full_note = QTextEdit()
        self.txt_full_note.setPlaceholderText("Full note text will appear here after analysis.")
        self.txt_full_note.setReadOnly(True)

        results_splitter.addWidget(self.txt_chat)
        results_splitter.addWidget(self.txt_full_note)
        results_splitter.setSizes([400, 600])

        layout.addWidget(results_splitter)

class AnalyticsTab(QWidget):
    """
    UI for the 'Analytics Dashboard' tab.
    """
    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("From:"))
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        controls_layout.addWidget(self.date_start)
        controls_layout.addWidget(QLabel("To:"))
        self.date_end = QDateEdit()
        self.date_end.setDate(QDate.currentDate())
        controls_layout.addWidget(self.date_end)

        self.chk_filter_pt = QCheckBox("PT")
        self.chk_filter_ot = QCheckBox("OT")
        self.chk_filter_slp = QCheckBox("SLP")
        for chk in [self.chk_filter_pt, self.chk_filter_ot, self.chk_filter_slp]:
            chk.setChecked(True)
            controls_layout.addWidget(chk)

        btn_refresh = QPushButton("Refresh Analytics")
        _style_action_button(btn_refresh, font_size=11, bold=True, height=32)
        btn_refresh.clicked.connect(self.refresh_requested)
        controls_layout.addWidget(btn_refresh)
        controls_layout.addStretch(1)

        layout.addLayout(controls_layout)

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        stats_group = QGroupBox("Summary Statistics")
        stats_layout = QGridLayout(stats_group)
        self.lbl_total_runs = QLabel("N/A")
        self.lbl_avg_score = QLabel("N/A")
        self.lbl_avg_flags = QLabel("N/A")
        self.lbl_top_category = QLabel("N/A")
        stats_layout.addWidget(QLabel("Total Runs Analyzed:"), 0, 0)
        stats_layout.addWidget(self.lbl_total_runs, 0, 1)
        stats_layout.addWidget(QLabel("Average Compliance Score:"), 1, 0)
        stats_layout.addWidget(self.lbl_avg_score, 1, 1)
        stats_layout.addWidget(QLabel("Average Flags per Run:"), 2, 0)
        stats_layout.addWidget(self.lbl_avg_flags, 2, 1)
        stats_layout.addWidget(QLabel("Most Frequent Finding Category:"), 3, 0)
        stats_layout.addWidget(self.lbl_top_category, 3, 1)

        layout.addWidget(stats_group)
