from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EHRConnector(ABC):
    """
    An abstract base class defining the interface for connecting to an
    external Electronic Health Record (EHR) system.

    This provides a blueprint for future integrations with systems like
    NetHealth, PointClickCare, or others.
    """

    @abstractmethod
    def __init__(self, api_config: Dict[str, Any]):
        """
        Initializes the connector with the necessary API configuration,
        such as base URL, API keys, or authentication credentials.
        """
        pass

    @abstractmethod
    def fetch_documents(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Fetches a list of available documents for a given patient.

        Args:
            patient_id: The unique identifier for the patient in the EHR system.

        Returns:
            A list of dictionaries, where each dictionary represents a document
            and should contain at least 'document_id' and 'document_name'.
            Example: [{"document_id": "123", "document_name": "PT Eval - 2023-10-27"}]
        """
        pass

    @abstractmethod
    def download_document(self, document_id: str) -> str:
        """
        Downloads the content of a specific document from the EHR.

        Args:
            document_id: The unique identifier for the document.

        Returns:
            The full text content of the document as a string.
        """
        pass

    @abstractmethod
    def upload_report(self, patient_id: str, report_html: str) -> bool:
        """
        Uploads the generated compliance report back to the patient's record in the EHR.

        Args:
            patient_id: The unique identifier for the patient.
            report_html: The full HTML content of the compliance report.

        Returns:
            True if the upload was successful, False otherwise.
        """
        pass
