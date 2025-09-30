import platform
import psutil
import torch
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt

class InfoDialogBase(QDialog):
    """Base class for informational dialogs."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(250, 250, 600, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #bbbbbb;
            }
            QTextBrowser {
                background-color: #3c3f41;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI components."""
        layout = QVBoxLayout(self)
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        layout.addWidget(self.content_browser)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #357abd; }
            QPushButton:focus { border: 1px solid #63a4ff; }
        """)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

class SystemInfoDialog(InfoDialogBase):
    """A dialog to display system information."""
    def __init__(self, parent=None):
        super().__init__("💻 System Information", parent)
        self.content_browser.setHtml(self.get_system_info_html())

    def get_system_info_html(self) -> str:
        """Returns formatted HTML with system information."""
        try:
            mem = psutil.virtual_memory()
            gpu_available = "Available" if torch.cuda.is_available() else "Not Available"
            return f"""
            <html><body style='font-family: sans-serif; font-size: 14px; color: #dddddd; line-height: 1.6;'>
                <h1 style='color: #4a90e2;'>System Information</h1>
                <p>Here are the details of the currently running system environment.</p>
                <ul>
                    <li><b>Operating System:</b> {platform.system()} {platform.release()}</li>
                    <li><b>Architecture:</b> {platform.machine()}</li>
                    <li><b>CPU Cores:</b> {psutil.cpu_count()}</li>
                    <li><b>Total RAM:</b> {mem.total / (1024**3):.2f} GB</li>
                    <li><b>Available RAM:</b> {mem.available / (1024**3):.2f} GB</li>
                    <li><b>GPU Support (CUDA):</b> {gpu_available}</li>
                </ul>
            </body></html>
            """
        except Exception as e:
            return f"<html><body><p>Could not retrieve system information: {e}</p></body></html>"

class FeaturesDialog(InfoDialogBase):
    """A dialog to display application features."""
    def __init__(self, parent=None):
        super().__init__("🚀 Technology & Features", parent)
        self.content_browser.setHtml(self.get_features_html())

    def get_features_html(self) -> str:
        """Returns formatted HTML with application features."""
        return """
        <html><body style='font-family: sans-serif; font-size: 14px; color: #dddddd; line-height: 1.6;'>
            <h1 style='color: #4a90e2;'>Technology & Features</h1>
            <p>This application is built with a modern technology stack to provide a fast and reliable experience.</p>
            <h3 style='color: #4a90e2;'>Core Technologies:</h3>
            <ul>
                <li><b>Backend:</b> FastAPI</li>
                <li><b>Frontend:</b> PyQt6</li>
                <li><b>Database:</b> SQLAlchemy with SQLite</li>
                <li><b>AI Models:</b> PyTorch, Transformers, Sentence-Transformers</li>
            </ul>
            <h3 style='color: #4a90e2;'>Key Features:</h3>
            <ul>
                <li><b>AI-Powered Analysis:</b> Uses local AI models to analyze clinical documents for compliance.</li>
                <li><b>Interactive Dashboard:</b> Visualizes compliance trends and common issues.</li>
                <li><b>Hybrid Search:</b> A sophisticated RAG pipeline uses keyword and semantic search to find relevant compliance rules.</li>
                <li><b>Full Rubric Management:</b> A GUI for adding, editing, and deleting compliance rubrics.</li>
                <li><b>Data Privacy:</b> All processing is done locally to ensure patient data remains secure.</li>
            </ul>
        </body></html>
        """

class RequirementsDialog(InfoDialogBase):
    """A dialog to display system requirements."""
    def __init__(self, parent=None):
        super().__init__("📋 System Requirements", parent)
        self.content_browser.setHtml(self.get_requirements_html())

    def get_requirements_html(self) -> str:
        """Returns formatted HTML with system requirements."""
        return """
        <html><body style='font-family: sans-serif; font-size: 14px; color: #dddddd; line-height: 1.6;'>
            <h1 style='color: #4a90e2;'>System Requirements & Performance</h1>
            <p>For the best experience, please ensure your system meets the following requirements.</p>
            <h3 style='color: #4a90e2;'>Minimum Requirements:</h3>
            <ul>
                <li><b>Python:</b> 3.10+</li>
                <li><b>RAM:</b> 8 GB</li>
                <li><b>CPU:</b> 4-core processor</li>
            </ul>
            <h3 style='color: #4a90e2;'>Recommended for Optimal Performance:</h3>
            <ul>
                <li><b>RAM:</b> 16 GB or more</li>
                <li><b>GPU:</b> NVIDIA GPU with 6GB+ VRAM for CUDA acceleration.</li>
            </ul>
            <h3 style='color: #4a90e2;'>Performance Settings</h3>
            <p>
                The <b>Performance Settings</b> dialog (under the "Tools" menu) allows you to adjust how the application uses your system's resources. You can select different AI models or change processing settings to balance speed and accuracy, which is especially useful on systems without a dedicated GPU.
            </p>
        </body></html>
        """
