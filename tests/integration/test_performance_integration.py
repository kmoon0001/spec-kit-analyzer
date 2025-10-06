"""
Integration tests for performance management system.
Tests the integration between performance manager, cache service, and GUI components.
"""

import pytest
from unittest.mock import patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


@pytest.mark.integration
class TestPerformanceIntegration:
    """Test performance system integration."""

    def test_performance_manager_initialization(self):
        """Test that performance manager initializes correctly."""
        try:
            from src.core.performance_manager import performance_manager

            # Should have a current profile
            assert performance_manager.current_profile is not None

            # Should have system info
            system_info = performance_manager.system_info
            assert "total_memory_gb" in system_info
            assert "cpu_count" in system_info

            # Should have a config
            config = performance_manager.config
            assert config.max_cache_memory_mb > 0
            assert config.batch_size > 0

        except ImportError:
            pytest.skip("Performance manager not available")

    def test_cache_service_integration(self):
        """Test cache service integration with performance manager."""
        try:
            from src.core.cache_service import cache_service, get_cache_stats

            # Test basic cache operations
            cache_service.set("test_key", "test_value")
            assert cache_service.get("test_key") == "test_value"

            # Test cache stats
            stats = get_cache_stats()
            assert "total_entries" in stats
            assert "memory_usage_mb" in stats
            assert stats["total_entries"] >= 1  # Should have our test entry

        except ImportError:
            pytest.skip("Cache service not available")

    def test_performance_integration_service(self):
        """Test the performance integration service."""
        try:
            from src.core.performance_integration import performance_integration

            # Test getting performance status
            status = performance_integration.get_performance_status()
            assert "timestamp" in status
            assert "monitoring_enabled" in status

            # Test optimization
            results = performance_integration.optimize_for_analysis()
            assert "cache_cleanup" in results
            assert "recommendations" in results

        except ImportError:
            pytest.skip("Performance integration service not available")

    @patch("src.core.performance_manager.psutil.virtual_memory")
    def test_memory_pressure_handling(self, mock_memory):
        """Test handling of memory pressure situations."""
        try:
            from src.core.performance_integration import performance_integration

            # Mock high memory usage
            mock_memory.return_value.percent = 85

            # Should trigger optimization
            results = performance_integration.optimize_for_analysis()

            # Should have recommendations for high memory usage
            assert len(results.get("recommendations", [])) > 0

        except ImportError:
            pytest.skip("Performance integration not available")

    @pytest.mark.skip(reason="GUI tests cannot be run in a headless environment.")
    def test_performance_status_widget_creation(self):
        """Test that performance status widget can be created."""
        try:
            from PySide6.QtWidgets import QApplication
            from src.gui.widgets.performance_status_widget import (
                PerformanceStatusWidget,
            )

            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication([])

            # Create widget
            widget = PerformanceStatusWidget()
            assert widget is not None

            # Test getting performance summary
            summary = widget.get_performance_summary()
            assert isinstance(summary, dict)

            # Cleanup
            widget.cleanup()

        except ImportError:
            pytest.skip("GUI components not available")

    @pytest.mark.skip(reason="GUI tests cannot be run in a headless environment.")
    def test_performance_settings_dialog_creation(self):
        """Test that performance settings dialog can be created."""
        try:
            from PySide6.QtWidgets import QApplication
            from src.gui.dialogs.performance_settings_dialog import (
                PerformanceSettingsDialog,
            )

            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication([])

            # Create dialog
            dialog = PerformanceSettingsDialog()
            assert dialog is not None

            # Test getting current settings
            settings = dialog.get_current_settings()
            assert isinstance(settings, dict)
            assert "profile" in settings

            # Cleanup
            dialog.close()

        except ImportError:
            pytest.skip("GUI components not available")


if __name__ == "__main__":
    pytest.main([__file__])
