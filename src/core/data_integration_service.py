"""
Data Integration Service - Comprehensive data provider system

This module provides the data integration layer that connects the reporting system
to all existing performance and compliance systems using clean interfaces and
dependency injection patterns.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Protocol, TypeVar, Generic
import json

from .report_generation_engine import DataProvider, ReportConfig, ReportType, TimeRange

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DataSourceType(Enum):
    """Types of data sources available"""
    PERFORMANCE_METRICS = "performance_metrics"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    SYSTEM_MONITORING = "system_monitoring"
    OPTIMIZATION_RESULTS = "optimization_results"
    TEST_RESULTS = "test_results"
    HISTORICAL_DATA = "historical_data"


class DataQuality(Enum):
    """Data quality indicators"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class DataSourceMetadata:
    """Metadata about a data source"""
    source_id: str
    source_type: DataSourceType
    description: str
    last_updated: datetime
    data_quality: DataQuality = DataQuality.UNKNOWN
    availability: bool = True
    schema_version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "description": self.description,
            "last_updated": self.last_updated.isoformat(),
            "data_quality": self.data_quality.value,
            "availability": self.availability,
            "schema_version": self.schema_version,
            "tags": self.tags
        }


@dataclass
class DataQuery:
    """Query specification for data retrieval"""
    source_types: List[DataSourceType]
    time_range: Optional[TimeRange] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    aggregation_level: str = "raw"  # raw, hourly, daily, weekly
    include_metadata: bool = True
    max_records: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "source_types": [st.value for st in self.source_types],
            "time_range": {
                "start_time": self.time_range.start_time.isoformat(),
                "end_time": self.time_range.end_time.isoformat()
            } if self.time_range else None,
            "filters": self.filters,
            "aggregation_level": self.aggregation_level,
            "include_metadata": self.include_metadata,
            "max_records": self.max_records
        }


@dataclass
class DataResult(Generic[T]):
    """Result container for data queries"""
    data: T
    metadata: DataSourceMetadata
    query: DataQuery
    retrieved_at: datetime
    record_count: int = 0
    has_more: bool = False
    next_cursor: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "data": self.data,
            "metadata": self.metadata.to_dict(),
            "query": self.query.to_dict(),
            "retrieved_at": self.retrieved_at.isoformat(),
            "record_count": self.record_count,
            "has_more": self.has_more,
            "next_cursor": self.next_cursor
        }


class BaseDataProvider(ABC):
    """Abstract base class for all data providers"""
    
    def __init__(self, provider_id: str, description: str):
        self.provider_id = provider_id
        self.description = description
        self.is_available = True
        self.last_health_check = datetime.now()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self.default_cache_duration = timedelta(minutes=5)
    
    @abstractmethod
    async def get_data(self, config: ReportConfig) -> Dict[str, Any]:
        """Get data for report generation (required by DataProvider protocol)"""
        pass
    
    @abstractmethod
    def supports_report_type(self, report_type: ReportType) -> bool:
        """Check if this provider supports the given report type"""
        pass
    
    @abstractmethod
    async def query_data(self, query: DataQuery) -> DataResult[Dict[str, Any]]:
        """Execute a data query and return results"""
        pass
    
    @abstractmethod
    async def get_metadata(self) -> DataSourceMetadata:
        """Get metadata about this data source"""
        pass
    
    async def health_check(self) -> bool:
        """Check if the data provider is healthy and available"""
        try:
            metadata = await self.get_metadata()
            self.is_available = metadata.availability
            self.last_health_check = datetime.now()
            return self.is_available
        except Exception as e:
            logger.error(f"Health check failed for provider {self.provider_id}: {e}")
            self.is_available = False
            return False
    
    def _get_cache_key(self, query: DataQuery) -> str:
        """Generate cache key for query"""
        return f"{self.provider_id}_{hash(str(query.to_dict()))}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return False
        
        if cache_key not in self._cache_ttl:
            return False
        
        return datetime.now() < self._cache_ttl[cache_key]
    
    def _cache_data(self, cache_key: str, data: Any, ttl: Optional[timedelta] = None) -> None:
        """Cache data with TTL"""
        self._cache[cache_key] = data
        cache_duration = ttl or self.default_cache_duration
        self._cache_ttl[cache_key] = datetime.now() + cache_duration
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
        self._cache_ttl.clear()