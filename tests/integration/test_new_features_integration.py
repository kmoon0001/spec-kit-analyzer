"""
Integration tests for all new features working together.

This module tests the integration of PDF export, plugin system, enhanced copilot,
and multi-agent workflows to ensure they work seamlessly together.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.core.pdf_export_service import pdf_export_service
from src.core.plugin_system import plugin_manager
from src.core.enterprise_copilot_service import enterprise_copilot_service
from src.core.multi_agent_orchestrator import multi_agent_orchestrator
from src.core.performance_monitor import performance_monitor
from src.core.enhanced_error_handler import enhanced_error_handler


class TestNewFeaturesIntegration:
    """Integration tests for new features."""
    
    @pytest.fixture
    def sample_report_data(self):
        """Sample report data for testing."""
        return {
            "title": "Integration Test Compliance Report",
            "generated_at": "2024-01-15T10:30:00",
            "document_name": "test_document.txt",
            "compliance_score": 87.5,
            "findings": [
                {
                    "rule_id": "TEST_001",
                    "risk_level": "high",
                    "evidence": "Missing medical necessity justification",
                    "issue": "Treatment goals lack specific functional outcomes",
                    "recommendation": "Add measurable functional goals with timelines",
                    "confidence_score": 0.85
                },
                {
                    "rule_id": "TEST_002", 
                    "risk_level": "medium",
                    "evidence": "Incomplete progress documentation",
                    "issue": "Patient response to treatment not documented",
                    "recommendation": "Document patient's subjective and objective response",
                    "confidence_score": 0.78
                }
            ],
            "charts": [
                {"title": "Compliance Trends", "data": [85, 87, 89]}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_pdf_export_integration(self, sample_report_data):
        """Test PDF export integration with performance monitoring."""
        # Mock WeasyPrint to avoid dependency issues in tests
        with patch('src.core.pdf_export_service.WEASYPRINT_AVAILABLE', True), \
             patch('src.core.pdf_export_service.HTML') as mock_html, \
             patch('src.core.pdf_export_service.CSS') as mock_css:
            
            # Setup mocks
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b"fake_pdf_content"
            
            # Test PDF export with performance monitoring
            with performance_monitor.track_operation("test", "pdf_export"):
                result = await pdf_export_service.export_report_to_pdf(sample_report_data)
            
            # Verify PDF was generated
            assert result == b"fake_pdf_content"
            
            # Verify performance was tracked
            recent_metrics = [m for m in performance_monitor.metrics_history if m.component == "test"]
            assert len(recent_metrics) > 0
            assert recent_metrics[-1].operation == "pdf_export"
    
    @pytest.mark.asyncio
    async def test_enterprise_copilot_integration(self):
        """Test enterprise copilot with enhanced knowledge base."""
        # Test compliance question
        response = await enterprise_copilot_service.process_query(
            query="How do I document medical necessity for PT?",
            context={"document_type": "evaluation"},
            user_id=1,
            department="Physical Therapy"
        )
        
        # Verify enhanced response
        assert response["answer"] is not None
        assert response["confidence"] > 0.0
        assert len(response["sources"]) > 0
        assert len(response["suggested_actions"]) > 0
        assert "query_id" in response
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow_integration(self):
        """Test multi-agent workflow orchestration."""
        document_content = """
        Patient: John Doe
        Date: 2024-01-15
        
        Progress Note:
        Patient demonstrates improved range of motion in left shoulder.
        ROM: 0-120 degrees (improved from 0-90 degrees last visit).
        Patient reports decreased pain from 8/10 to 5/10.
        Continuing with current treatment plan.
        """
        
        rubric_data = {
            "rules": [
                {"id": "DOC_001", "description": "Medical necessity must be documented"},
                {"id": "DOC_002", "description": "Functional outcomes must be measurable"}
            ]
        }
        
        user_preferences = {
            "analysis_depth": "comprehensive",
            "include_recommendations": True
        }
        
        # Execute multi-agent workflow
        result = await multi_agent_orchestrator.execute_workflow(
            document_content=document_content,
            rubric_data=rubric_data,
            user_preferences=user_preferences
        )
        
        # Verify workflow results
        assert result["success"] is True
        assert result["overall_confidence"] > 0.0
        assert "agent_results" in result
        assert len(result["agent_results"]) > 0
        assert "quality_metrics" in result
    
    def test_error_handler_integration(self):
        """Test enhanced error handling integration."""
        # Simulate an error
        test_exception = ValueError("Test error for integration testing")
        
        # Handle error with enhanced handler
        enhanced_error = enhanced_error_handler.handle_error(
            test_exception,
            component="integration_test",
            operation="test_operation",
            user_id=1
        )
        
        # Verify enhanced error properties
        assert enhanced_error.error_id is not None
        assert enhanced_error.severity is not None
        assert enhanced_error.category is not None
        assert enhanced_error.user_message is not None
        assert len(enhanced_error.recovery_suggestions) > 0
        
        # Verify error can be serialized for API responses
        error_dict = enhanced_error.to_dict()
        assert "error_id" in error_dict
        assert "user_message" in error_dict
        assert "recovery_suggestions" in error_dict
    
    def test_performance_monitor_integration(self):
        """Test performance monitoring integration."""
        # Test operation tracking
        with performance_monitor.track_operation("test_component", "test_operation"):
            # Simulate some work
            import time
            time.sleep(0.1)
        
        # Verify metric was recorded
        recent_metrics = [m for m in performance_monitor.metrics_history if m.component == "test_component"]
        assert len(recent_metrics) > 0
        
        latest_metric = recent_metrics[-1]
        assert latest_metric.operation == "test_operation"
        assert latest_metric.duration_ms > 0
        assert latest_metric.success is True
    
    def test_plugin_system_integration(self):
        """Test plugin system discovery and management."""
        # Test plugin discovery
        discovered_plugins = plugin_manager.discover_plugins()
        
        # Verify discovery works (may be empty but shouldn't crash)
        assert isinstance(discovered_plugins, list)
        
        # Test plugin status retrieval
        plugin_statuses = {}
        for plugin_name in plugin_manager.plugin_metadata:
            status = plugin_manager.get_plugin_status(plugin_name)
            plugin_statuses[plugin_name] = status
        
        # Verify status structure
        for status in plugin_statuses.values():
            assert "name" in status
            assert "discovered" in status
            assert "loaded" in status
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, sample_report_data):
        """Test complete end-to-end workflow with all new features."""
        try:
            # 1. Process document with multi-agent analysis
            document_content = "Test clinical document for compliance analysis"
            rubric_data = {"rules": [{"id": "TEST", "description": "Test rule"}]}
            user_preferences = {"detailed_analysis": True}
            
            # Multi-agent analysis
            analysis_result = await multi_agent_orchestrator.execute_workflow(
                document_content=document_content,
                rubric_data=rubric_data,
                user_preferences=user_preferences
            )
            
            # 2. Generate enhanced report data
            enhanced_report_data = {
                **sample_report_data,
                "multi_agent_analysis": analysis_result,
                "performance_metrics": performance_monitor.get_system_health().__dict__
            }
            
            # 3. Export to PDF
            with patch('src.core.pdf_export_service.WEASYPRINT_AVAILABLE', True), \
                 patch('src.core.pdf_export_service.HTML') as mock_html:
                
                mock_html_instance = Mock()
                mock_html.return_value = mock_html_instance
                mock_html_instance.write_pdf.return_value = b"test_pdf_content"
                
                pdf_result = await pdf_export_service.export_report_to_pdf(enhanced_report_data)
                
                # Verify end-to-end success
                assert pdf_result == b"test_pdf_content"
            
            # 4. Get performance insights
            performance_data = performance_monitor.get_component_performance("test", 1)
            assert isinstance(performance_data, dict)
            
            # 5. Test copilot query about the analysis
            copilot_response = await enterprise_copilot_service.process_query(
                query="What were the main findings in this analysis?",
                context={"analysis_result": analysis_result},
                user_id=1
            )
            
            assert copilot_response["success"] is not False  # May not have success key
            assert copilot_response["answer"] is not None
            
            logger.info("End-to-end workflow test completed successfully")
            
        except Exception as e:
            logger.error(f"End-to-end workflow test failed: {e}")
            raise


class TestFeatureInteroperability:
    """Test how new features work together."""
    
    @pytest.mark.asyncio
    async def test_copilot_with_performance_monitoring(self):
        """Test copilot queries with performance monitoring."""
        queries = [
            "How do I improve documentation quality?",
            "What are Medicare requirements for PT notes?",
            "Help me create better treatment goals"
        ]
        
        for query in queries:
            with performance_monitor.track_operation("copilot_test", "process_query"):
                response = await enterprise_copilot_service.process_query(
                    query=query,
                    context={},
                    user_id=1
                )
                
                # Verify response quality
                assert response["confidence"] > 0.0
                assert len(response["answer"]) > 50  # Substantial response
        
        # Verify performance was tracked
        copilot_metrics = [m for m in performance_monitor.metrics_history if m.component == "copilot_test"]
        assert len(copilot_metrics) == len(queries)
    
    def test_error_handling_with_performance_monitoring(self):
        """Test error handling integration with performance monitoring."""
        # Simulate an error during a monitored operation
        def failing_operation():
            raise ConnectionError("Simulated network failure")
        
        try:
            with performance_monitor.track_operation("error_test", "failing_operation"):
                failing_operation()
        except ConnectionError as e:
            # Handle with enhanced error handler
            enhanced_error = enhanced_error_handler.handle_error(
                e,
                component="error_test",
                operation="failing_operation"
            )
            
            # Verify error was properly handled
            assert enhanced_error.category.value == "network"
            assert len(enhanced_error.recovery_suggestions) > 0
        
        # Verify performance metric recorded the failure
        error_metrics = [m for m in performance_monitor.metrics_history 
                        if m.component == "error_test" and not m.success]
        assert len(error_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_plugin_system_with_error_handling(self):
        """Test plugin system with enhanced error handling."""
        # Test plugin loading with error handling
        try:
            # Attempt to load a non-existent plugin
            result = plugin_manager.load_plugin("non_existent_plugin")
            assert result is False  # Should fail gracefully
            
        except Exception as e:
            # Should be handled gracefully by the plugin system
            enhanced_error = enhanced_error_handler.handle_error(
                e,
                component="plugin_system",
                operation="load_plugin"
            )
            
            assert enhanced_error.category.value in ["system", "configuration"]
            assert "plugin" in enhanced_error.user_message.lower()


class TestSystemStability:
    """Test system stability with all new features enabled."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test multiple operations running concurrently."""
        # Create multiple concurrent tasks
        tasks = []
        
        # PDF export tasks
        sample_data = {"title": "Test", "generated_at": "2024-01-15", "findings": []}
        
        with patch('src.core.pdf_export_service.WEASYPRINT_AVAILABLE', True), \
             patch('src.core.pdf_export_service.HTML') as mock_html:
            
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b"test_content"
            
            for i in range(3):
                task = pdf_export_service.export_report_to_pdf(sample_data)
                tasks.append(task)
        
        # Copilot query tasks
        for i in range(3):
            task = enterprise_copilot_service.process_query(
                query=f"Test query {i}",
                context={},
                user_id=1
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify most operations succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len