"""
System Resource Monitor

Monitors system resources (RAM, CPU) to prevent crashes and ensure
graceful degradation when resources are constrained.

Key Features:
    - Real-time RAM/CPU monitoring
    - Predictive resource checks before starting jobs
    - Configurable thresholds for warnings and job denial
    - Thread-safe operation
    
Architecture:
    - Uses psutil for accurate system metrics
    - Emits signals when resource limits approached
    - Provides decision logic for job acceptance
"""

import psutil
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QTimer


logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Current system resource metrics."""
    ram_percent: float
    ram_available_mb: float
    ram_used_mb: float
    ram_total_mb: float
    cpu_percent: float
    cpu_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'ram_percent': self.ram_percent,
            'ram_available_mb': self.ram_available_mb,
            'ram_used_mb': self.ram_used_mb,
            'ram_total_mb': self.ram_total_mb,
            'cpu_percent': self.cpu_percent,
            'cpu_count': self.cpu_count
        }


@dataclass
class ResourceLimits:
    """Resource limit thresholds."""
    # RAM limits (percentage)
    ram_warning_threshold: float = 75.0    # Warn user
    ram_critical_threshold: float = 85.0   # Deny new jobs
    ram_danger_threshold: float = 95.0     # Kill jobs if possible
    
    # CPU limits (percentage)
    cpu_warning_threshold: float = 80.0
    cpu_critical_threshold: float = 90.0
    
    # Minimum required RAM for heavy operations (MB)
    min_ram_for_analysis: float = 500.0
    min_ram_for_model_load: float = 1000.0


class ResourceMonitor(QObject):
    """
    Monitor system resources and make job admission decisions.
    
    This class prevents crashes and freezes by:
    1. Monitoring RAM/CPU continuously
    2. Warning when resources are low
    3. Denying jobs when resources are critical
    4. Providing metrics for UI display
    
    Thread Safety:
        - All methods are thread-safe
        - Emits signals on main thread
        - Can be called from worker threads
    """
    
    # Signals
    metrics_updated = Signal(dict)      # Current metrics
    warning_issued = Signal(str, str)   # (resource_type, message)
    critical_alert = Signal(str, str)   # (resource_type, message)
    resources_recovered = Signal()      # Resources back to normal
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        """
        Initialize resource monitor.
        
        Args:
            limits: Custom resource limits (uses defaults if None)
        """
        super().__init__()
        self.limits = limits or ResourceLimits()
        self._in_warning_state = False
        self._in_critical_state = False
        
        # Update timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_metrics)
        
        logger.info(f"ResourceMonitor initialized with limits: {self.limits}")
    
    def start_monitoring(self, interval_ms: int = 1000):
        """
        Start continuous resource monitoring.
        
        Args:
            interval_ms: Update interval in milliseconds
        """
        self._timer.start(interval_ms)
        logger.info(f"Resource monitoring started (interval: {interval_ms}ms)")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self._timer.stop()
        logger.info("Resource monitoring stopped")
    
    def get_current_metrics(self) -> ResourceMetrics:
        """
        Get current system resource metrics.
        
        Returns:
            ResourceMetrics object with current values
            
        Thread Safety:
            Safe to call from any thread
        """
        try:
            mem = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            metrics = ResourceMetrics(
                ram_percent=mem.percent,
                ram_available_mb=mem.available / (1024 * 1024),
                ram_used_mb=mem.used / (1024 * 1024),
                ram_total_mb=mem.total / (1024 * 1024),
                cpu_percent=cpu_percent,
                cpu_count=psutil.cpu_count()
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting resource metrics: {e}")
            # Return safe defaults
            return ResourceMetrics(0, 0, 0, 0, 0, 1)
    
    def can_start_job(self, job_type: str = "general") -> Tuple[bool, str]:
        """
        Check if system has resources to start a new job.
        
        Args:
            job_type: Type of job ("analysis", "model_load", "general")
            
        Returns:
            (can_start, reason) tuple
            
        Examples:
            >>> can_start, reason = monitor.can_start_job("analysis")
            >>> if not can_start:
            ...     show_error_dialog(reason)
        """
        metrics = self.get_current_metrics()
        
        # Check RAM
        if metrics.ram_percent >= self.limits.ram_critical_threshold:
            return False, f"Insufficient RAM: {metrics.ram_percent:.1f}% used (critical threshold: {self.limits.ram_critical_threshold}%)"
        
        # Check job-specific RAM requirements
        if job_type == "analysis" and metrics.ram_available_mb < self.limits.min_ram_for_analysis:
            return False, f"Insufficient RAM for analysis: {metrics.ram_available_mb:.0f}MB available (need {self.limits.min_ram_for_analysis:.0f}MB)"
        
        if job_type == "model_load" and metrics.ram_available_mb < self.limits.min_ram_for_model_load:
            return False, f"Insufficient RAM for model loading: {metrics.ram_available_mb:.0f}MB available (need {self.limits.min_ram_for_model_load:.0f}MB)"
        
        # Check CPU
        if metrics.cpu_percent >= self.limits.cpu_critical_threshold:
            return False, f"CPU overloaded: {metrics.cpu_percent:.1f}% usage (critical threshold: {self.limits.cpu_critical_threshold}%)"
        
        # Warn if close to limits
        if metrics.ram_percent >= self.limits.ram_warning_threshold:
            logger.warning(f"RAM usage high: {metrics.ram_percent:.1f}%")
        
        if metrics.cpu_percent >= self.limits.cpu_warning_threshold:
            logger.warning(f"CPU usage high: {metrics.cpu_percent:.1f}%")
        
        return True, "Resources available"
    
    def _update_metrics(self):
        """Internal method to update and emit metrics."""
        metrics = self.get_current_metrics()
        
        # Emit metrics for UI display
        self.metrics_updated.emit(metrics.to_dict())
        
        # Check for warnings
        if metrics.ram_percent >= self.limits.ram_critical_threshold:
            if not self._in_critical_state:
                self._in_critical_state = True
                self.critical_alert.emit(
                    "RAM",
                    f"Critical RAM usage: {metrics.ram_percent:.1f}% - New jobs will be denied"
                )
        elif metrics.ram_percent >= self.limits.ram_warning_threshold:
            if not self._in_warning_state:
                self._in_warning_state = True
                self.warning_issued.emit(
                    "RAM",
                    f"High RAM usage: {metrics.ram_percent:.1f}%"
                )
        else:
            # Resources recovered
            if self._in_warning_state or self._in_critical_state:
                self._in_warning_state = False
                self._in_critical_state = False
                self.resources_recovered.emit()
        
        # Similar for CPU
        if metrics.cpu_percent >= self.limits.cpu_critical_threshold:
            if not self._in_critical_state:
                self.critical_alert.emit(
                    "CPU",
                    f"Critical CPU usage: {metrics.cpu_percent:.1f}%"
                )
        elif metrics.cpu_percent >= self.limits.cpu_warning_threshold:
            if not self._in_warning_state:
                self.warning_issued.emit(
                    "CPU",
                    f"High CPU usage: {metrics.cpu_percent:.1f}%"
                )
    
    def get_optimal_thread_count(self) -> int:
        """
        Calculate optimal thread pool size based on current resources.
        
        Returns:
            Recommended number of threads
            
        Logic:
            - Base on CPU count and current load
            - Reduce if RAM is constrained
            - Never exceed CPU count
            - Minimum of 1 thread
        """
        metrics = self.get_current_metrics()
        cpu_count = metrics.cpu_count
        
        # Start with CPU count
        optimal = cpu_count
        
        # Reduce if CPU heavily loaded
        if metrics.cpu_percent > 70:
            optimal = max(1, cpu_count // 2)
        
        # Reduce if RAM constrained
        if metrics.ram_percent > 80:
            optimal = max(1, optimal // 2)
        
        return optimal

