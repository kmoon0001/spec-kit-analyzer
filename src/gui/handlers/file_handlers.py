"""File handling operations for the main window."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.gui.dialogs.batch_analysis_dialog import BatchAnalysisDialog

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow

logger = logging.getLogger(__name__)


class FileHandlers:
    """
    Handles file operations and document management for the application.

    This class encapsulates all file-related operations including document selection,
    file validation, content preview generation, and batch processing workflows.
    It provides a clean interface between the UI and file system operations while
    maintaining proper error handling and user feedback.

    Attributes:
        main_window: Reference to the main application window instance

    Supported File Types:
        - PDF documents (.pdf)
        - Microsoft Word documents (.docx, .doc)
        - Plain text files (.txt)
        - Markdown files (.md)
        - JSON files (.json)

    Example:
        >>> file_handlers = FileHandlers(main_window)
        >>> file_handlers.prompt_for_document()  # Open file selection dialog
        >>> file_handlers.prompt_for_folder()    # Open batch processing dialog
    """

    def __init__(self, main_window: MainApplicationWindow) -> None:
        """
        Initialize the file handlers with a reference to the main window.

        Args:
            main_window: The main application window instance that this handler
                        will operate on. Must be a fully initialized MainApplicationWindow
                        with file_display and run_analysis_button attributes.

        Raises:
            TypeError: If main_window is not a valid MainApplicationWindow instance.
        """
        if not hasattr(main_window, 'statusBar'):
            raise TypeError("main_window must be a valid MainApplicationWindow instance")
        self.main_window = main_window

    def prompt_for_document(self) -> None:
        """
        Open a file selection dialog for choosing a clinical document.

        This method presents a native file dialog to the user, allowing them to
        select a clinical document for compliance analysis. The dialog is pre-configured
        with appropriate file type filters and starts in the user's home directory.

        Supported file types are filtered to ensure compatibility with the document
        processing pipeline. If a file is selected, it automatically triggers the
        file loading and preview generation process.

        Side Effects:
            - Opens a native file selection dialog
            - If file selected, calls set_selected_file() to load the document
            - Updates UI state to reflect the selected document
            - Enables/disables analysis buttons based on file validity

        File Type Support:
            - PDF documents: Full text extraction with OCR fallback
            - Word documents: Native content extraction
            - Text files: Direct content loading
            - Markdown files: Plain text processing
            - JSON files: Structured data parsing

        Example:
            >>> file_handlers.prompt_for_document()
            # Opens file dialog, user selects document, UI updates automatically
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Select clinical document",
            str(Path.home()),
            "Documents (*.pdf *.docx *.txt *.md *.json)"
        )
        if file_path:
            self.set_selected_file(Path(file_path))

    def set_selected_file(self, file_path: Path) -> None:
        """Set the selected file and update UI accordingly."""
        if self.main_window.run_analysis_button:
            self.main_window.run_analysis_button.setEnabled(False)
        self.main_window._cached_preview_content = ""

        try:
            max_preview_chars = 2_000_000
            with open(file_path, encoding="utf-8", errors="ignore") as stream:
                content = stream.read(max_preview_chars)
        except FileNotFoundError:
            self.main_window.statusBar().showMessage(f"File not found: {file_path.name}", 5000)
            placeholder = f"Preview unavailable: {file_path.name} not found."
            self.main_window._selected_file = file_path
            self.main_window._cached_preview_content = placeholder
            if self.main_window.file_display:
                self.main_window.file_display.setPlainText(placeholder)
            if self.main_window.run_analysis_button:
                self.main_window.run_analysis_button.setEnabled(True)
            return
        except Exception as exc:
            self.main_window._selected_file = None
            error_message = f"Could not display preview: {exc}"
            if self.main_window.file_display:
                self.main_window.file_display.setPlainText(error_message)
            self.main_window.statusBar().showMessage(f"Failed to load {file_path.name}", 5000)
            return

        self.main_window._selected_file = file_path
        self.main_window._cached_preview_content = content

        # Show clear document status instead of confusing description
        file_size_mb = len(content) / (1024 * 1024)
        file_info = f"""✅ DOCUMENT READY FOR ANALYSIS

📄 {file_path.name}
📊 Size: {file_size_mb:.1f} MB ({len(content):,} characters)
📁 Location: {file_path.parent.name}/
📅 Modified: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}

✨ Document successfully loaded and ready for compliance analysis!
Click 'Run Analysis' to begin processing.
        """
        if self.main_window.file_display:
            self.main_window.file_display.setPlainText(file_info)
        self.main_window.statusBar().showMessage(f"✅ Document loaded: {self.main_window._selected_file.name}", 3000)
        if self.main_window.run_analysis_button:
            self.main_window.run_analysis_button.setEnabled(True)

    def prompt_for_folder(self) -> None:
        """Open folder dialog for batch analysis."""
        folder_path = QFileDialog.getExistingDirectory(
            self.main_window,
            "Select folder for batch analysis",
            str(Path.home())
        )
        if folder_path:
            analysis_data = {
                "discipline": self.main_window.rubric_selector.currentData() or "" if self.main_window.rubric_selector else "",
                "analysis_mode": "rubric",
            }
            dialog = BatchAnalysisDialog(folder_path, self.main_window.auth_token, analysis_data, self.main_window)
            dialog.exec()

    def export_report(self) -> None:
        """Export the current report to file."""
        if not self.main_window._current_payload:
            QMessageBox.information(self.main_window, "No report", "Run an analysis before exporting a report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save report",
            str(Path.home() / "compliance_report.html"),
            "HTML Files (*.html)",
        )
        if not file_path:
            return

        try:
            if hasattr(self.main_window, 'report_preview_browser') and self.main_window.report_preview_browser:
                Path(file_path).write_text(self.main_window.report_preview_browser.toHtml(), encoding='utf-8')
            else:
                # Fallback to generating report HTML
                from src.core.report_generator import ReportGenerator
                report_generator = ReportGenerator()
                analysis = self.main_window._current_payload.get("analysis", {})
                doc_name = self.main_window._selected_file.name if self.main_window._selected_file else "Document"
                report_html = report_generator.generate_html_report(analysis_result=analysis, doc_name=doc_name)
                Path(file_path).write_text(report_html, encoding='utf-8')

            self.main_window.statusBar().showMessage(f"Report exported to {file_path}", 5000)
        except Exception as e:
            QMessageBox.warning(self.main_window, "Export Failed", f"Failed to export report: {str(e)}")

    def export_report_pdf(self) -> None:
        """Export the current report as PDF."""
        if not self.main_window._current_payload:
            QMessageBox.information(self.main_window, "No Report", "No analysis report available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Export Report as PDF", "", "PDF Files (*.pdf)"
        )

        if file_path:
            try:
                import shutil

                from src.core.pdf_export_service import PDFExportService

                # Get HTML content from current payload
                html_content = self.main_window._current_payload.get("report_html", "")
                if not html_content:
                    QMessageBox.warning(self.main_window, "No Content", "Report HTML content not available.")
                    return

                # Initialize PDF export service
                pdf_service = PDFExportService(output_dir="temp/reports")

                # Get document name for metadata
                doc_name = self.main_window._current_payload.get("document_name", "Compliance Report")

                # Export to PDF
                result = pdf_service.export_to_pdf(
                    html_content=html_content,
                    document_name=doc_name,
                    filename=Path(file_path).stem,
                    metadata={
                        "title": f"Compliance Analysis - {doc_name}",
                        "author": "Therapy Compliance Analyzer",
                        "subject": "Clinical Documentation Compliance Report"
                    }
                )

                if result["success"]:
                    # Copy the generated PDF to the user's chosen location
                    shutil.copy2(result["pdf_path"], file_path)

                    self.main_window.statusBar().showMessage(f"✅ Report exported to: {file_path}", 5000)
                    QMessageBox.information(self.main_window, "Export Successful", f"Report exported successfully to:\n{file_path}")
                else:
                    error_msg = result.get("error", "Unknown error occurred")
                    QMessageBox.warning(self.main_window, "Export Failed", f"PDF export failed:\n{error_msg}\n\nTip: Install weasyprint for better PDF support:\npip install weasyprint")

            except Exception as e:
                logger.error("PDF export failed: %s", str(e))
                QMessageBox.warning(self.main_window, "Export Failed", f"Failed to export report: {str(e)}\n\nTip: Install weasyprint:\npip install weasyprint")

    def export_report_html(self) -> None:
        """Export the current report as HTML."""
        if not self.main_window._current_payload:
            QMessageBox.information(self.main_window, "No Report", "No analysis report available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Export Report as HTML", "", "HTML Files (*.html)"
        )

        if file_path:
            try:
                from src.core.report_generator import ReportGenerator
                report_generator = ReportGenerator()
                analysis = self.main_window._current_payload.get("analysis", {})
                doc_name = self.main_window._selected_file.name if self.main_window._selected_file else "Document"
                report_html = self.main_window._current_payload.get("report_html") or report_generator.generate_html_report(
                    analysis_result=analysis, doc_name=doc_name
                )

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_html)

                self.main_window.statusBar().showMessage(f"✅ Report exported to: {file_path}", 5000)
                QMessageBox.information(self.main_window, "Export Successful", f"Report exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self.main_window, "Export Failed", f"Failed to export report: {str(e)}")

    def open_document_preview(self) -> None:
        """Open document preview in a popup window."""
        if not self.main_window._selected_file:
            QMessageBox.information(self.main_window, "No Document", "No document selected to preview.")
            return

        # Create popup dialog
        from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

        from src.gui.widgets.medical_theme import medical_theme
        from src.gui.widgets.micro_interactions import AnimatedButton

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle(f"📄 Document Preview - {self.main_window._selected_file.name}")
        # Make dialog responsive to parent window size
        parent_size = self.main_window.size()
        dialog_width = min(900, int(parent_size.width() * 0.75))
        dialog_height = min(700, int(parent_size.height() * 0.75))
        dialog.resize(dialog_width, dialog_height)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        # Document browser
        doc_browser = QTextBrowser(dialog)
        doc_browser.setPlainText(self.main_window._cached_preview_content or "Loading document...")
        layout.addWidget(doc_browser)

        # Close button
        close_btn = AnimatedButton("✖️ Close", dialog)
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        layout.addWidget(close_btn)

        dialog.exec()
