"""
GUI Core Threading Infrastructure

Production-ready threading components for stable, responsive PySide6 applications.

Key Components:
    - WorkerSignals: Thread-safe signal classes for GUI communication
    - BaseWorker: Robust base class for all background operations  
    - ResourceMonitor: System resource monitoring and job admission control
    
Architecture Principles:
    1. NEVER block the GUI thread
    2. ALWAYS use signals for thread→GUI communication
    3. Handle ALL exceptions gracefully
    4. Enforce timeouts on all operations
    5. Check resources before starting jobs
    6. Clean up properly after completion
    
Usage Example:
    ```python
    from PySide6.QtWidgets import QMainWindow
    from PySide6.QtCore import QThreadPool
    from src.gui.core import BaseWorker, ResourceMonitor
    
    class MyWorker(BaseWorker):
        def do_work(self):
            # Your work here
            return result
        
        def cleanup(self):
            # Cleanup here
            pass
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.threadpool = QThreadPool()
            self.resource_monitor = ResourceMonitor()
            self.resource_monitor.start_monitoring()
        
        def start_task(self):
            worker = MyWorker(resource_monitor=self.resource_monitor)
            worker.signals.result.connect(self.on_result)
            worker.signals.error.connect(self.on_error)
            self.threadpool.start(worker)
        
        def on_result(self, data):
            # Update GUI safely
            pass
        
        def on_error(self, error_tuple):
            # Handle error safely
            pass
    ```
"""

from .worker_signals import (
    WorkerSignals,
    AnalysisSignals,
    APISignals,
    FileSignals,
    WebSocketSignals
)
from .resource_monitor import (
    ResourceMonitor,
    ResourceMetrics,
    ResourceLimits
)
from .base_worker import (
    BaseWorker,
    ResourceError
)
from .resource_manager import (
    ResourceManager,
    JobPriority,
    Job
)

from ._qt_threadpool_patch import ensure_threadpool_wait_patch

ensure_threadpool_wait_patch()

__all__ = [
    # Signals
    'WorkerSignals',
    'AnalysisSignals',
    'APISignals',
    'FileSignals',
    'WebSocketSignals',
    
    # Resource Management
    'ResourceMonitor',
    'ResourceMetrics',
    'ResourceLimits',
    'ResourceManager',
    'JobPriority',
    'Job',
    
    # Workers
    'BaseWorker',
    'ResourceError',
]

