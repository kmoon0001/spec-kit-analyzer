import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestComplianceAPI:
    """Test suite for the compliance evaluation API endpoint."""

    async def test_evaluate_endpoint_success_one_finding(
        self, authenticated_client: AsyncClient
    ):
        """
        Test the /evaluate endpoint with a document that should trigger exactly one finding.
        This document satisfies all rules except for the 'Goals' rule.
        """
        payload = {
            "id": "doc1",
            "text": "The patient's main goal is to improve ambulation. The therapist signed the document, establishing medical necessity and referencing the plan of care.",
            "discipline": "pt",
            "document_type": "Progress Note",
        }
        response = await authenticated_client.post("/compliance/evaluate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert not data["is_compliant"]
        assert (
            len(data["findings"]) == 1
        ), f"Expected 1 finding, but got {len(data['findings'])}"
        assert "goals" in data["findings"][0]["rule"]["issue_title"].lower()

    async def test_evaluate_endpoint_fully_compliant(
        self, authenticated_client: AsyncClient
    ):
        """
        Test the /evaluate endpoint with a document that should be fully compliant.
        """
        payload = {
            "id": "doc2",
            "text": "The patient's main goal is to improve ambulation, which is a measurable goal. The therapist signed the document, establishing medical necessity and referencing the plan of care.",
            "discipline": "pt",
            "document_type": "Progress Note",
        }
        response = await authenticated_client.post("/compliance/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"], (
            "Expected document to be compliant, but it had findings: "
            f"{[f['rule']['issue_title'] for f in data['findings']]}"
        )
        assert len(data["findings"]) == 0

    async def test_evaluate_endpoint_missing_signature(
        self, authenticated_client: AsyncClient
    ):
        """
        Test a document that is missing a required keyword (signature), but satisfies other rules.
        """
        payload = {
            "id": "doc3",
            "text": "The patient is progressing well. Medical necessity is established and we are following the plan of care.",
            "discipline": "pt",
            "document_type": "Evaluation",
        }
        response = await authenticated_client.post("/compliance/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert not data["is_compliant"]
        assert (
            len(data["findings"]) == 1
        ), f"Expected 1 finding, but got {len(data['findings'])}"
        assert "signature" in data["findings"][0]["rule"]["issue_title"].lower()

    async def test_evaluate_endpoint_bad_request(
        self, authenticated_client: AsyncClient
    ):
        """Test the /evaluate endpoint with an invalid payload."""
        payload = {
            "id": "doc4",
            "text": "This is a test.",
            # Missing discipline and document_type
        }
        response = await authenticated_client.post("/compliance/evaluate", json=payload)
        assert response.status_code == 422  # Unprocessable Entity
