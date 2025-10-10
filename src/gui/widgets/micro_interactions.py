"""Micro-interactions and Animations - Smooth transitions and visual feedback."""

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSequentialAnimationGroup,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QPushButton, QWidget


class AnimatedButton(QPushButton):
    """Button with smooth hover and click animations."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setup_animations()
        self.original_color = None

    def setup_animations(self):
        """Setup hover and click animations."""
        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Click animation
        self.click_animation = QPropertyAnimation(self, b"geometry")
        self.click_animation.setDuration(100)
        self.click_animation.setEasingCurve(QEasingCurve.Type.OutBack)

        # Color animation effect
        self.color_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.color_effect)

        self.opacity_animation = QPropertyAnimation(self.color_effect, b"opacity")
        self.opacity_animation.setDuration(200)

    def enterEvent(self, event):
        """Handle mouse enter with animation."""
        super().enterEvent(event)

        # Slight scale up on hover
        current_rect = self.geometry()
        hover_rect = QRect(
            current_rect.x() - 2,
            current_rect.y() - 1,
            current_rect.width() + 4,
            current_rect.height() + 2)

        self.hover_animation.setStartValue(current_rect)
        self.hover_animation.setEndValue(hover_rect)
        self.hover_animation.start()

        # Fade effect
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.9)
        self.opacity_animation.start()

    def leaveEvent(self, event):
        """Handle mouse leave with animation."""
        super().leaveEvent(event)

        # Return to original size
        current_rect = self.geometry()
        original_rect = QRect(
            current_rect.x() + 2,
            current_rect.y() + 1,
            current_rect.width() - 4,
            current_rect.height() - 2)

        self.hover_animation.setStartValue(current_rect)
        self.hover_animation.setEndValue(original_rect)
        self.hover_animation.start()

        # Restore opacity
        self.opacity_animation.setStartValue(0.9)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def mousePressEvent(self, event):
        """Handle mouse press with click animation."""
        super().mousePressEvent(event)

        # Quick scale down on click
        current_rect = self.geometry()
        click_rect = QRect(
            current_rect.x() + 1,
            current_rect.y() + 1,
            current_rect.width() - 2,
            current_rect.height() - 2)

        self.click_animation.setStartValue(current_rect)
        self.click_animation.setEndValue(click_rect)
        self.click_animation.start()


class FadeInWidget(QWidget):
    """Widget that fades in when shown."""

    fade_completed = Signal()

    def setup_fade_animation(self):
        """Setup fade in animation."""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.finished.connect(self.fade_completed.emit)

    def fade_in(self):
        """Start fade in animation."""
        self.fade_animation.start()

    def fade_out(self, callback=None):
        """Start fade out animation."""
        fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out_animation.setDuration(200)
        fade_out_animation.setStartValue(1.0)
        fade_out_animation.setEndValue(0.0)
        fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        if callback:
            fade_out_animation.finished.connect(callback)

        fade_out_animation.start()


class SlideInWidget(QWidget):
    """Widget that slides in from a direction."""

    slide_completed = Signal()

    def setup_slide_animation(self):
        """Setup slide animation."""
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(400)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.slide_animation.finished.connect(self.slide_completed.emit)

    def slide_in(self):
        """Start slide in animation."""
        if not self.parent():
            return

        parent_rect = self.parent().rect()
        final_rect = self.geometry()

        # Calculate start position based on direction
        if self.direction == "left":
            start_rect = QRect(
                -final_rect.width(),
                final_rect.y(),
                final_rect.width(),
                final_rect.height())
        elif self.direction == "right":
            start_rect = QRect(
                parent_rect.width(),
                final_rect.y(),
                final_rect.width(),
                final_rect.height())
        elif self.direction == "top":
            start_rect = QRect(
                final_rect.x(),
                -final_rect.height(),
                final_rect.width(),
                final_rect.height())
        else:  # bottom
            start_rect = QRect(
                final_rect.x(),
                parent_rect.height(),
                final_rect.width(),
                final_rect.height())

        self.setGeometry(start_rect)
        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(final_rect)
        self.slide_animation.start()


class PulseAnimation(QWidget):
    """Widget with pulsing animation for notifications."""

    def setup_pulse_animation(self):
        """Setup pulse animation."""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.pulse_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setStartValue(1.0)
        self.pulse_animation.setEndValue(0.3)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)

        # Create looping animation
        self.pulse_group = QSequentialAnimationGroup()

        # Fade out
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(500)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.5)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutSine)

        # Fade in
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(500)
        fade_in.setStartValue(0.5)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutSine)

        self.pulse_group.addAnimation(fade_out)
        self.pulse_group.addAnimation(fade_in)
        self.pulse_group.setLoopCount(-1)  # Infinite loop

    def start_pulse(self):
        """Start pulsing animation."""
        if not self.is_pulsing:
            self.is_pulsing = True
            self.pulse_group.start()

    def stop_pulse(self):
        """Stop pulsing animation."""
        if self.is_pulsing:
            self.is_pulsing = False
            self.pulse_group.stop()
            self.opacity_effect.setOpacity(1.0)


class LoadingSpinner(QLabel):
    """Animated loading spinner."""

    def setup_spinner(self):
        """Setup spinner animation."""
        self.setFixedSize(self.size, self.size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Rotation animation
        self.rotation_animation = QPropertyAnimation(self, b"rotation")
        self.rotation_animation.setDuration(1000)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)
        self.rotation_animation.valueChanged.connect(self.update_rotation)

    def update_rotation(self, angle):
        """Update spinner rotation."""
        self.angle = angle
        self.update()

    def start_spinning(self):
        """Start spinner animation."""
        self.rotation_animation.start()
        self.show()

    def stop_spinning(self):
        """Stop spinner animation."""
        self.rotation_animation.stop()
        self.hide()

    def paintEvent(self, event):
        """Paint the spinner."""
        from PySide6.QtGui import QPainter, QPen

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw spinner
        pen = QPen(QColor(59, 130, 246))  # Blue color
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Draw arc
        rect = self.rect().adjusted(4, 4, -4, -4)
        painter.drawArc(rect, self.angle * 16, 120 * 16)


class ProgressRipple(QWidget):
    """Ripple effect for progress indication."""

    def setup_ripple_timer(self):
        """Setup ripple animation timer."""
        self.ripple_timer = QTimer()
        self.ripple_timer.timeout.connect(self.update_ripples)
        self.ripple_timer.start(50)  # 20 FPS

    def add_ripple(self, position: QPoint):
        """Add a new ripple at position."""
        ripple = {"center": position, "radius": 0, "opacity": 1.0, "max_radius": 100}
        self.ripples.append(ripple)

    def update_ripples(self):
        """Update ripple animations."""
        for ripple in self.ripples[:]:
            ripple["radius"] += 3
            ripple["opacity"] -= 0.02

            if ripple["opacity"] <= 0 or ripple["radius"] >= ripple["max_radius"]:
                self.ripples.remove(ripple)

        if self.ripples:
            self.update()

    def setup_tooltip(self):
        """Setup enhanced tooltip."""
        self.setWindowFlags(Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Styling
        self.setStyleSheet(
            """
            QLabel {
                background-color: rgba(30, 41, 59, 0.95);
                color: white;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
                max-width: 250px;
            }
        """)

        self.setText(self.content)
        self.setWordWrap(True)
        self.adjustSize()

        # Fade in animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_animated(self, position: QPoint):
        """Show tooltip with animation at position."""
        self.move(position)
        self.show()
        self.fade_in_animation.start()

        # Auto-hide after 3 seconds
        QTimer.singleShot(3000, self.hide)
