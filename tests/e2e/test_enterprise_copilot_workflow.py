"""
E2E Test: Enterprise Copilot Workflow

Tests the complete Enterprise Copilot user journey including queries,
responses, follow-ups, and integration with other system components.
"""

import time
from typing import Any

import pytest

from tests.e2e.conftest import E2ETestHelper


class TestEnterpriseCopilotWorkflow:
    """Test Enterprise Copilot functionality end-to-end."""

    @pytest.mark.asyncio
    async def test_basic_copilot_query_workflow(self, e2e_helper: E2ETestHelper, e2e_test_config: dict[str, Any]):
        """
        Test basic copilot query and response workflow.

        Workflow Steps:
        1. Submit compliance question
        2. Receive AI response
        3. Verify response quality
        4. Test follow-up questions
        """
        # Step 1: Submit compliance question
        print("Step 1: Submitting compliance question...")

        query_data = {
            "query": "What are the Medicare documentation requirements for physical therapy progress notes?",
            "context": {"discipline": "pt", "document_type": "progress_note"},
            "department": "physical_therapy",
            "priority": "normal",
        }

        start_time = time.time()
        response = e2e_helper.client.post("/enterprise-copilot/ask", json=query_data, headers=e2e_helper.headers)
        response_time = time.time() - start_time

        assert response.status_code == 200
        result = response.json()

        # Step 2: Verify response structure
        print("Step 2: Verifying response structure...")
        assert result["success"] is True
        assert "response" in result
        assert "confidence" in result
        assert "sources" in result
        assert "suggested_actions" in result
        assert "follow_up_questions" in result

        # Step 3: Verify response quality
        print("Step 3: Verifying response quality...")
        assert len(result["response"]) > 50  # Substantial response
        assert result["confidence"] >= 0.5  # Reasonable confidence
        assert isinstance(result["sources"], list)
        assert isinstance(result["suggested_actions"], list)
        assert isinstance(result["follow_up_questions"], list)

        # Verify performance
        assert response_time <= e2e_test_config["performance_thresholds"]["api_response"]

        print(f"✅ Basic copilot query completed in {response_time:.2f} seconds")

        # Step 4: Test follow-up question
        if result["follow_up_questions"]:
            print("Step 4: Testing follow-up question...")
            follow_up_query = {
                "query": result["follow_up_questions"][0],
                "context": query_data["context"],
                "department": query_data["department"],
                "priority": "normal",
            }

            follow_up_response = e2e_helper.client.post(
                "/enterprise-copilot/ask", json=follow_up_query, headers=e2e_helper.headers
            )

            assert follow_up_response.status_code == 200
            follow_up_result = follow_up_response.json()
            assert follow_up_result["success"] is True

            print("✅ Follow-up question handled successfully")

    @pytest.mark.asyncio
    async def test_copilot_capabilities_discovery(self, e2e_helper: E2ETestHelper):
        """Test copilot capabilities discovery."""

        print("Testing copilot capabilities discovery...")

        response = e2e_helper.client.get("/enterprise-copilot/capabilities", headers=e2e_helper.headers)

        assert response.status_code == 200
        capabilities = response.json()

        # Verify capabilities structure
        assert "capabilities" in capabilities
        assert "supported_queries" in capabilities
        assert "response_formats" in capabilities

        # Verify capabilities content
        caps = capabilities["capabilities"]
        assert isinstance(caps, list)
        assert len(caps) > 0

        for capability in caps:
            assert "name" in capability
            assert "description" in capability
            assert "examples" in capability
            assert isinstance(capability["examples"], list)

        print("✅ Capabilities discovery test passed")

    @pytest.mark.asyncio
    async def test_workflow_automation_creation(self, e2e_helper: E2ETestHelper):
        """Test workflow automation creation through copilot."""

        print("Testing workflow automation creation...")

        automation_request = {
            "workflow_type": "compliance_monitoring",
            "parameters": {"frequency": "daily", "disciplines": ["pt", "ot"], "alert_threshold": 70},
            "schedule": "0 9 * * *",  # Daily at 9 AM
        }

        response = e2e_helper.client.post(
            "/enterprise-copilot/workflow/automate", json=automation_request, headers=e2e_helper.headers
        )

        # Note: This might require admin privileges
        if response.status_code == 403:
            print("⚠️ Workflow automation requires admin privileges (expected)")
            return

        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert "automation_id" in result
        assert result["workflow_type"] == automation_request["workflow_type"]

        print("✅ Workflow automation creation test passed")

    @pytest.mark.asyncio
    async def test_copilot_help_system(self, e2e_helper: E2ETestHelper):
        """Test copilot help system and topic discovery."""

        print("Testing copilot help system...")

        response = e2e_helper.client.get("/enterprise-copilot/help/topics", headers=e2e_helper.headers)

        assert response.status_code == 200
        help_data = response.json()

        # Verify help structure
        assert "help_topics" in help_data
        assert "quick_actions" in help_data

        topics = help_data["help_topics"]
        assert isinstance(topics, list)
        assert len(topics) > 0

        for topic in topics:
            assert "category" in topic
            assert "examples" in topic
            assert isinstance(topic["examples"], list)

        # Verify quick actions
        quick_actions = help_data["quick_actions"]
        assert isinstance(quick_actions, list)
        assert len(quick_actions) > 0

        print("✅ Help system test passed")

    @pytest.mark.asyncio
    async def test_copilot_status_monitoring(self, e2e_helper: E2ETestHelper):
        """Test copilot system status monitoring."""

        print("Testing copilot status monitoring...")

        response = e2e_helper.client.get("/enterprise-copilot/status", headers=e2e_helper.headers)

        assert response.status_code == 200
        status = response.json()

        # Verify status structure
        assert "status" in status
        assert "version" in status
        assert "capabilities_enabled" in status
        assert "last_updated" in status

        # Verify status values
        assert status["status"] in ["operational", "degraded", "error"]
        assert status["capabilities_enabled"] is True

        # Optional fields that might be present
        optional_fields = ["uptime", "active_sessions", "total_queries_today", "average_response_time_ms"]
        for field in optional_fields:
            if field in status:
                assert isinstance(status[field], (int, float, str))

        print("✅ Status monitoring test passed")

    @pytest.mark.asyncio
    async def test_discipline_specific_queries(self, e2e_helper: E2ETestHelper):
        """Test copilot responses to discipline-specific queries."""

        discipline_queries = {
            "pt": "What are the key components of a physical therapy evaluation?",
            "ot": "How should occupational therapy goals be documented?",
            "slp": "What are Medicare requirements for speech therapy progress notes?",
        }

        for discipline, query in discipline_queries.items():
            print(f"Testing {discipline.upper()} specific query...")

            query_data = {
                "query": query,
                "context": {"discipline": discipline},
                "department": f"{discipline}_department",
                "priority": "normal",
            }

            response = e2e_helper.client.post("/enterprise-copilot/ask", json=query_data, headers=e2e_helper.headers)

            assert response.status_code == 200
            result = response.json()

            assert result["success"] is True
            assert len(result["response"]) > 30
            assert result["confidence"] > 0.3

            # Response should be relevant to the discipline
            response_text = result["response"].lower()
            discipline_terms = {
                "pt": ["physical", "therapy", "movement", "exercise"],
                "ot": ["occupational", "activities", "daily living", "functional"],
                "slp": ["speech", "language", "communication", "swallowing"],
            }

            relevant_terms = discipline_terms[discipline]
            found_terms = sum(1 for term in relevant_terms if term in response_text)
            assert found_terms >= 1, f"Response not relevant to {discipline}"

            print(f"✅ {discipline.upper()} query test passed")

    @pytest.mark.asyncio
    async def test_copilot_error_handling(self, e2e_helper: E2ETestHelper):
        """Test copilot error handling with invalid queries."""

        error_test_cases = [
            {
                "name": "empty_query",
                "data": {"query": "", "context": {}, "priority": "normal"},
                "expected_status": [400, 422],
            },
            {
                "name": "invalid_priority",
                "data": {"query": "Test query", "context": {}, "priority": "invalid"},
                "expected_status": [400, 422],
            },
            {
                "name": "malformed_context",
                "data": {"query": "Test query", "context": "invalid", "priority": "normal"},
                "expected_status": [400, 422],
            },
        ]

        for test_case in error_test_cases:
            print(f"Testing error handling: {test_case['name']}")

            response = e2e_helper.client.post(
                "/enterprise-copilot/ask", json=test_case["data"], headers=e2e_helper.headers
            )

            assert response.status_code in test_case["expected_status"]

            # If it's a 200 response, it should indicate failure
            if response.status_code == 200:
                result = response.json()
                assert result.get("success") is False

            print(f"✅ Error handling test '{test_case['name']}' passed")

    @pytest.mark.asyncio
    async def test_copilot_performance_under_load(self, e2e_helper: E2ETestHelper, e2e_test_config: dict[str, Any]):
        """Test copilot performance under concurrent load."""

        print("Testing copilot performance under load...")

        # Prepare multiple queries
        queries = [
            "What are Medicare documentation requirements?",
            "How should treatment goals be written?",
            "What constitutes medical necessity?",
            "How often should progress notes be written?",
            "What are the key components of an evaluation?",
        ]

        # Submit queries concurrently (simulate with rapid sequential requests)
        start_time = time.time()
        responses = []

        for _i, query in enumerate(queries):
            query_data = {"query": query, "context": {"test_id": i}, "priority": "normal"}

            response = e2e_helper.client.post("/enterprise-copilot/ask", json=query_data, headers=e2e_helper.headers)

            responses.append(response)

        total_time = time.time() - start_time

        # Verify all responses
        successful_responses = 0
        for i, response in enumerate(responses):
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    successful_responses += 1

        # Should handle most queries successfully
        success_rate = successful_responses / len(queries)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"

        # Performance should be reasonable
        avg_time_per_query = total_time / len(queries)
        max_acceptable_time = e2e_test_config["performance_thresholds"]["api_response"] * 2
        assert avg_time_per_query <= max_acceptable_time

        print(
            f"✅ Load test passed: {successful_responses}/{len(queries)} successful, avg {avg_time_per_query:.2f}s per query"
        )
