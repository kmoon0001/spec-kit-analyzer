"""
Responsive Layout System - Adaptive UI that scales to different screen sizes.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QSplitter, QScrollArea
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QResizeEvent, QFont


class ResponsiveWidget(QWidget):
    """Base widget that adapts to screen size changes."""

    breakpoint_changed = Signal(str)  # 'mobile', 'tablet', 'desktop', 'large'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_breakpoint = "desktop"
        self.breakpoints = {
            "mobile": 480,
            "tablet": 768,
            "desktop": 1024,
            "large": 1440,
        }

        # Responsive timer to debounce resize events
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.handle_responsive_change)

    def resizeEvent(self, event: QResizeEvent | None):
        """Handle resize events with debouncing."""
        super().resizeEvent(event)
        self.resize_timer.start(100)  # 100ms debounce

    def handle_responsive_change(self):
        """Handle responsive breakpoint changes."""
        width = self.width()
        new_breakpoint = self.get_breakpoint(width)

        if new_breakpoint != self.current_breakpoint:
            self.current_breakpoint = new_breakpoint
            self.breakpoint_changed.emit(new_breakpoint)
            self.adapt_to_breakpoint(new_breakpoint)

    def get_breakpoint(self, width: int) -> str:
        """Determine current breakpoint based on width."""
        if width < self.breakpoints["mobile"]:
            return "mobile"
        elif width < self.breakpoints["tablet"]:
            return "tablet"
        elif width < self.breakpoints["desktop"]:
            return "desktop"
        else:
            return "large"

    def adapt_to_breakpoint(self, breakpoint: str):
        """Override in subclasses to handle breakpoint changes."""
        pass

    def get_responsive_font_size(self, base_size: int) -> int:
        """Get font size adjusted for current breakpoint."""
        multipliers = {"mobile": 0.85, "tablet": 0.9, "desktop": 1.0, "large": 1.1}
        return int(base_size * multipliers.get(self.current_breakpoint, 1.0))

    def get_responsive_spacing(self, base_spacing: int) -> int:
        """Get spacing adjusted for current breakpoint."""
        multipliers = {"mobile": 0.7, "tablet": 0.85, "desktop": 1.0, "large": 1.2}
        return int(base_spacing * multipliers.get(self.current_breakpoint, 1.0))


class VirtualScrollArea(QScrollArea):
    """Virtual scrolling for large datasets."""

    def __init__(self, item_height: int = 50, parent=None):
        super().__init__(parent)
        self.item_height = item_height
        self.items: list = []
        self.visible_items: dict = {}
        self.buffer_size = 5  # Extra items to render outside viewport

        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.setWidget(self.content_widget)

        # Connect scroll events
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            scrollbar.valueChanged.connect(self.update_visible_items)

    def set_items(self, items: list):
        """Set the list of items to display."""
        self.items = items
        self.update_content_size()
        self.update_visible_items()

    def update_content_size(self):
        """Update the content widget size based on item count."""
        total_height = len(self.items) * self.item_height
        self.content_widget.setMinimumHeight(total_height)

    def update_visible_items(self):
        """Update which items are visible in the viewport."""
        if not self.items:
            return

        viewport_top = self.verticalScrollBar().value()
        viewport_height = self.viewport().height()
        viewport_bottom = viewport_top + viewport_height

        # Calculate visible range with buffer
        first_visible = max(0, (viewport_top // self.item_height) - self.buffer_size)
        last_visible = min(
            len(self.items) - 1,
            (viewport_bottom // self.item_height) + self.buffer_size,
        )

        # Remove items outside visible range
        for index in list(self.visible_items.keys()):
            if index < first_visible or index > last_visible:
                widget = self.visible_items.pop(index)
                self.content_layout.removeWidget(widget)
                widget.deleteLater()

        # Add items in visible range
        for index in range(first_visible, last_visible + 1):
            if index not in self.visible_items:
                item_widget = self.create_item_widget(self.items[index], index)
                self.visible_items[index] = item_widget

                # Insert at correct position
                insert_position = sum(1 for i in self.visible_items.keys() if i < index)
                self.content_layout.insertWidget(insert_position, item_widget)

    def create_item_widget(self, item_data, index: int) -> QWidget:
        """Override in subclasses to create item widgets."""
        from PySide6.QtWidgets import QLabel

        widget = QLabel(f"Item {index}: {str(item_data)}")
        widget.setFixedHeight(self.item_height)
        return widget


class AdaptiveGridLayout(QGridLayout):
    """Grid layout that adapts column count based on available space."""

    def __init__(self, min_item_width: int = 200, parent=None):
        super().__init__(parent)
        self.min_item_width = min_item_width
        self.items: list = []

    def add_adaptive_widget(self, widget: QWidget):
        """Add widget that will be positioned adaptively."""
        self.items.append(widget)
        self.relayout_items()

    def relayout_items(self):
        """Relayout items based on available width."""
        if not self.items or not self.parent():
            return

        # Clear current layout
        for i in reversed(range(self.count())):
            self.itemAt(i).widget().setParent(None)

        # Calculate optimal column count
        available_width = self.parent().width() - 40  # Account for margins
        columns = max(1, available_width // self.min_item_width)

        # Add items to grid
        for i, widget in enumerate(self.items):
            row = i // columns
            col = i % columns
            self.addWidget(widget, row, col)


class ScalableFont:
    """Font scaling system for accessibility."""

    @staticmethod
    def get_scaled_font(base_size: int, scale_factor: float = 1.0) -> QFont:
        """Get font scaled by system preferences."""
        font = QFont()
        scaled_size = max(8, int(base_size * scale_factor))
        font.setPointSize(scaled_size)
        return font

    @staticmethod
    def get_system_scale_factor() -> float:
        """Get system font scale factor."""
        # This would integrate with system accessibility settings
        # For now, return 1.0 (could be made configurable)
        return 1.0

    @staticmethod
    def apply_font_scaling(widget: QWidget, base_size: int):
        """Apply font scaling to a widget."""
        scale_factor = ScalableFont.get_system_scale_factor()
        font = ScalableFont.get_scaled_font(base_size, scale_factor)
        widget.setFont(font)


class ResponsiveSplitter(QSplitter):
    """Splitter that adapts orientation based on screen size."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mobile_threshold = 768
        self.setChildrenCollapsible(False)

    def resizeEvent(self, event):
        """Handle resize to change orientation if needed."""
        super().resizeEvent(event)

        width = self.width()
        if width < self.mobile_threshold:
            # Stack vertically on small screens
            if self.orientation() != Qt.Orientation.Vertical:
                self.setOrientation(Qt.Orientation.Vertical)
        else:
            # Side by side on larger screens
            if self.orientation() != Qt.Orientation.Horizontal:
                self.setOrientation(Qt.Orientation.Horizontal)


class AccessibleWidget(QWidget):
    """Base widget with accessibility features."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_accessibility()

    def setup_accessibility(self):
        """Setup accessibility features."""
        # Enable focus
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

        # Set accessible properties
        self.setAccessibleName(self.__class__.__name__)

    def set_accessible_description(self, description: str):
        """Set accessible description for screen readers."""
        self.setAccessibleDescription(description)

    def set_accessible_role(self, role: str):
        """Set accessible role."""
        # Map common roles to Qt accessibility
        # This would be implemented with proper Qt accessibility APIs
        pass


class HighContrastSupport:
    """High contrast mode support for accessibility."""

    @staticmethod
    def is_high_contrast_enabled() -> bool:
        """Check if system high contrast mode is enabled."""
        # This would check system settings
        return False

    @staticmethod
    def get_high_contrast_stylesheet() -> str:
        """Get high contrast stylesheet."""
        return """
        * {
            background-color: black;
            color: white;
            border: 2px solid white;
        }

        QPushButton {
            background-color: #000080;
            color: white;
            border: 2px solid white;
        }

        QPushButton:hover {
            background-color: #0000FF;
        }

        QLineEdit, QTextEdit {
            background-color: white;
            color: black;
            border: 2px solid black;
        }
        """
