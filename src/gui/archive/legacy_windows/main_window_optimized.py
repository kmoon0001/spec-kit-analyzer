"""
Optimized Main Window - Therapy Compliance Analyzer
Uses component-based architecture for better maintainability.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QTextBrowser, QLabel,
    QPushButton, QComboBox, QProgressBar, QStatusBar,
    QFileDialog, QMessageBox, QGroupBox
)

from src.config import get_settings
from src.core.report_generator import ReportGenerator
from src.gui.components import HeaderComponent, StatusComponent, ThemeManager

settings = get_settings()


class OptimizedMainWindow(QMainWindow):
    """
    Optimized main window using component-based architecture.
    
    Features:
    - Component-based design for better maintainability
    - Centralized theme management
    - Modular status indicators
    - Clean separation of concerns
    """
    
    def __init__(self):
        super().__init__()
        
        # Core attributes
        self.access_token = "direct_access"
        self.username = "local_user"
        self.is_admin = True
        self._current_file_path = None
        self._current_document_text = ""
        self._analysis_running = False
        
        # Services
        self.report_generator = ReportGenerator()
        
        # Components
        self.theme_manager = ThemeManager()
        self.header_component = None
        self.status_component = None
        
        # Initialize UI
        self.init_ui()
        self.setup_connections()
        
        # Apply initial theme
        self.theme_manager.apply_theme()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Therapy Compliance Analyzer - Optimized")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create header component
        self.header_component = HeaderComponent()
        main_layout.addWidget(self.header_component)
        
        # Create main content
        self.create_main_content(main_layout)
        
        # Create status bar
        self.create_status_bar()
        
    def create_main_content(self, parent_layout):
        """Create the main content area."""
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Analysis tab
        analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(analysis_tab, "📄 Analysis")
        
        # Dashboard tab (placeholder)
        dashboard_tab = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_tab)
        dashboard_layout.addWidget(QLabel("Dashboard functionality coming soon..."))
        self.tab_widget.addTab(dashboard_tab, "📊 Dashboard")
        
        parent_layout.addWidget(self.tab_widget)
        
    def create_analysis_tab(self):
        """Create the analysis tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Document panel
        doc_panel = QGroupBox("Document Content")
        doc_layout = QVBoxLayout(doc_panel)
        self.document_display = QTextBrowser()
        doc_layout.addWidget(self.document_display)
        splitter.addWidget(doc_panel)
        
        # Results panel
        results_panel = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_panel)
        self.results_display = QTextBrowser()
        results_layout.addWidget(self.results_display)
        splitter.addWidget(results_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        return tab_widget
        
    def create_control_panel(self):
        """Create the control panel."""
        panel = QGroupBox("Analysis Controls")
        layout = QHBoxLayout(panel)
        
        # Upload button
        self.upload_button = QPushButton("📁 Upload Document")
        self.upload_button.clicked.connect(self.upload_document)
        
        # Rubric selector
        self.rubric_combo = QComboBox()
        self.rubric_combo.addItems([
            "PT Compliance Rubric",
            "OT Compliance Rubric", 
            "SLP Compliance Rubric"
        ])
        
        # Analyze button
        self.analyze_button = QPushButton("🔍 Run Analysis")
        self.analyze_button.clicked.connect(self.run_analysis)
        self.analyze_button.setEnabled(False)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        layout.addWidget(self.upload_button)
        layout.addWidget(QLabel("Rubric:"))
        layout.addWidget(self.rubric_combo)
        layout.addWidget(self.analyze_button)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        
        return panel
        
    def create_status_bar(self):
        """Create the status bar with components."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Main status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # AI status component
        self.status_component = StatusComponent()
        self.status_bar.addPermanentWidget(self.status_component)
        
        # Start simulated AI loading
        self.simulate_ai_loading()
        
    def setup_connections(self):
        """Setup signal connections."""
        # Header component connections
        self.header_component.theme_toggle_requested.connect(self.toggle_theme)
        self.header_component.logo_clicked.connect(self.on_logo_clicked)
        
        # Theme manager connections
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        # Status component connections
        self.status_component.status_clicked.connect(self.on_status_clicked)
        
    def upload_document(self):
        """Handle document upload."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "Documents (*.pdf *.docx *.txt);;All Files (*)"
        )
        
        if file_path:
            self._current_file_path = file_path
            self.load_document(file_path)
            
    def load_document(self, file_path: str):
        """Load and display document."""
        try:
            # Simple file loading (would integrate with document service)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            self.document_display.setPlainText(content[:5000] + "..." if len(content) > 5000 else content)
            self.analyze_button.setEnabled(True)
            self.status_label.setText(f"Loaded: {file_path.split('/')[-1]}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load document: {str(e)}")
            
    def run_analysis(self):
        """Run document analysis."""
        if not self._current_file_path:
            QMessageBox.warning(self, "Warning", "Please upload a document first.")
            return
            
        self._analysis_running = True
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Analysis in progress...")
        
        # Simulate analysis
        self.simulate_analysis()
        
    def simulate_analysis(self):
        """Simulate analysis process."""
        self.progress_value = 0
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.update_analysis_progress)
        self.analysis_timer.start(100)  # Update every 100ms
        
    def update_analysis_progress(self):
        """Update analysis progress."""
        self.progress_value += 2
        self.progress_bar.setValue(self.progress_value)
        
        if self.progress_value >= 100:
            self.analysis_timer.stop()
            self.complete_analysis()
            
    def complete_analysis(self):
        """Complete the analysis."""
        self._analysis_running = False
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis completed")
        
        # Display mock results
        results = {
            "overall_score": 85,
            "findings": [
                {"risk": "High", "issue": "Missing treatment frequency", "recommendation": "Add specific frequency (e.g., '3x/week')"},
                {"risk": "Medium", "issue": "Vague functional goals", "recommendation": "Use SMART goal criteria"},
                {"risk": "Low", "issue": "Minor documentation formatting", "recommendation": "Use consistent date format"}
            ]
        }
        
        self.display_results(results)
        
    def display_results(self, results: dict):
        """Display analysis results."""
        html_content = f"""
        <h2>Analysis Results</h2>
        <p><strong>Overall Compliance Score:</strong> {results['overall_score']}/100</p>
        <h3>Findings:</h3>
        <ul>
        """
        
        for finding in results['findings']:
            html_content += f"""
            <li>
                <strong>{finding['risk']} Risk:</strong> {finding['issue']}<br>
                <em>Recommendation:</em> {finding['recommendation']}
            </li>
            """
            
        html_content += "</ul>"
        self.results_display.setHtml(html_content)
        
    def simulate_ai_loading(self):
        """Simulate AI model loading."""
        models = list(self.status_component.models.keys())
        self.loading_index = 0
        
        def load_next_model():
            if self.loading_index < len(models):
                model_name = models[self.loading_index]
                self.status_component.update_model_status(model_name, True)
                self.loading_index += 1
                QTimer.singleShot(800, load_next_model)
                
        QTimer.singleShot(1000, load_next_model)
        
    def toggle_theme(self):
        """Toggle application theme."""
        self.theme_manager.toggle_theme()
        
    def on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        is_dark = theme_name == "dark"
        self.header_component.update_theme_button(is_dark)
        
        # Apply component-specific styles
        if is_dark:
            self.header_component.setStyleSheet(self.header_component.get_dark_theme_stylesheet())
        else:
            self.header_component.setStyleSheet(self.header_component.get_default_stylesheet())
            
    def on_logo_clicked(self):
        """Handle logo clicks."""
        # Could implement easter eggs here
        pass
        
    def on_status_clicked(self, model_name: str):
        """Handle status indicator clicks."""
        status = self.status_component.models[model_name]
        QMessageBox.information(
            self,
            f"{model_name} Status",
            f"{model_name} is {'Ready' if status else 'Not Ready'}"
        )
        
    def start(self):
        """Start the application."""
        self.show()
        
    def closeEvent(self, event):
        """Handle application close."""
        event.accept()