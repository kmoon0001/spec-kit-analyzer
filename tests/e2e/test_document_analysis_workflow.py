"""
E2E Test: Complete Document Analysis Workflow

Tests the complete user journey from document upload through analysis to report export.
This is the core workflow that users will experience most frequently.
"""

import time
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.conftest import E2ETestHelper


def _extract_rubric_id(rubric: dict[str, Any]) -> str:
    """Return rubric identifier compatible with legacy analysis endpoints."""
    value = rubric.get("value", rubric.get("id"))
    return str(value) if value is not None else ""


class TestDocumentAnalysisWorkflow:
    """Test complete document analysis workflow end-to-end."""

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(
        self,
        e2e_helper: E2ETestHelper,
        sample_document_file: Path,
        test_rubric_data: dict[str, Any],
        e2e_test_config: dict[str, Any],
    ):
        """
        Test the complete document analysis workflow.

        Workflow Steps:
        1. Upload document
        2. Select rubric
        3. Start analysis
        4. Monitor progress
        5. Retrieve results
        6. Export report
        """
        # Step 1: Upload document
        print("Step 1: Uploading document...")
        upload_response = e2e_helper.upload_document(sample_document_file)

        assert "document_id" in upload_response
        assert upload_response["status"] == "success"
        document_id = upload_response["document_id"]

        # Step 2: Verify document is accessible
        print("Step 2: Verifying document accessibility...")
        doc_response = e2e_helper.client.get(f"/documents/{document_id}", headers=e2e_helper.headers)
        assert doc_response.status_code == 200
        doc_data = doc_response.json()
        assert doc_data["id"] == document_id
        assert "content" in doc_data

        # Step 3: Get available rubrics
        print("Step 3: Getting available rubrics...")
        rubrics_response = e2e_helper.client.get("/rubrics", headers=e2e_helper.headers)
        assert rubrics_response.status_code == 200
        rubrics = rubrics_response.json()["rubrics"]
        assert len(rubrics) > 0

        # Use first available rubric
        rubric_id = _extract_rubric_id(rubrics[0])

        # Step 4: Start analysis
        print("Step 4: Starting analysis...")
        start_time = time.time()
        analysis_response = e2e_helper.start_analysis(document_id, rubric_id)

        assert "task_id" in analysis_response
        assert analysis_response["status"] == "started"
        task_id = analysis_response["task_id"]

        # Step 5: Wait for analysis completion
        print("Step 5: Waiting for analysis completion...")
        results = e2e_helper.wait_for_analysis(
            task_id, timeout=e2e_test_config["performance_thresholds"]["document_analysis"]
        )

        analysis_time = time.time() - start_time
        print(f"Analysis completed in {analysis_time:.2f} seconds")

        # Verify analysis results
        assert results["status"] == "completed"
        assert "findings" in results
        assert "overall_score" in results
        assert isinstance(results["overall_score"], int | float)
        assert 0 <= results["overall_score"] <= 100

        # Step 6: Verify findings structure
        print("Step 6: Verifying findings structure...")
        findings = results["findings"]
        assert isinstance(findings, list)

        for finding in findings:
            assert "id" in finding
            assert "title" in finding
            assert "description" in finding
            assert "severity" in finding
            assert finding["severity"] in ["low", "medium", "high"]
            assert "confidence" in finding
            assert 0 <= finding["confidence"] <= 1

        # Step 7: Export report to PDF
        print("Step 7: Exporting report to PDF...")
        pdf_start_time = time.time()
        pdf_response = e2e_helper.client.post(f"/export-pdf/{task_id}", headers=e2e_helper.headers)
        pdf_export_time = time.time() - pdf_start_time

        assert pdf_response.status_code == 200
        pdf_result = pdf_response.json()
        assert pdf_result["success"] is True
        assert "pdf_info" in pdf_result

        print(f"PDF export completed in {pdf_export_time:.2f} seconds")

        # Verify performance thresholds
        assert analysis_time <= e2e_test_config["performance_thresholds"]["document_analysis"]
        assert pdf_export_time <= e2e_test_config["performance_thresholds"]["pdf_export"]

        print("[OK] Complete document analysis workflow test passed!")

    @pytest.mark.asyncio
    async def test_analysis_with_different_document_types(
        self, e2e_helper: E2ETestHelper, temp_upload_dir: Path, e2e_test_config: dict[str, Any]
    ):
        """Test analysis with different document types."""

        # Create different document types
        document_types = {
            "progress_note": """
                PROGRESS NOTE
                Patient: Test Patient
                Date: 2024-01-15

                SUBJECTIVE: Patient reports improvement
                OBJECTIVE: ROM improved, strength 4/5
                ASSESSMENT: Good progress noted
                PLAN: Continue current treatment
            """,
            "evaluation": """
                INITIAL EVALUATION
                Patient: Test Patient
                Date: 2024-01-15

                HISTORY: Patient presents with lower back pain
                EXAMINATION: Limited ROM, decreased strength
                ASSESSMENT: Lumbar strain with functional limitations
                PLAN: PT 3x/week for 4 weeks
            """,
            "discharge_summary": """
                DISCHARGE SUMMARY
                Patient: Test Patient
                Date: 2024-01-15

                TREATMENT SUMMARY: Patient completed 12 sessions
                OUTCOMES: Achieved all functional goals
                RECOMMENDATIONS: Home exercise program
                FOLLOW-UP: PRN basis
            """,
        }

        for doc_type, content in document_types.items():
            print(f"Testing {doc_type} document...")

            # Create document file
            doc_file = temp_upload_dir / f"test_{doc_type}.txt"
            doc_file.write_text(content)

            # Upload and analyze
            upload_response = e2e_helper.upload_document(doc_file)
            assert upload_response["status"] == "success"

            document_id = upload_response["document_id"]

            # Get rubric and start analysis
            rubrics_response = e2e_helper.client.get("/rubrics", headers=e2e_helper.headers)
            rubrics_payload = rubrics_response.json()["rubrics"]
            rubric_id = _extract_rubric_id(rubrics_payload[0])

            analysis_response = e2e_helper.start_analysis(document_id, rubric_id)
            task_id = analysis_response["task_id"]

            # Wait for completion
            results = e2e_helper.wait_for_analysis(task_id, timeout=60)

            # Verify results
            assert results["status"] == "completed"
            assert "document_type" in results
            assert results["overall_score"] >= 0

            print(f"[OK] {doc_type} analysis completed successfully")

    @pytest.mark.asyncio
    async def test_concurrent_analysis(
        self, e2e_helper: E2ETestHelper, temp_upload_dir: Path, e2e_test_config: dict[str, Any]
    ):
        """Test concurrent document analysis to verify system handles load."""

        # Create multiple test documents
        num_documents = 3
        task_ids = []

        print(f"Starting {num_documents} concurrent analyses...")

        for i in range(num_documents):
            # Create document
            content = f"""
                PROGRESS NOTE {i + 1}
                Patient: Test Patient {i + 1}
                Date: 2024-01-15

                SUBJECTIVE: Patient {i + 1} reports status
                OBJECTIVE: Measurements for patient {i + 1}
                ASSESSMENT: Assessment for patient {i + 1}
                PLAN: Plan for patient {i + 1}
            """

            doc_file = temp_upload_dir / f"concurrent_test_{i + 1}.txt"
            doc_file.write_text(content)

            # Upload document
            upload_response = e2e_helper.upload_document(doc_file)
            document_id = upload_response["document_id"]

            # Start analysis
            rubrics_response = e2e_helper.client.get("/rubrics", headers=e2e_helper.headers)
            rubrics_payload = rubrics_response.json()["rubrics"]
            assert rubrics_payload, "No rubrics available for analysis"
            rubric_id = _extract_rubric_id(rubrics_payload[0])

            analysis_response = e2e_helper.start_analysis(document_id, rubric_id)
            task_ids.append(analysis_response["task_id"])

        # Wait for all analyses to complete
        start_time = time.time()
        completed_results = []

        for i, task_id in enumerate(task_ids):
            print(f"Waiting for analysis {i + 1}/{num_documents}...")
            results = e2e_helper.wait_for_analysis(task_id, timeout=180)
            completed_results.append(results)

        total_time = time.time() - start_time
        print(f"All {num_documents} analyses completed in {total_time:.2f} seconds")

        # Verify all completed successfully
        for i, results in enumerate(completed_results):
            assert results["status"] == "completed"
            assert results["overall_score"] >= 0
            print(f"[OK] Concurrent analysis {i + 1} completed successfully")

        # Verify reasonable performance (should not be much slower than sequential)
        expected_max_time = e2e_test_config["performance_thresholds"]["document_analysis"] * 2
        assert total_time <= expected_max_time, f"Concurrent analysis took too long: {total_time}s"

    @pytest.mark.asyncio
    async def test_error_handling_invalid_document(self, e2e_helper: E2ETestHelper, temp_upload_dir: Path):
        """Test error handling with invalid documents."""

        # Test with empty document
        empty_doc = temp_upload_dir / "empty.txt"
        empty_doc.write_text("")

        with empty_doc.open("rb") as f:
            upload_response = e2e_helper.client.post(
                "/upload-document",
                files={"file": (empty_doc.name, f, "text/plain")},
                headers=e2e_helper.headers,
            )

        # Should handle empty document gracefully
        if upload_response.status_code == 200:
            # If upload succeeds, analysis should handle empty content
            document_id = upload_response.json()["document_id"]
            rubrics_response = e2e_helper.client.get("/rubrics", headers=e2e_helper.headers)
            rubrics_payload = rubrics_response.json()["rubrics"]
            assert rubrics_payload, "No rubrics available for error handling test"
            rubric_id = _extract_rubric_id(rubrics_payload[0])

            analysis_response = e2e_helper.start_analysis(document_id, rubric_id)

            if analysis_response.get("task_id"):
                results = e2e_helper.wait_for_analysis(analysis_response["task_id"], timeout=60)
                # Should complete but with low score or specific handling
                assert results["status"] in ["completed", "failed"]
        else:
            # Upload rejection is also acceptable
            assert upload_response.status_code in [400, 422]

        print("[OK] Error handling test completed")

    @pytest.mark.asyncio
    async def test_analysis_progress_monitoring(self, e2e_helper: E2ETestHelper, sample_document_file: Path):
        """Test that analysis progress can be monitored in real-time."""

        # Upload document and start analysis
        upload_response = e2e_helper.upload_document(sample_document_file)
        document_id = upload_response["document_id"]

        rubrics_response = e2e_helper.client.get("/rubrics", headers=e2e_helper.headers)
        rubrics_payload = rubrics_response.json()["rubrics"]
        assert rubrics_payload, "No rubrics available for progress monitoring test"
        rubric_id = _extract_rubric_id(rubrics_payload[0])

        analysis_response = e2e_helper.start_analysis(document_id, rubric_id)
        task_id = analysis_response["task_id"]

        # Monitor progress
        progress_states = []
        max_checks = 30
        check_count = 0

        while check_count < max_checks:
            response = e2e_helper.client.get(f"/analysis-status/{task_id}", headers=e2e_helper.headers)

            assert response.status_code == 200
            status_data = response.json()
            progress_states.append(status_data["status"])

            if status_data["status"] in ["completed", "failed"]:
                break

            time.sleep(1)
            check_count += 1

        # Verify we saw progress states
        assert len(progress_states) > 0
        assert progress_states[-1] in ["completed", "failed"]

        # Should have seen some intermediate states
        possible_states = ["pending", "processing", "analyzing", "completed"]
        seen_states = set(progress_states)
        assert len(seen_states.intersection(possible_states)) >= 2

        print(f"[OK] Progress monitoring test completed. Saw states: {seen_states}")
