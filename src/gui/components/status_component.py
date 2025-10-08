"""
Status Component - AI Model Status Indicators
Provides visual feedback on AI model loading and availability.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class StatusComponent(QWidget):
    """
    Component for displaying AI model status indicators.
    
    Signals:
        status_clicked: Emitted when a status indicator is clicked
    """
    
    status_clicked = Signal(str)  # model_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.models = {
            "Phi-2 LLM": False,           # Microsoft Phi-2 2.7B parameter model
            "FAISS+BM25": False,          # Hybrid retrieval system
            "Fact Checker": False,        # Secondary verification model
            "BioBERT": False,             # Biomedical BERT for medical NER
            "ClinicalBERT": False,        # Clinical notes specialized BERT
            "Chat Assistant": False,      # Local conversational AI
            "MiniLM-L6": False,          # sentence-transformers embedding model
        }
        self.status_labels = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize the status UI with responsive scaling."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Set minimum size to prevent excessive shrinking
        self.setMinimumWidth(450)  # Increased to accommodate longer model names
        self.setMinimumHeight(30)
        
        # Add error message display capability
        self.error_message = ""
        
        for model_name in self.models:
            # Status indicator with better scaling
            indicator = QLabel("●")
            indicator.setStyleSheet("""
                QLabel {
                    color: red; 
                    font-size: 14px; 
                    font-weight: bold;
                    min-width: 16px;
                    max-width: 16px;
                }
            """)
            indicator.setToolTip(f"{model_name}: Not Ready")
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Model name label with responsive sizing and word wrap
            name_label = QLabel(model_name)
            name_label.setWordWrap(True)  # Enable word wrapping
            name_label.setStyleSheet("""
                QLabel {
                    font-size: 10px; 
                    color: #666;
                    min-width: 45px;
                    max-width: 80px;
                    padding: 3px 6px;
                    border-radius: 4px;
                    border: 1px solid #dc2626;
                    background: rgba(220, 38, 38, 0.1);
                    font-weight: 500;
                }
                QLabel:hover {
                    background: rgba(220, 38, 38, 0.2);
                    color: #dc2626;
                }
            """)
            name_label.setCursor(Qt.CursorShape.PointingHandCursor)
            name_label.mousePressEvent = lambda event, name=model_name: self.on_status_clicked(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Add to layout with proper sizing
            layout.addWidget(indicator, 0)  # Don't stretch indicator
            layout.addWidget(name_label, 1)  # Allow label to stretch
            
            self.status_labels[model_name] = {
                'indicator': indicator,
                'label': name_label
            }
            
    def update_model_status(self, model_name: str, status: bool):
        """Update individual model status with improved styling."""
        if model_name in self.status_labels:
            self.models[model_name] = status
            
            indicator = self.status_labels[model_name]['indicator']
            label = self.status_labels[model_name]['label']
            
            if status:
                indicator.setStyleSheet("""
                    QLabel {
                        color: #059669; 
                        font-size: 14px; 
                        font-weight: bold;
                        min-width: 16px;
                        max-width: 16px;
                    }
                """)
                indicator.setToolTip(f"{model_name}: Ready ✅")
                label.setStyleSheet("""
                    QLabel {
                        font-size: 10px; 
                        color: #059669;
                        font-weight: 500;
                        min-width: 45px;
                        max-width: 80px;
                        padding: 3px 6px;
                        border-radius: 4px;
                        border: 1px solid #059669;
                        background: rgba(5, 150, 105, 0.1);
                    }
                    QLabel:hover {
                        background: rgba(5, 150, 105, 0.2);
                        color: #047857;
                    }
                """)
            else:
                indicator.setStyleSheet("""
                    QLabel {
                        color: #dc2626; 
                        font-size: 14px; 
                        font-weight: bold;
                        min-width: 16px;
                        max-width: 16px;
                    }
                """)
                indicator.setToolTip(f"{model_name}: Not Ready ❌")
                label.setStyleSheet("""
                    QLabel {
                        font-size: 11px; 
                        color: #666;
                        min-width: 50px;
                        padding: 2px 4px;
                        border-radius: 3px;
                    }
                    QLabel:hover {
                        background: #f1f5f9;
                        color: #1d4ed8;
                    }
                """)
                
    def set_all_ready(self):
        """Set all models as ready."""
        for model_name in self.models:
            self.update_model_status(model_name, True)
            
    def set_all_loading(self):
        """Set all models as loading with improved styling."""
        for model_name in self.models:
            self.models[model_name] = False
            indicator = self.status_labels[model_name]['indicator']
            label = self.status_labels[model_name]['label']
            
            indicator.setStyleSheet("""
                QLabel {
                    color: #d97706; 
                    font-size: 14px; 
                    font-weight: bold;
                    min-width: 16px;
                    max-width: 16px;
                }
            """)
            indicator.setToolTip(f"{model_name}: Loading... ⏳")
            
            label.setStyleSheet("""
                QLabel {
                    font-size: 10px; 
                    color: #d97706;
                    min-width: 45px;
                    max-width: 80px;
                    padding: 3px 6px;
                    border-radius: 4px;
                    border: 1px solid #d97706;
                    background: rgba(217, 119, 6, 0.1);
                    font-weight: 500;
                }
                QLabel:hover {
                    background: rgba(217, 119, 6, 0.2);
                    color: #b45309;
                }
            """)
            
    def get_overall_status(self) -> dict:
        """Get overall status summary."""
        ready_count = sum(self.models.values())
        total_count = len(self.models)
        
        return {
            'ready_count': ready_count,
            'total_count': total_count,
            'all_ready': ready_count == total_count,
            'percentage': (ready_count / total_count) * 100 if total_count > 0 else 0
        }
        
    def on_status_clicked(self, model_name: str):
        """Handle status indicator click."""
        self.status_clicked.emit(model_name)
        
    def get_status_text(self) -> str:
        """Get human-readable status text."""
        status = self.get_overall_status()
        
        if status['all_ready']:
            return "AI Models: Ready"
        elif status['ready_count'] == 0:
            return "AI Models: Loading..."
        else:
            return f"AI Models: {status['ready_count']}/{status['total_count']}"
            
    def get_status_color(self) -> str:
        """Get appropriate color for current status."""
        status = self.get_overall_status()
        
        if status['all_ready']:
            return "green"
        elif status['ready_count'] == 0:
            return "red"
        else:
            return "orange"
    
    def set_error_message(self, message: str) -> None:
        """Set error message with hover tooltip for full visibility."""
        self.error_message = message
        if message:
            # Truncate message for display but keep full message in tooltip
            display_message = message[:50] + "..." if len(message) > 50 else message
            self.setToolTip(f"Error Details: {message}")
            self.setStyleSheet(f"""
                QWidget {{
                    background: rgba(220, 38, 38, 0.1);
                    border: 1px solid #dc2626;
                    border-radius: 4px;
                    padding: 2px;
                }}
                QWidget:hover {{
                    background: rgba(220, 38, 38, 0.2);
                }}
            """)
        else:
            self.setToolTip("")
            self.setStyleSheet("")