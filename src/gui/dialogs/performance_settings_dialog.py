"""
Performance Settings Dialog - Configure system performance based on hardware capabilities.
Integrates with the performance manager and help system for optimal user experience.
"""
import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton, QProgressBar,
    QTextEdit, QTabWidget, QWidget, QMessageBox
)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread

logger = logging.getLogger(__name__)

class SystemInfoWorker(QThread):
    """Background worker to gather system information without blocking UI."""
    
    info_ready = pyqtSignal(dict)
    
    def run(self):
        """Gather comprehensive system information."""
        try:
            from ...core.performance_manager import SystemProfiler
            system_info = SystemProfiler.get_system_info()
            self.info_ready.emit(system_info)
        except Exception as e:
            logger.error(f"Error gathering system info: {e}")
            self.info_ready.emit({})

class PerformanceSettingsDialog(QDialog):
    """
    Advanced performance configuration dialog with real-time monitoring.
    Provides user-friendly interface for optimizing system performance.
    """
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Performance Settings")
        self.setModal(True)
        self.resize(800, 600)
        
        # Initialize performance manager
        try:
            from ...core.performance_manager import performance_manager, PerformanceProfile
            self.performance_manager = performance_manager
            self.PerformanceProfile = PerformanceProfile
        except ImportError:
            logger.error("Performance manager not available")
            self.performance_manager = None
            self.PerformanceProfile = None
        
        # Initialize help system
        try:
            from ..widgets.help_system import help_system
            self.help_system = help_system
        except ImportError:
            logger.warning("Help system not available")
            self.help_system = None
        
        self.system_info = {}
        self.current_settings = {}
        
        self.setup_ui()
        self.load_current_settings()
        self.start_system_monitoring()
        
        # Load system info in background
        self.system_worker = SystemInfoWorker()
        self.system_worker.info_ready.connect(self.update_system_info)
        self.system_worker.start()
    
    def setup_ui(self):
        """Setup the performance settings UI with tabs and monitoring."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Performance Profiles Tab
        self.setup_profiles_tab()
        
        # Advanced Settings Tab
        self.setup_advanced_tab()
        
        # System Monitor Tab
        self.setup_monitor_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Help button
        help_button = QPushButton("Help")
        help_button.clicked.connect(self.show_help)
        
        # Reset to defaults
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        
        # Apply and Cancel buttons
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_settings)
        
        button_layout.addWidget(help_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
    
    def setup_profiles_tab(self):
        """Setup the performance profiles tab."""
        profiles_widget = QWidget()
        layout = QVBoxLayout(profiles_widget)
        
        # Profile selection group
        profile_group = QGroupBox("Performance Profile")
        profile_layout = QVBoxLayout(profile_group)
        
        # Profile selector
        profile_selector_layout = QHBoxLayout()
        profile_selector_layout.addWidget(QLabel("Current Profile:"))
        
        self.profile_combo = QComboBox()
        if self.PerformanceProfile:
            for profile in self.PerformanceProfile:
                self.profile_combo.addItem(profile.value.title(), profile)
        
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        profile_selector_layout.addWidget(self.profile_combo)
        
        # Auto-detect button
        auto_detect_button = QPushButton("Auto-Detect Optimal")
        auto_detect_button.clicked.connect(self.auto_detect_profile)
        profile_selector_layout.addWidget(auto_detect_button)
        
        profile_layout.addLayout(profile_selector_layout)
        
        # Profile description
        self.profile_description = QTextEdit()
        self.profile_description.setMaximumHeight(120)
        self.profile_description.setReadOnly(True)
        profile_layout.addWidget(self.profile_description)
        
        layout.addWidget(profile_group)
        
        # System recommendations group
        recommendations_group = QGroupBox("System Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(150)
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.recommendations_text)
        
        layout.addWidget(recommendations_group)
        
        # Performance impact preview
        impact_group = QGroupBox("Expected Performance Impact")
        impact_layout = QGridLayout(impact_group)
        
        impact_layout.addWidget(QLabel("Analysis Speed:"), 0, 0)
        self.speed_indicator = QProgressBar()
        self.speed_indicator.setRange(0, 100)
        impact_layout.addWidget(self.speed_indicator, 0, 1)
        
        impact_layout.addWidget(QLabel("Memory Usage:"), 1, 0)
        self.memory_indicator = QProgressBar()
        self.memory_indicator.setRange(0, 100)
        impact_layout.addWidget(self.memory_indicator, 1, 1)
        
        impact_layout.addWidget(QLabel("GPU Utilization:"), 2, 0)
        self.gpu_indicator = QProgressBar()
        self.gpu_indicator.setRange(0, 100)
        impact_layout.addWidget(self.gpu_indicator, 2, 1)
        
        layout.addWidget(impact_group)
        
        layout.addStretch()
        self.tab_widget.addTab(profiles_widget, "Performance Profiles")
    
    def setup_advanced_tab(self):
        """Setup the advanced settings tab."""
        advanced_widget = QWidget()
        layout = QVBoxLayout(advanced_widget)
        
        # Memory settings group
        memory_group = QGroupBox("Memory Management")
        memory_layout = QGridLayout(memory_group)
        
        memory_layout.addWidget(QLabel("Max Cache Memory (MB):"), 0, 0)
        self.cache_memory_spin = QSpinBox()
        self.cache_memory_spin.setRange(256, 8192)
        self.cache_memory_spin.setSuffix(" MB")
        memory_layout.addWidget(self.cache_memory_spin, 0, 1)
        
        memory_layout.addWidget(QLabel("Embedding Cache Size:"), 1, 0)
        self.embedding_cache_spin = QSpinBox()
        self.embedding_cache_spin.setRange(100, 5000)
        memory_layout.addWidget(self.embedding_cache_spin, 1, 1)
        
        memory_layout.addWidget(QLabel("NER Cache Size:"), 2, 0)
        self.ner_cache_spin = QSpinBox()
        self.ner_cache_spin.setRange(50, 2000)
        memory_layout.addWidget(self.ner_cache_spin, 2, 1)
        
        layout.addWidget(memory_group)
        
        # AI/ML settings group
        ai_group = QGroupBox("AI/ML Configuration")
        ai_layout = QGridLayout(ai_group)
        
        self.use_gpu_check = QCheckBox("Use GPU Acceleration")
        ai_layout.addWidget(self.use_gpu_check, 0, 0, 1, 2)
        
        self.model_quantization_check = QCheckBox("Enable Model Quantization")
        ai_layout.addWidget(self.model_quantization_check, 1, 0, 1, 2)
        
        ai_layout.addWidget(QLabel("Batch Size:"), 2, 0)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 16)
        ai_layout.addWidget(self.batch_size_spin, 2, 1)
        
        ai_layout.addWidget(QLabel("Max Sequence Length:"), 3, 0)
        self.sequence_length_spin = QSpinBox()
        self.sequence_length_spin.setRange(256, 4096)
        self.sequence_length_spin.setSingleStep(256)
        ai_layout.addWidget(self.sequence_length_spin, 3, 1)
        
        layout.addWidget(ai_group)
        
        # Processing settings group
        processing_group = QGroupBox("Processing Configuration")
        processing_layout = QGridLayout(processing_group)
        
        self.parallel_processing_check = QCheckBox("Enable Parallel Processing")
        processing_layout.addWidget(self.parallel_processing_check, 0, 0, 1, 2)
        
        self.async_operations_check = QCheckBox("Enable Async Operations")
        processing_layout.addWidget(self.async_operations_check, 1, 0, 1, 2)
        
        processing_layout.addWidget(QLabel("Max Workers:"), 2, 0)
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        processing_layout.addWidget(self.max_workers_spin, 2, 1)
        
        processing_layout.addWidget(QLabel("Chunk Size:"), 3, 0)
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(500, 8000)
        self.chunk_size_spin.setSingleStep(500)
        processing_layout.addWidget(self.chunk_size_spin, 3, 1)
        
        layout.addWidget(processing_group)
        
        # Database settings group
        db_group = QGroupBox("Database Configuration")
        db_layout = QGridLayout(db_group)
        
        db_layout.addWidget(QLabel("Connection Pool Size:"), 0, 0)
        self.pool_size_spin = QSpinBox()
        self.pool_size_spin.setRange(5, 50)
        db_layout.addWidget(self.pool_size_spin, 0, 1)
        
        layout.addWidget(db_group)
        
        layout.addStretch()
        self.tab_widget.addTab(advanced_widget, "Advanced Settings")
    
    def setup_monitor_tab(self):
        """Setup the system monitoring tab."""
        monitor_widget = QWidget()
        layout = QVBoxLayout(monitor_widget)
        
        # Real-time system info
        system_group = QGroupBox("System Information")
        system_layout = QGridLayout(system_group)
        
        # System specs
        system_layout.addWidget(QLabel("Total Memory:"), 0, 0)
        self.total_memory_label = QLabel("Detecting...")
        system_layout.addWidget(self.total_memory_label, 0, 1)
        
        system_layout.addWidget(QLabel("CPU Cores:"), 1, 0)
        self.cpu_cores_label = QLabel("Detecting...")
        system_layout.addWidget(self.cpu_cores_label, 1, 1)
        
        system_layout.addWidget(QLabel("GPU Available:"), 2, 0)
        self.gpu_available_label = QLabel("Detecting...")
        system_layout.addWidget(self.gpu_available_label, 2, 1)
        
        system_layout.addWidget(QLabel("GPU Memory:"), 3, 0)
        self.gpu_memory_label = QLabel("Detecting...")
        system_layout.addWidget(self.gpu_memory_label, 3, 1)
        
        layout.addWidget(system_group)
        
        # Real-time monitoring
        monitoring_group = QGroupBox("Real-time Monitoring")
        monitoring_layout = QGridLayout(monitoring_group)
        
        monitoring_layout.addWidget(QLabel("System Memory Usage:"), 0, 0)
        self.system_memory_bar = QProgressBar()
        self.system_memory_bar.setRange(0, 100)
        monitoring_layout.addWidget(self.system_memory_bar, 0, 1)
        self.system_memory_label = QLabel("0%")
        monitoring_layout.addWidget(self.system_memory_label, 0, 2)
        
        monitoring_layout.addWidget(QLabel("Process Memory Usage:"), 1, 0)
        self.process_memory_bar = QProgressBar()
        self.process_memory_bar.setRange(0, 2048)  # MB
        monitoring_layout.addWidget(self.process_memory_bar, 1, 1)
        self.process_memory_label = QLabel("0 MB")
        monitoring_layout.addWidget(self.process_memory_label, 1, 2)
        
        monitoring_layout.addWidget(QLabel("Cache Usage:"), 2, 0)
        self.cache_usage_bar = QProgressBar()
        self.cache_usage_bar.setRange(0, 100)
        monitoring_layout.addWidget(self.cache_usage_bar, 2, 1)
        self.cache_usage_label = QLabel("0 MB")
        monitoring_layout.addWidget(self.cache_usage_label, 2, 2)
        
        layout.addWidget(monitoring_group)
        
        # Performance recommendations
        perf_recommendations_group = QGroupBox("Performance Recommendations")
        perf_recommendations_layout = QVBoxLayout(perf_recommendations_group)
        
        self.perf_recommendations_text = QTextEdit()
        self.perf_recommendations_text.setMaximumHeight(150)
        self.perf_recommendations_text.setReadOnly(True)
        perf_recommendations_layout.addWidget(self.perf_recommendations_text)
        
        layout.addWidget(perf_recommendations_group)
        
        layout.addStretch()
        self.tab_widget.addTab(monitor_widget, "System Monitor")
        
        # Start monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitoring)
        self.monitor_timer.start(2000)  # Update every 2 seconds
    
    def load_current_settings(self):
        """Load current performance settings."""
        if not self.performance_manager:
            return
        
        try:
            config = self.performance_manager.config
            profile = self.performance_manager.current_profile
            
            # Set profile combo
            profile_index = self.profile_combo.findData(profile)
            if profile_index >= 0:
                self.profile_combo.setCurrentIndex(profile_index)
            
            # Load advanced settings
            self.cache_memory_spin.setValue(config.max_cache_memory_mb)
            self.embedding_cache_spin.setValue(config.embedding_cache_size)
            self.ner_cache_spin.setValue(config.ner_cache_size)
            self.use_gpu_check.setChecked(config.use_gpu)
            self.model_quantization_check.setChecked(config.model_quantization)
            self.batch_size_spin.setValue(config.batch_size)
            self.sequence_length_spin.setValue(config.max_sequence_length)
            self.parallel_processing_check.setChecked(config.parallel_processing)
            self.async_operations_check.setChecked(config.async_operations)
            self.max_workers_spin.setValue(config.max_workers)
            self.chunk_size_spin.setValue(config.chunk_size)
            self.pool_size_spin.setValue(config.connection_pool_size)
            
            self.update_profile_description()
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def on_profile_changed(self):
        """Handle profile selection change."""
        self.update_profile_description()
        self.update_performance_indicators()
    
    def update_profile_description(self):
        """Update the profile description text."""
        current_profile = self.profile_combo.currentData()
        if not current_profile:
            return
        
        descriptions = {
            "conservative": """
            <b>Conservative Profile</b><br>
            Optimized for systems with 6-8GB RAM and integrated graphics.<br><br>
            <b>Features:</b><br>
            • CPU-only processing for maximum compatibility<br>
            • Quantized AI models to reduce memory usage<br>
            • Small cache sizes to minimize memory footprint<br>
            • Sequential processing to avoid resource conflicts<br><br>
            <b>Best for:</b> Business laptops, older systems, shared computers
            """,
            "balanced": """
            <b>Balanced Profile</b><br>
            Optimized for systems with 8-12GB RAM and optional dedicated GPU.<br><br>
            <b>Features:</b><br>
            • GPU acceleration when available<br>
            • Moderate cache sizes for good performance<br>
            • Parallel processing for faster analysis<br>
            • Async operations for responsive UI<br><br>
            <b>Best for:</b> Modern business laptops, workstations
            """,
            "aggressive": """
            <b>Aggressive Profile</b><br>
            Optimized for systems with 12-16GB+ RAM and dedicated GPU.<br><br>
            <b>Features:</b><br>
            • Full GPU acceleration and large models<br>
            • Large cache sizes for maximum speed<br>
            • Maximum parallel processing<br>
            • All performance optimizations enabled<br><br>
            <b>Best for:</b> High-end workstations, gaming PCs, servers
            """
        }
        
        description = descriptions.get(current_profile.value, "Custom configuration")
        self.profile_description.setHtml(description)
    
    def update_performance_indicators(self):
        """Update performance impact indicators."""
        current_profile = self.profile_combo.currentData()
        if not current_profile:
            return
        
        # Simulate performance indicators based on profile
        indicators = {
            "conservative": {"speed": 40, "memory": 30, "gpu": 0},
            "balanced": {"speed": 70, "memory": 60, "gpu": 50},
            "aggressive": {"speed": 95, "memory": 85, "gpu": 90}
        }
        
        profile_indicators = indicators.get(current_profile.value, {"speed": 50, "memory": 50, "gpu": 25})
        
        self.speed_indicator.setValue(profile_indicators["speed"])
        self.memory_indicator.setValue(profile_indicators["memory"])
        self.gpu_indicator.setValue(profile_indicators["gpu"])
    
    def auto_detect_profile(self):
        """Auto-detect optimal performance profile."""
        if not self.performance_manager:
            return
        
        try:
            from ...core.performance_manager import SystemProfiler
            system_info = SystemProfiler.get_system_info()
            recommended_profile = SystemProfiler.recommend_profile(system_info)
            
            # Set the recommended profile
            profile_index = self.profile_combo.findData(recommended_profile)
            if profile_index >= 0:
                self.profile_combo.setCurrentIndex(profile_index)
            
            # Show recommendation message
            QMessageBox.information(
                self,
                "Auto-Detection Complete",
                f"Recommended profile: {recommended_profile.value.title()}\n\n"
                f"Based on your system:\n"
                f"• {system_info.get('total_memory_gb', 'Unknown')}GB RAM\n"
                f"• {system_info.get('cpu_count', 'Unknown')} CPU cores\n"
                f"• GPU: {'Available' if system_info.get('cuda_available') else 'Not available'}"
            )
            
        except Exception as e:
            logger.error(f"Error in auto-detection: {e}")
            QMessageBox.warning(self, "Auto-Detection Failed", f"Could not detect optimal settings: {e}")
    
    def update_system_info(self, system_info: Dict[str, Any]):
        """Update system information display."""
        self.system_info = system_info
        
        self.total_memory_label.setText(f"{system_info.get('total_memory_gb', 'Unknown')} GB")
        self.cpu_cores_label.setText(str(system_info.get('cpu_count', 'Unknown')))
        
        if system_info.get('cuda_available'):
            self.gpu_available_label.setText("Yes")
            self.gpu_memory_label.setText(f"{system_info.get('gpu_memory_gb', 'Unknown')} GB")
        else:
            self.gpu_available_label.setText("No")
            self.gpu_memory_label.setText("N/A")
        
        self.update_recommendations()
    
    def update_monitoring(self):
        """Update real-time monitoring information."""
        if not self.performance_manager:
            return
        
        try:
            memory_stats = self.performance_manager.get_memory_usage()
            
            # Update system memory
            system_percent = memory_stats.get('system_used_percent', 0)
            self.system_memory_bar.setValue(int(system_percent))
            self.system_memory_label.setText(f"{system_percent:.1f}%")
            
            # Update process memory
            process_mb = memory_stats.get('process_memory_mb', 0)
            self.process_memory_bar.setValue(int(process_mb))
            self.process_memory_label.setText(f"{process_mb:.1f} MB")
            
            # Update cache usage (if available)
            try:
                from ...core.cache_service import get_cache_stats
                cache_stats = get_cache_stats()
                cache_mb = cache_stats.get('memory_usage_mb', 0)
                cache_limit = memory_stats.get('cache_limit_mb', 1024)
                cache_percent = (cache_mb / cache_limit * 100) if cache_limit > 0 else 0
                
                self.cache_usage_bar.setValue(int(cache_percent))
                self.cache_usage_label.setText(f"{cache_mb:.1f} MB")
            except ImportError:
                pass
            
        except Exception as e:
            logger.error(f"Error updating monitoring: {e}")
    
    def update_recommendations(self):
        """Update performance recommendations based on system info."""
        recommendations = []
        
        if self.system_info:
            memory_gb = self.system_info.get('total_memory_gb', 0)
            has_gpu = self.system_info.get('cuda_available', False)
            
            if memory_gb < 8:
                recommendations.append("• Consider using Conservative profile for optimal performance")
                recommendations.append("• Close other applications during analysis to free memory")
            elif memory_gb >= 16 and has_gpu:
                recommendations.append("• Your system can handle Aggressive profile for maximum speed")
                recommendations.append("• GPU acceleration is available for faster processing")
            else:
                recommendations.append("• Balanced profile is recommended for your system")
            
            if not has_gpu:
                recommendations.append("• Consider upgrading to a system with dedicated GPU for better performance")
        
        if not recommendations:
            recommendations.append("• System information not yet available")
        
        self.recommendations_text.setPlainText("\n".join(recommendations))
        self.perf_recommendations_text.setPlainText("\n".join(recommendations))
    
    def show_help(self):
        """Show help information for performance settings."""
        if self.help_system:
            self.help_system.show_tooltip(self, "performance_settings")
        else:
            QMessageBox.information(
                self,
                "Performance Settings Help",
                "Performance settings allow you to optimize the application based on your hardware.\n\n"
                "• Conservative: Best for 6-8GB RAM systems\n"
                "• Balanced: Best for 8-12GB RAM systems\n"
                "• Aggressive: Best for 12GB+ RAM systems with GPU\n\n"
                "Use Auto-Detect to automatically choose the best profile for your system."
            )
    
    def reset_to_defaults(self):
        """Reset settings to system defaults."""
        if not self.performance_manager:
            return
        
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "This will reset all performance settings to system defaults. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.auto_detect_profile()
    
    def apply_settings(self):
        """Apply current settings without closing dialog."""
        if not self.performance_manager:
            return
        
        try:
            # Get selected profile
            current_profile = self.profile_combo.currentData()
            if current_profile:
                self.performance_manager.set_profile(current_profile)
            
            # Emit settings changed signal
            self.settings_changed.emit(self.get_current_settings())
            
            QMessageBox.information(self, "Settings Applied", "Performance settings have been applied successfully.")
            
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to apply settings: {e}")
    
    def accept_settings(self):
        """Apply settings and close dialog."""
        self.apply_settings()
        self.accept()
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary."""
        return {
            'profile': self.profile_combo.currentData(),
            'max_cache_memory_mb': self.cache_memory_spin.value(),
            'embedding_cache_size': self.embedding_cache_spin.value(),
            'ner_cache_size': self.ner_cache_spin.value(),
            'use_gpu': self.use_gpu_check.isChecked(),
            'model_quantization': self.model_quantization_check.isChecked(),
            'batch_size': self.batch_size_spin.value(),
            'max_sequence_length': self.sequence_length_spin.value(),
            'parallel_processing': self.parallel_processing_check.isChecked(),
            'async_operations': self.async_operations_check.isChecked(),
            'max_workers': self.max_workers_spin.value(),
            'chunk_size': self.chunk_size_spin.value(),
            'connection_pool_size': self.pool_size_spin.value()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance status for main window display."""
        try:
            memory_stats = self.performance_manager.get_memory_usage() if self.performance_manager else {}
            
            return {
                'current_profile': self.current_profile.value if self.current_profile else 'Unknown',
                'system_memory_percent': memory_stats.get('system_used_percent', 0),
                'process_memory_mb': memory_stats.get('process_memory_mb', 0),
                'gpu_available': self.system_info.get('cuda_available', False),
                'cache_enabled': True,
                'performance_status': self._get_performance_status()
            }
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'performance_status': 'Error'}
    
    def _get_performance_status(self) -> str:
        """Determine overall performance status."""
        try:
            memory_stats = self.performance_manager.get_memory_usage() if self.performance_manager else {}
            memory_percent = memory_stats.get('system_used_percent', 0)
            
            if memory_percent > 85:
                return 'High Memory Usage'
            elif memory_percent > 70:
                return 'Moderate Load'
            else:
                return 'Optimal'
        except Exception:
            return 'Unknown'
    
    def start_system_monitoring(self):
        """Start system monitoring if available."""
        try:
            self.update_monitoring()
        except Exception as e:
            logger.error(f"Error starting system monitoring: {e}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop monitoring timer
        if hasattr(self, 'monitor_timer'):
            self.monitor_timer.stop()
        
        # Stop system worker
        if hasattr(self, 'system_worker') and self.system_worker.isRunning():
            self.system_worker.quit()
            self.system_worker.wait()
        
        event.accept()