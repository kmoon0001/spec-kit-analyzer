"""
Performance Monitoring System

Comprehensive performance monitoring and metrics collection for all system components.
Provides real-time insights into system health, performance bottlenecks, and optimization opportunities.
"""

import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import uuid

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    timestamp: datetime
    component: str
    operation: str
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """System health snapshot."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_threads: int
    response_time_avg: float
    error_rate: float
    throughput: float


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    
    This system provides:
    - Real-time performance metrics collection
    - System health monitoring and alerting
    - Performance trend analysis and reporting
    - Bottleneck identification and optimization suggestions
    - Resource usage tracking and optimization
    
    Features:
    - Component-level performance tracking
    - Memory and CPU usage monitoring
    - Response time analysis
    - Error rate tracking
    - Throughput measurement
    - Performance alerts and notifications
    
    Example:
        >>> monitor = PerformanceMonitor()
        >>> with monitor.track_operation("pdf_export", "generate_report"):
        ...     generate_pdf_report()
        >>> health = monitor.get_system_health()
        >>> print(f"System health: {health.cpu_usage}% CPU")
    """
    
    def __init__(self, max_metrics_history: int = 10000):
        """Initialize the performance monitoring system."""
        self.max_metrics_history = max_metrics_history
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        self.component_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.performance_thresholds = self._initialize_thresholds()
        self.alerts_enabled = True
        self.monitoring_active = True
        
        # Background monitoring thread
        self.monitor_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Performance monitoring system initialized")
    
    def track_operation(self, component: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracking operation performance.
        
        Args:
            component: Component name (e.g., "pdf_export", "ai_analysis")
            operation: Operation name (e.g., "generate_report", "analyze_document")
            metadata: Additional metadata to track
            
        Example:
            >>> with monitor.track_operation("ai_analysis", "compliance_check"):
            ...     result = analyze_compliance(document)
        """
        return OperationTracker(self, component, operation, metadata or {})
    
    async def track_async_operation(self, 
                                  component: str, 
                                  operation: str, 
                                  func: Callable, 
                                  *args, 
                                  **kwargs) -> Any:
        """
        Track an async operation and return its result.
        
        Args:
            component: Component name
            operation: Operation name
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Result of the function execution
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = self._get_cpu_usage()
        operation_id = str(uuid.uuid4())
        
        # Track active operation
        self.active_operations[operation_id] = {
            "component": component,
            "operation": operation,
            "start_time": start_time,
            "start_memory": start_memory
        }
        
        try:
            result = await func(*args, **kwargs)
            success = True
            return result
            
        except Exception:
            success = False
            raise
            
        finally:
            # Calculate metrics
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            end_memory = self._get_memory_usage()
            end_cpu = self._get_cpu_usage()
            
            # Create metric
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                component=component,
                operation=operation,
                duration_ms=duration_ms,
                memory_usage_mb=end_memory - start_memory,
                cpu_usage_percent=(end_cpu + start_cpu) / 2,
                success=success,
                metadata=kwargs.get('metadata', {})
            )
            
            # Store metric
            self._store_metric(metric)
            
            # Remove from active operations
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    def record_metric(self,
                     component: str,
                     operation: str,
                     duration_ms: float,
                     success: bool = True,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Manually record a performance metric.
        
        Args:
            component: Component name
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            success: Whether the operation was successful
            metadata: Additional metadata
        """
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            memory_usage_mb=self._get_memory_usage(),
            cpu_usage_percent=self._get_cpu_usage(),
            success=success,
            metadata=metadata or {}
        )
        
        self._store_metric(metric)
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health snapshot."""
        # Calculate recent metrics
        recent_metrics = [m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(minutes=5)]
        
        if recent_metrics:
            avg_response_time = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
            error_rate = sum(1 for m in recent_metrics if not m.success) / len(recent_metrics)
            throughput = len(recent_metrics) / 5.0  # Operations per minute
        else:
            avg_response_time = 0.0
            error_rate = 0.0
            throughput = 0.0
        
        return SystemHealth(
            timestamp=datetime.now(),
            cpu_usage=self._get_cpu_usage(),
            memory_usage=self._get_memory_usage_percent(),
            disk_usage=self._get_disk_usage(),
            active_threads=threading.active_count(),
            response_time_avg=avg_response_time,
            error_rate=error_rate,
            throughput=throughput
        )
    
    def get_component_performance(self, component: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance statistics for a specific component.
        
        Args:
            component: Component name
            hours: Number of hours to analyze
            
        Returns:
            Dict containing performance statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        component_metrics = [
            m for m in self.metrics_history 
            if m.component == component and m.timestamp > cutoff_time
        ]
        
        if not component_metrics:
            return {
                "component": component,
                "total_operations": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "min_duration_ms": 0.0,
                "max_duration_ms": 0.0,
                "avg_memory_usage_mb": 0.0,
                "operations_per_hour": 0.0
            }
        
        successful_ops = [m for m in component_metrics if m.success]
        durations = [m.duration_ms for m in component_metrics]
        memory_usage = [m.memory_usage_mb for m in component_metrics]
        
        return {
            "component": component,
            "total_operations": len(component_metrics),
            "success_rate": len(successful_ops) / len(component_metrics),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "avg_memory_usage_mb": sum(memory_usage) / len(memory_usage),
            "operations_per_hour": len(component_metrics) / hours,
            "error_count": len(component_metrics) - len(successful_ops),
            "p95_duration_ms": self._calculate_percentile(durations, 95),
            "p99_duration_ms": self._calculate_percentile(durations, 99)
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance trends over time.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dict containing trend analysis
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"trends": [], "summary": "No data available"}
        
        # Group metrics by hour
        hourly_metrics = defaultdict(list)
        for metric in recent_metrics:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_metrics[hour_key].append(metric)
        
        trends = []
        for hour, metrics in sorted(hourly_metrics.items()):
            avg_duration = sum(m.duration_ms for m in metrics) / len(metrics)
            success_rate = sum(1 for m in metrics if m.success) / len(metrics)
            
            trends.append({
                "hour": hour.isoformat(),
                "operation_count": len(metrics),
                "avg_duration_ms": avg_duration,
                "success_rate": success_rate,
                "throughput": len(metrics)
            })
        
        return {
            "trends": trends,
            "summary": f"Analyzed {len(recent_metrics)} operations over {hours} hours"
        }
    
    def get_bottlenecks(self, threshold_ms: float = 1000.0) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks.
        
        Args:
            threshold_ms: Duration threshold for identifying slow operations
            
        Returns:
            List of bottleneck information
        """
        recent_metrics = [m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(hours=1)]
        slow_operations = [m for m in recent_metrics if m.duration_ms > threshold_ms]
        
        # Group by component and operation
        bottlenecks = defaultdict(list)
        for metric in slow_operations:
            key = f"{metric.component}.{metric.operation}"
            bottlenecks[key].append(metric)
        
        result = []
        for operation, metrics in bottlenecks.items():
            avg_duration = sum(m.duration_ms for m in metrics) / len(metrics)
            result.append({
                "operation": operation,
                "occurrence_count": len(metrics),
                "avg_duration_ms": avg_duration,
                "max_duration_ms": max(m.duration_ms for m in metrics),
                "impact_score": len(metrics) * avg_duration,  # Simple impact calculation
                "recommendations": self._get_optimization_recommendations(operation, avg_duration)
            })
        
        # Sort by impact score
        result.sort(key=lambda x: x["impact_score"], reverse=True)
        return result
    
    def _store_metric(self, metric: PerformanceMetric):
        """Store a performance metric."""
        self.metrics_history.append(metric)
        self.component_metrics[metric.component].append(metric)
        
        # Check for performance alerts
        if self.alerts_enabled:
            self._check_performance_alerts(metric)
    
    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any performance alerts."""
        thresholds = self.performance_thresholds.get(metric.component, {})
        
        # Duration alert
        if metric.duration_ms > thresholds.get("max_duration_ms", 5000):
            logger.warning(f"Performance alert: {metric.component}.{metric.operation} took {metric.duration_ms:.1f}ms")
        
        # Memory alert
        if metric.memory_usage_mb > thresholds.get("max_memory_mb", 100):
            logger.warning(f"Memory alert: {metric.component}.{metric.operation} used {metric.memory_usage_mb:.1f}MB")
        
        # Error rate alert
        component_recent = [m for m in self.component_metrics[metric.component][-10:]]
        if len(component_recent) >= 5:
            error_rate = sum(1 for m in component_recent if not m.success) / len(component_recent)
            if error_rate > thresholds.get("max_error_rate", 0.1):
                logger.error(f"Error rate alert: {metric.component} has {error_rate:.1%} error rate")
    
    def _background_monitoring(self):
        """Background thread for continuous system monitoring."""
        while self.monitoring_active:
            try:
                # Record system health metrics
                health = self.get_system_health()
                
                # Check system-level alerts
                if health.cpu_usage > 90:
                    logger.warning(f"High CPU usage: {health.cpu_usage:.1f}%")
                
                if health.memory_usage > 90:
                    logger.warning(f"High memory usage: {health.memory_usage:.1f}%")
                
                if health.error_rate > 0.1:
                    logger.warning(f"High error rate: {health.error_rate:.1%}")
                
                # Sleep for monitoring interval
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_memory_usage_percent(self) -> float:
        """Get system memory usage percentage."""
        return psutil.virtual_memory().percent
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=0.1)
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage."""
        return psutil.disk_usage('/').percent
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _get_optimization_recommendations(self, operation: str, avg_duration: float) -> List[str]:
        """Get optimization recommendations for slow operations."""
        recommendations = []
        
        if "pdf_export" in operation:
            recommendations.extend([
                "Consider reducing PDF complexity or size",
                "Implement PDF generation caching",
                "Use background processing for large reports"
            ])
        elif "ai_analysis" in operation:
            recommendations.extend([
                "Optimize document chunking strategy",
                "Implement result caching for similar documents",
                "Consider using smaller AI models for faster processing"
            ])
        elif "database" in operation:
            recommendations.extend([
                "Add database indexes for frequently queried fields",
                "Implement query result caching",
                "Consider database connection pooling"
            ])
        else:
            recommendations.extend([
                "Profile the operation to identify bottlenecks",
                "Consider implementing caching",
                "Optimize algorithm complexity"
            ])
        
        return recommendations
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize performance thresholds for different components."""
        return {
            "pdf_export": {
                "max_duration_ms": 10000,  # 10 seconds
                "max_memory_mb": 200,
                "max_error_rate": 0.05
            },
            "ai_analysis": {
                "max_duration_ms": 30000,  # 30 seconds
                "max_memory_mb": 500,
                "max_error_rate": 0.1
            },
            "database": {
                "max_duration_ms": 1000,   # 1 second
                "max_memory_mb": 50,
                "max_error_rate": 0.01
            },
            "ehr_integration": {
                "max_duration_ms": 15000,  # 15 seconds
                "max_memory_mb": 100,
                "max_error_rate": 0.05
            }
        }


class OperationTracker:
    """Context manager for tracking individual operations."""
    
    def __init__(self, monitor: PerformanceMonitor, component: str, operation: str, metadata: Dict[str, Any]):
        self.monitor = monitor
        self.component = component
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = self.monitor._get_memory_usage()
        self.start_cpu = self.monitor._get_cpu_usage()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration_ms = (end_time - self.start_time) * 1000
        end_memory = self.monitor._get_memory_usage()
        end_cpu = self.monitor._get_cpu_usage()
        
        success = exc_type is None
        
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            component=self.component,
            operation=self.operation,
            duration_ms=duration_ms,
            memory_usage_mb=end_memory - self.start_memory,
            cpu_usage_percent=(end_cpu + self.start_cpu) / 2,
            success=success,
            metadata=self.metadata
        )
        
        self.monitor._store_metric(metric)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()