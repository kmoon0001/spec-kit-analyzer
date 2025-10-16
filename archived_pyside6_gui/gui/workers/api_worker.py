"""
API/Network Worker (Production Version)

Handles all API calls in background thread with:
    - Automatic retry logic
    - Timeout management
    - Network error handling
    - Request/response logging
    - Connection pooling support

NEVER makes API calls on GUI thread!
"""

import time
import logging
import requests
from typing import Any
from collections.abc import Callable
from urllib.parse import urljoin

from src.gui.core import BaseWorker, APISignals, ResourceMonitor


logger = logging.getLogger(__name__)


class APIWorker(BaseWorker):
    """
    Production-ready API call worker.

    Handles HTTP requests with:
        - Automatic retries with exponential backoff
        - Configurable timeouts
        - Connection error handling
        - Request/response validation
        - Progress reporting for long operations

    Usage:
        ```python
        worker = APIWorker(
            method='POST',
            endpoint='/analyze',
            data={'text': 'document'},
            timeout=30,
            max_retries=3
        )
        worker.signals.result.connect(on_success)
        worker.signals.error.connect(on_error)
        worker.signals.retry_attempted.connect(on_retry)

        threadpool.start(worker)
        ```
    """

    def __init__(
        self,
        method: str,
        endpoint: str,
        base_url: str = "http://127.0.0.1:8001",
        data: dict | None = None,
        json_data: dict | None = None,
        headers: dict | None = None,
        files: dict | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        resource_monitor: ResourceMonitor | None = None,
    ):
        """
        Initialize API worker.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/analyze')
            base_url: Base API URL
            data: Form data
            json_data: JSON data
            headers: Request headers
            files: Files to upload
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_delay: Initial delay between retries (doubles each time)
            resource_monitor: Resource monitor instance
        """
        # Total timeout = timeout * (max_retries + 1)
        super().__init__(
            timeout_seconds=timeout * (max_retries + 1), resource_monitor=resource_monitor, job_type="general"
        )

        self.method = method.upper()
        self.endpoint = endpoint
        self.base_url = base_url
        self.data = data
        self.json_data = json_data
        self.headers = headers or {}
        self.files = files
        self.request_timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Build full URL
        self.url = urljoin(self.base_url, self.endpoint)

    def create_signals(self) -> APISignals:
        """Use specialized API signals."""
        return APISignals()

    def do_work(self) -> dict[str, Any]:
        """
        Execute API request with retry logic.

        Returns:
            Response data (JSON parsed)

        Raises:
            requests.RequestException: On network errors
            requests.Timeout: On timeout
            requests.HTTPError: On HTTP errors (4xx, 5xx)
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            if self.is_cancelled():
                return {}

            try:
                # Emit request sent signal
                self.signals.request_sent.emit(
                    f"{self.method} {self.url} (attempt {attempt + 1}/{self.max_retries + 1})"
                )

                # Make request
                response = self._make_request()

                # Check response
                response.raise_for_status()

                # Parse JSON response
                try:
                    result = response.json()
                except ValueError:
                    # Not JSON, return text
                    result = {"text": response.text}

                # Emit success signal
                self.signals.response_received.emit(result)

                return result

            except requests.Timeout as e:
                last_exception = e
                logger.warning(f"Request timeout (attempt {attempt + 1}): {self.url}")

                if attempt < self.max_retries:
                    self._handle_retry(attempt, "Timeout")
                else:
                    raise

            except requests.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries:
                    self._handle_retry(attempt, "Connection Error")
                else:
                    self.signals.network_error.emit(str(e))
                    raise

            except requests.HTTPError as e:
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    logger.error(f"HTTP client error: {e.response.status_code}")
                    raise

                # Retry on 5xx errors (server errors)
                last_exception = e
                logger.warning(f"HTTP server error (attempt {attempt + 1}): {e.response.status_code}")

                if attempt < self.max_retries:
                    self._handle_retry(attempt, f"HTTP {e.response.status_code}")
                else:
                    raise

            except Exception as e:
                # Unknown error - don't retry
                logger.error(f"Unexpected error in API request: {e}")
                raise

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception

        raise RuntimeError("API request failed without exception")

    def _make_request(self) -> requests.Response:
        """
        Make the actual HTTP request.

        Returns:
            Response object
        """
        return requests.request(
            method=self.method,
            url=self.url,
            data=self.data,
            json=self.json_data,
            headers=self.headers,
            files=self.files,
            timeout=self.request_timeout,
        )

    def _handle_retry(self, attempt: int, reason: str):
        """
        Handle retry logic with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)
            reason: Reason for retry
        """
        delay = self.retry_delay * (2**attempt)  # Exponential backoff

        self.signals.retry_attempted.emit(attempt + 1, reason)
        self.report_status(f"Retrying in {delay:.1f}s due to {reason}...")

        # Sleep with cancellation check
        sleep_start = time.time()
        while time.time() - sleep_start < delay:
            if self.is_cancelled():
                return
            time.sleep(0.1)

    def cleanup(self):
        """Clean up resources."""
        # Close any open connections, files, etc.
        logger.debug(f"API worker cleanup: {self.method} {self.url}")


class StreamingAPIWorker(APIWorker):
    """
    API worker for streaming responses (e.g., SSE, chunked transfer).

    Reports progress as chunks are received.
    """

    def __init__(self, *args, chunk_callback: Callable[[bytes], None] | None = None, **kwargs):
        """
        Initialize streaming API worker.

        Args:
            chunk_callback: Called for each received chunk
            *args, **kwargs: Passed to APIWorker
        """
        super().__init__(*args, **kwargs)
        self.chunk_callback = chunk_callback
        self._chunks = []

    def _make_request(self) -> requests.Response:
        """Make streaming request."""
        response = requests.request(
            method=self.method,
            url=self.url,
            data=self.data,
            json=self.json_data,
            headers=self.headers,
            files=self.files,
            timeout=self.request_timeout,
            stream=True,  # Enable streaming
        )

        # Process chunks
        total_bytes = 0
        for chunk in response.iter_content(chunk_size=8192):
            if self.is_cancelled():
                break

            if chunk:
                total_bytes += len(chunk)
                self._chunks.append(chunk)

                # Report progress
                self.report_progress(total_bytes, total_bytes, f"Received {total_bytes} bytes")

                # Call chunk callback
                if self.chunk_callback:
                    self.chunk_callback(chunk)

        # Reconstruct response
        response._content = b"".join(self._chunks)
        return response
