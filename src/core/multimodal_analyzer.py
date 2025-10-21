"""
Multi-Modal Analysis System
Implements analysis of text, images, tables, and structured data together
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import json
import uuid
import base64
import io
from pathlib import Path

from src.core.centralized_logging import get_logger, performance_tracker
from src.core.type_safety import Result, ErrorHandler

logger = get_logger(__name__)


class ModalityType(Enum):
    """Types of modalities in multi-modal analysis."""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    STRUCTURED_DATA = "structured_data"
    AUDIO = "audio"
    VIDEO = "video"


class AnalysisType(Enum):
    """Types of multi-modal analysis."""
    OCR_TEXT_EXTRACTION = "ocr_text_extraction"
    LAYOUT_ANALYSIS = "layout_analysis"
    TABLE_STRUCTURE_RECOGNITION = "table_structure_recognition"
    DATA_FUSION = "data_fusion"
    CROSS_MODAL_REASONING = "cross_modal_reasoning"
    CONSISTENCY_CHECKING = "consistency_checking"


class FusionStrategy(Enum):
    """Strategies for fusing multi-modal data."""
    EARLY_FUSION = "early_fusion"
    LATE_FUSION = "late_fusion"
    INTERMEDIATE_FUSION = "intermediate_fusion"
    ATTENTION_FUSION = "attention_fusion"
    HIERARCHICAL_FUSION = "hierarchical_fusion"


@dataclass
class ModalityData:
    """Data for a specific modality."""
    modality_id: str
    modality_type: ModalityType
    content: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any]
    confidence: float
    processing_time_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ModalityAnalysis:
    """Analysis result for a specific modality."""
    modality_id: str
    modality_type: ModalityType
    analysis_type: AnalysisType
    extracted_content: Dict[str, Any]
    confidence: float
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiModalResult:
    """Final result from multi-modal analysis."""
    analysis_id: str
    modality_analyses: List[ModalityAnalysis]
    fused_result: Dict[str, Any]
    fusion_strategy: FusionStrategy
    overall_confidence: float
    consistency_score: float
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiModalAnalyzer:
    """
    Multi-modal analysis system for processing text, images, tables, and structured data.

    Features:
    - OCR and text extraction from images
    - Table structure recognition and data extraction
    - Layout analysis and document understanding
    - Cross-modal consistency checking
    - Data fusion strategies
    - Performance monitoring
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the multi-modal analyzer."""
        self.config_path = config_path or "config/multimodal_analysis.yaml"
        self.modality_analyzers: Dict[ModalityType, Any] = {}
        self.fusion_engines: Dict[FusionStrategy, Any] = {}
        self.analysis_history: List[MultiModalResult] = []

        # Performance tracking
        self.total_analyses = 0
        self.successful_analyses = 0
        self.average_confidence = 0.0
        self.average_processing_time = 0.0

        # Initialize components
        self._initialize_modality_analyzers()
        self._initialize_fusion_engines()

        logger.info("MultiModalAnalyzer initialized with %d modality analyzers", len(self.modality_analyzers))

    def _initialize_modality_analyzers(self) -> None:
        """Initialize analyzers for different modalities."""
        try:
            # Text analyzer
            self.modality_analyzers[ModalityType.TEXT] = {
                "type": "text",
                "models": ["clinical_ner", "sentiment_analyzer", "topic_extractor"],
                "processing_methods": ["entity_extraction", "sentiment_analysis", "topic_modeling"],
                "confidence_threshold": 0.7
            }

            # Image analyzer (OCR + layout analysis)
            self.modality_analyzers[ModalityType.IMAGE] = {
                "type": "image",
                "models": ["ocr_engine", "layout_analyzer", "object_detector"],
                "processing_methods": ["text_extraction", "layout_analysis", "object_detection"],
                "confidence_threshold": 0.8,
                "supported_formats": ["png", "jpg", "jpeg", "tiff", "pdf"]
            }

            # Table analyzer
            self.modality_analyzers[ModalityType.TABLE] = {
                "type": "table",
                "models": ["table_structure_recognizer", "cell_extractor", "data_validator"],
                "processing_methods": ["structure_recognition", "cell_extraction", "data_validation"],
                "confidence_threshold": 0.85,
                "max_cells": 1000
            }

            # Structured data analyzer
            self.modality_analyzers[ModalityType.STRUCTURED_DATA] = {
                "type": "structured_data",
                "models": ["json_parser", "xml_parser", "csv_parser"],
                "processing_methods": ["parsing", "validation", "extraction"],
                "confidence_threshold": 0.9,
                "supported_formats": ["json", "xml", "csv", "yaml"]
            }

            # Audio analyzer (placeholder for future implementation)
            self.modality_analyzers[ModalityType.AUDIO] = {
                "type": "audio",
                "models": ["speech_to_text", "audio_classifier"],
                "processing_methods": ["transcription", "classification"],
                "confidence_threshold": 0.7,
                "supported_formats": ["wav", "mp3", "m4a"]
            }

            # Video analyzer (placeholder for future implementation)
            self.modality_analyzers[ModalityType.VIDEO] = {
                "type": "video",
                "models": ["video_analyzer", "frame_extractor"],
                "processing_methods": ["frame_extraction", "motion_analysis"],
                "confidence_threshold": 0.6,
                "supported_formats": ["mp4", "avi", "mov"]
            }

            logger.info("Initialized %d modality analyzers", len(self.modality_analyzers))

        except Exception as e:
            logger.error("Failed to initialize modality analyzers: %s", e)
            raise

    def _initialize_fusion_engines(self) -> None:
        """Initialize fusion engines for different strategies."""
        try:
            # Early fusion (combine raw features)
            self.fusion_engines[FusionStrategy.EARLY_FUSION] = {
                "type": "early_fusion",
                "description": "Combine raw features from all modalities",
                "complexity": "high",
                "performance": "good",
                "use_case": "When modalities are highly correlated"
            }

            # Late fusion (combine final results)
            self.fusion_engines[FusionStrategy.LATE_FUSION] = {
                "type": "late_fusion",
                "description": "Combine final results from each modality",
                "complexity": "low",
                "performance": "moderate",
                "use_case": "When modalities are independent"
            }

            # Intermediate fusion (combine intermediate representations)
            self.fusion_engines[FusionStrategy.INTERMEDIATE_FUSION] = {
                "type": "intermediate_fusion",
                "description": "Combine intermediate representations",
                "complexity": "medium",
                "performance": "good",
                "use_case": "Balanced approach for mixed modalities"
            }

            # Attention fusion (use attention mechanisms)
            self.fusion_engines[FusionStrategy.ATTENTION_FUSION] = {
                "type": "attention_fusion",
                "description": "Use attention mechanisms for fusion",
                "complexity": "high",
                "performance": "excellent",
                "use_case": "Complex multi-modal reasoning"
            }

            # Hierarchical fusion (hierarchical combination)
            self.fusion_engines[FusionStrategy.HIERARCHICAL_FUSION] = {
                "type": "hierarchical_fusion",
                "description": "Hierarchical combination of modalities",
                "complexity": "medium",
                "performance": "good",
                "use_case": "When modalities have hierarchical relationships"
            }

            logger.info("Initialized %d fusion engines", len(self.fusion_engines))

        except Exception as e:
            logger.error("Failed to initialize fusion engines: %s", e)
            raise

    async def analyze_multimodal_document(
        self,
        modalities: List[ModalityData],
        fusion_strategy: Optional[FusionStrategy] = None,
        timeout_seconds: float = 60.0
    ) -> Result[MultiModalResult, str]:
        """Analyze a multi-modal document."""
        try:
            start_time = datetime.now()
            analysis_id = str(uuid.uuid4())
            self.total_analyses += 1

            if not modalities:
                return Result.error("No modalities provided for analysis")

            # Analyze each modality
            modality_analyses = []
            for modality_data in modalities:
                try:
                    analysis = await self._analyze_modality(modality_data, timeout_seconds)
                    if analysis:
                        modality_analyses.append(analysis)
                except Exception as e:
                    logger.warning("Failed to analyze modality %s: %s", modality_data.modality_id, e)
                    continue

            if not modality_analyses:
                return Result.error("All modality analyses failed")

            # Select fusion strategy
            if not fusion_strategy:
                fusion_strategy = self._select_fusion_strategy(modality_analyses)

            # Perform fusion
            fused_result = await self._perform_fusion(modality_analyses, fusion_strategy, timeout_seconds)

            # Calculate overall metrics
            overall_confidence = self._calculate_overall_confidence(modality_analyses)
            consistency_score = self._calculate_consistency_score(modality_analyses)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create result
            result = MultiModalResult(
                analysis_id=analysis_id,
                modality_analyses=modality_analyses,
                fused_result=fused_result,
                fusion_strategy=fusion_strategy,
                overall_confidence=overall_confidence,
                consistency_score=consistency_score,
                processing_time_ms=processing_time,
                metadata={
                    "total_modalities": len(modalities),
                    "successful_modalities": len(modality_analyses),
                    "timestamp": datetime.now(timezone.utc)
                }
            )

            # Store in history
            self.analysis_history.append(result)
            if len(self.analysis_history) > 1000:
                self.analysis_history = self.analysis_history[-500:]

            # Update performance metrics
            self._update_performance_metrics(result)

            self.successful_analyses += 1
            return Result.success(result)

        except Exception as e:
            logger.error("Multi-modal analysis failed: %s", e)
            return Result.error(f"Multi-modal analysis failed: {e}")

    async def _analyze_modality(
        self,
        modality_data: ModalityData,
        timeout_seconds: float
    ) -> Optional[ModalityAnalysis]:
        """Analyze a specific modality."""
        try:
            analyzer_config = self.modality_analyzers[modality_data.modality_type]
            start_time = datetime.now()

            # Process based on modality type
            if modality_data.modality_type == ModalityType.TEXT:
                extracted_content = await self._analyze_text(modality_data.content)
            elif modality_data.modality_type == ModalityType.IMAGE:
                extracted_content = await self._analyze_image(modality_data.content)
            elif modality_data.modality_type == ModalityType.TABLE:
                extracted_content = await self._analyze_table(modality_data.content)
            elif modality_data.modality_type == ModalityType.STRUCTURED_DATA:
                extracted_content = await self._analyze_structured_data(modality_data.content)
            elif modality_data.modality_type == ModalityType.AUDIO:
                extracted_content = await self._analyze_audio(modality_data.content)
            elif modality_data.modality_type == ModalityType.VIDEO:
                extracted_content = await self._analyze_video(modality_data.content)
            else:
                logger.warning("Unsupported modality type: %s", modality_data.modality_type)
                return None

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Calculate confidence
            confidence = self._calculate_modality_confidence(extracted_content, analyzer_config)

            # Determine analysis type
            analysis_type = self._determine_analysis_type(modality_data.modality_type, extracted_content)

            analysis = ModalityAnalysis(
                modality_id=modality_data.modality_id,
                modality_type=modality_data.modality_type,
                analysis_type=analysis_type,
                extracted_content=extracted_content,
                confidence=confidence,
                processing_time_ms=processing_time,
                metadata={
                    "analyzer_config": analyzer_config,
                    "original_confidence": modality_data.confidence
                }
            )

            logger.info("Analyzed modality %s with confidence %.3f",
                       modality_data.modality_type.value, confidence)

            return analysis

        except Exception as e:
            logger.error("Modality analysis failed for %s: %s", modality_data.modality_type.value, e)
            return None

    async def _analyze_text(self, content: str) -> Dict[str, Any]:
        """Analyze text content."""
        try:
            # Simulate text analysis (in real implementation, this would use actual NLP models)
            await asyncio.sleep(0.01)  # Simulate processing time

            # Extract entities (simplified)
            entities = []
            medical_patterns = [
                (r'\b(?:patient|client|individual)\b', 'PATIENT'),
                (r'\b(?:diagnosis|condition|disorder)\b', 'DIAGNOSIS'),
                (r'\b(?:treatment|therapy|intervention)\b', 'TREATMENT'),
                (r'\b(?:medication|drug|prescription)\b', 'MEDICATION')
            ]

            for pattern, entity_type in medical_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "text": match.group(),
                        "label": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.8
                    })

            # Extract topics (simplified)
            topics = []
            topic_patterns = [
                r'\b(?:cardiology|neurology|orthopedics|pediatrics)\b',
                r'\b(?:physical therapy|occupational therapy|speech therapy)\b'
            ]

            for pattern in topic_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                topics.extend(matches)

            return {
                "text_content": content,
                "entities": entities[:20],  # Limit to 20 entities
                "topics": list(set(topics))[:10],  # Remove duplicates and limit
                "word_count": len(content.split()),
                "sentence_count": len(re.split(r'[.!?]+', content)),
                "analysis_type": "text_extraction"
            }

        except Exception as e:
            logger.error("Text analysis failed: %s", e)
            return {"text_content": content, "entities": [], "topics": [], "error": str(e)}

    async def _analyze_image(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """Analyze image content (OCR + layout analysis)."""
        try:
            # Simulate image analysis (in real implementation, this would use actual OCR and layout models)
            await asyncio.sleep(0.05)  # Simulate processing time

            # Mock OCR text extraction
            ocr_text = "Mock OCR text extracted from image. This would contain actual text from the image."

            # Mock layout analysis
            layout_elements = [
                {"type": "text_block", "bbox": [10, 10, 200, 50], "text": "Header text"},
                {"type": "table", "bbox": [10, 60, 300, 200], "rows": 5, "cols": 3},
                {"type": "text_block", "bbox": [10, 210, 200, 250], "text": "Footer text"}
            ]

            # Mock object detection
            detected_objects = [
                {"class": "table", "confidence": 0.9, "bbox": [10, 60, 300, 200]},
                {"class": "text", "confidence": 0.8, "bbox": [10, 10, 200, 50]}
            ]

            return {
                "ocr_text": ocr_text,
                "layout_elements": layout_elements,
                "detected_objects": detected_objects,
                "image_metadata": {
                    "format": "png",
                    "size": "800x600",
                    "dpi": 300
                },
                "analysis_type": "ocr_and_layout"
            }

        except Exception as e:
            logger.error("Image analysis failed: %s", e)
            return {"ocr_text": "", "layout_elements": [], "detected_objects": [], "error": str(e)}

    async def _analyze_table(self, content: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze table content."""
        try:
            # Simulate table analysis (in real implementation, this would use actual table recognition models)
            await asyncio.sleep(0.03)  # Simulate processing time

            # Mock table structure recognition
            table_structure = {
                "rows": 5,
                "columns": 4,
                "headers": ["Patient ID", "Diagnosis", "Treatment", "Date"],
                "data_types": ["string", "string", "string", "date"]
            }

            # Mock cell extraction
            cells = []
            for row in range(5):
                for col in range(4):
                    cells.append({
                        "row": row,
                        "column": col,
                        "value": f"Mock cell {row}-{col}",
                        "confidence": 0.9
                    })

            # Mock data validation
            validation_results = {
                "valid_cells": len(cells),
                "invalid_cells": 0,
                "missing_cells": 0,
                "data_quality_score": 0.95
            }

            return {
                "table_structure": table_structure,
                "cells": cells,
                "validation_results": validation_results,
                "analysis_type": "table_extraction"
            }

        except Exception as e:
            logger.error("Table analysis failed: %s", e)
            return {"table_structure": {}, "cells": [], "validation_results": {}, "error": str(e)}

    async def _analyze_structured_data(self, content: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze structured data content."""
        try:
            # Simulate structured data analysis (in real implementation, this would use actual parsers)
            await asyncio.sleep(0.01)  # Simulate processing time

            # Mock parsing
            parsed_data = {
                "type": "json",
                "fields": ["patient_id", "diagnosis", "treatment", "date"],
                "records": 10,
                "valid": True
            }

            # Mock validation
            validation_results = {
                "schema_valid": True,
                "data_types_valid": True,
                "required_fields_present": True,
                "validation_score": 0.98
            }

            return {
                "parsed_data": parsed_data,
                "validation_results": validation_results,
                "analysis_type": "structured_data_parsing"
            }

        except Exception as e:
            logger.error("Structured data analysis failed: %s", e)
            return {"parsed_data": {}, "validation_results": {}, "error": str(e)}

    async def _analyze_audio(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """Analyze audio content (placeholder)."""
        try:
            # Simulate audio analysis (in real implementation, this would use actual speech-to-text models)
            await asyncio.sleep(0.02)  # Simulate processing time

            return {
                "transcription": "Mock audio transcription text",
                "confidence": 0.8,
                "duration": 30.0,
                "language": "en",
                "analysis_type": "speech_to_text"
            }

        except Exception as e:
            logger.error("Audio analysis failed: %s", e)
            return {"transcription": "", "confidence": 0.0, "error": str(e)}

    async def _analyze_video(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """Analyze video content (placeholder)."""
        try:
            # Simulate video analysis (in real implementation, this would use actual video analysis models)
            await asyncio.sleep(0.1)  # Simulate processing time

            return {
                "frames_analyzed": 100,
                "objects_detected": ["person", "medical_equipment"],
                "duration": 60.0,
                "analysis_type": "video_analysis"
            }

        except Exception as e:
            logger.error("Video analysis failed: %s", e)
            return {"frames_analyzed": 0, "objects_detected": [], "error": str(e)}

    def _calculate_modality_confidence(
        self,
        extracted_content: Dict[str, Any],
        analyzer_config: Dict[str, Any]
    ) -> float:
        """Calculate confidence for modality analysis."""
        try:
            # Base confidence from analyzer config
            base_confidence = analyzer_config.get("confidence_threshold", 0.7)

            # Adjust based on extracted content quality
            if "error" in extracted_content:
                return 0.0

            # Adjust based on content richness
            content_richness = 0.0
            if "entities" in extracted_content and extracted_content["entities"]:
                content_richness += 0.2
            if "topics" in extracted_content and extracted_content["topics"]:
                content_richness += 0.2
            if "cells" in extracted_content and extracted_content["cells"]:
                content_richness += 0.3
            if "transcription" in extracted_content and extracted_content["transcription"]:
                content_richness += 0.3

            # Calculate final confidence
            confidence = base_confidence + content_richness

            return min(1.0, max(0.0, confidence))

        except Exception as e:
            logger.error("Confidence calculation failed: %s", e)
            return 0.5

    def _determine_analysis_type(
        self,
        modality_type: ModalityType,
        extracted_content: Dict[str, Any]
    ) -> AnalysisType:
        """Determine analysis type based on modality and content."""
        try:
            if modality_type == ModalityType.TEXT:
                return AnalysisType.OCR_TEXT_EXTRACTION
            elif modality_type == ModalityType.IMAGE:
                if "layout_elements" in extracted_content:
                    return AnalysisType.LAYOUT_ANALYSIS
                else:
                    return AnalysisType.OCR_TEXT_EXTRACTION
            elif modality_type == ModalityType.TABLE:
                return AnalysisType.TABLE_STRUCTURE_RECOGNITION
            elif modality_type == ModalityType.STRUCTURED_DATA:
                return AnalysisType.DATA_FUSION
            else:
                return AnalysisType.CROSS_MODAL_REASONING

        except Exception as e:
            logger.error("Analysis type determination failed: %s", e)
            return AnalysisType.DATA_FUSION

    def _select_fusion_strategy(self, modality_analyses: List[ModalityAnalysis]) -> FusionStrategy:
        """Select appropriate fusion strategy based on modality analyses."""
        try:
            # Count modality types
            modality_types = [analysis.modality_type for analysis in modality_analyses]
            unique_types = set(modality_types)

            # Select strategy based on number and types of modalities
            if len(unique_types) == 1:
                return FusionStrategy.LATE_FUSION
            elif len(unique_types) == 2:
                return FusionStrategy.INTERMEDIATE_FUSION
            elif len(unique_types) >= 3:
                return FusionStrategy.ATTENTION_FUSION
            else:
                return FusionStrategy.LATE_FUSION

        except Exception as e:
            logger.error("Fusion strategy selection failed: %s", e)
            return FusionStrategy.LATE_FUSION

    async def _perform_fusion(
        self,
        modality_analyses: List[ModalityAnalysis],
        fusion_strategy: FusionStrategy,
        timeout_seconds: float
    ) -> Dict[str, Any]:
        """Perform fusion of modality analyses."""
        try:
            fusion_config = self.fusion_engines[fusion_strategy]

            # Simulate fusion processing
            await asyncio.sleep(0.02)  # Simulate processing time

            # Combine extracted content from all modalities
            fused_content = {
                "text_content": [],
                "entities": [],
                "tables": [],
                "structured_data": [],
                "images": [],
                "audio": [],
                "video": []
            }

            for analysis in modality_analyses:
                content = analysis.extracted_content

                if analysis.modality_type == ModalityType.TEXT:
                    if "text_content" in content:
                        fused_content["text_content"].append(content["text_content"])
                    if "entities" in content:
                        fused_content["entities"].extend(content["entities"])

                elif analysis.modality_type == ModalityType.IMAGE:
                    fused_content["images"].append(content)

                elif analysis.modality_type == ModalityType.TABLE:
                    fused_content["tables"].append(content)

                elif analysis.modality_type == ModalityType.STRUCTURED_DATA:
                    fused_content["structured_data"].append(content)

                elif analysis.modality_type == ModalityType.AUDIO:
                    fused_content["audio"].append(content)

                elif analysis.modality_type == ModalityType.VIDEO:
                    fused_content["video"].append(content)

            # Perform consistency checking
            consistency_results = self._check_cross_modal_consistency(fused_content)

            # Generate final fused result
            fused_result = {
                "fused_content": fused_content,
                "consistency_results": consistency_results,
                "fusion_strategy": fusion_strategy.value,
                "modality_count": len(modality_analyses),
                "total_entities": len(fused_content["entities"]),
                "total_tables": len(fused_content["tables"]),
                "total_images": len(fused_content["images"])
            }

            logger.info("Fusion completed using %s strategy", fusion_strategy.value)

            return fused_result

        except Exception as e:
            logger.error("Fusion failed: %s", e)
            return {"error": str(e), "fusion_strategy": fusion_strategy.value}

    def _check_cross_modal_consistency(self, fused_content: Dict[str, Any]) -> Dict[str, Any]:
        """Check consistency across modalities."""
        try:
            consistency_results = {
                "overall_consistency": 0.8,
                "text_image_consistency": 0.9,
                "text_table_consistency": 0.85,
                "table_image_consistency": 0.75,
                "inconsistencies": [],
                "confidence": 0.8
            }

            # Check for inconsistencies (simplified)
            text_content = fused_content.get("text_content", [])
            tables = fused_content.get("tables", [])

            if text_content and tables:
                # Mock consistency check
                consistency_results["text_table_consistency"] = 0.85

            return consistency_results

        except Exception as e:
            logger.error("Consistency checking failed: %s", e)
            return {"overall_consistency": 0.5, "error": str(e)}

    def _calculate_overall_confidence(self, modality_analyses: List[ModalityAnalysis]) -> float:
        """Calculate overall confidence from modality analyses."""
        try:
            if not modality_analyses:
                return 0.0

            # Calculate weighted average confidence
            total_confidence = sum(analysis.confidence for analysis in modality_analyses)
            overall_confidence = total_confidence / len(modality_analyses)

            return min(1.0, max(0.0, overall_confidence))

        except Exception as e:
            logger.error("Overall confidence calculation failed: %s", e)
            return 0.0

    def _calculate_consistency_score(self, modality_analyses: List[ModalityAnalysis]) -> float:
        """Calculate consistency score across modalities."""
        try:
            if len(modality_analyses) < 2:
                return 1.0  # Perfect consistency for single modality

            # Calculate confidence variance
            confidences = [analysis.confidence for analysis in modality_analyses]
            mean_confidence = sum(confidences) / len(confidences)
            variance = sum((c - mean_confidence) ** 2 for c in confidences) / len(confidences)

            # Convert variance to consistency score
            consistency_score = max(0.0, 1.0 - variance)

            return min(1.0, max(0.0, consistency_score))

        except Exception as e:
            logger.error("Consistency score calculation failed: %s", e)
            return 0.5

    def _update_performance_metrics(self, result: MultiModalResult) -> None:
        """Update performance metrics."""
        try:
            # Update average confidence
            if self.total_analyses > 0:
                self.average_confidence = (
                    (self.average_confidence * (self.total_analyses - 1) + result.overall_confidence)
                    / self.total_analyses
                )

            # Update average processing time
            if self.total_analyses > 0:
                self.average_processing_time = (
                    (self.average_processing_time * (self.total_analyses - 1) + result.processing_time_ms)
                    / self.total_analyses
                )

        except Exception as e:
            logger.error("Performance metrics update failed: %s", e)

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "total_analyses": self.total_analyses,
            "successful_analyses": self.successful_analyses,
            "success_rate": self.successful_analyses / max(1, self.total_analyses),
            "average_confidence": self.average_confidence,
            "average_processing_time_ms": self.average_processing_time,
            "total_modality_analyzers": len(self.modality_analyzers),
            "total_fusion_engines": len(self.fusion_engines),
            "analysis_history_size": len(self.analysis_history),
            "supported_modalities": [modality.value for modality in ModalityType],
            "supported_fusion_strategies": [strategy.value for strategy in FusionStrategy]
        }


# Global instance
multimodal_analyzer = MultiModalAnalyzer()
