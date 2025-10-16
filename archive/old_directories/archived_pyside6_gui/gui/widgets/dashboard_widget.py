"""Dashboard widget for displaying compliance analytics and overview metrics."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget


class DashboardWidget(QWidget):
    """A widget to display an overview of compliance metrics, including
    key performance indicators and recent analysis activity.
    """

    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        """Construct the main UI components of the dashboard."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("Compliance Dashboard", self)
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(self.refresh_button)
        main_layout.addLayout(header_layout)

        # --- KPIs Section ---
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        self.total_docs_label = self._create_kpi_box("Total Documents", "0")
        self.avg_score_label = self._create_kpi_box("Avg. Compliance", "0.0%")
        kpi_layout.addWidget(self.total_docs_label)
        kpi_layout.addWidget(self.avg_score_label)
        main_layout.addLayout(kpi_layout)

        # --- Compliance Breakdown Section ---
        self.breakdown_layout = QGridLayout()
        self.breakdown_layout.setSpacing(10)
        main_layout.addLayout(self.breakdown_layout)

        main_layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply theme-aware stylesheets to the dashboard components."""
        self.setStyleSheet("""
            QFrame#kpiBox {
                border: 1px solid palette(mid);
                border-radius: 5px;
                background-color: palette(base);
            }
            QProgressBar {
                border: 1px solid palette(mid);
                border-radius: 4px;
                text-align: center;
                background-color: palette(base);
            }
            QProgressBar::chunk {
                background-color: palette(highlight);
                border-radius: 3px;
                margin: 1px;
            }
        """)

    def _create_kpi_box(self, title: str, initial_value: str) -> QWidget:
        """Helper to create a styled box for a key performance indicator."""
        box = QFrame(self)
        box.setFrameShape(QFrame.Shape.StyledPanel)
        box.setFrameShadow(QFrame.Shadow.Raised)
        box.setObjectName("kpiBox")

        layout = QVBoxLayout(box)
        title_label = QLabel(title, box)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(initial_value, box)
        font = value_label.font()
        font.setPointSize(24)
        font.setBold(True)
        value_label.setFont(font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName("kpiValueLabel")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        box.setProperty("value_label", value_label)
        return box

    def load_data(self, data: dict[str, Any]) -> None:
        """Populates the dashboard with data from the API."""
        total_docs = data.get("total_documents_analyzed", 0)
        avg_score = data.get("overall_compliance_score", 0.0)

        total_docs_value_label = self.total_docs_label.property("value_label")
        total_docs_value_label.setText(str(total_docs))

        avg_score_value_label = self.avg_score_label.property("value_label")
        avg_score_value_label.setText(f"{avg_score}%")

        self._clear_layout(self.breakdown_layout)
        categories = data.get("compliance_by_category", {})
        row = 0
        for name, score in sorted(categories.items()):
            label = QLabel(name, self)
            progress = QProgressBar(self)
            progress.setValue(int(score))
            progress.setFormat(f"{score}%")
            progress.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.breakdown_layout.addWidget(label, row, 0)
            self.breakdown_layout.addWidget(progress, row, 1)
            row += 1

    def _clear_layout(self, layout: QGridLayout) -> None:
        """Removes all widgets from a QGridLayout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


__all__ = ["DashboardWidget"]
