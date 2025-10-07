"""
Tests for Data Integration Service

This module provides comprehensive tests for the data integration layer,
including all data providers and the main integration service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.core.data_integration_service import (
    DataIntegrationService,
    PerformanceDataProvider,
    DataSourceType,
    DataQuality,
    DataQuery,
    DataResult,
    DataSourceMetadata
)
from src.core.report_generation_engine import ReportConfig, ReportType, TimeRange


class TestDataSourceMetadata:
    """Test DataSourceMetadata functionality"""
    
    def test_metadata_creation(self):
        """Test creating metadata with all fields"""
        metadata = DataSourceMetadata(
            source_id="test_source",
            source_type=DataSourceType.PERFORMANCE_METRICS,
            description="Test data source",
            last_updated=datetime.now(),
            data_quality=DataQuality.HIGH,
            availability=True,
            tags=["test", "performance"]
        )
        
        assert metadata.source_id == "test_source"
        assert metadata.source_type == DataSourceType.PERFORMANCE_METRICS
        assert metadata.data_quality == DataQuality.HIGH
        assert metadata.availability is True
        assert "test" in metadata.tags
    
    def test_metadata_to_dict(self):
        """Test metadata serialization to dictionary"""
        metadata = DataSourceMetadata(
            source_id="test_source",
            source_type=DataSourceType.PERFORMANCE_METRICS,
            description="Test data source",
            last_updated=datetime.now(),
            tags=["test"]
        )
        
        result = metadata.to_dict()
        
        assert result["source_id"] == "test_source"
        assert result["source_type"] == "performance_metrics"
        assert result["description"] == "Test data source"
        assert "last_updated" in result
        assert result["tags"] == ["test"]


class TestDataQuery:
    """Test DataQuery functionality"""
    
    def test_query_creation(self):
        """Test creating a data query"""
        time_range = TimeRange.last_hours(24)
        query = DataQuery(
            source_types=[DataSourceType.PERFORMANCE_METRICS],
            time_range=time_range,
            filters={"metric_type": "response_time"},
            aggregation_level="hourly"
        )
        
        assert DataSourceType.PERFORMANCE_METRICS in query.source_types
        assert query.time_range == time_range
        assert query.filters["metric_type"] == "response_time"
        assert query.aggregation_level == "hourly"
    
    def test_query_to_dict(self):
        """Test query serialization to dictionary"""
        time_range = TimeRange.last_hours(24)
        query = DataQuery(
            source_types=[DataSourceType.PERFORMANCE_METRICS],
            time_range=time_range,
            filters={"test": "value"}
        )
        
        result = query.to_dict()
        
        assert result["source_types"] == ["performance_metrics"]
        assert "time_range" in result
        assert result["filters"]["test"] == "value"


class TestDataResult:
    """Test DataResult functionality"""
    
    def test_result_creation(self):
        """Test creating a data result"""
        metadata = DataSourceMetadata(
            source_id="test",
            source_type=DataSourceType.PERFORMANCE_METRICS,
            description="Test",
            last_updated=datetime.now()
        )
        
        query = DataQuery(source_types=[DataSourceType.PERFORMANCE_METRICS])
        
        result = DataResult(
            data={"test": "data"},
            metadata=metadata,
            query=query,
            retrieved_at=datetime.now(),
            record_count=1
        )
        
        assert result.data["test"] == "data"
        assert result.metadata == metadata
        assert result.query == query
        assert result.record_count == 1
    
    def test_result_to_dict(self):
        """Test result serialization to dictionary"""
        metadata = DataSourceMetadata(
            source_id="test",
            source_type=DataSourceType.PERFORMANCE_METRICS,
            description="Test",
            last_updated=datetime.now()
        )
        
        query = DataQuery(source_types=[DataSourceType.PERFORMANCE_METRICS])
        
        result = DataResult(
            data={"test": "data"},
            metadata=metadata,
            query=query,
            retrieved_at=datetime.now()
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["data"]["test"] == "data"
        assert "metadata" in result_dict
        assert "query" in result_dict
        assert "retrieved_at" in result_dict


class TestPerformanceDataProvider:
    """Test PerformanceDataProvider functionality"""
    
    @pytest.fixture
    def provider(self):
        """Create a performance data provider for testing"""
        return PerformanceDataProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.provider_id == "performance_metrics"
        assert "performance" in provider.description.lower()
        assert provider.is_available is True
    
    def test_supports_report_type(self, provider):
        """Test report type support checking"""
        assert provider.supports_report_type(ReportType.PERFORMANCE_ANALYSIS) is True
        assert provider.supports_report_type(ReportType.DASHBOARD) is True
        assert provider.supports_report_type(ReportType.COMPLIANCE_ANALYSIS) is False
    
    @pytest.mark.asyncio
    async def test_get_data(self, provider):
        """Test getting data for report generation"""
        config = ReportConfig(
            report_type=ReportType.PERFORMANCE_ANALYSIS,
            title="Test Report",
            time_range=TimeRange.last_hours(24)
        )
        
        data = await provider.get_data(config)
        
        assert "performance_metrics" in data
        assert "optimization_results" in data
        assert "summary" in data
        assert isinstance(data["summary"], dict)
    
    @pytest.mark.asyncio
    async def test_query_data(self, provider):
        """Test querying data with specific query"""
        query = DataQuery(
            source_types=[DataSourceType.PERFORMANCE_METRICS],
            time_range=TimeRange.last_hours(1)
        )
        
        result = await provider.query_data(query)
        
        assert isinstance(result, DataResult)
        assert "performance_metrics" in result.data
        assert "optimization_results" in result.data
        assert result.metadata.source_id == "performance_metrics"
    
    @pytest.mark.asyncio
    async def test_get_metadata(self, provider):
        """Test getting provider metadata"""
        metadata = await provider.get_metadata()
        
        assert metadata.source_id == "performance_metrics"
        assert metadata.source_type == DataSourceType.PERFORMANCE_METRICS
        assert metadata.data_quality == DataQuality.HIGH
        assert "performance" in metadata.tags
    
    @pytest.mark.asyncio
    async def test_health_check(self, provider):
        """Test provider health check"""
        is_healthy = await provider.health_check()
        
        assert is_healthy is True
        assert provider.is_available is True
    
    @pytest.mark.asyncio
    async def test_caching(self, provider):
        """Test data caching functionality"""
        query = DataQuery(
            source_types=[DataSourceType.PERFORMANCE_METRICS],
            time_range=TimeRange.last_hours(1)
        )
        
        # First query should fetch data
        result1 = await provider.query_data(query)
        
        # Second query should use cache
        result2 = await provider.query_data(query)
        
        assert result1.data == result2.data
        
        # Clear cache and verify
        provider.clear_cache()
        result3 = await provider.query_data(query)
        
        assert result3.data is not None  # Should still work after cache clear


# Compliance and Monitoring providers will be added in future iterations


class TestDataIntegrationService:
    """Test DataIntegrationService functionality"""
    
    @pytest.fixture
    def service(self):
        """Create a data integration service for testing"""
        return DataIntegrationService()
    
    def test_service_initialization(self, service):
        """Test service initialization with default providers"""
        assert len(service.providers) == 1  # Performance provider only for now
        assert "performance_metrics" in service.providers
    
    def test_register_provider(self, service):
        """Test registering a new provider"""
        # Create a mock provider
        mock_provider = Mock()
        mock_provider.provider_id = "test_provider"
        mock_provider.get_metadata = AsyncMock(return_value=DataSourceMetadata(
            source_id="test_provider",
            source_type=DataSourceType.HISTORICAL_DATA,
            description="Test provider",
            last_updated=datetime.now()
        ))
        
        service.register_provider(mock_provider)
        
        assert "test_provider" in service.providers
        assert service.providers["test_provider"] == mock_provider
    
    def test_unregister_provider(self, service):
        """Test unregistering a provider"""
        # Unregister an existing provider
        service.unregister_provider("performance_metrics")
        
        assert "performance_metrics" not in service.providers
    
    @pytest.mark.asyncio
    async def test_query_data(self, service):
        """Test querying data from multiple providers"""
        query = DataQuery(
            source_types=[DataSourceType.PERFORMANCE_METRICS, DataSourceType.SYSTEM_MONITORING]
        )
        
        results = await service.query_data(query)
        
        assert isinstance(results, dict)
        assert len(results) >= 1  # Should have at least one result
        
        # Check that results contain expected providers
        provider_ids = list(results.keys())
        assert any("performance" in pid or "monitoring" in pid for pid in provider_ids)
    
    @pytest.mark.asyncio
    async def test_get_available_providers(self, service):
        """Test getting metadata for all providers"""
        providers_metadata = await service.get_available_providers()
        
        assert isinstance(providers_metadata, dict)
        assert len(providers_metadata) == 1  # Default providers
        
        for provider_id, metadata in providers_metadata.items():
            assert isinstance(metadata, DataSourceMetadata)
            assert metadata.source_id == provider_id
    
    @pytest.mark.asyncio
    async def test_health_check_all_providers(self, service):
        """Test health checking all providers"""
        health_status = await service.health_check_all_providers()
        
        assert isinstance(health_status, dict)
        assert len(health_status) == 1  # Default providers
        
        for provider_id, is_healthy in health_status.items():
            assert isinstance(is_healthy, bool)
            assert provider_id in service.providers
    
    def test_get_provider_registry(self, service):
        """Test getting the provider registry"""
        registry = service.get_provider_registry()
        
        assert isinstance(registry, dict)
        assert DataSourceType.PERFORMANCE_METRICS in registry
        # Additional providers will be added in future iterations
    
    def test_clear_all_caches(self, service):
        """Test clearing caches for all providers"""
        # This should not raise any exceptions
        service.clear_all_caches()
        
        # Verify that all providers had their caches cleared
        for provider in service.providers.values():
            assert len(provider._cache) == 0
            assert len(provider._cache_ttl) == 0


class TestIntegrationScenarios:
    """Test integration scenarios and error handling"""
    
    @pytest.mark.asyncio
    async def test_error_handling_in_query(self):
        """Test error handling when provider fails"""
        service = DataIntegrationService()
        
        # Create a mock provider that raises an exception
        mock_provider = Mock()
        mock_provider.provider_id = "failing_provider"
        mock_provider.is_available = True
        mock_provider.query_data = AsyncMock(side_effect=Exception("Provider failed"))
        mock_provider.get_metadata = AsyncMock(return_value=DataSourceMetadata(
            source_id="failing_provider",
            source_type=DataSourceType.PERFORMANCE_METRICS,
            description="Failing provider",
            last_updated=datetime.now()
        ))
        
        service.register_provider(mock_provider)
        
        query = DataQuery(source_types=[DataSourceType.PERFORMANCE_METRICS])
        results = await service.query_data(query)
        
        # Should still return results, with error information
        assert "failing_provider" in results
        assert "error" in results["failing_provider"].data
    
    @pytest.mark.asyncio
    async def test_no_providers_for_source_type(self):
        """Test querying when no providers support the source type"""
        service = DataIntegrationService()
        
        # Query for a source type that no provider supports
        query = DataQuery(source_types=[DataSourceType.HISTORICAL_DATA])
        results = await service.query_data(query)
        
        # Should return empty results
        assert isinstance(results, dict)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_provider_unavailable(self):
        """Test behavior when provider is unavailable"""
        service = DataIntegrationService()
        
        # Mark a provider as unavailable
        service.providers["performance_metrics"].is_available = False
        
        query = DataQuery(source_types=[DataSourceType.PERFORMANCE_METRICS])
        results = await service.query_data(query)
        
        # Should not include the unavailable provider
        assert "performance_metrics" not in results or len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__])