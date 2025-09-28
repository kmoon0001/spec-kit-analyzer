"""
Optimized LLM Service with adaptive performance management.
Supports GPU acceleration, model quantization, and intelligent batching.
"""
import torch
import logging
from typing import List, Dict, Any, Optional, Union
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig
)
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor
import gc
from .performance_manager import get_performance_config, performance_manager
from .cache_service import cache_service

logger = logging.getLogger(__name__)

class OptimizedLLMService:
    """
    High-performance LLM service that adapts to system capabilities.
    """
    
    def __init__(self):
        self.config = get_performance_config()
        self.device = self._setup_device()
        self.tokenizer = None
        self.model = None
        self.embedding_model = None
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        logger.info(f"LLM Service initialized with device: {self.device}")
        logger.info(f"Performance config: GPU={self.config.use_gpu}, Quantization={self.config.model_quantization}")
    
    def _setup_device(self) -> str:
        """Setup optimal device based on performance configuration."""
        if self.config.use_gpu and torch.cuda.is_available():
            device = "cuda"
            # Log GPU info
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory // (1024**3)
            logger.info(f"Using GPU: {gpu_name} ({gpu_memory}GB)")
        else:
            device = "cpu"
            logger.info("Using CPU for inference")
        
        return device
    
    def _get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Get quantization configuration if enabled."""
        if not self.config.model_quantization:
            return None
        
        # Use 4-bit quantization for memory efficiency
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
    
    async def load_models(self, 
                         model_name: str = "microsoft/DialoGPT-medium",
                         embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Load LLM and embedding models with optimal configuration.
        """
        try:
            logger.info("Loading models...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Setup model loading parameters
            model_kwargs = {
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "device_map": "auto" if self.device == "cuda" else None,
                "low_cpu_mem_usage": True
            }
            
            # Add quantization if enabled
            quantization_config = self._get_quantization_config()
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
                logger.info("Using 4-bit quantization for memory efficiency")
            
            # Load main model
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                **model_kwargs
            )
            
            # Load embedding model (always use CPU for embeddings to save GPU memory)
            embedding_device = "cpu"  # Keep embeddings on CPU
            self.embedding_model = SentenceTransformer(
                embedding_model_name,
                device=embedding_device
            )
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """Intelligently chunk text based on performance settings."""
        chunk_size = self.config.chunk_size
        
        # Simple sentence-aware chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def generate_text(self, 
                           prompt: str, 
                           max_length: int = 512,
                           temperature: float = 0.7) -> str:
        """
        Generate text with adaptive batching and caching.
        """
        # Check cache first
        cache_key = f"generate_{hash(prompt)}_{max_length}_{temperature}"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Adaptive batch size based on current memory usage
            _ = performance_manager.get_optimal_batch_size()  # For future use
            
            # Tokenize input
            inputs = self.tokenizer.encode(
                prompt, 
                return_tensors="pt",
                max_length=self.config.max_sequence_length,
                truncation=True
            )
            
            if self.device == "cuda":
                inputs = inputs.to(self.device)
            
            # Generate with memory management
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=min(max_length, self.config.max_sequence_length),
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
            
            # Decode result
            generated_text = self.tokenizer.decode(
                outputs[0], 
                skip_special_tokens=True
            )
            
            # Remove the original prompt from the result
            result = generated_text[len(prompt):].strip()
            
            # Cache result
            cache_service.set(cache_key, result, ttl_hours=24)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            # Perform cleanup on error
            performance_manager.adaptive_cleanup()
            raise
    
    async def get_embeddings(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Get embeddings with caching and batch processing.
        """
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False
        
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            from .cache_service import EmbeddingCache
            cached_embedding = EmbeddingCache.get_embedding(text)
            if cached_embedding:
                results.append(cached_embedding)
            else:
                results.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Process uncached texts in batches
        if uncached_texts:
            try:
                batch_size = self.config.batch_size
                
                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i:i + batch_size]
                    batch_embeddings = self.embedding_model.encode(
                        batch,
                        convert_to_tensor=False,
                        show_progress_bar=False
                    )
                    
                    # Store results and cache
                    for j, embedding in enumerate(batch_embeddings):
                        original_index = uncached_indices[i + j]
                        embedding_list = embedding.tolist()
                        results[original_index] = embedding_list
                        
                        # Cache the embedding
                        from .cache_service import EmbeddingCache
                        EmbeddingCache.set_embedding(uncached_texts[i + j], embedding_list)
                
            except Exception as e:
                logger.error(f"Error computing embeddings: {e}")
                performance_manager.adaptive_cleanup()
                raise
        
        return results[0] if single_text else results
    
    async def analyze_compliance(self, 
                               document_text: str, 
                               rubric_rules: List[Dict]) -> Dict[str, Any]:
        """
        Analyze document compliance with intelligent chunking and parallel processing.
        """
        try:
            # Chunk document for processing
            chunks = self._chunk_text(document_text)
            
            if self.config.parallel_processing and len(chunks) > 1:
                # Process chunks in parallel
                tasks = []
                for chunk in chunks:
                    task = self._analyze_chunk(chunk, rubric_rules)
                    tasks.append(task)
                
                chunk_results = await asyncio.gather(*tasks)
            else:
                # Process chunks sequentially
                chunk_results = []
                for chunk in chunks:
                    result = await self._analyze_chunk(chunk, rubric_rules)
                    chunk_results.append(result)
            
            # Combine results
            combined_result = self._combine_chunk_results(chunk_results)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in compliance analysis: {e}")
            performance_manager.adaptive_cleanup()
            raise
    
    async def _analyze_chunk(self, chunk: str, rubric_rules: List[Dict]) -> Dict[str, Any]:
        """Analyze a single chunk of text."""
        # This would contain the actual compliance analysis logic
        # For now, return a placeholder structure
        return {
            "chunk": chunk[:100] + "..." if len(chunk) > 100 else chunk,
            "findings": [],
            "compliance_score": 0.85
        }
    
    def _combine_chunk_results(self, chunk_results: List[Dict]) -> Dict[str, Any]:
        """Combine results from multiple chunks."""
        all_findings = []
        total_score = 0
        
        for result in chunk_results:
            all_findings.extend(result.get("findings", []))
            total_score += result.get("compliance_score", 0)
        
        average_score = total_score / len(chunk_results) if chunk_results else 0
        
        return {
            "findings": all_findings,
            "compliance_score": average_score,
            "chunks_processed": len(chunk_results)
        }
    
    def cleanup(self):
        """Clean up resources and memory."""
        if self.model:
            del self.model
        if self.embedding_model:
            del self.embedding_model
        if self.tokenizer:
            del self.tokenizer
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        gc.collect()
        logger.info("LLM Service cleaned up")

# Global service instance
llm_service = OptimizedLLMService()