"""
Professional styling for Therapy Compliance Analyzer
"""

MAIN_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: #f8fafc;
}

/* Menu Bar */
QMenuBar {
    background-color: #1e40af;
    color: white;
    padding: 8px;
    font-size: 14px;
    font-weight: 500;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 16px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #2563eb;
}

QMenu {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}

/* Tab Widget */
QTabWidget::pane {
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    background-color: white;
    padding: 16px;
}

QTabBar::tab {
    background-color: #e2e8f0;
    color: #475569;
    padding: 12px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 14px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: white;
    color: #1e40af;
    border-bottom: 3px solid #2563eb;
}

QTabBar::tab:hover {
    background-color: #cbd5e1;
}

/* Group Boxes */
QGroupBox {
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px;
    background-color: white;
    font-weight: 600;
    font-size: 14px;
    color: #1e40af;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    background-color: white;
    border-radius: 4px;
}

/* Buttons */
QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #2563eb;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #cbd5e1;
    color: #94a3b8;
}

/* Primary Button (Run Analysis) */
QPushButton#primaryButton {
    background-color: #10b981;
    font-size: 14px;
    padding: 12px 32px;
}

QPushButton#primaryButton:hover {
    background-color: #059669;
}

/* Danger Button (Stop) */
QPushButton#dangerButton {
    background-color: #ef4444;
}

QPushButton#dangerButton:hover {
    background-color: #dc2626;
}

/* Secondary Button */
QPushButton#secondaryButton {
    background-color: #64748b;
}

QPushButton#secondaryButton:hover {
    background-color: #475569;
}

/* Text Edit / Text Browser */
QTextEdit, QTextBrowser {
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    background-color: white;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
}

QTextEdit:focus, QTextBrowser:focus {
    border-color: #3b82f6;
}

/* Combo Box */
QComboBox {
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    background-color: white;
    min-height: 36px;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: url(none);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #64748b;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    background-color: white;
    selection-background-color: #dbeafe;
    selection-color: #1e40af;
    padding: 4px;
}

/* Progress Bar */
QProgressBar {
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
    font-size: 13px;
    background-color: #f1f5f9;
    min-height: 28px;
}

QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 6px;
}

/* Table Widget */
QTableWidget {
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    background-color: white;
    gridline-color: #e2e8f0;
    font-size: 13px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #f1f5f9;
}

QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #1e40af;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    font-weight: 600;
    font-size: 13px;
}

QHeaderView::section:first {
    border-top-left-radius: 8px;
}

QHeaderView::section:last {
    border-top-right-radius: 8px;
}

/* Labels */
QLabel {
    color: #334155;
    font-size: 13px;
}

QLabel#headerLabel {
    font-size: 24px;
    font-weight: 700;
    color: #1e40af;
    padding: 16px;
}

QLabel#scoreLabel {
    font-size: 18px;
    font-weight: 700;
    color: #10b981;
}

/* Status Bar */
QStatusBar {
    background-color: #f1f5f9;
    color: #475569;
    border-top: 1px solid #e2e8f0;
    padding: 8px;
    font-size: 12px;
}

/* Splitter */
QSplitter::handle {
    background-color: #e2e8f0;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #3b82f6;
}

/* Scroll Bar */
QScrollBar:vertical {
    border: none;
    background-color: #f1f5f9;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #f1f5f9;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94a3b8;
}

/* Tool Button */
QToolButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QToolButton:hover {
    background-color: #2563eb;
}

QToolButton::menu-indicator {
    image: none;
}
"""

DARK_THEME = """
/* Dark Theme */
QMainWindow {
    background-color: #0f172a;
}

QMenuBar {
    background-color: #1e293b;
    color: #e2e8f0;
}

QMenuBar::item:selected {
    background-color: #334155;
}

QMenu {
    background-color: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
}

QMenu::item:selected {
    background-color: #334155;
}

QTabWidget::pane {
    border: 2px solid #334155;
    background-color: #1e293b;
}

QTabBar::tab {
    background-color: #334155;
    color: #94a3b8;
}

QTabBar::tab:selected {
    background-color: #1e293b;
    color: #60a5fa;
}

QGroupBox {
    border: 2px solid #334155;
    background-color: #1e293b;
    color: #60a5fa;
}

QPushButton {
    background-color: #3b82f6;
}

QPushButton:hover {
    background-color: #2563eb;
}

QTextEdit, QTextBrowser {
    border: 2px solid #334155;
    background-color: #1e293b;
    color: #e2e8f0;
}

QComboBox {
    border: 2px solid #334155;
    background-color: #1e293b;
    color: #e2e8f0;
}

QTableWidget {
    border: 2px solid #334155;
    background-color: #1e293b;
    color: #e2e8f0;
    gridline-color: #334155;
}

QHeaderView::section {
    background-color: #334155;
    color: #60a5fa;
}

QLabel {
    color: #e2e8f0;
}

QStatusBar {
    background-color: #1e293b;
    color: #94a3b8;
    border-top: 1px solid #334155;
}
"""
