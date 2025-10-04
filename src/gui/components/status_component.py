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
            "Generator": False,
            "Retriever": False,
            "Fact Checker": False,
            "NER": False,
            "Chat": False,
            "Embeddings": False,
        }
        self.status_labels = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize the status UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        for model_name in self.models:
            # Status indicator
            indicator = QLabel("●")
            indicator.setStyleSheet("color: red; font-size: 12px;")
            indicator.setToolTip(f"{model_name}: Not Ready")
            
            # Model name label
            name_label = QLabel(model_name)
            name_label.setStyleSheet("font-size: 10px; color: #666;")
            name_label.setCursor(Qt.CursorShape.PointingHandCursor)
            name_label.mousePressEvent = lambda event, name=model_name: self.on_status_clicked(name)
            
            layout.addWidget(indicator)
            layout.addWidget(name_label)
            
            self.status_labels[model_name] = {
                'indicator': indicator,
                'label': name_label
            }
            
    def update_model_status(self, model_name: str, status: bool):
        """Update individual model status."""
        if model_name in self.status_labels:
            self.models[model_name] = status
            
            indicator = self.status_labels[model_name]['indicator']
            label = self.status_labels[model_name]['label']
            
            if status:
                indicator.setStyleSheet("color: green; font-size: 12px;")
                indicator.setToolTip(f"{model_name}: Ready")
                label.setStyleSheet("font-size: 10px; color: #333;")
            else:
                indicator.setStyleSheet("color: red; font-size: 12px;")
                indicator.setToolTip(f"{model_name}: Not Ready")
                label.setStyleSheet("font-size: 10px; color: #666;")
                
    def set_all_ready(self):
        """Set all models as ready."""
        for model_name in self.models:
            self.update_model_status(model_name, True)
            
    def set_all_loading(self):
        """Set all models as loading."""
        for model_name in self.models:
            self.update_model_status(model_name, False)
            indicator = self.status_labels[model_name]['indicator']
            indicator.setStyleSheet("color: orange; font-size: 12px;")
            indicator.setToolTip(f"{model_name}: Loading...")
            
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