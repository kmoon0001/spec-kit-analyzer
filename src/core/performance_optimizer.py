import asyncio
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
import sqlalchemy
import sqlalchemy.exc
from requests.exceptions import HTTPError

from src.core.advanced_cache_service import advanced_cache_service
from src.core.cache_service import get_cache_stats

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for system optimization."""

    avg_response_time_ms: float
    cache_hit_rate: float
    memory_usage_mb: float
    operations_per_minute: float
    efficiency_score: float
    bottlenecks: list[str]
    recommendations: list[str]
    timestamp: datetime


class PerformanceOptimizer:
    """Main performance optimization service."""

    def __init__(self):
        """Initialize performance optimizer."""
        self.advanced_cache = advanced_cache_service
        self.optimization_history = []
        self.last_optimization = None
        self.optimization_in_progress = False
        self._lock = threading.Lock()

        # Performance thresholds
        self.performance_thresholds: dict[str, float] = {
            "min_hit_rate": 0.7,
            "max_response_time_ms": 500.0,
            "max_memory_usage_mb": 1024.0,
            "min_efficiency_score": 70.0,
        }

        logger.info("Performance optimizer initialized")

    async def analyze_performance(self) -> PerformanceMetrics:
        """Analyze current system performance and identify optimization opportunities."""
        logger.info("Starting performance analysis")

        try:
            # Get comprehensive cache statistics
            cache_stats = await self.advanced_cache.get_comprehensive_stats()

            # Extract key metrics
            base_stats = cache_stats.get("cache_stats", {})
            performance_data = cache_stats.get("performance_metrics", {})
            overall_stats = performance_data.get("overall_stats", {})

            # Calculate performance metrics
            avg_response_time = overall_stats.get("avg_response_time_ms", 0.0)
            cache_hit_rate = overall_stats.get("overall_hit_rate", 0.0)
            memory_usage = base_stats.get("memory_usage_mb", 0.0)
            ops_per_minute = overall_stats.get("operations_per_minute", 0.0)
            efficiency_score = overall_stats.get("cache_efficiency_score", 0.0)

            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(cache_stats)

            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(cache_stats, bottlenecks)

            metrics = PerformanceMetrics(
                avg_response_time_ms=avg_response_time,
                cache_hit_rate=cache_hit_rate,
                memory_usage_mb=memory_usage,
                operations_per_minute=ops_per_minute,
                efficiency_score=efficiency_score,
                bottlenecks=bottlenecks,
                recommendations=recommendations,
                timestamp=datetime.now(),
            )

            logger.info(
                "Performance analysis complete - Efficiency: %s, ",
                efficiency_score,
                f"Hit Rate: {cache_hit_rate * 100}, Response Time: {avg_response_time}ms",
            )

            return metrics

        except Exception as e:
            logger.exception("Error during performance analysis: %s", e)
            # Return default metrics on error
            return PerformanceMetrics(
                avg_response_time_ms=0.0,
                cache_hit_rate=0.0,
                memory_usage_mb=0.0,
                operations_per_minute=0.0,
                efficiency_score=0.0,
                bottlenecks=[f"Analysis error: {e!s}"],
                recommendations=["Fix analysis errors before optimization"],
                timestamp=datetime.now(),
            )

    async def optimize_performance(self, aggressive: bool = False, target_improvement: float = 20.0) -> dict[str, Any]:
        """Execute comprehensive performance optimization.

        Args:
            aggressive: Whether to use aggressive optimization strategies
            target_improvement: Target performance improvement percentage

        Returns:
            Dictionary with optimization results and metrics

        """
        if self.optimization_in_progress:
            return {"status": "already_in_progress", "message": "Optimization already running"}

        with self._lock:
            if self.optimization_in_progress:
                return {"status": "already_in_progress", "message": "Optimization already running"}
            self.optimization_in_progress = True

        start_time = time.time()
        logger.info(
            "Starting performance optimization (aggressive: %s, ",
            aggressive,
            f"target: {target_improvement}% improvement)",
        )

        try:
            # Get baseline performance metrics
            baseline_metrics = await self.analyze_performance()

            optimization_results: dict[str, Any] = {
                "status": "in_progress",
                "baseline_metrics": baseline_metrics,
                "optimizations_applied": [],
                "performance_improvements": {},
                "errors": [],
            }

            # Phase 1: Cache Optimization
            logger.info("Phase 1: Executing cache optimization")
            try:
                cache_optimization = await self.advanced_cache.optimize_cache_performance()
                optimization_results["optimizations_applied"].append("cache_optimization")
                optimization_results["cache_optimization_results"] = cache_optimization
            except Exception as e:
                error_msg = f"Cache optimization failed: {e!s}"
                optimization_results["errors"].append(error_msg)
                logger.warning(error_msg)

            # Phase 2: Memory Optimization
            logger.info("Phase 2: Executing memory optimization")
            try:
                memory_optimization = await self._optimize_memory_usage(aggressive)
                optimization_results["optimizations_applied"].append("memory_optimization")
                optimization_results["memory_optimization_results"] = memory_optimization
            except Exception as e:
                error_msg = f"Memory optimization failed: {e!s}"
                optimization_results["errors"].append(error_msg)
                logger.warning(error_msg)

            # Phase 3: Proactive Cache Warming
            if aggressive:
                logger.info("Phase 3: Executing proactive cache warming")
                try:
                    warming_optimization = await self._execute_proactive_warming()
                    optimization_results["optimizations_applied"].append("proactive_warming")
                    optimization_results["warming_optimization_results"] = warming_optimization
                except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
                    error_msg = f"Proactive warming failed: {e!s}"
                    optimization_results["errors"].append(error_msg)
                    logger.warning(error_msg)

            # Phase 4: Performance Validation
            logger.info("Phase 4: Validating performance improvements")
            await asyncio.sleep(1)  # Allow optimizations to take effect

            final_metrics = await self.analyze_performance()
            optimization_results["final_metrics"] = final_metrics

            # Calculate improvements
            improvements = self._calculate_performance_improvements(baseline_metrics, final_metrics)
            optimization_results["performance_improvements"] = improvements

            # Determine success
            total_improvement = improvements.get("overall_improvement_percent", 0.0)
            success = total_improvement >= target_improvement or len(optimization_results["errors"]) == 0

            optimization_results.update(
                {
                    "status": "completed" if success else "partial_success",
                    "total_improvement_percent": total_improvement,
                    "target_achieved": total_improvement >= target_improvement,
                    "duration_seconds": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Store optimization history
            self.optimization_history.append(optimization_results)
            self.last_optimization = datetime.now()

            # Keep only last 10 optimization records
            if len(self.optimization_history) > 10:
                self.optimization_history = self.optimization_history[-10:]

            logger.info(
                "Performance optimization completed in %ss - ",
                time.time() - start_time,
                f"Overall improvement: {total_improvement}%",
            )

            return optimization_results

        except Exception as e:
            logger.exception("Performance optimization failed: %s", e)
            return {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
            }

        finally:
            with self._lock:
                self.optimization_in_progress = False

    async def _optimize_memory_usage(self, aggressive: bool = False) -> dict[str, Any]:
        """Optimize memory usage through intelligent cache management."""
        logger.debug("Starting memory optimization")

        memory_results: dict[str, Any] = {
            "initial_memory_mb": 0.0,
            "final_memory_mb": 0.0,
            "memory_freed_mb": 0.0,
            "caches_cleaned": [],
            "aggressive_mode": aggressive,
        }

        try:
            # Get initial memory usage
            initial_stats = get_cache_stats()
            memory_results["initial_memory_mb"] = initial_stats.get("memory_usage_mb", 0.0)

            # Clean expired cache entries
            from src.core.cache_service import DocumentCache, EmbeddingCache, LLMResponseCache, NERCache

            # Clear expired entries from all caches
            for cache_class, cache_name in [
                (EmbeddingCache, "embedding"),
                (NERCache, "ner"),
                (DocumentCache, "document"),
                (LLMResponseCache, "llm"),
            ]:
                try:
                    # Try to get cache instance and clear expired entries
                    if hasattr(cache_class, "_cache") and hasattr(cache_class._cache, "clear_expired"):
                        cache_class._cache.clear_expired()
                        memory_results["caches_cleaned"].append(f"{cache_name}_expired")
                except (ImportError, ModuleNotFoundError, AttributeError) as e:
                    logger.warning("Error cleaning %s cache: %s", cache_name, e)

            # Aggressive memory optimization
            if aggressive:
                # Clear low-priority caches if memory usage is high
                current_stats = get_cache_stats()
                if current_stats.get("memory_usage_mb", 0) > 800:  # 800MB threshold
                    # Clear document cache (least critical for performance)
                    DocumentCache.clear()
                    memory_results["caches_cleaned"].append("document_full_clear")

                    # Reduce LLM cache size by clearing older entries
                    try:
                        if hasattr(LLMResponseCache, "_cache") and hasattr(LLMResponseCache._cache, "_cleanup_if_needed"):
                            if hasattr(LLMResponseCache._cache, "max_memory_mb"):
                                LLMResponseCache._cache.max_memory_mb = 128  # Reduce from 256MB
                            LLMResponseCache._cache._cleanup_if_needed()
                            memory_results["caches_cleaned"].append("llm_size_reduction")
                    except (AttributeError, TypeError) as e:
                        logger.warning("Could not reduce LLM cache size: %s", e)

            # Get final memory usage
            final_stats = get_cache_stats()
            memory_results["final_memory_mb"] = final_stats.get("memory_usage_mb", 0.0)
            memory_results["memory_freed_mb"] = memory_results["initial_memory_mb"] - memory_results["final_memory_mb"]

            logger.debug("Memory optimization completed - Freed %.1fMB", memory_results["memory_freed_mb"])

        except Exception as e:
            logger.exception("Memory optimization error: %s", e)
            memory_results["error"] = str(e)

        return memory_results

    async def _execute_proactive_warming(self) -> dict[str, Any]:
        """Execute proactive cache warming for commonly used operations."""
        logger.debug("Starting proactive cache warming")

        warming_results = {
            "warming_requests_scheduled": 0,
            "warming_executed": False,
            "items_warmed": 0,
        }

        try:
            # Schedule warming for common medical terms and phrases
            common_medical_texts = [
                "physical therapy assessment",
                "occupational therapy evaluation",
                "speech therapy progress note",
                "treatment frequency documentation",
                "medical necessity justification",
                "goals and objectives review",
                "functional improvement progress",
                "discharge planning assessment",
            ]

            # Schedule embedding warming
            self.advanced_cache.cache_warming.schedule_warming(
                cache_type="embedding", items=common_medical_texts, priority=7
            )
            warming_results["warming_requests_scheduled"] += len(common_medical_texts)

            # Schedule NER warming for common compliance phrases
            ner_items = [
                {"text": text, "model_name": "clinical_ner"}
                for text in common_medical_texts[:5]  # Limit to avoid overload
            ]

            self.advanced_cache.cache_warming.schedule_warming(cache_type="ner", items=ner_items, priority=6)
            warming_results["warming_requests_scheduled"] += len(ner_items)

            # Execute warming (limited to avoid performance impact)
            warming_execution = await self.advanced_cache.cache_warming.execute_warming(max_items=20)
            warming_results["warming_executed"] = True
            warming_results["warming_execution_results"] = warming_execution
            warming_results["items_warmed"] = warming_execution.get("total_items_warmed", 0)

            logger.debug("Proactive warming completed - %s items warmed", warming_results["items_warmed"])

        except Exception as e:
            logger.exception("Proactive warming error: %s", e)
            warming_results["error"] = str(e)

        return warming_results

    def _identify_bottlenecks(self, cache_stats: dict[str, Any]) -> list[str]:
        """Identify performance bottlenecks from cache statistics."""
        bottlenecks = []

        try:
            base_stats = cache_stats.get("cache_stats", {})
            performance_data = cache_stats.get("performance_metrics", {})
            overall_stats = performance_data.get("overall_stats", {})

            # Check hit rate
            hit_rate = overall_stats.get("overall_hit_rate", 0.0)
            if hit_rate < self.performance_thresholds["min_hit_rate"]:
                bottlenecks.append(
                    f"Low cache hit rate: {hit_rate * 100} (target: {self.performance_thresholds['min_hit_rate']:.1%})"
                )

            # Check response time
            response_time = overall_stats.get("avg_response_time_ms", 0.0)
            if response_time > self.performance_thresholds["max_response_time_ms"]:
                bottlenecks.append(
                    f"High response time: {response_time}ms (target: <{self.performance_thresholds['max_response_time_ms']}ms)"
                )

            # Check memory usage
            memory_usage = base_stats.get("memory_usage_mb", 0.0)
            if memory_usage > self.performance_thresholds["max_memory_usage_mb"]:
                bottlenecks.append(
                    f"High memory usage: {memory_usage}MB (target: <{self.performance_thresholds['max_memory_usage_mb']}MB)"
                )

            # Check efficiency score
            efficiency = overall_stats.get("cache_efficiency_score", 0.0)
            if efficiency < self.performance_thresholds["min_efficiency_score"]:
                bottlenecks.append(
                    f"Low efficiency score: {efficiency} (target: >{self.performance_thresholds['min_efficiency_score']})"
                )

            # Check system memory pressure
            system_memory = base_stats.get("system_memory_percent", 0.0)
            if system_memory > 85:
                bottlenecks.append(f"High system memory pressure: {system_memory}%")

        except Exception as e:
            bottlenecks.append(f"Error analyzing bottlenecks: {e!s}")

        return bottlenecks

    def _generate_optimization_recommendations(self, cache_stats: dict[str, Any], bottlenecks: list[str]) -> list[str]:
        """Generate specific optimization recommendations."""
        recommendations = []

        try:
            performance_data = cache_stats.get("performance_metrics", {})
            base_recommendations = performance_data.get("optimization_recommendations", [])
            recommendations.extend(base_recommendations)

            # Add specific recommendations based on bottlenecks
            for bottleneck in bottlenecks:
                if "hit rate" in bottleneck.lower():
                    recommendations.append("Consider increasing cache TTL values or cache size limits")
                    recommendations.append("Implement proactive cache warming for frequently accessed data")

                if "response time" in bottleneck.lower():
                    recommendations.append("Enable batch processing for multiple operations")
                    recommendations.append("Implement cache prefetching for predictable access patterns")

                if "memory usage" in bottleneck.lower():
                    recommendations.append("Reduce cache size limits or implement more aggressive cleanup")
                    recommendations.append("Consider memory-efficient data structures")

                if "efficiency" in bottleneck.lower():
                    recommendations.append("Review caching strategies and optimize cache key generation")
                    recommendations.append("Implement intelligent cache eviction policies")

            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recommendations.append(rec)

            recommendations = unique_recommendations

        except Exception as e:
            recommendations.append(f"Error generating recommendations: {e!s}")

        return recommendations

    def _calculate_performance_improvements(
        self, baseline: PerformanceMetrics, final: PerformanceMetrics
    ) -> dict[str, float]:
        """Calculate performance improvements between baseline and final metrics."""
        improvements = {}

        try:
            # Response time improvement (lower is better)
            if baseline.avg_response_time_ms > 0:
                response_improvement = (
                    (baseline.avg_response_time_ms - final.avg_response_time_ms) / baseline.avg_response_time_ms * 100
                )
                improvements["response_time_improvement_percent"] = response_improvement

            # Hit rate improvement (higher is better)
            if baseline.cache_hit_rate >= 0:
                hit_rate_improvement = (final.cache_hit_rate - baseline.cache_hit_rate) * 100
                improvements["hit_rate_improvement_percent"] = hit_rate_improvement

            # Memory usage improvement (lower is better)
            if baseline.memory_usage_mb > 0:
                memory_improvement = (baseline.memory_usage_mb - final.memory_usage_mb) / baseline.memory_usage_mb * 100
                improvements["memory_usage_improvement_percent"] = memory_improvement

            # Efficiency score improvement (higher is better)
            if baseline.efficiency_score > 0:
                efficiency_improvement = (
                    (final.efficiency_score - baseline.efficiency_score) / baseline.efficiency_score * 100
                )
                improvements["efficiency_improvement_percent"] = efficiency_improvement

            # Overall improvement (weighted average)
            weights = {"response_time": 0.3, "hit_rate": 0.3, "memory": 0.2, "efficiency": 0.2}
            overall_improvement = (
                improvements.get("response_time_improvement_percent", 0) * weights["response_time"]
                + improvements.get("hit_rate_improvement_percent", 0) * weights["hit_rate"]
                + improvements.get("memory_usage_improvement_percent", 0) * weights["memory"]
                + improvements.get("efficiency_improvement_percent", 0) * weights["efficiency"]
            )
            improvements["overall_improvement_percent"] = overall_improvement

        except Exception as e:
            improvements["calculation_error"] = str(e)

        return improvements

    def get_optimization_status(self) -> dict[str, Any]:
        """Get current optimization status and history."""
        with self._lock:
            return {
                "optimization_in_progress": self.optimization_in_progress,
                "last_optimization": self.last_optimization.isoformat() if self.last_optimization else None,
                "optimization_count": len(self.optimization_history),
                "recent_optimizations": self.optimization_history[-3:] if self.optimization_history else [],
                "performance_thresholds": self.performance_thresholds,
            }

    async def schedule_periodic_optimization(self, interval_hours: float = 24.0, aggressive: bool = False) -> None:
        """Schedule periodic performance optimization.

        Args:
            interval_hours: Hours between optimization runs
            aggressive: Whether to use aggressive optimization

        """
        logger.info("Scheduling periodic optimization every %s hours (aggressive: {aggressive})", interval_hours)

        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds

                logger.info("Starting scheduled performance optimization")
                result = await self.optimize_performance(aggressive=aggressive, target_improvement=10.0)

                if result.get("status") == "completed":
                    improvement = result.get("total_improvement_percent", 0)
                    logger.info("Scheduled optimization completed with %.1f%% improvement", improvement)
                else:
                    logger.warning("Scheduled optimization had issues: %s", result.get("status"))

            except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
                logger.exception("Error in scheduled optimization: %s", e)
                # Continue the loop even if one optimization fails
                continue


# Global performance optimizer instance
# Global performance optimizer instance
# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


class LLMResponseCache:
    """LLM response cache implementation."""

    _cache: dict[str, str] = {}

    @classmethod
    def get_response(cls, model_name: str, prompt: str) -> str | None:
        return cls._cache.get(f"{model_name}:{prompt}")

    @classmethod
    def set_response(cls, model_name: str, prompt: str, response: str, ttl_hours: int = 24):
        cls._cache[f"{model_name}:{prompt}"] = response

    @classmethod
    def memory_usage_mb(cls) -> float:
        return len(str(cls._cache)) / (1024 * 1024)

    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

    @classmethod
    def clear(cls):
        cls._cache.clear()


class DocumentCache:
    """Document cache implementation."""

    _cache: dict[str, dict] = {}

    @classmethod
    def get_document(cls, doc_id: str) -> dict | None:
        return cls._cache.get(doc_id)

    @classmethod
    def set_document(cls, doc_id: str, document: dict):
        cls._cache[doc_id] = document

    @classmethod
    def memory_usage_mb(cls) -> float:
        return len(str(cls._cache)) / (1024 * 1024)

    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

    @classmethod
    def clear(cls):
        cls._cache.clear()
