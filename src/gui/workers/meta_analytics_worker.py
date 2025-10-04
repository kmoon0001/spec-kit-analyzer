"""
Meta Analytics Worker for background data loading.

Handles API calls to fetch organizational analytics data without blocking the UI.
Follows the established worker patterns for consistency with other GUI workers.
"""

import logging
from typing import Any, Dict, Optional

import requests
from PySide6.QtCore import QObject, Signal

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MetaAnalyticsWorker(QObject):
    """Background worker for loading meta analytics data."""

    success = Signal(dict)  # Consistent with other workers
    error = Signal(str)
    finished = Signal()  # Standard completion signal
    progress_updated = Signal(str)

    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.base_url = settings.paths.api_url.rstrip("/")
        self.token = token
        self.days_back = 90
        self.discipline = None
        self.load_type = "overview"

    def set_parameters(
        self,
        days_back: int = 90,
        discipline: Optional[str] = None,
        load_type: str = "overview",
    ):
        """Set parameters for the data loading."""
        self.days_back = days_back
        self.discipline = discipline
        self.load_type = load_type

    def set_peer_comparison(self, user_id: int, days_back: int = 90):
        """Convenience method to set up peer comparison for a specific user."""
        self.days_back = days_back
        self.load_type = f"peer_comparison_{user_id}"

    def run(self):
        """Main worker thread execution."""
        try:
            self.progress_updated.emit("Loading organizational analytics...")

            headers = {"Authorization": f"Bearer {self.token}"}

            if self.load_type == "overview":
                data = self.load_organizational_overview(headers)
            elif self.load_type == "training":
                data = self.load_training_needs(headers)
            elif self.load_type == "trends":
                data = self.load_team_trends(headers)
            elif self.load_type == "benchmarks":
                data = self.load_benchmarks(headers)
            elif self.load_type == "alerts":
                data = self.load_performance_alerts(headers)
            elif self.load_type == "discipline_comparison":
                data = self.load_discipline_comparison(headers)
            elif self.load_type.startswith("peer_comparison_"):
                # Extract user_id from load_type like "peer_comparison_123"
                user_id = int(self.load_type.split("_")[-1])
                data = self.load_peer_comparison(headers, user_id)
            else:
                data = self.load_organizational_overview(headers)

            self.progress_updated.emit("Analytics loaded successfully")
            self.success.emit(data)

        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except requests.exceptions.JSONDecodeError:
                    pass
            logger.exception("Failed to load meta analytics data")
            self.error.emit(f"Failed to load analytics: {error_detail}")
        except Exception as e:
            logger.exception("Unexpected error loading meta analytics data")
            self.error.emit(f"An unexpected error occurred: {str(e)}")
        finally:
            self.finished.emit()

    def load_organizational_overview(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Load comprehensive organizational overview."""
        self.progress_updated.emit("Loading organizational overview...")

        params = {"days_back": self.days_back}
        if self.discipline:
            params["discipline"] = self.discipline

        response = requests.get(
            f"{self.base_url}/meta-analytics/organizational-overview",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def load_training_needs(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Load training needs analysis."""
        self.progress_updated.emit("Analyzing training needs...")

        params = {"days_back": self.days_back}
        if self.discipline:
            params["discipline"] = self.discipline

        response = requests.get(
            f"{self.base_url}/meta-analytics/training-needs",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def load_team_trends(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Load team performance trends."""
        self.progress_updated.emit("Loading performance trends...")

        weeks_back = max(4, self.days_back // 7)
        params = {"weeks_back": weeks_back}
        if self.discipline:
            params["discipline"] = self.discipline

        response = requests.get(
            f"{self.base_url}/meta-analytics/team-trends",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def load_benchmarks(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Load benchmarking data."""
        self.progress_updated.emit("Loading benchmark data...")

        params = {"days_back": self.days_back}

        response = requests.get(
            f"{self.base_url}/meta-analytics/benchmarks",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def load_performance_alerts(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Load performance alerts for immediate attention."""
        self.progress_updated.emit("Loading performance alerts...")

        response = requests.get(
            f"{self.base_url}/meta-analytics/performance-alerts",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def load_discipline_comparison(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Load discipline comparison data."""
        self.progress_updated.emit("Loading discipline comparison...")

        params = {"days_back": self.days_back}

        response = requests.get(
            f"{self.base_url}/meta-analytics/discipline-comparison",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def load_peer_comparison(
        self, headers: Dict[str, str], user_id: int
    ) -> Dict[str, Any]:
        """Load peer comparison data for a specific user."""
        self.progress_updated.emit("Loading peer comparison...")

        params = {"days_back": self.days_back}

        response = requests.get(
            f"{self.base_url}/meta-analytics/peer-comparison/{user_id}",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()
