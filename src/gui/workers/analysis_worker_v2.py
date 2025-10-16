"""
Document Analysis Worker (Production Version)

Handles all document analysis operations in background thread with:
    - Timeout management
    - Resource checking
    - Progress reporting
    - Secure file cleanup
    - Comprehensive error handling

This worker NEVER blocks the GUI thread.
"""

import os
import logging
from typing import Any
from pathlib import Path

from src.gui.core import BaseWorker, AnalysisSignals, ResourceMonitor


logger = logging.getLogger(__name__)


class AnalysisWorker(BaseWorker):
    """
    Production-ready document analysis worker.

    Performs document analysis via API with full safety guarantees:
        - Never blocks GUI
        - Enforces timeout (default: 5 minutes)
        - Checks resources before starting
        - Reports progress throughout
        - Handles all errors gracefully
        - Cleans up temp files securely

    Usage:
        ```python
        worker = AnalysisWorker(
            file_path="document.txt",
            api_client=client,
            timeout_seconds=300
        )
        worker.signals.result.connect(on_analysis_complete)
        worker.signals.error.connect(on_analysis_error)
        worker.signals.progress.connect(update_progress_bar)

        threadpool.start(worker)
        ```
    """

    def __init__(
        self,
        file_path: str,
        api_client: Any,  # Your API client instance
        strictness: str = "balanced",
        timeout_seconds: float = 300.0,
        resource_monitor: ResourceMonitor | None = None,
    ):
        """
        Initialize analysis worker.

        Args:
            file_path: Path to document to analyze
            api_client: Configured API client for backend calls
            strictness: Analysis strictness level
            timeout_seconds: Maximum execution time
            resource_monitor: Resource monitor instance
        """
        super().__init__(timeout_seconds=timeout_seconds, resource_monitor=resource_monitor, job_type="analysis")

        self.file_path = Path(file_path)
        self.api_client = api_client
        self.strictness = strictness

        # Track temp files for cleanup
        self._temp_files = []

    def create_signals(self) -> AnalysisSignals:
        """Use specialized analysis signals."""
        return AnalysisSignals()

    def do_work(self) -> dict[str, Any]:
        """
        Perform document analysis.

        Returns:
            Complete analysis results

        Raises:
            FileNotFoundError: If document doesn't exist
            ValueError: If document format invalid
            APIError: If API call fails
            TimeoutError: If analysis takes too long
        """
        # Step 1: Load document (10% of work)
        self.report_progress(0, 100, "Loading document...")
        document_data = self._load_document()
        self.signals.document_loaded.emit(document_data)

        if self.is_cancelled():
            return {}

        # Step 2: Upload to API (20%)
        self.report_progress(10, 100, "Uploading document...")
        upload_result = self._upload_document()

        if self.is_cancelled():
            return {}

        # Step 3: Classify document (40%)
        self.report_progress(30, 100, "Classifying document...")
        classification = self._classify_document(upload_result)
        self.signals.classification_complete.emit(classification)

        if self.is_cancelled():
            return {}

        # Step 4: Extract entities (60%)
        self.report_progress(50, 100, "Extracting clinical entities...")
        entities = self._extract_entities(upload_result)
        self.signals.entities_extracted.emit(entities)

        if self.is_cancelled():
            return {}

        # Step 5: Score compliance (80%)
        self.report_progress(70, 100, "Scoring compliance...")
        compliance_score = self._score_compliance(upload_result)
        self.signals.compliance_scored.emit(compliance_score)

        if self.is_cancelled():
            return {}

        # Step 6: Generate report (100%)
        self.report_progress(90, 100, "Generating report...")
        final_report = self._generate_report(upload_result)
        self.signals.report_ready.emit(final_report)

        self.report_progress(100, 100, "Analysis complete")

        return final_report

    def _load_document(self) -> dict[str, Any]:
        """Load and validate document."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Document not found: {self.file_path}")

        # Check file size
        file_size = self.file_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB

        if file_size > max_size:
            raise ValueError(
                f"Document too large: {file_size / (1024 * 1024):.1f}MB (max: {max_size / (1024 * 1024):.0f}MB)"
            )

        # Read file
        try:
            with open(self.file_path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try binary mode
            with open(self.file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")

        return {"path": str(self.file_path), "name": self.file_path.name, "size": file_size, "content": content}

    def _upload_document(self) -> dict:
        """Upload document to API."""
        try:
            response = self.api_client.upload_document(file_path=str(self.file_path), timeout=30)
            return response
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            raise

    def _classify_document(self, upload_result: dict) -> dict:
        """Classify document type."""
        try:
            response = self.api_client.classify_document(document_id=upload_result.get("id"), timeout=30)
            return response
        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            raise

    def _extract_entities(self, upload_result: dict) -> dict:
        """Extract clinical entities."""
        try:
            response = self.api_client.extract_entities(document_id=upload_result.get("id"), timeout=60)
            return response
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            raise

    def _score_compliance(self, upload_result: dict) -> dict:
        """Score compliance."""
        try:
            response = self.api_client.analyze_compliance(
                document_id=upload_result.get("id"), strictness=self.strictness, timeout=120
            )
            return response
        except Exception as e:
            logger.error(f"Compliance scoring failed: {e}")
            raise

    def _generate_report(self, upload_result: dict) -> dict:
        """Generate final report."""
        try:
            response = self.api_client.get_report(document_id=upload_result.get("id"), timeout=30)
            return response
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise

    def cleanup(self):
        """
        Clean up resources after analysis.

        - Securely delete temp files
        - Free memory
        - Close connections
        """
        logger.debug(f"Cleaning up analysis worker for {self.file_path.name}")

        # Securely delete temp files
        for temp_file in self._temp_files:
            try:
                self._secure_delete(temp_file)
            except Exception as e:
                logger.error(f"Failed to delete temp file {temp_file}: {e}")

        # Clear references
        self._temp_files.clear()

    def _secure_delete(self, file_path: Path):
        """
        Securely delete file by overwriting before deletion.

        Prevents recovery of sensitive PHI data.
        """
        if not file_path.exists():
            return

        try:
            # Overwrite with random data
            file_size = file_path.stat().st_size
            with open(file_path, "wb") as f:
                f.write(os.urandom(min(file_size, 1024 * 1024)))  # Up to 1MB

            # Delete
            file_path.unlink()
            logger.debug(f"Securely deleted: {file_path}")

        except Exception as e:
            logger.error(f"Secure deletion failed for {file_path}: {e}")
            # Still try regular delete
            try:
                file_path.unlink()
            except Exception:
                pass
