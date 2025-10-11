import json
import os

import httpx
import requests
from PySide6.QtCore import QObject, Signal
from requests.exceptions import HTTPError

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


import logging

logger = logging.getLogger(__name__)

class AnalysisStarterWorker(QObject):
    """A one-shot worker to start analysis using the httpx library."""

    success = Signal(str)
    error = Signal(str)
    finished = Signal() # Added finished signal

    def __init__(self, file_path: str, data: dict, token: str):
        super().__init__()
        self.file_path = file_path
        self.data = data
        self.token = token

    def run(self):
        """Sends the request to start the analysis and emits the result."""
        logger.debug("AnalysisStarterWorker run started for file: %s", os.path.basename(self.file_path))
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            with open(self.file_path, "rb") as f:
                files = {"file": (os.path.basename(self.file_path), f, "application/octet-stream")}
                logger.debug("Sending analysis request to %s/analysis/analyze", API_URL)
                with httpx.Client() as client:
                    response = client.post(
                        f"{API_URL}/analysis/analyze",
                        files=files,
                        data=self.data,
                        headers=headers,
                        timeout=120.0,  # Increased timeout for file upload and task creation
                    )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            logger.debug("Analysis started successfully, task_id: %s", task_id)
            self.success.emit(task_id)

        except httpx.RequestError as e:
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except (TypeError, ValueError, json.JSONDecodeError):
                    pass
            logger.error("Failed to start analysis: %s", error_detail)
            self.error.emit(f"Failed to start analysis: {error_detail}")
        except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
            logger.error("An unexpected error occurred during analysis start: %s", e)
            self.error.emit(f"An unexpected error occurred: {e}")
        finally:
            logger.debug("AnalysisStarterWorker run finished.")
            self.finished.emit() # Emit finished signal
