"""
Worker Signals for Thread-Safe Communication

This module provides standardized signal classes for safe communication
between worker threads and the GUI main thread. All GUI updates MUST
occur via these signals to prevent crashes and race conditions.

Architecture Pattern:
    Worker Thread (QRunnable) → Emit Signal → Main Thread (GUI) → Update UI

Never call GUI methods directly from worker threads!
"""

from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    """
    Standard signals for all worker threads.

    All workers should use these signals to communicate with the main GUI thread.
    This ensures thread-safe UI updates and proper error handling.

    Signals:
        started: Emitted when worker begins execution
        finished: Emitted when worker completes (success or failure)
        result: Emitted with successful result data
        error: Emitted with (exception_type, exception_value, traceback_string)
        progress: Emitted with (current, total, message) for progress updates
        status: Emitted with status message string for user feedback
        cancelled: Emitted when worker is cancelled/aborted
        resource_warning: Emitted when resource constraints detected
    """

    # Basic lifecycle signals
    started = Signal()
    finished = Signal()
    cancelled = Signal()

    # Data signals
    result = Signal(object)  # Any successful result
    error = Signal(tuple)  # (exc_type, exc_value, traceback_str)

    # Progress signals
    progress = Signal(int, int, str)  # (current, total, message)
    status = Signal(str)  # Status message for user

    # Resource signals
    resource_warning = Signal(str)  # RAM/CPU warning message


class AnalysisSignals(WorkerSignals):
    """
    Specialized signals for document analysis workers.

    Extends WorkerSignals with analysis-specific events.
    """

    # Analysis-specific signals
    document_loaded = Signal(dict)  # Document metadata
    classification_complete = Signal(dict)  # Classification results
    entities_extracted = Signal(dict)  # NER results
    compliance_scored = Signal(dict)  # Compliance score
    report_ready = Signal(dict)  # Final report data


class APISignals(WorkerSignals):
    """
    Specialized signals for API/network workers.

    Handles API-specific events like timeouts, retries, and network errors.
    """

    # Network-specific signals
    request_sent = Signal(str)  # Request details
    response_received = Signal(dict)  # Response data
    retry_attempted = Signal(int, str)  # (attempt_number, reason)
    timeout_warning = Signal(float)  # Seconds until timeout
    network_error = Signal(str)  # Network error details


class FileSignals(WorkerSignals):
    """
    Specialized signals for file I/O workers.

    Handles file processing, secure deletion, and I/O errors.
    """

    # File-specific signals
    file_opened = Signal(str)  # File path
    file_chunk_read = Signal(int, int)  # (bytes_read, total_bytes)
    file_saved = Signal(str)  # Saved file path
    file_deleted = Signal(str)  # Deleted file path (after secure wipe)
    io_error = Signal(str, str)  # (file_path, error_message)


class WebSocketSignals(WorkerSignals):
    """
    Specialized signals for WebSocket workers.

    Handles real-time bidirectional communication.
    """

    # WebSocket-specific signals
    connected = Signal(str)  # WebSocket URL
    disconnected = Signal(str)  # Disconnect reason
    message_received = Signal(dict)  # Incoming message
    connection_error = Signal(str)  # Connection error details
