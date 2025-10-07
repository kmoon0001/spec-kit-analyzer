"""
Tests for Data Aggregator

This module tests the comprehensive metric processing, aggregation, and storage
functionality including time-series data management and automatic cleanup.
"""


from src.core.data_aggregator import (
    AggregationLevel
)


class TestAggregationLevel:
    """Test aggregation level enum."""
    
    def test_aggregation_levels(self):
        """Test aggregation level values."""
        assert AggregationLevel.RAW.value == "raw"
        assert AggregationLevel.SHORT_TERM.value == "short"
        assert AggregationLevel.MEDIUM_TERM.value == "medium"
        assert AggregationLevel.LONG_TERM.value == "long"


class TestAggregatedMetric:
    """Test aggregated metric data."""