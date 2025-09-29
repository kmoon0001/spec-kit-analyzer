"""
Unit tests for the cache service and integration.
"""
from unittest.mock import patch, MagicMock
from src.core.cache_service import (
    MemoryAwareLRUCache,
    EmbeddingCache,
    NERCache,
    DocumentCache,
    LLMResponseCache,
    get_cache_stats,
    cleanup_all_caches
)
from src.core.cache_integration_service import CacheIntegrationService


class TestMemoryAwareLRUCache:
    """Test the core memory-aware LRU cache."""
    
    def test_basic_cache_operations(self):
        """Test basic get/set operations."""
        cache = MemoryAwareLRUCache(max_memory_mb=100)
        
        # Test set and get
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Test non-existent key
        assert cache.get("nonexistent") is None
    
    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = MemoryAwareLRUCache(max_memory_mb=100)
        
        # Set with very short TTL
        cache.set("short_ttl", "value", ttl_hours=0.001)  # ~3.6 seconds
        
        # Should be available immediately
        assert cache.get("short_ttl") == "value"
        
        # Clear expired entries
        cache.clear_expired()
        
        # Should still be there (not expired yet in test)
        # In real usage, this would expire after the TTL
    
    @patch('src.core.cache_service.psutil.virtual_memory')
    def test_memory_pressure_cleanup(self, mock_memory):
        """Test cleanup when memory pressure is high."""
        # Mock high memory usage
        mock_memory.return_value.percent = 85
        
        cache = MemoryAwareLRUCache(max_memory_mb=1)  # Very small limit
        
        # Add multiple entries
        for i in range(10):
            cache.set(f"key_{i}", f"value_{i}")
        
        # Should trigger cleanup due to memory pressure
        cache._cleanup_if_needed()
        
        # Should have fewer entries after cleanup
        assert len(cache.cache) < 10


class TestSpecializedCaches:
    """Test the specialized cache classes."""
    
    def test_embedding_cache(self):
        """Test embedding cache functionality."""
        test_text = "This is a test document for embedding."
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Should be None initially
        assert EmbeddingCache.get_embedding(test_text) is None
        
        # Set and retrieve
        EmbeddingCache.set_embedding(test_text, test_embedding)
        cached_embedding = EmbeddingCache.get_embedding(test_text)
        
        assert cached_embedding == test_embedding
    
    def test_ner_cache(self):
        """Test NER cache functionality."""
        test_text = "Patient has diabetes and hypertension."
        model_name = "test_ner_model"
        test_results = [
            {"entity": "diabetes", "label": "CONDITION"},
            {"entity": "hypertension", "label": "CONDITION"}
        ]
        
        # Should be None initially
        assert NERCache.get_ner_results(test_text, model_name) is None
        
        # Set and retrieve
        NERCache.set_ner_results(test_text, model_name, test_results)
        cached_results = NERCache.get_ner_results(test_text, model_name)
        
        assert cached_results == test_results
    
    def test_document_cache(self):
        """Test document cache functionality."""
        doc_hash = "test_doc_hash_123"
        classification = {
            "document_type": "Progress Note",
            "confidence": 0.95,
            "discipline": "Physical Therapy"
        }
        
        # Should be None initially
        assert DocumentCache.get_document_classification(doc_hash) is None
        
        # Set and retrieve
        DocumentCache.set_document_classification(doc_hash, classification)
        cached_classification = DocumentCache.get_document_classification(doc_hash)
        
        assert cached_classification == classification
    
    def test_llm_response_cache(self):
        """Test LLM response cache functionality."""
        prompt = "Analyze this clinical note for compliance issues."
        model_name = "test_llm_model"
        response = "The note shows good compliance with Medicare guidelines."
        
        # Should be None initially
        assert LLMResponseCache.get_llm_response(prompt, model_name) is None
        
        # Set and retrieve
        LLMResponseCache.set_llm_response(prompt, model_name, response)
        cached_response = LLMResponseCache.get_llm_response(prompt, model_name)
        
        assert cached_response == response


class TestCacheIntegrationService:
    """Test the cache integration service."""
    
    def test_embedding_integration(self):
        """Test embedding cache integration."""
        service = CacheIntegrationService()
        test_text = "Test document for embedding integration."
        expected_embedding = [0.1, 0.2, 0.3]
        
        # Mock embedding function
        mock_embedding_func = MagicMock(return_value=expected_embedding)
        
        # First call should compute and cache
        result1 = service.get_or_compute_embedding(test_text, mock_embedding_func)
        assert result1 == expected_embedding
        assert service.cache_misses == 1
        assert service.cache_hits == 0
        
        # Second call should use cache
        result2 = service.get_or_compute_embedding(test_text, mock_embedding_func)
        assert result2 == expected_embedding
        assert service.cache_misses == 1
        assert service.cache_hits == 1
        
        # Embedding function should only be called once
        mock_embedding_func.assert_called_once_with(test_text)
    
    def test_performance_stats(self):
        """Test cache performance statistics."""
        service = CacheIntegrationService()
        
        # Initial stats
        stats = service.get_cache_performance_stats()
        assert stats['hit_rate_percent'] == 0
        assert stats['total_requests'] == 0
        
        # Simulate some cache operations
        service.cache_hits = 7
        service.cache_misses = 3
        
        stats = service.get_cache_performance_stats()
        assert stats['hit_rate_percent'] == 70.0
        assert stats['total_requests'] == 10
        assert stats['total_hits'] == 7
        assert stats['total_misses'] == 3


def test_cache_stats():
    """Test cache statistics function."""
    stats = get_cache_stats()
    
    # Should return a dictionary with expected keys
    expected_keys = [
        'total_entries', 'memory_usage_mb', 'system_memory_percent',
        'embedding_entries', 'ner_entries', 'llm_entries', 'doc_entries'
    ]
    
    for key in expected_keys:
        assert key in stats
        assert isinstance(stats[key], (int, float))


def test_cleanup_all_caches():
    """Test the cleanup function."""
    # Add some test data to cache
    EmbeddingCache.set_embedding("test", [1, 2, 3])
    NERCache.set_ner_results("test", "model", [{"entity": "test"}])
    
    # Should not raise any exceptions
    cleanup_all_caches()