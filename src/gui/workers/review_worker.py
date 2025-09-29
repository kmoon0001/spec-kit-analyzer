"""
Worker for the Collaborative Review Mode feature.
"""
import logging
import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from ...config import get_settings

settings = get_settings()
API_URL = settings.api_url

logger = logging.getLogger(__name__)

class ReviewRequestWorker(QObject):
    """
    Worker thread that calls the API endpoint to request a review for a report.
    """
    success = pyqtSignal(str)  # Emits a success message
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, report_id: int, token: str):
        super().__init__()
        self.report_id = report_id
        self.token = token

    @pyqtSlot()
    def run(self):
        """Execute the review request."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            logger.info(f"Requesting review for report ID: {self.report_id}")
            response = requests.post(f"{API_URL}/reviews/reports/{self.report_id}/request-review", headers=headers, timeout=30)

            if response.status_code == 200:
                self.success.emit("Successfully requested review. A supervisor will be notified.")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"Review request API error: {response.status_code} - {error_detail}")
                self.error.emit(f"API Error ({response.status_code}): {error_detail}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Review request failed: {e}", exc_info=True)
            self.error.emit(f"A network error occurred: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in ReviewRequestWorker: {e}", exc_info=True)
            self.error.emit(f"An unexpected error occurred: {e}")
        finally:
            self.finished.emit()