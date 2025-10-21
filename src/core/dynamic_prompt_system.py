"""
Dynamic Prompt System
Implements adaptive prompting based on document characteristics and context
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import json
import uuid
import re
from pathlib import Path

from src.core.centralized_logging import get_logger, performance_tracker
from src.core.type_safety import Result, ErrorHandler

logger = get_logger(__name__)


class PromptType(Enum):
    """Types of prompts."""
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    CLINICAL_REASONING = "clinical_reasoning"
    FACT_VERIFICATION = "fact_verification"
    BIAS_DETECTION = "bias_detection"
    ENTITY_EXTRACTION = "entity_extraction"
    DOCUMENT_CLASSIFICATION = "document_classification"
    EXPLANATION_GENERATION = "explanation_generation"
    CONFIDENCE_CALIBRATION = "confidence_calibration"


class DocumentComplexity(Enum):
    """Document complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class PromptStrategy(Enum):
    """Prompt strategies."""
    TEMPLATE_BASED = "template_based"
    CONTEXT_AWARE = "context_aware"
    ADAPTIVE = "adaptive"
    HIERARCHICAL = "hierarchical"
    ITERATIVE = "iterative"


@dataclass
class DocumentAnalysis:
    """Analysis of document characteristics."""
    document_id: str
    complexity: DocumentComplexity
    document_type: str
    discipline: str
    length: int
    entities: List[Dict[str, Any]]
    key_topics: List[str]
    technical_level: str
    urgency_level: str
    confidence_indicators: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """A prompt template."""
    template_id: str
    prompt_type: PromptType
    template_text: str
    variables: List[str]
    complexity_level: DocumentComplexity
    strategy: PromptStrategy
    effectiveness_score: float
    usage_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedPrompt:
    """A generated prompt."""
    prompt_id: str
    template_id: str
    prompt_text: str
    variables_used: Dict[str, str]
    complexity_level: DocumentComplexity
    strategy_used: PromptStrategy
    confidence: float
    expected_effectiveness: float
    generation_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicPromptSystem:
    """
    Dynamic prompt system for adaptive prompting.

    Features:
    - Document analysis and characterization
    - Template selection based on context
    - Adaptive prompt generation
    - Performance tracking and optimization
    - Multi-strategy prompting
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the dynamic prompt system."""
        self.config_path = config_path or "config/dynamic_prompts.yaml"
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.document_analyzers: Dict[str, Any] = {}
        self.prompt_strategies: Dict[PromptStrategy, Any] = {}
        self.generation_history: List[GeneratedPrompt] = []

        # Performance tracking
        self.total_prompts_generated = 0
        self.successful_generations = 0
        self.average_effectiveness = 0.0
        self.average_generation_time = 0.0

        # Initialize components
        self._initialize_prompt_templates()
        self._initialize_document_analyzers()
        self._initialize_prompt_strategies()

        logger.info("DynamicPromptSystem initialized with %d templates", len(self.prompt_templates))

    def _initialize_prompt_templates(self) -> None:
        """Initialize prompt templates for different types and complexities."""
        try:
            # Compliance Analysis Templates
            self.prompt_templates["compliance_simple"] = PromptTemplate(
                template_id="compliance_simple",
                prompt_type=PromptType.COMPLIANCE_ANALYSIS,
                template_text="""
Analyze the following clinical document for compliance with {discipline} standards:

Document: {document_text}

Please identify:
1. Compliance issues
2. Areas of concern
3. Recommendations for improvement

Focus on the most critical compliance requirements for {discipline}.
""",
                variables=["discipline", "document_text"],
                complexity_level=DocumentComplexity.SIMPLE,
                strategy=PromptStrategy.TEMPLATE_BASED,
                effectiveness_score=0.8
            )

            self.prompt_templates["compliance_complex"] = PromptTemplate(
                template_id="compliance_complex",
                prompt_type=PromptType.COMPLIANCE_ANALYSIS,
                template_text="""
Perform a comprehensive compliance analysis of the following {discipline} document:

Document: {document_text}

Context: {context}

Entities identified: {entities}

Please provide:
1. Detailed compliance assessment
2. Specific rule violations
3. Risk assessment
4. Corrective action recommendations
5. Priority levels for each finding

Consider the following factors:
- Clinical accuracy
- Documentation standards
- Regulatory requirements
- Patient safety implications
- Professional standards

Provide evidence-based analysis with specific references to compliance rules.
""",
                variables=["discipline", "document_text", "context", "entities"],
                complexity_level=DocumentComplexity.COMPLEX,
                strategy=PromptStrategy.CONTEXT_AWARE,
                effectiveness_score=0.9
            )

            # Clinical Reasoning Templates
            self.prompt_templates["clinical_reasoning"] = PromptTemplate(
                template_id="clinical_reasoning",
                prompt_type=PromptType.CLINICAL_REASONING,
                template_text="""
Analyze the clinical reasoning in the following document:

Document: {document_text}

Clinical entities: {entities}

Please evaluate:
1. Logical flow of clinical reasoning
2. Evidence-based decision making
3. Clinical judgment quality
4. Potential reasoning gaps
5. Recommendations for improvement

Consider the clinical context and evidence hierarchy.
""",
                variables=["document_text", "entities"],
                complexity_level=DocumentComplexity.MODERATE,
                strategy=PromptStrategy.HIERARCHICAL,
                effectiveness_score=0.85
            )

            # Fact Verification Templates
            self.prompt_templates["fact_verification"] = PromptTemplate(
                template_id="fact_verification",
                prompt_type=PromptType.FACT_VERIFICATION,
                template_text="""
Verify the factual accuracy of the following clinical statements:

Statements: {statements}

Context: {context}

Please:
1. Identify factual claims
2. Assess accuracy based on available evidence
3. Flag potential inaccuracies
4. Suggest corrections if needed
5. Provide confidence levels for each assessment

Use evidence-based medicine principles for verification.
""",
                variables=["statements", "context"],
                complexity_level=DocumentComplexity.MODERATE,
                strategy=PromptStrategy.ITERATIVE,
                effectiveness_score=0.88
            )

            # Bias Detection Templates
            self.prompt_templates["bias_detection"] = PromptTemplate(
                template_id="bias_detection",
                prompt_type=PromptType.BIAS_DETECTION,
                template_text="""
Analyze the following document for potential biases:

Document: {document_text}

Please identify:
1. Demographic biases
2. Linguistic biases
3. Clinical biases
4. Cognitive biases
5. Systemic biases

For each bias found:
- Describe the bias type
- Explain the potential impact
- Suggest mitigation strategies
- Provide confidence assessment

Consider fairness, equity, and objectivity in clinical documentation.
""",
                variables=["document_text"],
                complexity_level=DocumentComplexity.MODERATE,
                strategy=PromptStrategy.ADAPTIVE,
                effectiveness_score=0.82
            )

            # Entity Extraction Templates
            self.prompt_templates["entity_extraction"] = PromptTemplate(
                template_id="entity_extraction",
                prompt_type=PromptType.ENTITY_EXTRACTION,
                template_text="""
Extract clinical entities from the following document:

Document: {document_text}

Please identify and classify:
1. Medical conditions
2. Medications
3. Procedures
4. Anatomical structures
5. Clinical measurements
6. Temporal references
7. Patient demographics

For each entity:
- Provide the text span
- Classify the entity type
- Assign confidence score
- Note any ambiguities

Use standard medical terminology and coding systems.
""",
                variables=["document_text"],
                complexity_level=DocumentComplexity.SIMPLE,
                strategy=PromptStrategy.TEMPLATE_BASED,
                effectiveness_score=0.9
            )

            # Document Classification Templates
            self.prompt_templates["document_classification"] = PromptTemplate(
                template_id="document_classification",
                prompt_type=PromptType.DOCUMENT_CLASSIFICATION,
                template_text="""
Classify the following clinical document:

Document: {document_text}

Please determine:
1. Document type (e.g., progress note, evaluation, discharge summary)
2. Clinical discipline (PT, OT, SLP, etc.)
3. Urgency level (routine, urgent, emergent)
4. Complexity level (simple, moderate, complex)
5. Key clinical domains

Provide:
- Primary classification
- Confidence score
- Supporting evidence
- Alternative classifications if applicable

Consider document structure, content, and clinical context.
""",
                variables=["document_text"],
                complexity_level=DocumentComplexity.SIMPLE,
                strategy=PromptStrategy.TEMPLATE_BASED,
                effectiveness_score=0.87
            )

            # Explanation Generation Templates
            self.prompt_templates["explanation_generation"] = PromptTemplate(
                template_id="explanation_generation",
                prompt_type=PromptType.EXPLANATION_GENERATION,
                template_text="""
Generate a comprehensive explanation for the following analysis result:

Analysis Result: {analysis_result}

Context: {context}

Entities: {entities}

Please provide:
1. Clear explanation of findings
2. Reasoning behind conclusions
3. Evidence supporting the analysis
4. Limitations and uncertainties
5. Recommendations for action

Make the explanation:
- Clinically relevant
- Evidence-based
- Easy to understand
- Actionable
- Transparent about confidence levels

Use appropriate clinical terminology while maintaining accessibility.
""",
                variables=["analysis_result", "context", "entities"],
                complexity_level=DocumentComplexity.MODERATE,
                strategy=PromptStrategy.CONTEXT_AWARE,
                effectiveness_score=0.89
            )

            # Confidence Calibration Templates
            self.prompt_templates["confidence_calibration"] = PromptTemplate(
                template_id="confidence_calibration",
                prompt_type=PromptType.CONFIDENCE_CALIBRATION,
                template_text="""
Calibrate confidence scores for the following analysis:

Analysis: {analysis}

Confidence Factors: {confidence_factors}

Please:
1. Assess current confidence levels
2. Identify uncertainty sources
3. Adjust confidence scores based on:
   - Evidence quality
   - Data completeness
   - Model certainty
   - External validation
4. Provide calibrated confidence ranges
5. Explain calibration rationale

Ensure confidence scores reflect true model uncertainty.
""",
                variables=["analysis", "confidence_factors"],
                complexity_level=DocumentComplexity.MODERATE,
                strategy=PromptStrategy.ADAPTIVE,
                effectiveness_score=0.86
            )

            logger.info("Initialized %d prompt templates", len(self.prompt_templates))

        except Exception as e:
            logger.error("Failed to initialize prompt templates: %s", e)
            raise

    def _initialize_document_analyzers(self) -> None:
        """Initialize document analyzers."""
        try:
            self.document_analyzers = {
                "complexity_analyzer": {
                    "type": "complexity",
                    "factors": ["length", "technical_terms", "sentence_structure", "medical_entities"],
                    "weights": [0.3, 0.3, 0.2, 0.2]
                },
                "entity_analyzer": {
                    "type": "entity",
                    "models": ["medical_ner", "clinical_ner", "temporal_ner"],
                    "confidence_threshold": 0.7
                },
                "topic_analyzer": {
                    "type": "topic",
                    "methods": ["keyword_extraction", "topic_modeling", "semantic_analysis"],
                    "max_topics": 10
                },
                "technical_analyzer": {
                    "type": "technical",
                    "indicators": ["medical_terminology", "clinical_procedures", "diagnostic_codes"],
                    "complexity_threshold": 0.5
                }
            }

            logger.info("Initialized %d document analyzers", len(self.document_analyzers))

        except Exception as e:
            logger.error("Failed to initialize document analyzers: %s", e)
            raise

    def _initialize_prompt_strategies(self) -> None:
        """Initialize prompt strategies."""
        try:
            self.prompt_strategies = {
                PromptStrategy.TEMPLATE_BASED: {
                    "type": "template_based",
                    "description": "Use predefined templates with variable substitution",
                    "complexity_threshold": 0.5,
                    "use_case": "Standard analysis tasks"
                },
                PromptStrategy.CONTEXT_AWARE: {
                    "type": "context_aware",
                    "description": "Adapt prompts based on document context and entities",
                    "complexity_threshold": 0.7,
                    "use_case": "Complex analysis with rich context"
                },
                PromptStrategy.ADAPTIVE: {
                    "type": "adaptive",
                    "description": "Dynamically adjust prompts based on performance",
                    "complexity_threshold": 0.8,
                    "use_case": "High-stakes analysis requiring optimization"
                },
                PromptStrategy.HIERARCHICAL: {
                    "type": "hierarchical",
                    "description": "Use multi-level prompting with progressive refinement",
                    "complexity_threshold": 0.9,
                    "use_case": "Very complex analysis requiring step-by-step reasoning"
                },
                PromptStrategy.ITERATIVE: {
                    "type": "iterative",
                    "description": "Use iterative prompting with feedback loops",
                    "complexity_threshold": 0.6,
                    "use_case": "Analysis requiring multiple passes and refinement"
                }
            }

            logger.info("Initialized %d prompt strategies", len(self.prompt_strategies))

        except Exception as e:
            logger.error("Failed to initialize prompt strategies: %s", e)
            raise

    async def generate_adaptive_prompt(
        self,
        document_text: str,
        prompt_type: PromptType,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 30.0
    ) -> Result[GeneratedPrompt, str]:
        """Generate an adaptive prompt based on document characteristics."""
        try:
            start_time = datetime.now()
            self.total_prompts_generated += 1

            # Analyze document characteristics
            document_analysis = await self._analyze_document(document_text, context)

            # Select appropriate template
            template = self._select_template(prompt_type, document_analysis)

            if not template:
                return Result.error(f"No suitable template found for {prompt_type.value}")

            # Select prompt strategy
            strategy = self._select_strategy(document_analysis, template)

            # Generate prompt
            generated_prompt = await self._generate_prompt(
                template, document_analysis, context, strategy, timeout_seconds
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Update template usage
            template.usage_count += 1

            # Store generation history
            self.generation_history.append(generated_prompt)
            if len(self.generation_history) > 1000:
                self.generation_history = self.generation_history[-500:]

            # Update performance metrics
            self._update_performance_metrics(generated_prompt, processing_time)

            self.successful_generations += 1
            return Result.success(generated_prompt)

        except Exception as e:
            logger.error("Adaptive prompt generation failed: %s", e)
            return Result.error(f"Prompt generation failed: {e}")

    async def _analyze_document(
        self,
        document_text: str,
        context: Optional[Dict[str, Any]]
    ) -> DocumentAnalysis:
        """Analyze document characteristics."""
        try:
            document_id = str(uuid.uuid4())

            # Analyze complexity
            complexity = await self._analyze_complexity(document_text)

            # Extract entities (simplified)
            entities = await self._extract_entities(document_text)

            # Extract key topics
            key_topics = await self._extract_topics(document_text)

            # Determine technical level
            technical_level = await self._determine_technical_level(document_text)

            # Determine urgency level
            urgency_level = await self._determine_urgency_level(document_text, context)

            # Identify confidence indicators
            confidence_indicators = await self._identify_confidence_indicators(document_text)

            # Determine document type and discipline from context
            document_type = context.get("document_type", "clinical_note") if context else "clinical_note"
            discipline = context.get("discipline", "general") if context else "general"

            analysis = DocumentAnalysis(
                document_id=document_id,
                complexity=complexity,
                document_type=document_type,
                discipline=discipline,
                length=len(document_text),
                entities=entities,
                key_topics=key_topics,
                technical_level=technical_level,
                urgency_level=urgency_level,
                confidence_indicators=confidence_indicators,
                metadata={
                    "analysis_timestamp": datetime.now(timezone.utc),
                    "context_provided": bool(context)
                }
            )

            logger.debug("Document analysis completed: complexity=%s, entities=%d, topics=%d",
                        complexity.value, len(entities), len(key_topics))

            return analysis

        except Exception as e:
            logger.error("Document analysis failed: %s", e)
            # Return default analysis
            return DocumentAnalysis(
                document_id=str(uuid.uuid4()),
                complexity=DocumentComplexity.MODERATE,
                document_type="clinical_note",
                discipline="general",
                length=len(document_text),
                entities=[],
                key_topics=[],
                technical_level="moderate",
                urgency_level="routine",
                confidence_indicators=[]
            )

    async def _analyze_complexity(self, document_text: str) -> DocumentComplexity:
        """Analyze document complexity."""
        try:
            # Simple complexity analysis based on length and structure
            length = len(document_text)
            sentences = len(re.split(r'[.!?]+', document_text))
            words = len(document_text.split())

            # Calculate complexity score
            avg_sentence_length = words / max(1, sentences)
            technical_terms = len(re.findall(r'\b[A-Z]{2,}\b', document_text))  # Acronyms
            medical_terms = len(re.findall(r'\b(?:patient|diagnosis|treatment|therapy|clinical)\b', document_text, re.IGNORECASE))

            complexity_score = (
                (length / 1000) * 0.3 +  # Length factor
                (avg_sentence_length / 20) * 0.2 +  # Sentence complexity
                (technical_terms / 10) * 0.3 +  # Technical terms
                (medical_terms / 20) * 0.2  # Medical terms
            )

            # Determine complexity level
            if complexity_score < 0.3:
                return DocumentComplexity.SIMPLE
            elif complexity_score < 0.6:
                return DocumentComplexity.MODERATE
            elif complexity_score < 0.8:
                return DocumentComplexity.COMPLEX
            else:
                return DocumentComplexity.VERY_COMPLEX

        except Exception as e:
            logger.error("Complexity analysis failed: %s", e)
            return DocumentComplexity.MODERATE

    async def _extract_entities(self, document_text: str) -> List[Dict[str, Any]]:
        """Extract entities from document (simplified)."""
        try:
            entities = []

            # Simple entity extraction (in real implementation, this would use NER models)
            medical_patterns = [
                (r'\b(?:patient|client|individual)\b', 'PATIENT'),
                (r'\b(?:diagnosis|condition|disorder)\b', 'DIAGNOSIS'),
                (r'\b(?:treatment|therapy|intervention)\b', 'TREATMENT'),
                (r'\b(?:medication|drug|prescription)\b', 'MEDICATION'),
                (r'\b(?:procedure|surgery|operation)\b', 'PROCEDURE'),
                (r'\b(?:pain|discomfort|symptom)\b', 'SYMPTOM')
            ]

            for pattern, entity_type in medical_patterns:
                matches = re.finditer(pattern, document_text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "text": match.group(),
                        "label": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.8
                    })

            return entities[:20]  # Limit to 20 entities

        except Exception as e:
            logger.error("Entity extraction failed: %s", e)
            return []

    async def _extract_topics(self, document_text: str) -> List[str]:
        """Extract key topics from document (simplified)."""
        try:
            # Simple topic extraction (in real implementation, this would use topic modeling)
            topics = []

            # Extract key medical terms
            medical_terms = re.findall(r'\b(?:cardiology|neurology|orthopedics|pediatrics|geriatrics|oncology|psychiatry)\b', document_text, re.IGNORECASE)
            topics.extend(medical_terms)

            # Extract treatment-related terms
            treatment_terms = re.findall(r'\b(?:physical therapy|occupational therapy|speech therapy|rehabilitation|counseling)\b', document_text, re.IGNORECASE)
            topics.extend(treatment_terms)

            # Remove duplicates and limit
            topics = list(set(topics))[:10]

            return topics

        except Exception as e:
            logger.error("Topic extraction failed: %s", e)
            return []

    async def _determine_technical_level(self, document_text: str) -> str:
        """Determine technical level of document."""
        try:
            # Count technical terms
            technical_terms = len(re.findall(r'\b[A-Z]{2,}\b', document_text))  # Acronyms
            medical_terms = len(re.findall(r'\b(?:diagnosis|prognosis|etiology|pathophysiology|pharmacology)\b', document_text, re.IGNORECASE))

            total_terms = technical_terms + medical_terms
            document_length = len(document_text.split())

            technical_ratio = total_terms / max(1, document_length)

            if technical_ratio < 0.05:
                return "basic"
            elif technical_ratio < 0.1:
                return "moderate"
            else:
                return "advanced"

        except Exception as e:
            logger.error("Technical level determination failed: %s", e)
            return "moderate"

    async def _determine_urgency_level(self, document_text: str, context: Optional[Dict[str, Any]]) -> str:
        """Determine urgency level of document."""
        try:
            # Check for urgency indicators
            urgent_keywords = ['urgent', 'emergency', 'critical', 'immediate', 'asap', 'stat']
            urgent_count = sum(1 for keyword in urgent_keywords if keyword in document_text.lower())

            # Check context for urgency
            context_urgency = context.get("urgency", "routine") if context else "routine"

            if urgent_count > 0 or context_urgency in ["urgent", "emergency"]:
                return "urgent"
            elif context_urgency == "priority":
                return "priority"
            else:
                return "routine"

        except Exception as e:
            logger.error("Urgency level determination failed: %s", e)
            return "routine"

    async def _identify_confidence_indicators(self, document_text: str) -> List[str]:
        """Identify confidence indicators in document."""
        try:
            indicators = []

            # Look for confidence-related phrases
            confidence_patterns = [
                r'\b(?:confident|certain|sure|definite)\b',
                r'\b(?:uncertain|unsure|unclear|ambiguous)\b',
                r'\b(?:likely|probably|possibly|maybe)\b',
                r'\b(?:evidence|data|research|study)\b'
            ]

            for pattern in confidence_patterns:
                matches = re.findall(pattern, document_text, re.IGNORECASE)
                if matches:
                    indicators.extend(matches)

            return list(set(indicators))[:10]  # Remove duplicates and limit

        except Exception as e:
            logger.error("Confidence indicator identification failed: %s", e)
            return []

    def _select_template(
        self,
        prompt_type: PromptType,
        document_analysis: DocumentAnalysis
    ) -> Optional[PromptTemplate]:
        """Select appropriate template based on prompt type and document analysis."""
        try:
            # Find templates matching the prompt type
            matching_templates = [
                template for template in self.prompt_templates.values()
                if template.prompt_type == prompt_type
            ]

            if not matching_templates:
                return None

            # Select template based on complexity
            complexity = document_analysis.complexity

            # Prefer templates that match complexity level
            complexity_matches = [
                template for template in matching_templates
                if template.complexity_level == complexity
            ]

            if complexity_matches:
                # Select template with highest effectiveness score
                return max(complexity_matches, key=lambda t: t.effectiveness_score)
            else:
                # Fall back to any matching template
                return max(matching_templates, key=lambda t: t.effectiveness_score)

        except Exception as e:
            logger.error("Template selection failed: %s", e)
            return None

    def _select_strategy(
        self,
        document_analysis: DocumentAnalysis,
        template: PromptTemplate
    ) -> PromptStrategy:
        """Select prompt strategy based on document analysis and template."""
        try:
            # Use template's preferred strategy if available
            if template.strategy:
                return template.strategy

            # Select strategy based on complexity
            complexity = document_analysis.complexity

            if complexity == DocumentComplexity.SIMPLE:
                return PromptStrategy.TEMPLATE_BASED
            elif complexity == DocumentComplexity.MODERATE:
                return PromptStrategy.CONTEXT_AWARE
            elif complexity == DocumentComplexity.COMPLEX:
                return PromptStrategy.ADAPTIVE
            else:  # VERY_COMPLEX
                return PromptStrategy.HIERARCHICAL

        except Exception as e:
            logger.error("Strategy selection failed: %s", e)
            return PromptStrategy.TEMPLATE_BASED

    async def _generate_prompt(
        self,
        template: PromptTemplate,
        document_analysis: DocumentAnalysis,
        context: Optional[Dict[str, Any]],
        strategy: PromptStrategy,
        timeout_seconds: float
    ) -> GeneratedPrompt:
        """Generate prompt using template and strategy."""
        try:
            prompt_id = str(uuid.uuid4())

            # Prepare variables for template
            variables = self._prepare_template_variables(template, document_analysis, context)

            # Generate prompt text
            prompt_text = template.template_text.format(**variables)

            # Apply strategy-specific modifications
            if strategy == PromptStrategy.CONTEXT_AWARE:
                prompt_text = self._apply_context_aware_modifications(prompt_text, document_analysis)
            elif strategy == PromptStrategy.ADAPTIVE:
                prompt_text = self._apply_adaptive_modifications(prompt_text, document_analysis)
            elif strategy == PromptStrategy.HIERARCHICAL:
                prompt_text = self._apply_hierarchical_modifications(prompt_text, document_analysis)
            elif strategy == PromptStrategy.ITERATIVE:
                prompt_text = self._apply_iterative_modifications(prompt_text, document_analysis)

            # Calculate confidence and effectiveness
            confidence = self._calculate_prompt_confidence(template, document_analysis, strategy)
            expected_effectiveness = self._calculate_expected_effectiveness(template, document_analysis, strategy)

            generated_prompt = GeneratedPrompt(
                prompt_id=prompt_id,
                template_id=template.template_id,
                prompt_text=prompt_text,
                variables_used=variables,
                complexity_level=document_analysis.complexity,
                strategy_used=strategy,
                confidence=confidence,
                expected_effectiveness=expected_effectiveness,
                generation_time_ms=0.0,  # Will be set by caller
                metadata={
                    "document_analysis": {
                        "complexity": document_analysis.complexity.value,
                        "entities_count": len(document_analysis.entities),
                        "topics_count": len(document_analysis.key_topics),
                        "technical_level": document_analysis.technical_level,
                        "urgency_level": document_analysis.urgency_level
                    },
                    "template_effectiveness": template.effectiveness_score,
                    "strategy_config": self.prompt_strategies[strategy]
                }
            )

            return generated_prompt

        except Exception as e:
            logger.error("Prompt generation failed: %s", e)
            raise

    def _prepare_template_variables(
        self,
        template: PromptTemplate,
        document_analysis: DocumentAnalysis,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Prepare variables for template substitution."""
        try:
            variables = {}

            # Basic variables
            variables["document_text"] = document_analysis.document_type
            variables["discipline"] = document_analysis.discipline

            # Context variables
            if context:
                variables.update({
                    "context": context.get("context", ""),
                    "entities": self._format_entities(document_analysis.entities),
                    "statements": context.get("statements", ""),
                    "analysis_result": context.get("analysis_result", ""),
                    "confidence_factors": context.get("confidence_factors", "")
                })

            # Document analysis variables
            variables.update({
                "entities": self._format_entities(document_analysis.entities),
                "topics": ", ".join(document_analysis.key_topics),
                "technical_level": document_analysis.technical_level,
                "urgency_level": document_analysis.urgency_level
            })

            return variables

        except Exception as e:
            logger.error("Template variable preparation failed: %s", e)
            return {}

    def _format_entities(self, entities: List[Dict[str, Any]]) -> str:
        """Format entities for template use."""
        try:
            if not entities:
                return "None identified"

            formatted = []
            for entity in entities[:10]:  # Limit to 10 entities
                formatted.append(f"{entity['text']} ({entity['label']})")

            return "; ".join(formatted)

        except Exception as e:
            logger.error("Entity formatting failed: %s", e)
            return "Error formatting entities"

    def _apply_context_aware_modifications(self, prompt_text: str, document_analysis: DocumentAnalysis) -> str:
        """Apply context-aware modifications to prompt."""
        try:
            # Add context-specific instructions
            if document_analysis.urgency_level == "urgent":
                prompt_text += "\n\nNote: This is an urgent case requiring immediate attention."

            if document_analysis.technical_level == "advanced":
                prompt_text += "\n\nUse advanced clinical terminology and evidence-based analysis."

            return prompt_text

        except Exception as e:
            logger.error("Context-aware modifications failed: %s", e)
            return prompt_text

    def _apply_adaptive_modifications(self, prompt_text: str, document_analysis: DocumentAnalysis) -> str:
        """Apply adaptive modifications to prompt."""
        try:
            # Add adaptive instructions based on complexity
            if document_analysis.complexity == DocumentComplexity.VERY_COMPLEX:
                prompt_text += "\n\nThis is a complex case requiring detailed analysis and careful consideration of multiple factors."

            return prompt_text

        except Exception as e:
            logger.error("Adaptive modifications failed: %s", e)
            return prompt_text

    def _apply_hierarchical_modifications(self, prompt_text: str, document_analysis: DocumentAnalysis) -> str:
        """Apply hierarchical modifications to prompt."""
        try:
            # Add hierarchical analysis instructions
            prompt_text += "\n\nPlease provide analysis in hierarchical levels:\n1. High-level overview\n2. Detailed analysis\n3. Specific recommendations"

            return prompt_text

        except Exception as e:
            logger.error("Hierarchical modifications failed: %s", e)
            return prompt_text

    def _apply_iterative_modifications(self, prompt_text: str, document_analysis: DocumentAnalysis) -> str:
        """Apply iterative modifications to prompt."""
        try:
            # Add iterative analysis instructions
            prompt_text += "\n\nPlease provide iterative analysis with:\n1. Initial assessment\n2. Refined analysis\n3. Final conclusions"

            return prompt_text

        except Exception as e:
            logger.error("Iterative modifications failed: %s", e)
            return prompt_text

    def _calculate_prompt_confidence(
        self,
        template: PromptTemplate,
        document_analysis: DocumentAnalysis,
        strategy: PromptStrategy
    ) -> float:
        """Calculate confidence for generated prompt."""
        try:
            # Base confidence from template effectiveness
            base_confidence = template.effectiveness_score

            # Adjust based on strategy
            strategy_adjustments = {
                PromptStrategy.TEMPLATE_BASED: 0.0,
                PromptStrategy.CONTEXT_AWARE: 0.05,
                PromptStrategy.ADAPTIVE: 0.1,
                PromptStrategy.HIERARCHICAL: 0.08,
                PromptStrategy.ITERATIVE: 0.06
            }

            strategy_adjustment = strategy_adjustments.get(strategy, 0.0)

            # Adjust based on document analysis quality
            analysis_quality = min(1.0, (
                len(document_analysis.entities) / 10.0 +
                len(document_analysis.key_topics) / 5.0 +
                (1.0 if document_analysis.confidence_indicators else 0.5)
            ) / 3.0)

            analysis_adjustment = (analysis_quality - 0.5) * 0.1

            # Calculate final confidence
            confidence = base_confidence + strategy_adjustment + analysis_adjustment

            return min(1.0, max(0.0, confidence))

        except Exception as e:
            logger.error("Confidence calculation failed: %s", e)
            return 0.5

    def _calculate_expected_effectiveness(
        self,
        template: PromptTemplate,
        document_analysis: DocumentAnalysis,
        strategy: PromptStrategy
    ) -> float:
        """Calculate expected effectiveness of generated prompt."""
        try:
            # Base effectiveness from template
            base_effectiveness = template.effectiveness_score

            # Adjust based on complexity match
            complexity_match = 1.0 if template.complexity_level == document_analysis.complexity else 0.8

            # Adjust based on strategy appropriateness
            strategy_appropriateness = {
                PromptStrategy.TEMPLATE_BASED: 0.9 if document_analysis.complexity == DocumentComplexity.SIMPLE else 0.7,
                PromptStrategy.CONTEXT_AWARE: 0.9 if document_analysis.complexity == DocumentComplexity.MODERATE else 0.8,
                PromptStrategy.ADAPTIVE: 0.9 if document_analysis.complexity == DocumentComplexity.COMPLEX else 0.8,
                PromptStrategy.HIERARCHICAL: 0.9 if document_analysis.complexity == DocumentComplexity.VERY_COMPLEX else 0.7,
                PromptStrategy.ITERATIVE: 0.85
            }

            strategy_score = strategy_appropriateness.get(strategy, 0.8)

            # Calculate final effectiveness
            effectiveness = base_effectiveness * complexity_match * strategy_score

            return min(1.0, max(0.0, effectiveness))

        except Exception as e:
            logger.error("Effectiveness calculation failed: %s", e)
            return 0.5

    def _update_performance_metrics(self, generated_prompt: GeneratedPrompt, processing_time_ms: float) -> None:
        """Update performance metrics."""
        try:
            # Update average effectiveness
            if self.total_prompts_generated > 0:
                self.average_effectiveness = (
                    (self.average_effectiveness * (self.total_prompts_generated - 1) + generated_prompt.expected_effectiveness)
                    / self.total_prompts_generated
                )

            # Update average generation time
            if self.total_prompts_generated > 0:
                self.average_generation_time = (
                    (self.average_generation_time * (self.total_prompts_generated - 1) + processing_time_ms)
                    / self.total_prompts_generated
                )

        except Exception as e:
            logger.error("Performance metrics update failed: %s", e)

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "total_prompts_generated": self.total_prompts_generated,
            "successful_generations": self.successful_generations,
            "success_rate": self.successful_generations / max(1, self.total_prompts_generated),
            "average_effectiveness": self.average_effectiveness,
            "average_generation_time_ms": self.average_generation_time,
            "total_templates": len(self.prompt_templates),
            "total_strategies": len(self.prompt_strategies),
            "generation_history_size": len(self.generation_history),
            "template_usage": {
                template_id: template.usage_count
                for template_id, template in self.prompt_templates.items()
            }
        }


# Global instance
dynamic_prompt_system = DynamicPromptSystem()
