"""
Worker for the Synergy Session feature.
"""
import logging
import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from ...config import get_settings

settings = get_settings()
API_URL = settings.api_url

logger = logging.getLogger(__name__)

class SynergyWorker(QObject):
    """
    Worker thread that calls the synergy session API endpoint.
    """
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, scenario: str, token: str):
        super().__init__()
        self.scenario = scenario
        self.token = token

    @pyqtSlot()
    def run(self):
        """Execute the synergy session request."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {"scenario": self.scenario}

            logger.info("Sending synergy session request to API.")
            response = requests.post(f"{API_URL}/synergy/synergy-session", json=payload, headers=headers, timeout=120)

            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"Synergy API error: {response.status_code} - {error_detail}")
                self.error.emit(f"API Error ({response.status_code}): {error_detail}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Synergy request failed: {e}", exc_info=True)
            self.error.emit(f"A network error occurred: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in SynergyWorker: {e}", exc_info=True)
            self.error.emit(f"An unexpected error occurred: {e}")
        finally:
            self.finished.emit()