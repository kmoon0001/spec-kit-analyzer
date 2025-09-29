"""
Worker for the supervisor's Review Dashboard.
"""
import logging
import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import List, Dict, Any

from ...config import get_settings

settings = get_settings()
API_URL = settings.api_url

logger = logging.getLogger(__name__)

class ReviewDashboardWorker(QObject):
    """
    Worker thread that calls the API to get a list of pending reviews.
    """
    success = pyqtSignal(list)  # Emits a list of pending review dictionaries
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, token: str):
        super().__init__()
        self.token = token

    @pyqtSlot()
    def run(self):
        """Execute the request to get pending reviews."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            logger.info("Fetching pending reviews for supervisor.")
            response = requests.get(f"{API_URL}/reviews/reviews/pending", headers=headers, timeout=30)

            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"Fetch pending reviews API error: {response.status_code} - {error_detail}")
                self.error.emit(f"API Error ({response.status_code}): {error_detail}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Fetch pending reviews failed: {e}", exc_info=True)
            self.error.emit(f"A network error occurred: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in ReviewDashboardWorker: {e}", exc_info=True)
            self.error.emit(f"An unexpected error occurred: {e}")
        finally:
            self.finished.emit()