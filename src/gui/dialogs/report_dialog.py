import logging
import urllib.parse
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QDialogButtonBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QUrl

# Local imports
from src.core.chat_service import ChatService
from .chat_dialog import ChatDialog

logger = logging.getLogger(__name__)


class ReportDialog(QDialog):
    """
    A dialog to display an HTML report, handle chat links, and provide a print option.
    """

    def __init__(self, report_html: str, chat_service: ChatService, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Report")
        self.setGeometry(150, 150, 900, 700)

        self.chat_service = chat_service

        self.main_layout = QVBoxLayout(self)

        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setHtml(report_html)
        # Ensure links are not opened externally, so we can handle them
        self.report_display.setOpenExternalLinks(False)
        self.main_layout.addWidget(self.report_display)

        self.button_box = QDialogButtonBox()
        self.print_button = QPushButton("Print to PDF")
        self.button_box.addButton(
            self.print_button, QDialogButtonBox.ButtonRole.ActionRole
        )
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        self.main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.print_button.clicked.connect(self.print_to_pdf)
        self.report_display.anchorClicked.connect(self.handle_anchor_click)
        self.button_box.rejected.connect(self.reject)

    def handle_anchor_click(self, url: QUrl):
        """Handles clicks on links within the report, specifically for chat."""
        if url.scheme() == "chat":
            if not self.chat_service:
                QMessageBox.critical(self, "Error", "Chat service is not available.")
                return

            initial_context = urllib.parse.unquote(url.path())
            chat_dialog = ChatDialog(
                initial_context=initial_context,
                chat_service=self.chat_service,
                parent=self,
            )
            chat_dialog.exec()
        else:
            logger.warning(f"Clicked on an unhandled link scheme: {url.scheme()}")

    def print_to_pdf(self):
        """Opens a file dialog to save the report content as a PDF."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report as PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            try:
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)

                self.report_display.document().print(printer)
                logger.info(f"Report successfully saved to {file_path}")
            except Exception as e:
                logger.error(f"Failed to print report to PDF: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Could not save PDF: {e}")
