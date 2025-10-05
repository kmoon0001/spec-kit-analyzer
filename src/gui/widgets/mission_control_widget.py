
from __future__ import annotations

from typing import Any, Iterable, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MissionControlWidget(QWidget):
    """Mission control dashboard summarising compliance performance."""

    start_analysis_requested = Signal()
    review_document_requested = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._recent_docs: list[dict[str, Any]] = []
        self._flagged_docs: list[dict[str, Any]] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update_overview(self, data: dict[str, Any]) -> None:
        score = (
            data.get("average_compliance")
            or data.get("compliance_score")
            or data.get("score")
            or 0
        )
        self.compliance_score_label.setText(f"{float(score):.0f}%")

        top_habits: Iterable[str] = (
            data.get("top_habits")
            or data.get("focus_areas")
            or data.get("habit_opportunities")
            or []
        )
        self._populate_list(
            self.habits_list,
            top_habits,
            empty_message="No trends identified yet."
        )

        self._recent_docs = list(data.get("recent_documents") or [])
        self._populate_documents(
            self.recent_list,
            self._recent_docs,
            empty_message="No recent documents."
        )

        self._flagged_docs = list(data.get("flagged_documents") or [])
        self._populate_documents(
            self.flagged_list,
            self._flagged_docs,
            empty_message="No flagged documents."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header = QLabel("Mission Control")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        layout.addWidget(header)

        summary_frame = self._build_summary_frame()
        layout.addWidget(summary_frame)

        lists_frame = self._build_lists_frame()
        layout.addWidget(lists_frame, stretch=1)

        layout.addStretch(1)

    def _build_summary_frame(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("missionControlSummary")
        frame.setFrameShape(QFrame.StyledPanel)
        grid = QGridLayout(frame)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(16)

        title = QLabel("Overall Compliance")
        title.setFont(QFont("Segoe UI", 10, QFont.Medium))
        grid.addWidget(title, 0, 0, Qt.AlignLeft)

        self.compliance_score_label = QLabel("--%")
        self.compliance_score_label.setFont(QFont("Segoe UI", 36, QFont.Bold))
        self.compliance_score_label.setStyleSheet("color: #2563eb;")
        grid.addWidget(self.compliance_score_label, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)

        action_container = QHBoxLayout()
        action_container.setSpacing(12)

        self.start_button = QPushButton("Start New Analysis")
        self.start_button.setObjectName("startAnalysisButton")
        self.start_button.clicked.connect(self.start_analysis_requested.emit)
        action_container.addWidget(self.start_button)

        self.review_button = QPushButton("Review Flagged Documents")
        self.review_button.clicked.connect(self._handle_review_flagged)
        action_container.addWidget(self.review_button)

        action_container.addStretch(1)
        grid.addLayout(action_container, 1, 1)

        habits_container = QVBoxLayout()
        habits_title = QLabel("Focus Habits")
        habits_title.setFont(QFont("Segoe UI", 10, QFont.Medium))
        habits_container.addWidget(habits_title)

        self.habits_list = QListWidget(self)
        self.habits_list.setObjectName("habitsList")
        self.habits_list.setMaximumHeight(120)
        habits_container.addWidget(self.habits_list)
        grid.addLayout(habits_container, 0, 2, 2, 1)

        frame.setStyleSheet(
            "#missionControlSummary {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8fafc, stop:1 #e0f2fe);"
            "  border-radius: 12px;"
            "}"
            "#startAnalysisButton {"
            "  background-color: #0ea5e9;"
            "  color: white;"
            "  padding: 10px 18px;"
            "  border-radius: 8px;"
            "  font-weight: 600;"
            "}"
            "#startAnalysisButton:hover {"
            "  background-color: #0284c7;"
            "}"
        )
        return frame

    def _build_lists_frame(self) -> QWidget:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setSpacing(16)

        recent_container, self.recent_list = self._create_list_panel(
            "Recent Documents",
            "Your 5 most recent analyses."
        )
        layout.addWidget(recent_container, stretch=1)

        flagged_container, self.flagged_list = self._create_list_panel(
            "Flagged Documents",
            "Notes needing immediate attention."
        )
        layout.addWidget(flagged_container, stretch=1)

        return container

    def _create_list_panel(self, title: str, subtitle: str) -> Tuple[QWidget, QListWidget]:
        wrapper = QFrame(self)
        wrapper.setFrameShape(QFrame.NoFrame)
        wrapper.setStyleSheet(
            "QFrame {"
            "  background: #ffffff;"
            "  border: 1px solid #e2e8f0;"
            "  border-radius: 12px;"
            "}"
        )
        outer_layout = QVBoxLayout(wrapper)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(8)

        title_label = QLabel(title, wrapper)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Medium))
        outer_layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle, wrapper)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("color: #64748b; font-size: 11px;")
        outer_layout.addWidget(subtitle_label)

        list_widget = QListWidget(wrapper)
        outer_layout.addWidget(list_widget)

        host = QWidget(self)
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.addWidget(wrapper)

        return host, list_widget

    def _populate_list(self, list_widget: QListWidget, items: Iterable[str], *, empty_message: str) -> None:
        list_widget.clear()
        has_items = False
        for text in items:
            has_items = True
            list_widget.addItem(str(text))
        if not has_items:
            placeholder = QListWidgetItem(empty_message)
            placeholder.setFlags(Qt.NoItemFlags)
            list_widget.addItem(placeholder)

    def _populate_documents(
        self,
        list_widget: QListWidget,
        documents: list[dict[str, Any]],
        *,
        empty_message: str,
    ) -> None:
        try:
            list_widget.itemActivated.disconnect()
        except (TypeError, RuntimeError):
            pass

        list_widget.clear()
        if not documents:
            placeholder = QListWidgetItem(empty_message)
            placeholder.setFlags(Qt.NoItemFlags)
            list_widget.addItem(placeholder)
            return

        for doc in documents[:5]:
            title = doc.get("title") or doc.get("name") or doc.get("document_name")
            if not title:
                title = f"Document {doc.get('id', '-') }"
            subtitle = doc.get("created_at") or doc.get("updated_at") or doc.get("discipline")
            display_text = title if not subtitle else f"{title}
{subtitle}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, doc)
            list_widget.addItem(item)

        list_widget.itemActivated.connect(self._handle_item_activated)

    def _handle_review_flagged(self) -> None:
        if not self._flagged_docs:
            return
        self.review_document_requested.emit(self._flagged_docs[0])

    def _handle_item_activated(self, item: QListWidgetItem) -> None:
        payload = item.data(Qt.UserRole)
        if isinstance(payload, dict):
            self.review_document_requested.emit(payload)
