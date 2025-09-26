from PyQt6.QtWidgets import (
    QPushButton, 
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QComboBox,
    QLabel,
    QGroupBox
)
from PyQt6.QtCore import Qt

class ControlPanel(QGroupBox):
    def __init__(self, main_window):
        super().__init__("Controls")
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        controls_layout = QVBoxLayout(self)

        # File operations
        file_ops_layout = QHBoxLayout()
        self.upload_button = QPushButton('Upload Document')
        self.upload_button.setToolTip("Upload a document for analysis.")
        self.upload_button.clicked.connect(self.main_window.open_file_dialog)
        file_ops_layout.addWidget(self.upload_button)
        self.clear_button = QPushButton('Clear Display')
        self.clear_button.setToolTip("Clear the document and analysis results.")
        self.clear_button.clicked.connect(self.main_window.clear_display)
        file_ops_layout.addWidget(self.clear_button)
        controls_layout.addLayout(file_ops_layout)

        # Analysis options
        analysis_ops_layout = QHBoxLayout()

        discipline_layout = QVBoxLayout()
        discipline_layout.addWidget(QLabel("Discipline:"))
        self.discipline_combo = QComboBox()
        self.discipline_combo.setToolTip("Select the discipline for analysis.")
        self.discipline_combo.addItems(["All", "PT", "OT", "SLP"])
        discipline_layout.addWidget(self.discipline_combo)
        analysis_ops_layout.addLayout(discipline_layout)

        rubric_layout = QVBoxLayout()
        rubric_layout.addWidget(QLabel("OR Select a Rubric:"))
        self.rubric_list_widget = QListWidget()
        self.rubric_list_widget.setToolTip("Select a rubric for analysis.")
        self.rubric_list_widget.setPlaceholderText("No rubric selected")
        self.rubric_list_widget.setMaximumHeight(100)
        rubric_layout.addWidget(self.rubric_list_widget)
        analysis_ops_layout.addLayout(rubric_layout)

        analysis_ops_layout.addStretch()

        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.setToolTip("Run the compliance analysis.")
        self.run_analysis_button.clicked.connect(self.main_window.run_analysis)
        analysis_ops_layout.addWidget(self.run_analysis_button, 0, Qt.AlignBottom)

        controls_layout.addLayout(analysis_ops_layout)
