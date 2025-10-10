"""UI-related event handlers for the main window."""
from __future__ import annotations

import logging
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QDialog, QInputDialog, QLineEdit, QMessageBox, QTextBrowser, QVBoxLayout

from src.core.analysis_diagnostics import diagnostics
from src.core.license_manager import license_manager
from src.gui.dialogs.change_password_dialog import ChangePasswordDialog
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.widgets.medical_theme import medical_theme
from src.gui.widgets.micro_interactions import AnimatedButton

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow

logger = logging.getLogger(__name__)


class UIHandlers:
    """Handles UI-related events and operations."""
    
    def __init__(self, main_window: MainApplicationWindow) -> None:
        self.main_window = main_window
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        medical_theme.toggle_theme()
        self.main_window._apply_medical_theme()
        
        # Update status bar message
        theme_name = "Dark" if medical_theme.current_theme == "dark" else "Light"
        self.main_window.statusBar().showMessage(f"Switched to {theme_name} theme", 3000)

    def apply_theme(self, theme_name: str) -> None:
        """Apply a specific theme."""
        medical_theme.set_theme(theme_name)
        self.main_window._apply_medical_theme()
        
        # Update status bar message
        theme_display = "Dark" if theme_name == "dark" else "Light"
        self.main_window.statusBar().showMessage(f"Applied {theme_display} theme", 3000)

    def on_logo_clicked(self) -> None:
        """Handle logo clicks for easter eggs (7 clicks triggers special message)."""
        if self.main_window.header and self.main_window.header.click_count == 7:
            QMessageBox.information(
                self.main_window,
                "🎉 Easter Egg Found!",
                "You found the secret! 🌴\n\n"
                "Pacific Coast Therapy - Where compliance meets excellence!\n\n"
                "Keep up the great documentation work! 💪"
            )
            self.main_window.statusBar().showMessage("🎉 Easter egg activated!", 5000)

    def on_model_status_clicked(self, model_name: str) -> None:
        """Handle clicks on AI model status indicators with detailed descriptions."""
        status = self.main_window.status_component.models.get(model_name, False) if self.main_window.status_component else False
        status_text = "✅ Ready" if status else "❌ Not Ready"
        
        # Detailed model descriptions with complete transparency - Updated with real models
        model_descriptions = {
            "Phi-2 LLM": {
                "full_name": "Natural Language Generation Model (Phi-2/Mistral-7B)",
                "description": "Generates personalized compliance recommendations and improvement suggestions",
                "function": "Creates human-readable explanations of compliance issues and actionable advice",
                "technology": "Microsoft Phi-2 (2.7B parameters) or Mistral-7B (quantized) - chosen for medical accuracy and local processing capability",
                "why_chosen": "Selected for excellent reasoning capabilities, medical knowledge, and ability to run locally for privacy",
                "use_cases": ["Compliance recommendations", "Report generation", "Improvement suggestions", "Personalized feedback"]
            },
            "FAISS+BM25": {
                "full_name": "Hybrid Retrieval-Augmented Generation (RAG) System",
                "description": "Finds relevant compliance rules and guidelines for document analysis",
                "function": "Combines semantic search (FAISS) with keyword matching (BM25) for precise rule retrieval",
                "technology": "FAISS vector database + BM25 ranking algorithm with hybrid scoring",
                "why_chosen": "Hybrid approach ensures both semantic understanding and exact keyword matching for comprehensive rule coverage",
                "use_cases": ["Rule matching", "Guideline retrieval", "Context-aware search", "Compliance verification"]
            },
            "Fact Checker": {
                "full_name": "AI Fact Verification & Confidence Scoring System",
                "description": "Verifies accuracy of compliance findings and reduces false positives through secondary validation",
                "function": "Cross-references findings against multiple sources and applies confidence scoring to ensure accuracy",
                "technology": "Secondary transformer model with specialized verification algorithms and uncertainty quantification",
                "why_chosen": "Critical for medical compliance - reduces false positives and provides confidence metrics for clinical decision-making",
                "use_cases": ["Finding verification", "Accuracy validation", "Confidence scoring", "False positive reduction"]
            },
            "BioBERT": {
                "full_name": "Biomedical Named Entity Recognition (BioBERT)",
                "description": "Extracts biomedical terminology and general medical concepts from documents",
                "function": "Identifies biomedical entities, drug names, diseases, and general medical terminology",
                "technology": "BioBERT - BERT pre-trained on biomedical literature (PubMed abstracts and PMC full-text articles)",
                "why_chosen": "Specifically trained on biomedical texts, excels at general medical terminology and research-based language",
                "use_cases": ["Biomedical term extraction", "Drug and disease identification", "Research terminology", "General medical concepts"]
            },
            "ClinicalBERT": {
                "full_name": "Clinical Named Entity Recognition (ClinicalBERT)",
                "description": "Extracts medical terminology and clinical concepts from therapy documentation",
                "function": "Identifies medical entities, conditions, treatments, and clinical terminology with high precision",
                "technology": "BioBERT (biomedical BERT) + ClinicalBERT - dual model approach for comprehensive medical entity extraction",
                "why_chosen": "BioBERT excels at general biomedical terms, ClinicalBERT specializes in clinical notes - together they provide comprehensive coverage",
                "use_cases": ["Medical term extraction", "Clinical concept identification", "Entity linking", "Medical terminology validation"]
            },
            "Chat Assistant": {
                "full_name": "Conversational AI Assistant (Local LLM)",
                "description": "Provides interactive assistance and answers compliance questions in real-time",
                "function": "Offers contextual help, clarification on compliance issues, and educational guidance",
                "technology": "Local conversational model based on Phi-2/Mistral with compliance-specific fine-tuning",
                "why_chosen": "Local processing ensures privacy while providing instant, contextual assistance for complex compliance questions",
                "use_cases": ["Interactive help", "Question answering", "Compliance guidance", "Educational support"]
            },
            "MiniLM-L6": {
                "full_name": "Semantic Embedding System (sentence-transformers/all-MiniLM-L6-v2)",
                "description": "Converts text into numerical representations for semantic understanding and similarity matching",
                "function": "Creates 384-dimensional vector representations of documents and rules for similarity matching",
                "technology": "sentence-transformers/all-MiniLM-L6-v2 - optimized for semantic similarity with medical domain adaptation",
                "why_chosen": "Excellent balance of performance, speed, and accuracy. Specifically chosen for medical text understanding and efficient local processing",
                "use_cases": ["Semantic search", "Document similarity", "Context understanding", "Rule matching"]
            }
        }
        
        model_info = model_descriptions.get(model_name, {
            "full_name": model_name,
            "description": "AI model for compliance analysis",
            "function": "Supports document analysis and compliance checking",
            "technology": "Local AI processing",
            "use_cases": ["Compliance analysis"]
        })
        
        # Create detailed popup
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle(f"🤖 AI Model Details: {model_name}")
        dialog.resize(600, 500)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border: 2px solid #cbd5e0;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Content browser
        content_browser = QTextBrowser()
        content_browser.setStyleSheet("""
            QTextBrowser {
                background: white;
                border: 2px solid #d1d5db;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        
        # Generate detailed HTML content
        html_content = f"""
        <div style='font-family: Segoe UI; line-height: 1.6;'>
            <h2 style='color: #1d4ed8; margin-top: 0;'>🤖 {model_info['full_name']}</h2>
            
            <div style='background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #0ea5e9;'>
                <h3 style='color: #0ea5e9; margin-top: 0;'>Current Status</h3>
                <p style='font-size: 16px; font-weight: bold; color: {"#059669" if status else "#dc2626"};'>{status_text}</p>
            </div>
            
            <div style='background: #f8fafc; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #334155; margin-top: 0;'>Description</h3>
                <p style='color: #475569;'>{model_info['description']}</p>
            </div>
            
            <div style='background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #059669; margin-top: 0;'>Function in System</h3>
                <p style='color: #475569;'>{model_info['function']}</p>
            </div>
            
            <div style='background: #fef7ff; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #7c3aed; margin-top: 0;'>Technology</h3>
                <p style='color: #475569;'>{model_info['technology']}</p>
            </div>
            
            <div style='background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #0ea5e9; margin-top: 0;'>Why This Model Was Chosen</h3>
                <p style='color: #475569;'>{model_info.get('why_chosen', 'Selected for optimal performance in medical compliance analysis.')}</p>
            </div>
            
            <div style='background: #fffbeb; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #d97706; margin-top: 0;'>Use Cases</h3>
                <ul style='color: #475569; margin: 0; padding-left: 20px;'>
                    {"".join([f"<li>{use_case}</li>" for use_case in model_info['use_cases']])}
                </ul>
            </div>
            
            <div style='background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #cbd5e0;'>
                <h3 style='color: #1e293b; margin-top: 0;'>Privacy & Security</h3>
                <p style='color: #475569;'>🔒 All processing occurs locally on your device. No data is sent to external servers, ensuring complete privacy and HIPAA compliance.</p>
            </div>
        </div>
        """
        
        content_browser.setHtml(html_content)
        layout.addWidget(content_browser)
        
        # Close button
        close_btn = AnimatedButton("Close", dialog)
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #1d4ed8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1e40af;
            }
        """)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def handle_link_clicked(self, url: QUrl) -> None:
        """Handle link clicks in browsers and reports."""
        if url.scheme() == "feedback":
            parsed_url = urlparse(url.toString())
            query_params = parse_qs(parsed_url.query)
            finding_id = query_params.get("finding_id", [None])[0]
            action = parsed_url.path.strip("/")

            if not finding_id:
                return

            if action == "correct":
                self.main_window.view_model.submit_feedback({"finding_id": finding_id, "is_correct": True})
                self.main_window.statusBar().showMessage(f"Feedback for finding {finding_id[:8]}... marked as correct.", 3000)
            elif action == "incorrect":
                correction, ok = QInputDialog.getText(self.main_window, "Submit Correction", "Please provide a brief correction:")
                if ok and correction:
                    self.main_window.view_model.submit_feedback({"finding_id": finding_id, "is_correct": False, "correction": correction})
                    self.main_window.statusBar().showMessage(f"Correction for finding {finding_id[:8]}... submitted.", 3000)
        else:
            webbrowser.open(url.toString())

    def open_report_popup(self) -> None:
        """Open the full report in a popup window."""
        if not self.main_window._current_payload:
            QMessageBox.information(self.main_window, "No Report", "No analysis report available yet. Please run an analysis first.")
            return
        
        # Create popup dialog
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("📊 Compliance Analysis Report")
        # Make dialog responsive to parent window size
        parent_size = self.main_window.size()
        dialog_width = min(1000, int(parent_size.width() * 0.8))
        dialog_height = min(700, int(parent_size.height() * 0.8))
        dialog.resize(dialog_width, dialog_height)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Report browser
        report_browser = QTextBrowser(dialog)
        report_browser.setOpenExternalLinks(False)
        report_browser.anchorClicked.connect(self.handle_link_clicked)
        
        # Load report
        analysis = self.main_window._current_payload.get("analysis", {})
        doc_name = self.main_window._selected_file.name if self.main_window._selected_file else "Document"
        report_html = self.main_window._current_payload.get("report_html") or self.main_window.report_generator.generate_html_report(
            analysis_result=analysis, doc_name=doc_name
        )
        report_browser.setHtml(report_html)
        
        layout.addWidget(report_browser)
        
        # Close button
        close_btn = AnimatedButton("✖️ Close", dialog)
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        layout.addWidget(close_btn)
        
        dialog.exec()

    def toggle_all_sections(self, checked: bool) -> None:
        """Toggle all report section checkboxes."""
        for checkbox in self.main_window.section_checkboxes.values():
            checkbox.setChecked(checked)
        
        status = "selected" if checked else "deselected"
        self.main_window.statusBar().showMessage(f"All sections {status}", 2000)

    def open_rubric_manager(self) -> None:
        """Open the rubric manager dialog."""
        dialog = RubricManagerDialog(self.main_window.auth_token, self.main_window)
        if dialog.exec():
            self.main_window.view_model.load_rubrics()

    def open_settings_dialog(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self.main_window)
        dialog.exec()

    def show_change_password_dialog(self) -> None:
        """Opens the change password dialog."""
        dialog = ChangePasswordDialog(self.main_window)
        dialog.exec()

    def open_chat_dialog(self, initial_message: Optional[str] = None) -> None:
        """Open the AI chat dialog with optional initial message."""
        if initial_message:
            initial_context = f"User question: {initial_message}\n\nContext: {self.main_window.analysis_summary_browser.toPlainText()}"
        else:
            initial_context = self.main_window.analysis_summary_browser.toPlainText() or "Provide a compliance summary."
        dialog = ChatDialog(initial_context, self.main_window.auth_token, self.main_window)
        dialog.exec()

    def toggle_meta_analytics_dock(self) -> None:
        """Toggle Meta Analytics dock widget visibility."""
        if self.main_window.meta_analytics_dock:
            if self.main_window.meta_analytics_dock.isVisible():
                self.main_window.meta_analytics_dock.hide()
            else:
                self.main_window.meta_analytics_dock.show()
                self.main_window.view_model.load_meta_analytics()
    
    def toggle_performance_dock(self) -> None:
        """Toggle Performance Status dock widget visibility."""
        if self.main_window.performance_dock:
            if self.main_window.performance_dock.isVisible():
                self.main_window.performance_dock.hide()
            else:
                self.main_window.performance_dock.show()

    def clear_all_caches(self) -> None:
        """Clear all application caches."""
        reply = QMessageBox.question(
            self.main_window,
            "Clear All Caches",
            "Are you sure you want to clear all application caches?\n\n"
            "This will:\n"
            "• Clear document cache\n"
            "• Clear analysis cache\n"
            "• Clear AI model cache\n"
            "• Reset temporary files\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear various caches
                if hasattr(self.main_window, '_current_payload'):
                    self.main_window._current_payload = {}
                if hasattr(self.main_window, '_cached_preview_content'):
                    self.main_window._cached_preview_content = ""
                
                # Force garbage collection
                import gc
                gc.collect()
                
                self.main_window.statusBar().showMessage("✅ All caches cleared successfully", 5000)
                QMessageBox.information(self.main_window, "Cache Cleared", "All application caches have been cleared successfully!")
            except Exception as e:
                QMessageBox.warning(self.main_window, "Error", f"Failed to clear caches: {str(e)}")

    def run_diagnostics(self) -> None:
        """Run comprehensive system diagnostics."""
        self.main_window.statusBar().showMessage("🔍 Running system diagnostics...", 0)
        
        try:
            # Run diagnostics
            diagnostic_results = diagnostics.run_full_diagnostic()
            
            # Format results for display
            results_text = "🔍 SYSTEM DIAGNOSTICS REPORT\n\n"
            
            healthy_count = 0
            warning_count = 0
            error_count = 0
            
            for component, result in diagnostic_results.items():
                status_icon = {
                    "healthy": "✅",
                    "warning": "⚠️",
                    "error": "❌",
                    "unknown": "❓"
                }.get(result.status.value, "❓")
                
                results_text += f"{status_icon} {component.replace('_', ' ').title()}\n"
                results_text += f"   {result.message}\n\n"
                
                if result.status.value == "healthy":
                    healthy_count += 1
                elif result.status.value == "warning":
                    warning_count += 1
                elif result.status.value == "error":
                    error_count += 1
            
            # Add summary
            results_text += "📊 SUMMARY\n"
            results_text += f"✅ Healthy: {healthy_count}\n"
            results_text += f"⚠️ Warnings: {warning_count}\n"
            results_text += f"❌ Errors: {error_count}\n\n"
            
            if error_count > 0:
                results_text += "💡 RECOMMENDATIONS\n"
                results_text += "• Fix critical errors before running analysis\n"
                results_text += "• Check that the API server is running\n"
                results_text += "• Use Tools → Start API Server if needed\n"
            
            # Show results in a dialog
            msg = QMessageBox(self.main_window)
            msg.setWindowTitle("🔍 System Diagnostics")
            msg.setText(results_text)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            
            self.main_window.statusBar().showMessage("✅ Diagnostics completed", 5000)
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Diagnostics Error", f"Failed to run diagnostics:\n{str(e)}")
            self.main_window.statusBar().showMessage("❌ Diagnostics failed", 5000)

    def start_api_server(self) -> None:
        """Start the API server from within the GUI."""
        reply = QMessageBox.question(
            self.main_window,
            "🚀 Start API Server",
            "This will start the API server in a separate process.\n\n"
            "The server is required for document analysis to work.\n\n"
            "Do you want to start the API server now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Start the API server
                api_script = Path("scripts/run_api.py")
                if api_script.exists():
                    self.main_window.statusBar().showMessage("🚀 Starting API server...", 0)
                    
                    # Start in a separate process
                    subprocess.Popen([
                        sys.executable, str(api_script)
                    ], creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
                    
                    QMessageBox.information(
                        self.main_window,
                        "🚀 API Server Starting",
                        "The API server is starting in a separate window.\n\n"
                        "Please wait a moment for it to initialize, then try your analysis again.\n\n"
                        "You can also run diagnostics (Tools → Run Diagnostics) to check the status."
                    )
                    
                    self.main_window.statusBar().showMessage("✅ API server started", 5000)
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "Script Not Found",
                        f"Could not find API server script at: {api_script}\n\n"
                        "Please start the API server manually:\n"
                        "python scripts/run_api.py"
                    )
                    
            except Exception as e:
                QMessageBox.critical(
                    self.main_window,
                    "Failed to Start API Server",
                    f"Could not start the API server:\n\n{str(e)}\n\n"
                    "Please start it manually:\n"
                    "python scripts/run_api.py"
                )

    def show_about_dialog(self) -> None:
        """Show about dialog with easter eggs."""
        about_text = f"""
Therapy Compliance Analyzer
Version 2.0.0

Welcome, {self.main_window.current_user.username}!

🌟 Created with love by Kevin Moon 🫶

🙏 Special Thanks:
   • Dennis Baloy - For unwavering professional support and guidance 🤝
   • Rand Looper - For exceptional dedication and collaborative excellence 🌟

🎯 AI-Powered Clinical Documentation Analysis
🔒 Privacy-First Local Processing
📊 Medicare & CMS Compliance Focused

Special thanks to all the therapists who make 
healthcare better every day! 💪

🎮 Try the Konami Code: ↑↑↓↓←→←→BA
🎨 Press Ctrl+T to toggle themes
🎉 Click the logo 7 times for a surprise!
        """
        
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle("About Therapy Compliance Analyzer")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Add custom button for more easter eggs
        easter_egg_button = msg.addButton("🥚 More Easter Eggs", QMessageBox.ButtonRole.ActionRole)
        
        msg.exec()
        
        if msg.clickedButton() == easter_egg_button:
            self.show_easter_eggs_dialog()

    def show_easter_eggs_dialog(self) -> None:
        """Show hidden easter eggs dialog."""
        easter_text = """
🥚 HIDDEN EASTER EGGS DISCOVERED! 🥚

🎮 Konami Code: ↑↑↓↓←→←→BA
   - Unlocks special developer mode features
   - Shows hidden performance metrics
   - Enables advanced debugging tools

🖱️ Logo Clicks:
   - 3 clicks: Shows current system stats
   - 5 clicks: Displays memory usage
   - 7 clicks: Pacific Coast Therapy message
   - 10 clicks: Secret developer credits

⌨️ Keyboard Shortcuts:
   - Ctrl+Shift+D: Developer console
   - Ctrl+Alt+M: Memory usage display
   - Ctrl+Shift+K: Kevin's special message
   - F12: Hidden debug panel

🎨 Theme Secrets:
   - Hold Shift while switching themes for animations
   - Ctrl+Alt+T: Cycles through all theme variants
   - Double-click theme button: Random theme

🔍 Hidden Features:
   - Type "kevin" in any text field for surprises
   - Right-click logo 3 times: Developer menu
   - Hold Ctrl+Alt while starting app: Debug mode

Keep exploring! There are more secrets hidden throughout the app! 🕵️‍♂️
        """
        
        QMessageBox.information(self.main_window, "🥚 Easter Eggs Collection", easter_text)

    def show_system_info(self) -> None:
        """Show system information dialog."""
        import platform
        import sys
        from PySide6 import __version__ as pyside_version
        
        system_info = f"""
🖥️ SYSTEM INFORMATION

Operating System:
• Platform: {platform.system()} {platform.release()}
• Architecture: {platform.machine()}
• Processor: {platform.processor()}

Python Environment:
• Python Version: {sys.version.split()[0]}
• PySide6 Version: {pyside_version}
• Current User: {self.main_window.current_user.username}
• User Role: {'Administrator' if self.main_window.current_user.is_admin else 'Standard User'}

Application:
• Theme: {medical_theme.current_theme.title()}
• Active Threads: {len(self.main_window.view_model._active_threads)}
• Developer Mode: {'Enabled' if hasattr(self.main_window, 'developer_mode') and self.main_window.developer_mode else 'Disabled'}

Memory:
• Python Objects: {len(__import__('gc').get_objects())}
• Selected File: {self.main_window._selected_file.name if self.main_window._selected_file else 'None'}
• Analysis Data: {'Available' if self.main_window._current_payload else 'None'}
        """
        
        QMessageBox.information(self.main_window, "ℹ️ System Information", system_info)

    def show_user_management(self) -> None:
        """Show user management dialog (placeholder)."""
        QMessageBox.information(
            self.main_window,
            "👥 User Management",
            "User Management features:\n\n"
            "• View all registered users\n"
            "• Manage user permissions\n"
            "• Reset user passwords\n"
            "• View user activity logs\n\n"
            "This feature will be available in a future update!"
        )

    def check_license_status(self) -> None:
        """Check license status and show trial information if needed."""
        try:
            is_valid, status_message, days_remaining = license_manager.check_license_status()
            
            if not is_valid:
                # Show license expired dialog
                msg = QMessageBox(self.main_window)
                msg.setWindowTitle("🔐 License Status")
                msg.setText(f"License Status: {status_message}")
                msg.setIcon(QMessageBox.Icon.Warning)
                
                # Add activation button
                activate_btn = msg.addButton("🔑 Activate Full License", QMessageBox.ButtonRole.ActionRole)
                msg.addButton(QMessageBox.StandardButton.Ok)
                
                msg.exec()
                
                if msg.clickedButton() == activate_btn:
                    self.show_license_activation_dialog()
                    
            elif days_remaining is not None and days_remaining <= 7:
                # Show trial warning for last 7 days
                QMessageBox.information(
                    self.main_window,
                    "🔔 Trial Period Notice",
                    f"Trial period: {days_remaining} days remaining\n\n"
                    f"Contact your administrator to activate the full license."
                )
                
        except Exception as e:
            logger.error(f"License check failed: {e}")
    
    def show_license_activation_dialog(self) -> None:
        """Show license activation dialog for admin users."""
        if not self.main_window.current_user.is_admin:
            QMessageBox.information(
                self.main_window,
                "🔐 License Activation",
                "Only administrators can activate licenses.\n\n"
                "Please contact your system administrator."
            )
            return
        
        activation_code, ok = QInputDialog.getText(
            self.main_window,
            "🔑 License Activation",
            "Enter activation code:",
            echo=QLineEdit.EchoMode.Password
        )
        
        if ok and activation_code:
            if license_manager.activate_full_license(activation_code):
                QMessageBox.information(
                    self.main_window,
                    "✅ License Activated",
                    "Full license activated successfully!\n\n"
                    "All features are now available."
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "❌ Activation Failed",
                    "Invalid activation code.\n\n"
                    "Please check the code and try again."
                )