# Production-Ready PySide6 Architecture

## 🎯 Overview

This document describes the **production-grade threading architecture** implemented for the Therapy Compliance Analyzer GUI application.

---

## 🏗️ Core Architecture Components

### 1. **Threading Infrastructure** (`src/gui/core/`)

#### **WorkerSignals** (`worker_signals.py`)
Thread-safe signal classes for GUI communication.

**Classes:**
- `WorkerSignals`: Base signals (started, finished, result, error, progress, status, cancelled, resource_warning)
- `AnalysisSignals`: Analysis-specific (document_loaded, classification_complete, entities_extracted, compliance_scored, report_ready)
- `APISignals`: Network-specific (request_sent, response_received, retry_attempted, timeout_warning, network_error)
- `FileSignals`: File I/O specific (file_opened, file_chunk_read, file_saved, file_deleted, io_error)
- `WebSocketSignals`: Real-time communication (connected, disconnected, message_received, connection_error)

**Key Benefits:**
- ✅ Type-safe signal definitions
- ✅ Consistent interface across all workers
- ✅ Specialized signals for specific operations

---

#### **ResourceMonitor** (`resource_monitor.py`)
System resource monitoring and job admission control.

**Features:**
- Real-time RAM/CPU monitoring
- Configurable thresholds (warning, critical, danger)
- Job admission decisions (`can_start_job()`)
- Optimal thread count calculation
- Resource recovery detection

**Usage:**
```python
monitor = ResourceMonitor()
monitor.start_monitoring(interval_ms=1000)

# Check before starting job
can_start, reason = monitor.can_start_job("analysis")
if not can_start:
    show_error_dialog(reason)
```

**Thresholds:**
- RAM Warning: 75%
- RAM Critical: 85% (deny new jobs)
- RAM Danger: 95% (kill jobs if possible)
- Min RAM for analysis: 500MB
- Min RAM for model load: 1000MB

---

#### **BaseWorker** (`base_worker.py`)
Abstract base class for all background workers.

**Responsibilities:**
- Automatic exception handling
- Timeout enforcement
- Resource checking before execution
- Progress reporting
- Cancellation support
- Automatic cleanup

**Subclass Pattern:**
```python
class MyWorker(BaseWorker):
    def create_signals(self):
        return WorkerSignals()
    
    def do_work(self):
        # Your work here
        self.report_progress(50, 100, "Half done...")
        return result
    
    def cleanup(self):
        # Clean up resources
        pass
```

**Safety Guarantees:**
- ✅ NEVER crashes on exceptions
- ✅ ALWAYS cleans up resources
- ✅ Enforces timeouts
- ✅ Checks resources before starting
- ✅ Reports all errors via signals

---

### 2. **Specialized Workers** (`src/gui/workers/`)

#### **AnalysisWorker** (`analysis_worker_v2.py`)
Document analysis with full safety guarantees.

**Features:**
- Step-by-step progress (loading, uploading, classifying, extracting, scoring, reporting)
- API timeout management
- Secure file cleanup
- Comprehensive error handling

**Signals Emitted:**
- `document_loaded`: Document metadata
- `classification_complete`: Classification results
- `entities_extracted`: NER results
- `compliance_scored`: Compliance scores
- `report_ready`: Final report
- `progress`: Current/total/message
- `error`: Exception details

---

#### **APIWorker** (`api_worker.py`)
Network requests with retry logic and error handling.

**Features:**
- Automatic retries with exponential backoff
- Configurable timeouts
- Connection error handling
- Request/response validation
- Progress reporting

**Usage:**
```python
worker = APIWorker(
    method='POST',
    endpoint='/analyze',
    json_data={'text': 'document'},
    timeout=30,
    max_retries=3
)
worker.signals.result.connect(on_success)
worker.signals.retry_attempted.connect(on_retry)
threadpool.start(worker)
```

---

#### **FileReadWorker, FileWriteWorker** (`file_worker.py`)
File I/O with progress and safety.

**Features:**
- Chunked reading for large files
- Atomic writes (temp file + rename)
- Encoding detection
- Progress updates
- Error recovery

---

#### **SecureFileDeleteWorker** (`file_worker.py`)
Secure file deletion for PHI/PII protection.

**Features:**
- Multiple-pass overwrite with random data
- Verification
- Batch deletion
- Progress reporting

**Usage:**
```python
worker = SecureFileDeleteWorker(
    file_paths=['/tmp/file1.txt', '/tmp/file2.txt'],
    overwrite_passes=3
)
worker.signals.file_deleted.connect(on_file_deleted)
threadpool.start(worker)
```

---

#### **WebSocketWorker** (`websocket_worker.py`)
Real-time WebSocket communication.

**Features:**
- Automatic reconnection
- Heartbeat/ping-pong
- Message queuing
- Clean shutdown
- Thread-safe message sending

**Usage:**
```python
worker = WebSocketWorker(
    url="ws://127.0.0.1:8001/ws/analysis/123"
)
worker.signals.message_received.connect(update_ui)
threadpool.start(worker)

# Send message from GUI
worker.send_message({'action': 'pause'})
```

---

### 3. **FastAPI WebSocket Endpoints** (`src/api/routers/websocket.py`)

#### **Analysis Progress** (`/ws/analysis/{task_id}`)
Real-time analysis progress updates.

**Message Types:**
- `progress`: Current progress (current, total, message)
- `status`: Status message
- `complete`: Analysis complete
- `error`: Error occurred
- `heartbeat`: Keep-alive

**Client Actions:**
- `ping`: Request pong
- `cancel`: Cancel analysis

---

#### **Health Monitoring** (`/ws/health`)
Real-time system health metrics.

**Streams:**
- CPU usage
- RAM usage
- API status
- Active tasks

**Update Frequency:** 1 second

---

#### **Log Streaming** (`/ws/logs`)
Real-time application logs.

**Features:**
- Live log streaming
- Filter by level
- Heartbeat keep-alive

---

## 📊 Architecture Benefits

### **1. GUI NEVER Freezes** ✅
- All heavy work in `QThreadPool`
- GUI thread only handles UI updates
- Signals ensure thread-safe communication

### **2. NO Crashes** ✅
- All exceptions caught and reported
- Resource checks prevent OOM
- Timeout prevents infinite hangs
- Clean shutdown on errors

### **3. User ALWAYS Informed** ✅
- Progress bars show real-time status
- Errors displayed with clear messages
- Resource warnings before denial
- Cancellation feedback

### **4. Secure & Clean** ✅
- Temp files securely deleted (overwrite first)
- Memory freed properly
- No resource leaks
- PHI data protected

### **5. Real-Time Updates** ✅
- WebSocket streaming (no polling)
- Low latency
- Bidirectional communication
- Automatic reconnection

---

## 🎯 Usage Patterns

### **Pattern 1: Long-Running Analysis**

```python
from PySide6.QtCore import QThreadPool
from src.gui.core import ResourceMonitor
from src.gui.workers.analysis_worker_v2 import AnalysisWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ONE threadpool for entire app
        self.threadpool = QThreadPool()
        
        # ONE resource monitor
        self.resource_monitor = ResourceMonitor()
        self.resource_monitor.start_monitoring()
        
        # Connect signals
        self.resource_monitor.warning_issued.connect(self.on_resource_warning)
    
    def analyze_document(self, file_path):
        # Create worker
        worker = AnalysisWorker(
            file_path=file_path,
            api_client=self.api_client,
            resource_monitor=self.resource_monitor
        )
        
        # Connect signals
        worker.signals.progress.connect(self.update_progress)
        worker.signals.result.connect(self.on_complete)
        worker.signals.error.connect(self.on_error)
        
        # Start (never blocks GUI!)
        self.threadpool.start(worker)
    
    def update_progress(self, current, total, message):
        # Safe - called on main thread
        self.progress_bar.setValue(int(100 * current / total))
        self.status_label.setText(message)
```

### **Pattern 2: API Call with Retries**

```python
from src.gui.workers.api_worker import APIWorker

def make_api_call(self):
    worker = APIWorker(
        method='GET',
        endpoint='/health',
        timeout=10,
        max_retries=3
    )
    
    worker.signals.result.connect(self.on_api_success)
    worker.signals.error.connect(self.on_api_error)
    worker.signals.retry_attempted.connect(self.on_retry)
    
    self.threadpool.start(worker)

def on_retry(self, attempt, reason):
    self.statusBar().showMessage(f"Retry {attempt}: {reason}")
```

### **Pattern 3: Real-Time Progress via WebSocket**

```python
from src.gui.workers.websocket_worker import AnalysisWebSocketWorker

def start_real_time_analysis(self, task_id):
    # Start WebSocket connection
    ws_worker = AnalysisWebSocketWorker(
        url=f"ws://127.0.0.1:8001/ws/analysis/{task_id}"
    )
    
    ws_worker.signals.message_received.connect(self.on_progress_update)
    ws_worker.signals.connected.connect(self.on_ws_connected)
    ws_worker.signals.disconnected.connect(self.on_ws_disconnected)
    
    self.threadpool.start(ws_worker)

def on_progress_update(self, message):
    # Real-time update (no polling!)
    if message['type'] == 'progress':
        self.progress_bar.setValue(message['current'])
        self.status_label.setText(message['message'])
```

### **Pattern 4: Secure File Cleanup**

```python
from src.gui.workers.file_worker import SecureFileDeleteWorker

def cleanup_temp_files(self):
    worker = SecureFileDeleteWorker(
        file_paths=self.temp_files,
        overwrite_passes=3
    )
    
    worker.signals.progress.connect(self.update_cleanup_progress)
    worker.signals.file_deleted.connect(self.on_file_deleted)
    
    self.threadpool.start(worker)
```

---

## 🔒 Security Features

### **1. Secure File Deletion**
- Multiple-pass overwrite with random data
- Final zero-fill pass
- Verification
- PHI protection

### **2. Resource Protection**
- RAM monitoring prevents OOM
- CPU monitoring prevents overload
- Job denial when resources critical
- Graceful degradation

### **3. Error Isolation**
- All exceptions caught
- Errors reported, never crash
- Clean state recovery
- User always informed

---

## 📈 Performance Optimizations

### **1. Adaptive Thread Pool**
- Dynamic thread count based on resources
- Reduced when RAM constrained
- Reduced when CPU overloaded
- Minimum of 1 thread

### **2. Chunked Processing**
- Large files read in chunks
- Memory-efficient streaming
- Progress reporting per chunk

### **3. WebSocket vs Polling**
- **Polling**: 1 request/second = 3600 requests/hour
- **WebSocket**: 1 connection = ~10 messages/hour
- **Savings**: 99.7% reduction in network overhead

---

## ✅ Best Practices Applied

1. ✅ **NEVER block GUI thread**
2. ✅ **ALWAYS use signals for thread→GUI communication**
3. ✅ **Handle ALL exceptions gracefully**
4. ✅ **Enforce timeouts on all operations**
5. ✅ **Check resources before starting jobs**
6. ✅ **Clean up properly after completion**
7. ✅ **Secure deletion of sensitive data**
8. ✅ **Real-time user feedback**
9. ✅ **Graceful degradation under load**
10. ✅ **Thread-safe design throughout**

---

## 🧪 Testing Scenarios

### **Covered:**
- ✅ Normal operation
- ✅ Timeout handling
- ✅ Out-of-memory scenarios
- ✅ Network failures
- ✅ File I/O errors
- ✅ Worker cancellation
- ✅ Resource exhaustion
- ✅ WebSocket reconnection

### **Verified:**
- ✅ GUI never freezes
- ✅ No crashes on errors
- ✅ Clean resource cleanup
- ✅ Accurate progress reporting
- ✅ Secure file deletion
- ✅ Real-time updates

---

## 📚 References

- [Qt QThreadPool Documentation](https://doc.qt.io/qt-6/qthreadpool.html)
- [Qt Signals & Slots](https://doc.qt.io/qt-6/signalsandslots.html)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

---

**Status:** ✅ **Production Ready**

All core threading infrastructure complete and tested.

