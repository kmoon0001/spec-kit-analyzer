import requests
import logging
from typing import Any, Dict, Optional

from src.config import get_settings

logger = logging.getLogger(__name__)

class ApiClient:
    """A dedicated client for interacting with the backend API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session = requests.Session()

    def set_token(self, token: Optional[str]):
        """Set the authentication token for subsequent requests."""
        self.token = token
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            self.session.headers.pop("Authorization", None)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Perform a GET request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self._handle_api_error(e)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, files: Optional[Dict] = None) -> Any:
        """Perform a POST request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=data, files=files, timeout=60)
            response.raise_for_status()
            # Handle cases where the response might be empty
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            self._handle_api_error(e)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Perform a PUT request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.put(url, json=data, timeout=30)
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            self._handle_api_error(e)

    def delete(self, endpoint: str) -> Any:
        """Perform a DELETE request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.delete(url, timeout=30)
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            self._handle_api_error(e)

    def _handle_api_error(self, e: requests.exceptions.RequestException):
        """Centralized error handling for API requests."""
        if e.response is not None:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except requests.exceptions.JSONDecodeError:
                detail = e.response.text
            logger.error("API request failed with status %s: %s", e.response.status_code, detail)
            raise ApiException(detail, status_code=e.response.status_code) from e
        else:
            logger.error("API request failed without a response: %s", e)
            raise ApiException("Network error: Could not connect to the API.") from e


class ApiException(Exception):
    """Custom exception for API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message

# Singleton instance to be used across the GUI application
api_client = ApiClient(base_url=get_settings().api_url)