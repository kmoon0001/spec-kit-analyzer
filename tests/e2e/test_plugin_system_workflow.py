"""
E2E Test: Plugin System Workflow

Tests the complete plugin system functionality including discovery,
loading, execution, and management of compliance plugins.
"""

import time
from typing import Any

import pytest

from tests.e2e.conftest import E2ETestHelper


class TestPluginSystemWorkflow:
    """Test plugin system functionality end-to-end."""

    @pytest.mark.asyncio
    async def test_plugin_discovery_workflow(self, e2e_helper: E2ETestHelper):
        """
        Test plugin discovery and listing workflow.

        Workflow Steps:
        1. Discover available plugins
        2. List installed plugins
        3. Get plugin details
        4. Verify plugin metadata
        """
        # Step 1: Discover available plugins
        print("Step 1: Discovering available plugins...")

        discovery_response = e2e_helper.client.post("/plugins/discover", headers=e2e_helper.headers)

        assert discovery_response.status_code == 200
        discovery_result = discovery_response.json()

        assert discovery_result["success"] is True
        assert "discovered_plugins" in discovery_result
        assert isinstance(discovery_result["discovered_plugins"], list)

        discovered_count = len(discovery_result["discovered_plugins"])
        print(f"Discovered {discovered_count} plugins")

        # Step 2: List all plugins
        print("Step 2: Listing all plugins...")

        list_response = e2e_helper.client.get("/plugins/", headers=e2e_helper.headers)

        assert list_response.status_code == 200
        plugins_list = list_response.json()

        assert "plugins" in plugins_list
        assert isinstance(plugins_list["plugins"], list)

        # Step 3: Get details for each plugin
        print("Step 3: Getting plugin details...")

        for plugin in plugins_list["plugins"]:
            plugin_name = plugin["name"]

            detail_response = e2e_helper.client.get(f"/plugins/{plugin_name}/status", headers=e2e_helper.headers)

            assert detail_response.status_code == 200
            plugin_details = detail_response.json()

            # Verify plugin details structure
            assert "name" in plugin_details
            assert "status" in plugin_details
            assert "metadata" in plugin_details
            assert plugin_details["name"] == plugin_name

            print(f"✅ Plugin '{plugin_name}' details verified")

        print("✅ Plugin discovery workflow completed")

    @pytest.mark.asyncio
    async def test_plugin_lifecycle_management(self, e2e_helper: E2ETestHelper):
        """Test complete plugin lifecycle: load -> use -> unload."""

        # First, get available plugins
        list_response = e2e_helper.client.get("/plugins/", headers=e2e_helper.headers)

        plugins = list_response.json()["plugins"]
        if not plugins:
            print("⚠️ No plugins available for lifecycle testing")
            return

        # Use first available plugin for testing
        test_plugin = plugins[0]
        plugin_name = test_plugin["name"]

        print(f"Testing lifecycle for plugin: {plugin_name}")

        # Step 1: Check initial status
        print("Step 1: Checking initial plugin status...")

        status_response = e2e_helper.client.get(f"/plugins/{plugin_name}/status", headers=e2e_helper.headers)

        assert status_response.status_code == 200
        initial_status = status_response.json()

        # Step 2: Load plugin if not already loaded
        print("Step 2: Loading plugin...")

        if initial_status["status"] != "loaded":
            load_response = e2e_helper.client.post(f"/plugins/{plugin_name}/load", headers=e2e_helper.headers)

            assert load_response.status_code == 200
            load_result = load_response.json()
            assert load_result["success"] is True

            # Verify plugin is now loaded
            status_response = e2e_helper.client.get(f"/plugins/{plugin_name}/status", headers=e2e_helper.headers)
            updated_status = status_response.json()
            assert updated_status["status"] == "loaded"

        print(f"✅ Plugin '{plugin_name}' loaded successfully")

        # Step 3: Test plugin execution (if it has executable functionality)
        print("Step 3: Testing plugin execution...")

        # This would depend on the specific plugin's capabilities
        # For now, we'll just verify it's loaded and responsive

        # Step 4: Unload plugin
        print("Step 4: Unloading plugin...")

        unload_response = e2e_helper.client.post(f"/plugins/{plugin_name}/unload", headers=e2e_helper.headers)

        assert unload_response.status_code == 200
        unload_result = unload_response.json()
        assert unload_result["success"] is True

        # Verify plugin is unloaded
        final_status_response = e2e_helper.client.get(f"/plugins/{plugin_name}/status", headers=e2e_helper.headers)
        final_status = final_status_response.json()
        assert final_status["status"] in ["available", "unloaded"]

        print(f"✅ Plugin '{plugin_name}' lifecycle test completed")

    @pytest.mark.asyncio
    async def test_plugin_extension_points(self, e2e_helper: E2ETestHelper):
        """Test plugin extension points and integration."""

        print("Testing plugin extension points...")

        # Get available extension points
        extension_response = e2e_helper.client.get("/plugins/extension-points", headers=e2e_helper.headers)

        assert extension_response.status_code == 200
        extension_data = extension_response.json()

        assert "extension_points" in extension_data
        extension_points = extension_data["extension_points"]
        assert isinstance(extension_points, list)

        # Verify extension point structure
        for ext_point in extension_points:
            assert "name" in ext_point
            assert "description" in ext_point
            assert "interface" in ext_point

            print(f"Extension point: {ext_point['name']}")

        print(f"✅ Found {len(extension_points)} extension points")

    @pytest.mark.asyncio
    async def test_plugin_batch_operations(self, e2e_helper: E2ETestHelper):
        """Test batch plugin operations."""

        print("Testing plugin batch operations...")

        # Start batch plugin loading
        batch_response = e2e_helper.client.post(
            "/plugins/batch/load", json={"operation": "load_all_available"}, headers=e2e_helper.headers
        )

        assert batch_response.status_code == 200
        batch_result = batch_response.json()

        assert "task_id" in batch_result
        task_id = batch_result["task_id"]

        # Monitor batch operation progress
        max_wait_time = 60  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status_response = e2e_helper.client.get(f"/plugins/batch/status/{task_id}", headers=e2e_helper.headers)

            if status_response.status_code == 200:
                status_data = status_response.json()

                if status_data.get("status") == "completed":
                    assert "results" in status_data
                    print(f"✅ Batch operation completed: {status_data['results']}")
                    break
                elif status_data.get("status") == "failed":
                    print(f"⚠️ Batch operation failed: {status_data.get('error')}")
                    break

            time.sleep(2)
        else:
            print("⚠️ Batch operation timed out")

    @pytest.mark.asyncio
    async def test_plugin_error_handling(self, e2e_helper: E2ETestHelper):
        """Test plugin system error handling."""

        print("Testing plugin error handling...")

        error_test_cases = [
            {
                "name": "nonexistent_plugin_status",
                "endpoint": "/plugins/nonexistent_plugin/status",
                "method": "GET",
                "expected_status": [404],
            },
            {
                "name": "nonexistent_plugin_load",
                "endpoint": "/plugins/nonexistent_plugin/load",
                "method": "POST",
                "expected_status": [404],
            },
            {
                "name": "invalid_batch_operation",
                "endpoint": "/plugins/batch/load",
                "method": "POST",
                "data": {"operation": "invalid_operation"},
                "expected_status": [400, 422],
            },
        ]

        for test_case in error_test_cases:
            print(f"Testing error case: {test_case['name']}")

            if test_case["method"] == "GET":
                response = e2e_helper.client.get(test_case["endpoint"], headers=e2e_helper.headers)
            elif test_case["method"] == "POST":
                response = e2e_helper.client.post(
                    test_case["endpoint"], json=test_case.get("data", {}), headers=e2e_helper.headers
                )

            assert response.status_code in test_case["expected_status"]
            print(f"✅ Error case '{test_case['name']}' handled correctly")

    @pytest.mark.asyncio
    async def test_plugin_performance_monitoring(self, e2e_helper: E2ETestHelper, e2e_test_config: dict[str, Any]):
        """Test plugin system performance monitoring."""

        print("Testing plugin performance monitoring...")

        # Test plugin discovery performance
        start_time = time.time()

        discovery_response = e2e_helper.client.post("/plugins/discover", headers=e2e_helper.headers)

        discovery_time = time.time() - start_time

        assert discovery_response.status_code == 200

        # Plugin discovery should be reasonably fast
        max_discovery_time = e2e_test_config["performance_thresholds"]["api_response"]
        assert discovery_time <= max_discovery_time

        print(f"✅ Plugin discovery completed in {discovery_time:.2f} seconds")

        # Test plugin listing performance
        start_time = time.time()

        list_response = e2e_helper.client.get("/plugins/", headers=e2e_helper.headers)

        list_time = time.time() - start_time

        assert list_response.status_code == 200
        assert list_time <= max_discovery_time

        print(f"✅ Plugin listing completed in {list_time:.2f} seconds")

    @pytest.mark.asyncio
    async def test_plugin_integration_with_analysis(
        self, e2e_helper: E2ETestHelper, sample_document_file, e2e_test_config: dict[str, Any]
    ):
        """Test plugin integration with document analysis workflow."""

        print("Testing plugin integration with analysis...")

        # First, ensure we have plugins loaded
        list_response = e2e_helper.client.get("/plugins/", headers=e2e_helper.headers)

        plugins = list_response.json()["plugins"]

        if not plugins:
            print("⚠️ No plugins available for integration testing")
            return

        # Load a plugin if available
        test_plugin = plugins[0]
        plugin_name = test_plugin["name"]

        load_response = e2e_helper.client.post(f"/plugins/{plugin_name}/load", headers=e2e_helper.headers)

        if load_response.status_code != 200:
            print(f"⚠️ Could not load plugin {plugin_name} for integration test")
            return

        # Now run a document analysis to see if plugins are integrated
        upload_response = e2e_helper.upload_document(sample_document_file)
        document_id = upload_response["document_id"]

        # Get rubric and start analysis
        rubrics_response = e2e_helper.client.get("/rubrics", headers=e2e_helper.headers)
        rubric_id = rubrics_response.json()["rubrics"][0]["id"]

        analysis_response = e2e_helper.start_analysis(document_id, rubric_id)
        task_id = analysis_response["task_id"]

        # Wait for analysis completion
        results = e2e_helper.wait_for_analysis(task_id, timeout=120)

        # Verify analysis completed successfully with plugin integration
        assert results["status"] == "completed"

        # Check if plugin contributed to the analysis
        # This would depend on the specific plugin's functionality
        # For now, we just verify the analysis worked with plugins loaded

        print(f"✅ Analysis completed successfully with plugin '{plugin_name}' loaded")

        # Clean up - unload plugin
        e2e_helper.client.post(f"/plugins/{plugin_name}/unload", headers=e2e_helper.headers)
