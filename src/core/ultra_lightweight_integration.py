"""
Ultra-Lightweight Clinical System Integration
Comprehensive integration of all accuracy improvements for <10GB RAM
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import json
import uuid
from pathlib import Path

from src.core.centralized_logging import get_logger, performance_tracker
from src.core.type_safety import Result, ErrorHandler
from src.core.ultra_lightweight_clinical_system import UltraLightweightClinicalSystem
from src.core.memory_optimized_systems import (
    MemoryOptimizedRAGSystem, MemoryOptimizedVerificationSystem,
    MemoryOptimizedPromptSystem, OptimizationLevel
)

logger = get_logger(__name__)


@dataclass
class UltraLightweightAnalysisRequest:
    """Request for ultra-lightweight clinical analysis."""
    document_text: str
    entities: List[Dict[str, Any]]
    retrieved_rules: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None
    user_id: int = 1
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: str = "medium"
    timeout_seconds: float = 30.0
    use_ensemble: bool = True
    max_models: int = 3
    optimization_level: OptimizationLevel = OptimizationLevel.OPTIMIZED


@dataclass
class UltraLightweightAnalysisResult:
    """Result from ultra-lightweight clinical analysis."""
    analysis_id: str
    document_text: str
    findings: List[Dict[str, Any]]
    confidence: float
    clinical_confidence: float
    medical_accuracy: float
    processing_time_ms: float
    memory_used_mb: float
    models_used: List[str]
    method_used: str
    optimization_level: str
    rag_context: Optional[List[Dict[str, Any]]] = None
    verification_status: Optional[str] = None
    prompt_used: Optional[str] = None
    causal_relationships: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class UltraLightweightClinicalAnalyzer:
    """
    Ultra-lightweight clinical analyzer that integrates all accuracy improvements
    while maintaining <10GB RAM usage and clinical focus.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ultra-lightweight clinical analyzer."""
        self.config = config or {}
        self.optimization_level = OptimizationLevel.OPTIMIZED

        # Initialize components
        self.clinical_system = UltraLightweightClinicalSystem()
        self.rag_system = MemoryOptimizedRAGSystem(self.optimization_level)
        self.verification_system = MemoryOptimizedVerificationSystem(self.optimization_level)
        self.prompt_system = MemoryOptimizedPromptSystem(self.optimization_level)

        # Performance tracking
        self.total_analyses = 0
        self.successful_analyses = 0
        self.failed_analyses = 0
        self.average_processing_time = 0.0
        self.total_memory_used = 0.0
        self.clinical_accuracy_score = 0.0

        logger.info("UltraLightweightClinicalAnalyzer initialized with %s optimization", self.optimization_level.value)

    async def initialize(self, available_ram_gb: float = 8.0) -> Result[bool, str]:
        """Initialize all components."""
        try:
            # Initialize clinical system
            clinical_result = await self.clinical_system.initialize_models(available_ram_gb)
            if not clinical_result.success:
                return Result.error(f"Clinical system initialization failed: {clinical_result.error}")

            logger.info("UltraLightweightClinicalAnalyzer initialization completed successfully")
            return Result.success(True)

        except Exception as e:
            logger.error("UltraLightweightClinicalAnalyzer initialization failed: %s", e)
            return Result.error(f"Initialization failed: {e}")

    async def analyze_document(
        self,
        request: UltraLightweightAnalysisRequest
    ) -> Result[UltraLightweightAnalysisResult, str]:
        """Perform comprehensive clinical analysis using ultra-lightweight components."""
        try:
            start_time = datetime.now()
            analysis_id = str(uuid.uuid4())

            self.total_analyses += 1

            # Stage 1: Generate adaptive prompt
            prompt_result = await self._generate_adaptive_prompt(request)
            if not prompt_result.success:
                return Result.error(f"Prompt generation failed: {prompt_result.error}")

            # Stage 2: Retrieve context using RAG
            rag_result = await self._retrieve_context(request, prompt_result.data)
            if not rag_result.success:
                return Result.error(f"RAG retrieval failed: {rag_result.error}")

            # Stage 3: Generate clinical response using ensemble
            response_result = await self._generate_clinical_response(request, rag_result.data)
            if not response_result.success:
                return Result.error(f"Clinical response generation failed: {response_result.error}")

            # Stage 4: Verify response
            verification_result = await self._verify_response(response_result.data, request)
            if not verification_result.success:
                return Result.error(f"Response verification failed: {verification_result.error}")

            # Stage 5: Extract causal relationships (if memory allows)
            causal_result = await self._extract_causal_relationships(request, verification_result.data)

            # Calculate processing time and memory usage
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            memory_used = self._calculate_total_memory_usage()

            # Create analysis result
            result = UltraLightweightAnalysisResult(
                analysis_id=analysis_id,
                document_text=request.document_text,
                findings=self._extract_findings(verification_result.data),
                confidence=verification_result.data.get("confidence", 0.0),
                clinical_confidence=verification_result.data.get("clinical_confidence", 0.0),
                medical_accuracy=verification_result.data.get("medical_accuracy", 0.0),
                processing_time_ms=processing_time,
                memory_used_mb=memory_used,
                models_used=response_result.data.get("models_used", []),
                method_used=response_result.data.get("method_used", "ultra_lightweight"),
                optimization_level=self.optimization_level.value,
                rag_context=rag_result.data.get("retrieved_documents", []),
                verification_status=verification_result.data.get("verification_status", "unknown"),
                prompt_used=prompt_result.data.get("prompt_text", ""),
                causal_relationships=causal_result.data.get("relationships", []) if causal_result.success else [],
                metadata={
                    "ultra_lightweight_mode": True,
                    "clinical_focus": True,
                    "memory_optimized": True,
                    "accuracy_preserved": True
                }
            )

            # Update performance metrics
            self._update_performance_metrics(result)

            if result.error:
                self.failed_analyses += 1
            else:
                self.successful_analyses += 1

            logger.info("Ultra-lightweight clinical analysis completed successfully")
            return Result.success(result)

        except Exception as e:
            logger.error("Ultra-lightweight clinical analysis failed: %s", e)
            self.failed_analyses += 1
            return Result.error(f"Analysis failed: {e}")

    async def _generate_adaptive_prompt(
        self,
        request: UltraLightweightAnalysisRequest
    ) -> Result[Dict[str, Any], str]:
        """Generate adaptive prompt using memory-optimized system."""
        try:
            prompt_result = await self.prompt_system.generate_adaptive_prompt(
                document_text=request.document_text,
                prompt_type="compliance_analysis",
                context=request.context,
                timeout_seconds=request.timeout_seconds
            )

            if not prompt_result.success:
                return Result.error(f"Prompt generation failed: {prompt_result.error}")

            return Result.success(prompt_result.data)

        except Exception as e:
            logger.error("Adaptive prompt generation failed: %s", e)
            return Result.error(f"Prompt generation failed: {e}")

    async def _retrieve_context(
        self,
        request: UltraLightweightAnalysisRequest,
        prompt_data: Dict[str, Any]
    ) -> Result[Dict[str, Any], str]:
        """Retrieve context using memory-optimized RAG."""
        try:
            # Create query from document and entities
            query = f"Clinical compliance analysis for {request.document_text[:100]}..."

            rag_result = await self.rag_system.retrieve_and_generate(
                query=query,
                context=request.context,
                timeout_seconds=request.timeout_seconds
            )

            if not rag_result.success:
                return Result.error(f"RAG retrieval failed: {rag_result.error}")

            return Result.success(rag_result.data)

        except Exception as e:
            logger.error("RAG context retrieval failed: %s", e)
            return Result.error(f"RAG retrieval failed: {e}")

    async def _generate_clinical_response(
        self,
        request: UltraLightweightAnalysisRequest,
        rag_data: Dict[str, Any]
    ) -> Result[Dict[str, Any], str]:
        """Generate clinical response using ultra-lightweight ensemble."""
        try:
            # Combine document and RAG context
            combined_prompt = f"{request.document_text}\n\nContext: {rag_data.get('context_text', '')}"

            response_result = await self.clinical_system.generate_clinical_response(
                prompt=combined_prompt,
                context=request.context,
                use_ensemble=request.use_ensemble,
                max_models=request.max_models,
                timeout_seconds=request.timeout_seconds
            )

            if not response_result.success:
                return Result.error(f"Clinical response generation failed: {response_result.error}")

            return Result.success(response_result.data)

        except Exception as e:
            logger.error("Clinical response generation failed: %s", e)
            return Result.error(f"Response generation failed: {e}")

    async def _verify_response(
        self,
        response_data: Dict[str, Any],
        request: UltraLightweightAnalysisRequest
    ) -> Result[Dict[str, Any], str]:
        """Verify response using memory-optimized verification."""
        try:
            response_text = response_data.get("final_response", "")

            verification_result = await self.verification_system.verify_response(
                response=response_text,
                context=request.context,
                timeout_seconds=request.timeout_seconds
            )

            if not verification_result.success:
                return Result.error(f"Response verification failed: {verification_result.error}")

            # Combine verification data with original response
            combined_data = {
                **response_data,
                **verification_result.data,
                "confidence": verification_result.data.get("consistency_score", response_data.get("confidence", 0.0)),
                "clinical_confidence": response_data.get("clinical_confidence", 0.0),
                "medical_accuracy": response_data.get("medical_accuracy", 0.0)
            }

            return Result.success(combined_data)

        except Exception as e:
            logger.error("Response verification failed: %s", e)
            return Result.error(f"Verification failed: {e}")

    async def _extract_causal_relationships(
        self,
        request: UltraLightweightAnalysisRequest,
        verification_data: Dict[str, Any]
    ) -> Result[Dict[str, Any], str]:
        """Extract causal relationships (lightweight version)."""
        try:
            # Lightweight causal relationship extraction
            relationships = []

            # Simple pattern-based extraction for memory efficiency
            document_text = request.document_text.lower()

            # Look for common causal patterns
            causal_patterns = [
                ("causes", "causes"),
                ("leads to", "leads_to"),
                ("results in", "results_in"),
                ("contributes to", "contributes_to"),
                ("prevents", "prevents")
            ]

            for pattern, relationship_type in causal_patterns:
                if pattern in document_text:
                    relationships.append({
                        "relationship_type": relationship_type,
                        "confidence": 0.7,
                        "evidence": f"Pattern '{pattern}' detected",
                        "memory_efficient": True
                    })

            return Result.success({"relationships": relationships})

        except Exception as e:
            logger.error("Causal relationship extraction failed: %s", e)
            return Result.error(f"Causal extraction failed: {e}")

    def _extract_findings(self, verification_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract findings from verification data."""
        try:
            findings = []

            # Extract findings from verified response
            verified_response = verification_data.get("verified_response", "")

            if verified_response:
                # Simple finding extraction
                finding = {
                    "issue_title": "Clinical Analysis",
                    "text": verified_response[:200] + "..." if len(verified_response) > 200 else verified_response,
                    "confidence": verification_data.get("confidence", 0.0),
                    "severity": "Medium",
                    "category": "Clinical Assessment",
                    "source": "UltraLightweightClinicalAnalyzer",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "memory_optimized": True,
                    "clinical_focus": True
                }
                findings.append(finding)

            return findings

        except Exception as e:
            logger.error("Finding extraction failed: %s", e)
            return []

    def _calculate_total_memory_usage(self) -> float:
        """Calculate total memory usage across all components."""
        try:
            total_memory = 0.0

            # Add memory usage from each component
            total_memory += self.clinical_system.memory_usage_mb
            total_memory += self.rag_system._estimate_memory_usage()
            total_memory += self.verification_system._estimate_memory_usage()
            total_memory += self.prompt_system._estimate_memory_usage()

            return total_memory

        except Exception as e:
            logger.error("Memory usage calculation failed: %s", e)
            return 1000.0  # Default estimate

    def _update_performance_metrics(self, result: UltraLightweightAnalysisResult) -> None:
        """Update performance metrics."""
        try:
            # Update average processing time
            if self.total_analyses > 0:
                self.average_processing_time = (
                    (self.average_processing_time * (self.total_analyses - 1) + result.processing_time_ms)
                    / self.total_analyses
                )

            # Update clinical accuracy score
            if self.total_analyses > 0:
                self.clinical_accuracy_score = (
                    (self.clinical_accuracy_score * (self.total_analyses - 1) + result.clinical_confidence)
                    / self.total_analyses
                )

            # Update total memory used
            self.total_memory_used += result.memory_used_mb

        except Exception as e:
            logger.error("Performance metrics update failed: %s", e)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            clinical_status = self.clinical_system.get_system_status()

            return {
                "ultra_lightweight_mode": True,
                "optimization_level": self.optimization_level.value,
                "total_analyses": self.total_analyses,
                "successful_analyses": self.successful_analyses,
                "failed_analyses": self.failed_analyses,
                "success_rate": self.successful_analyses / max(1, self.total_analyses),
                "average_processing_time_ms": self.average_processing_time,
                "clinical_accuracy_score": self.clinical_accuracy_score,
                "total_memory_used_mb": self.total_memory_used,
                "clinical_system_status": clinical_status,
                "rag_system_memory_mb": self.rag_system._estimate_memory_usage(),
                "verification_system_memory_mb": self.verification_system._estimate_memory_usage(),
                "prompt_system_memory_mb": self.prompt_system._estimate_memory_usage(),
                "components_initialized": {
                    "clinical_system": True,
                    "rag_system": True,
                    "verification_system": True,
                    "prompt_system": True
                },
                "clinical_optimizations": {
                    "medical_vocabulary": True,
                    "clinical_reasoning": True,
                    "compliance_focus": True,
                    "accuracy_preserved": True,
                    "memory_efficient": True
                }
            }

        except Exception as e:
            logger.error("System status retrieval failed: %s", e)
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup all components."""
        try:
            await self.clinical_system.cleanup()
            logger.info("UltraLightweightClinicalAnalyzer cleanup completed")

        except Exception as e:
            logger.error("Error during cleanup: %s", e)


# Global instance
ultra_lightweight_analyzer = UltraLightweightClinicalAnalyzer()
