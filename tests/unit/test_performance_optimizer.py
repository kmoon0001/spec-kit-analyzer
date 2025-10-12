"""Tests for performance optimization functionality."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.core.advanced_cache_service import BatchCacheOperations, CachePerformanceMonitor, CacheWarmingService
from src.core.performance_optimizer import PerformanceMetrics, PerformanceOptimizer, performance_optimizer


class TestCachePerformanceMonitor:
    """Test cache performance monitoring functionality."""

    def test_initialization(self):
        """Test performance monitor initialization."""
        monitor = CachePerformanceMonitor(window_size=100)

        assert monitor.window_size == 100
        assert len(monitor.operation_times) == 0
        assert len(monitor.hit_miss_history) == 0
        assert len(monitor.cache_metrics) == 0

    def test_record_operation(self):
        """Test recording cache operations."""
        monitor = CachePerformanceMonitor(window_size=10)

        # Record some operations
        monitor.record_operation("test_cache", "get", 50.0, True)
        monitor.record_operation("test_cache", "get", 75.0, False)
        monitor.record_operation("test_cache", "set", 25.0, True)

        # Check operation times recorded
        assert len(monitor.operation_times) == 3
        assert len(monitor.hit_miss_history) == 3

        # Check cache metrics updated
        metrics = monitor.cache_metrics["test_cache"]
        assert metrics.hits == 2
        assert metrics.misses == 1
        assert metrics.total_requests == 3
        assert metrics.hit_rate == 2 / 3
        assert metrics.avg_response_time_ms > 0

    def test_performance_summary(self):
        """Test getting performance summary."""
        monitor = CachePerformanceMonitor()

        # Add some test data
        for _i in range(10):
            hit = _i % 2 == 0  # 50% hit rate
            duration = 50.0 + _i * 10  # Increasing duration
            monitor.record_operation("test_cache", "get", duration, hit)

        summary = monitor.get_performance_summary()

        assert "overall_stats" in summary
        assert "cache_specific_stats" in summary
        assert "recent_performance" in summary
        assert "optimization_recommendations" in summary

        overall_stats = summary["overall_stats"]
        assert overall_stats["total_operations"] == 10
        assert overall_stats["overall_hit_rate"] == 0.5
        assert overall_stats["avg_response_time_ms"] > 0

    def test_recommendations_generation(self):
        """Test optimization recommendations generation."""
        monitor = CachePerformanceMonitor()

        # Add data that should trigger recommendations
        for _ in range(20):
            # Low hit rate and high response times
            monitor.record_operation("slow_cache", "get", 500.0, False)

        summary = monitor.get_performance_summary()
        recommendations = summary["optimization_recommendations"]

        assert len(recommendations) > 0
        assert any("hit rate" in rec.lower() for rec in recommendations)


class TestBatchCacheOperations:
    """Test batch cache operations functionality."""

    def test_initialization(self):
        """Test batch operations initialization."""
        batch_ops = BatchCacheOperations()

        assert batch_ops.executor is not None
        assert batch_ops.performance_monitor is None

    @pytest.mark.asyncio
    async def test_batch_get_embeddings(self):
        """Test batch embedding retrieval."""
        batch_ops = BatchCacheOperations()

        texts = ["test text 1", "test text 2", "test text 3"]

        # Mock the embedding cache
        with patch("src.core.advanced_cache_service.EmbeddingCache") as mock_cache:
            mock_cache.get_embedding.return_value = [0.1, 0.2, 0.3]  # Mock embedding

            results = await batch_ops.batch_get_embeddings(texts)

            assert len(results) == len(texts)
            assert all(text in results for text in texts)
            assert mock_cache.get_embedding.call_count == len(texts)

    @pytest.mark.asyncio
    async def test_batch_set_embeddings(self):
        """Test batch embedding storage."""
        batch_ops = BatchCacheOperations()

        embeddings = {"text1": [0.1, 0.2, 0.3], "text2": [0.4, 0.5, 0.6], "text3": [0.7, 0.8, 0.9]}

        # Mock the embedding cache
        with patch("src.core.advanced_cache_service.EmbeddingCache") as mock_cache:
            await batch_ops.batch_set_embeddings(embeddings, ttl_hours=12.0)

            assert mock_cache.set_embedding.call_count == len(embeddings)

    @pytest.mark.asyncio
    async def test_batch_get_ner_results(self):
        """Test batch NER results retrieval."""
        batch_ops = BatchCacheOperations()

        texts = ["medical text 1", "medical text 2"]
        model_name = "clinical_ner"

        # Mock the NER cache
        with patch("src.core.advanced_cache_service.NERCache") as mock_cache:
            mock_cache.get_ner_results.return_value = [{"entity": "test", "score": 0.9}]

            results = await batch_ops.batch_get_ner_results(texts, model_name)

            assert len(results) == len(texts)
            assert all(text in results for text in texts)
            assert mock_cache.get_ner_results.call_count == len(texts)

    def test_cleanup(self):
        """Test batch operations cleanup."""
        batch_ops = BatchCacheOperations()

        # Should not raise an exception
        batch_ops.cleanup()


class TestCacheWarmingService:
    """Test cache warming service functionality."""

    def test_initialization(self):
        """Test cache warming service initialization."""
        warming_service = CacheWarmingService()

        assert warming_service.warming_queue is not None
        assert warming_service.warming_in_progress is False

    def test_schedule_warming(self):
        """Test scheduling cache warming requests."""
        warming_service = CacheWarmingService()

        items = ["text1", "text2", "text3"]
        warming_service.schedule_warming("embedding", items, priority=8)

        assert len(warming_service.warming_queue) == 1

        request = warming_service.warming_queue[0]
        assert request["cache_type"] == "embedding"
        assert request["items"] == items
        assert request["priority"] == 8

    def test_priority_ordering(self):
        """Test that warming requests are ordered by priority."""
        warming_service = CacheWarmingService()

        # Add requests with different priorities
        warming_service.schedule_warming("embedding", ["low"], priority=3)
        warming_service.schedule_warming("ner", ["high"], priority=9)
        warming_service.schedule_warming("llm", ["medium"], priority=6)

        assert len(warming_service.warming_queue) == 3

        # Check that highest priority is first
        assert warming_service.warming_queue[0]["priority"] == 9
        assert warming_service.warming_queue[1]["priority"] == 6
        assert warming_service.warming_queue[2]["priority"] == 3

    @pytest.mark.asyncio
    async def test_execute_warming(self):
        """Test executing cache warming."""
        warming_service = CacheWarmingService()

        # Schedule some warming requests
        warming_service.schedule_warming("embedding", ["text1", "text2"], priority=5)

        # Mock the warming methods
        with patch.object(warming_service, "_warm_embeddings", new_callable=AsyncMock) as mock_warm:
            result = await warming_service.execute_warming(max_items=10)

            assert result["status"] == "completed"
            assert result["total_items_warmed"] == 2
            assert mock_warm.called

    def test_get_warming_status(self):
        """Test getting warming status."""
        warming_service = CacheWarmingService()

        # Add some requests
        warming_service.schedule_warming("embedding", ["text1"], priority=5)
        warming_service.schedule_warming("ner", ["text2", "text3"], priority=7)

        status = warming_service.get_warming_status()

        assert status["warming_in_progress"] is False
        assert status["queue_size"] == 2
        assert "queued_items_by_type" in status

        items_by_type = status["queued_items_by_type"]
        assert items_by_type["embedding"] == 1
        assert items_by_type["ner"] == 2


class TestPerformanceOptimizer:
    """Test main performance optimizer functionality."""

    def test_initialization(self):
        """Test performance optimizer initialization."""
        optimizer = PerformanceOptimizer()

        assert optimizer.advanced_cache is not None
        assert optimizer.optimization_history == []
        assert optimizer.last_optimization is None
        assert optimizer.optimization_in_progress is False
        assert "min_hit_rate" in optimizer.performance_thresholds

    @pytest.mark.asyncio
    async def test_analyze_performance(self):
        """Test performance analysis."""
        optimizer = PerformanceOptimizer()

        # Mock the advanced cache service
        mock_stats = {
            "cache_stats": {"memory_usage_mb": 256.0, "system_memory_percent": 45.0},
            "performance_metrics": {
                "overall_stats": {
                    "avg_response_time_ms": 150.0,
                    "overall_hit_rate": 0.75,
                    "operations_per_minute": 120.0,
                    "cache_efficiency_score": 85.0,
                }
            },
        }

        with patch.object(
            optimizer.advanced_cache, "get_comprehensive_stats", new_callable=AsyncMock, return_value=mock_stats
        ):
            metrics = await optimizer.analyze_performance()

            assert isinstance(metrics, PerformanceMetrics)
            assert metrics.avg_response_time_ms == 150.0
            assert metrics.cache_hit_rate == 0.75
            assert metrics.memory_usage_mb == 256.0
            assert metrics.efficiency_score == 85.0
            assert isinstance(metrics.bottlenecks, list)
            assert isinstance(metrics.recommendations, list)

    @pytest.mark.asyncio
    async def test_optimize_performance(self):
        """Test performance optimization execution."""
        optimizer = PerformanceOptimizer()

        # Mock the analysis and optimization methods
        mock_metrics = PerformanceMetrics(
            avg_response_time_ms=200.0,
            cache_hit_rate=0.6,
            memory_usage_mb=400.0,
            operations_per_minute=80.0,
            efficiency_score=60.0,
            bottlenecks=["Low hit rate"],
            recommendations=["Increase cache size"],
            timestamp=datetime.now(),
        )

        with patch.object(optimizer, "analyze_performance", return_value=mock_metrics):
            with patch.object(
                optimizer.advanced_cache,
                "optimize_cache_performance",
                new_callable=AsyncMock,
                return_value={"status": "completed"},
            ):
                with patch.object(
                    optimizer, "_optimize_memory_usage", new_callable=AsyncMock, return_value={"memory_freed_mb": 50.0}
                ):
                    result = await optimizer.optimize_performance(target_improvement=15.0)

                    assert result["status"] in ["completed", "partial_success"]
                    assert "baseline_metrics" in result
                    assert "final_metrics" in result
                    assert "optimizations_applied" in result
                    assert "performance_improvements" in result

    def test_identify_bottlenecks(self):
        """Test bottleneck identification."""
        optimizer = PerformanceOptimizer()

        # Create cache stats that should trigger bottleneck detection
        cache_stats = {
            "cache_stats": {
                "memory_usage_mb": 1200.0,  # Above threshold
                "system_memory_percent": 90.0,  # High system memory
            },
            "performance_metrics": {
                "overall_stats": {
                    "overall_hit_rate": 0.4,  # Below threshold
                    "avg_response_time_ms": 800.0,  # Above threshold
                    "cache_efficiency_score": 50.0,  # Below threshold
                }
            },
        }

        bottlenecks = optimizer._identify_bottlenecks(cache_stats)

        assert len(bottlenecks) > 0
        assert any("hit rate" in bottleneck.lower() for bottleneck in bottlenecks)
        assert any("response time" in bottleneck.lower() for bottleneck in bottlenecks)
        assert any("memory" in bottleneck.lower() for bottleneck in bottlenecks)

    def test_generate_optimization_recommendations(self):
        """Test optimization recommendation generation."""
        optimizer = PerformanceOptimizer()

        cache_stats = {"performance_metrics": {"optimization_recommendations": ["Base recommendation"]}}

        bottlenecks = ["Low cache hit rate: 40%", "High response time: 800ms", "High memory usage: 1200MB"]

        recommendations = optimizer._generate_optimization_recommendations(cache_stats, bottlenecks)

        assert len(recommendations) > 0
        assert "Base recommendation" in recommendations
        assert any("cache TTL" in rec or "cache size" in rec for rec in recommendations)
        assert any("batch processing" in rec or "prefetching" in rec for rec in recommendations)

    def test_calculate_performance_improvements(self):
        """Test performance improvement calculations."""
        optimizer = PerformanceOptimizer()

        baseline = PerformanceMetrics(
            avg_response_time_ms=200.0,
            cache_hit_rate=0.6,
            memory_usage_mb=400.0,
            operations_per_minute=80.0,
            efficiency_score=60.0,
            bottlenecks=[],
            recommendations=[],
            timestamp=datetime.now(),
        )

        final = PerformanceMetrics(
            avg_response_time_ms=120.0,  # 40% improvement
            cache_hit_rate=0.8,  # 20% improvement
            memory_usage_mb=300.0,  # 25% improvement
            operations_per_minute=100.0,
            efficiency_score=80.0,  # 33% improvement
            bottlenecks=[],
            recommendations=[],
            timestamp=datetime.now(),
        )

        improvements = optimizer._calculate_performance_improvements(baseline, final)

        assert improvements["response_time_improvement_percent"] == pytest.approx(40.0)
        assert improvements["hit_rate_improvement_percent"] == pytest.approx(20.0, rel=1e-7)
        assert improvements["memory_usage_improvement_percent"] == pytest.approx(25.0)
        assert improvements["efficiency_improvement_percent"] > 30.0
        assert "overall_improvement_percent" in improvements

    def test_get_optimization_status(self):
        """Test getting optimization status."""
        optimizer = PerformanceOptimizer()

        status = optimizer.get_optimization_status()

        assert "optimization_in_progress" in status
        assert "last_optimization" in status
        assert "optimization_count" in status
        assert "recent_optimizations" in status
        assert "performance_thresholds" in status

        assert status["optimization_in_progress"] is False
        assert status["optimization_count"] == 0
        assert status["recent_optimizations"] == []

    @pytest.mark.asyncio
    async def test_memory_optimization(self):
        """Test memory optimization functionality."""
        optimizer = PerformanceOptimizer()

        # Mock cache stats
        with patch("src.core.performance_optimizer.get_cache_stats") as mock_stats:
            mock_stats.side_effect = [
                {"memory_usage_mb": 500.0},  # Initial
                {"memory_usage_mb": 400.0},  # Final
            ]

            result = await optimizer._optimize_memory_usage(aggressive=True)

            assert "initial_memory_mb" in result
            assert "final_memory_mb" in result
            assert "memory_freed_mb" in result
            assert "caches_cleaned" in result
            assert result["aggressive_mode"] is True

    @pytest.mark.asyncio
    async def test_proactive_warming(self):
        """Test proactive cache warming."""
        optimizer = PerformanceOptimizer()

        # Mock the cache warming service
        mock_warming_result = {"status": "completed", "total_items_warmed": 15, "duration_ms": 1500.0}

        with patch.object(
            optimizer.advanced_cache.cache_warming,
            "execute_warming",
            new_callable=AsyncMock,
            return_value=mock_warming_result,
        ):
            result = await optimizer._execute_proactive_warming()

            assert result["warming_executed"] is True
            assert result["items_warmed"] == 15
            assert "warming_requests_scheduled" in result


@pytest.mark.integration
class TestPerformanceOptimizerIntegration:
    """Integration tests for performance optimizer."""

    @pytest.mark.asyncio
    async def test_full_optimization_cycle(self):
        """Test complete optimization cycle."""
        optimizer = PerformanceOptimizer()

        # This test runs the actual optimization cycle
        # It should complete without errors even if no significant improvements are made
        result = await optimizer.optimize_performance(
            aggressive=False,
            target_improvement=5.0,  # Low target for testing
        )

        assert "status" in result
        assert result["status"] in ["completed", "partial_success", "failed"]
        assert "baseline_metrics" in result
        assert "final_metrics" in result
        assert "duration_seconds" in result

        # Check that optimization history was updated
        status = optimizer.get_optimization_status()
        assert status["optimization_count"] == 1
        assert len(status["recent_optimizations"]) == 1

    @pytest.mark.asyncio
    async def test_performance_analysis_with_real_cache(self):
        """Test performance analysis with real cache data."""
        optimizer = PerformanceOptimizer()

        # Add some data to caches to make analysis meaningful
        from src.core.cache_service import EmbeddingCache, NERCache

        # Add test data
        EmbeddingCache.set_embedding("test text", [0.1, 0.2, 0.3])
        NERCache.set_ner_results("medical text", "test_model", [{"entity": "test"}])

        # Run analysis
        metrics = await optimizer.analyze_performance()

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.timestamp is not None
        assert isinstance(metrics.bottlenecks, list)
        assert isinstance(metrics.recommendations, list)

        # Cleanup
        EmbeddingCache.clear()
        NERCache.clear()


def test_global_performance_optimizer():
    """Test that global performance optimizer instance is available."""
    assert performance_optimizer is not None
    assert isinstance(performance_optimizer, PerformanceOptimizer)
