"""
QuadrantWidget - A custom widget to display analysis findings in a 2x2
Eisenhower Matrix layout. This provides a clear, prioritized view of feedback.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QGroupBox,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from typing import List, Dict, Any

class QuadrantFindingWidget(QFrame):
    """A small, styled widget to represent a single finding, including its associated 7 Habit."""
    def __init__(self, title: str, text: str, habit: Dict[str, str] | None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QuadrantFindingWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-bottom: 8px;
                padding: 8px;
            }
            .habitLabel {
                font-size: 9px;
                color: #6c757d;
                font-style: italic;
                padding-top: 4px;
            }
            .habitName {
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)

        title_label = QLabel(f"<b>{title}</b>")
        title_label.setWordWrap(True)

        text_label = QLabel(text)
        text_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(text_label)

        if habit:
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(line)

            habit_name = habit.get("name", "N/A")
            habit_explanation = habit.get("explanation", "N/A")

            habit_label = QLabel(f"<span class='habitName'>Principle:</span> {habit_name} &mdash; {habit_explanation}")
            habit_label.setWordWrap(True)
            habit_label.setObjectName("habitLabel")
            layout.addWidget(habit_label)

        layout.setSpacing(4)

class QuadrantWidget(QWidget):
    """
    A widget that displays a list of findings in a 2x2 grid, representing
    the Eisenhower Matrix (Urgent/Important).
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.quadrants: Dict[str, QWidget] = {}
        self._init_ui()

    def _init_ui(self):
        """Initializes the four quadrants."""
        quadrant_definitions = {
            "Q1": ("Q1: Urgent & Important", "Critical issues needing immediate attention."),
            "Q2": ("Q2: Not Urgent & Important", "High-impact improvements to plan and schedule."),
            "Q3": ("Q3: Urgent & Not Important", "Low-impact tasks to delegate or minimize."),
            "Q4": ("Q4: Not Urgent & Not Important", "Minor suggestions or low-confidence findings."),
        }

        positions = [("Q1", 0, 0), ("Q2", 0, 1), ("Q3", 1, 0), ("Q4", 1, 1)]

        for name, (title, subtitle) in quadrant_definitions.items():
            group_box = QGroupBox(title)
            group_box.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #ced4da;
                    border-radius: 6px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                }
            """)

            main_vbox = QVBoxLayout(group_box)

            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-style: italic; color: #6c757d; font-size: 10px;")
            subtitle_label.setWordWrap(True)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            scroll_area.setWidget(content_widget)

            main_vbox.addWidget(subtitle_label)
            main_vbox.addWidget(scroll_area)

            self.quadrants[name] = content_widget

            row, col = next(p[1:] for p in positions if p[0] == name)
            self.grid_layout.addWidget(group_box, row, col)

    def clear_findings(self):
        """Removes all findings from all quadrants."""
        for quadrant_name, content_widget in self.quadrants.items():
            layout = content_widget.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def display_findings(self, findings: List[Dict[str, Any]]):
        """Populates the quadrants with a list of findings."""
        self.clear_findings()

        if not findings:
            # Display a message if there are no findings
            self.quadrants["Q2"].layout().addWidget(QLabel("No compliance findings were identified. Excellent work!"))
            return

        for finding in findings:
            quadrant_name = finding.get("quadrant", "Q4") # Default to Q4

            content_widget = self.quadrants.get(quadrant_name)
            if content_widget:
                title = finding.get("issue_title", "Unnamed Finding")
                text = finding.get("personalized_tip", "No details provided.")
                habit = finding.get("habit")

                finding_widget = QuadrantFindingWidget(title, text, habit)
                content_widget.layout().addWidget(finding_widget)

        # Add a stretch to the bottom to keep items packed at the top
        for _, content_widget in self.quadrants.items():
            content_widget.layout().addStretch(1)

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Example usage:
    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)

    quadrant_view = QuadrantWidget()
    main_layout.addWidget(quadrant_view)

    # Example findings data
    example_findings = [
        {"issue_title": "Missing Signature", "personalized_tip": "The document must be signed.", "quadrant": "Q1"},
        {"issue_title": "Medical Necessity Not Justified", "personalized_tip": "Clearly state why continued therapy is required.", "quadrant": "Q2"},
        {"issue_title": "Vague Goal", "personalized_tip": "Make the goal 'improve strength' more specific, e.g., 'improve strength by 1 grade'.", "quadrant": "Q2"},
        {"issue_title": "Incorrect Date Format", "personalized_tip": "Use MM/DD/YYYY format.", "quadrant": "Q3"},
        {"issue_title": "Minor Typo", "personalized_tip": "Correct 'teh' to 'the'.", "quadrant": "Q4"},
    ]

    quadrant_view.display_findings(example_findings)

    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec())