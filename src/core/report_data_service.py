"""
Report Data Aggregation Service

This module handles data aggregation from multiple sources for report generation.
Separated from the main engine for better maintainability and testing.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .report_models import DataProvider, ReportType

logger = logging.getLogger(__name__)


class DataAggregationService:
    """Service for aggregating data from multiple sources for reports"""
    
    def __init__(self):
        self.data_providers: Dict[str, DataProvider] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        self.default_cache_duration = timedelta(minutes=5)
    
    def register_data_provider(self, name: str, provider: DataProvider) -> None:
        """Register a data provider"""
        self.data_providers[name] = provider
        logger.info(f"Registered data provider: {name}")
    
    def unregister_data_provider(self, name: str) -> None:
        """Unregister a data provider"""
        if name in self.data_providers:
            del self.data_providers[name]
            logger.info(f"Unregistered data provider: {name}")
    
    def get_aggregated_data(self, report_type: ReportType, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get aggregated data from all relevant providers"""
        cache_key = f"{report_type.value}_{hash(str(sorted(filters.items())))}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Returning cached data for {cache_key}")
            return self.cache[cache_key]
        
        aggregated_data = {}
        
        for provider_name, provider in self.data_providers.items():
            try:
                if provider.supports_report_type(report_type):
                    provider_data = provider.get_data(report_type, filters)
                    aggregated_data[provider_name] = provider_data
                    logger.debug(f"Got data from provider: {provider_name}")
            except Exception as e:
                logger.error(f"Error getting data from provider {provider_name}: {e}")
                aggregated_data[provider_name] = {"error": str(e)}
        
        # Cache the result
        self.cache[cache_key] = aggregated_data
        self.cache_ttl[cache_key] = datetime.now() + self.default_cache_duration
        
        return aggregated_data
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        if cache_key not in self.cache_ttl:
            return False
        
        return datetime.now() < self.cache_ttl[cache_key]
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
        self.cache_ttl.clear()
        logger.info("Cleared data aggregation cache")
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all registered providers"""
        status = {}
        for name, provider in self.data_providers.items():
            try:
                # Test if provider is responsive
                test_data = provider.get_data(ReportType.PERFORMANCE_ANALYSIS, {})
                status[name] = {
                    "status": "healthy",
                    "supports_types": [rt.value for rt in ReportType if provider.supports_report_type(rt)],
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                status[name] = {
                    "status": "error",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        return status