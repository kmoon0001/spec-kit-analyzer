"""Enhanced confidence calibration and context optimization utilities."""

import logging
import re
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConfidenceMetrics:
    """Structured confidence metrics for analysis results."""
    overall_confidence: float
    entity_confidence: float
    fact_check_confidence: float
    context_confidence: float
    reasoning: str

class ConfidenceCalibrator:
    """Advanced confidence calibration using multiple signals."""

    def __init__(self):
        self.confidence_weights = {
            'entity_overlap': 0.3,
            'fact_consistency': 0.25,
            'context_relevance': 0.2,
            'prompt_adherence': 0.15,
            'output_quality': 0.1
        }

    def calibrate_confidence(self,
                           analysis_result: Dict[str, Any],
                           entities: List[Dict[str, Any]],
                           fact_check_results: List[bool],
                           context_relevance: float) -> ConfidenceMetrics:
        """Calculate calibrated confidence using multiple signals."""

        # Entity confidence (based on NER scores and overlap)
        entity_confidence = self._calculate_entity_confidence(entities)

        # Fact check confidence (based on consistency checks)
        fact_check_confidence = self._calculate_fact_check_confidence(fact_check_results)

        # Context relevance (how well retrieved context matches document)
        context_confidence = context_relevance

        # Prompt adherence (how well output follows JSON structure)
        prompt_adherence = self._calculate_prompt_adherence(analysis_result)

        # Output quality (length, coherence, completeness)
        output_quality = self._calculate_output_quality(analysis_result)

        # Weighted overall confidence
        overall_confidence = (
            entity_confidence * self.confidence_weights['entity_overlap'] +
            fact_check_confidence * self.confidence_weights['fact_consistency'] +
            context_confidence * self.confidence_weights['context_relevance'] +
            prompt_adherence * self.confidence_weights['prompt_adherence'] +
            output_quality * self.confidence_weights['output_quality']
        )

        # Generate reasoning
        reasoning = self._generate_confidence_reasoning(
            entity_confidence, fact_check_confidence, context_confidence,
            prompt_adherence, output_quality
        )

        return ConfidenceMetrics(
            overall_confidence=overall_confidence,
            entity_confidence=entity_confidence,
            fact_check_confidence=fact_check_confidence,
            context_confidence=context_confidence,
            reasoning=reasoning
        )

    def _calculate_entity_confidence(self, entities: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on entity extraction quality."""
        if not entities:
            return 0.3  # Low confidence for no entities

        # Average entity confidence
        avg_score = sum(entity.get('score', 0.0) for entity in entities) / len(entities)

        # Bonus for high-confidence entities
        high_conf_entities = sum(1 for e in entities if e.get('score', 0.0) > 0.8)
        diversity_bonus = min(0.2, high_conf_entities * 0.05)

        return min(1.0, avg_score + diversity_bonus)

    def _calculate_fact_check_confidence(self, fact_check_results: List[bool]) -> float:
        """Calculate confidence based on fact-checking results."""
        if not fact_check_results:
            return 0.5  # Neutral when no fact checks performed

        consistency_rate = sum(fact_check_results) / len(fact_check_results)
        return consistency_rate

    def _calculate_prompt_adherence(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate how well the output follows the expected JSON structure."""
        required_fields = ['summary', 'findings']
        found_fields = sum(1 for field in required_fields if field in analysis_result)

        structure_score = found_fields / len(required_fields)

        # Check for proper JSON structure
        if isinstance(analysis_result.get('findings'), list):
            structure_score += 0.2

        return min(1.0, structure_score)

    def _calculate_output_quality(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate output quality based on completeness and coherence."""
        quality_score = 0.0

        # Summary quality
        summary = analysis_result.get('summary', '')
        if len(summary) > 20 and len(summary) < 200:
            quality_score += 0.3

        # Findings quality
        findings = analysis_result.get('findings', [])
        if findings:
            quality_score += 0.4

            # Check individual finding quality
            for finding in findings:
                if all(finding.get(field) for field in ['issue_title', 'confidence', 'priority']):
                    quality_score += 0.1

        # Citations quality
        citations = analysis_result.get('citations', [])
        if citations:
            quality_score += 0.2

        return min(1.0, quality_score)

    def _generate_confidence_reasoning(self,
                                     entity_conf: float,
                                     fact_conf: float,
                                     context_conf: float,
                                     prompt_conf: float,
                                     output_conf: float) -> str:
        """Generate human-readable confidence reasoning."""
        factors = []

        if entity_conf > 0.7:
            factors.append("strong entity recognition")
        elif entity_conf < 0.4:
            factors.append("weak entity recognition")

        if fact_conf > 0.8:
            factors.append("high fact consistency")
        elif fact_conf < 0.5:
            factors.append("factual inconsistencies detected")

        if context_conf > 0.7:
            factors.append("good context relevance")
        elif context_conf < 0.4:
            factors.append("poor context matching")

        if prompt_conf > 0.8:
            factors.append("proper output format")
        else:
            factors.append("formatting issues")

        if output_conf > 0.7:
            factors.append("high output quality")
        else:
            factors.append("output quality concerns")

        return f"Confidence based on: {', '.join(factors)}"

class ContextOptimizer:
    """Advanced context window management and optimization."""

    def __init__(self, max_context_length: int = 1024):
        self.max_context_length = max_context_length
        self.token_ratio = 4  # Rough chars per token

    def optimize_context(self,
                        document_text: str,
                        context_rules: List[str],
                        entities: List[Dict[str, Any]]) -> Tuple[str, List[str], Dict[str, Any]]:
        """Optimize context for maximum information density."""

        # Calculate available context space
        doc_tokens = len(document_text) // self.token_ratio
        available_tokens = self.max_context_length - doc_tokens - 200  # Reserve for prompt

        if available_tokens <= 0:
            # Document too long, need aggressive summarization
            optimized_doc = self._summarize_document(document_text)
            optimized_rules = self._prioritize_rules(context_rules, entities, available_tokens)
        else:
            optimized_doc = document_text
            optimized_rules = self._prioritize_rules(context_rules, entities, available_tokens)

        optimization_info = {
            'original_tokens': doc_tokens,
            'available_tokens': available_tokens,
            'rules_included': len(optimized_rules),
            'optimization_applied': doc_tokens > available_tokens
        }

        return optimized_doc, optimized_rules, optimization_info

    def _summarize_document(self, text: str) -> str:
        """Create a concise summary of the document."""
        # Extract key sentences (simple heuristic)
        sentences = re.split(r'[.!?]+', text)

        # Prioritize sentences with clinical terms
        clinical_terms = ['patient', 'therapy', 'treatment', 'assessment', 'goal', 'progress']
        scored_sentences = []

        for sentence in sentences:
            if len(sentence.strip()) > 10:
                score = sum(1 for term in clinical_terms if term.lower() in sentence.lower())
                scored_sentences.append((score, sentence.strip()))

        # Take top sentences
        scored_sentences.sort(reverse=True)
        summary_sentences = [s[1] for s in scored_sentences[:5]]

        return '. '.join(summary_sentences) + '.'

    def _prioritize_rules(self,
                         rules: List[str],
                         entities: List[Dict[str, Any]],
                         available_tokens: int) -> List[str]:
        """Prioritize rules based on entity relevance."""
        if not entities or available_tokens <= 0:
            return []

        # Extract entity types
        entity_types = [e.get('entity_group', '').lower() for e in entities]

        # Score rules by relevance
        scored_rules = []
        for rule in rules:
            score = 0
            rule_lower = rule.lower()

            # Score based on entity type matches
            for entity_type in entity_types:
                if entity_type in rule_lower:
                    score += 2

            # Score based on clinical relevance
            clinical_terms = ['therapy', 'treatment', 'assessment', 'documentation', 'compliance']
            for term in clinical_terms:
                if term in rule_lower:
                    score += 1

            scored_rules.append((score, rule))

        # Sort by score and take top rules that fit
        scored_rules.sort(reverse=True)

        selected_rules = []
        current_tokens = 0

        for score, rule in scored_rules:
            rule_tokens = len(rule) // self.token_ratio
            if current_tokens + rule_tokens <= available_tokens:
                selected_rules.append(rule)
                current_tokens += rule_tokens
            else:
                break

        return selected_rules

class PromptOptimizer:
    """Advanced prompt engineering for better tokenization and context usage."""

    def __init__(self):
        self.prompt_templates = {
            'analysis': self._get_optimized_analysis_prompt(),
            'classification': self._get_optimized_classification_prompt(),
            'fact_check': self._get_optimized_fact_check_prompt()
        }

    def optimize_prompt(self,
                       prompt_type: str,
                       document_text: str,
                       context_rules: List[str],
                       entities: List[Dict[str, Any]],
                       discipline: str) -> str:
        """Create an optimized prompt for maximum context efficiency."""

        template = self.prompt_templates.get(prompt_type, self.prompt_templates['analysis'])

        # Optimize entity list for prompt
        entity_summary = self._summarize_entities(entities)

        # Optimize context rules
        context_summary = self._summarize_context(context_rules)

        # Fill template with optimized content
        optimized_prompt = template.format(
            discipline=discipline,
            entity_summary=entity_summary,
            document_text=document_text,
            context_summary=context_summary
        )

        return optimized_prompt

    def _get_optimized_analysis_prompt(self) -> str:
        """Optimized analysis prompt with better tokenization."""
        return """Clinical Compliance Analysis

Discipline: {discipline}
Key Entities: {entity_summary}

Document:
{document_text}

Relevant Guidelines:
{context_summary}

Analyze compliance. Output JSON:
{{
  "summary": "Brief compliance assessment",
  "findings": [
    {{
      "issue": "Description",
      "confidence": 0.0-1.0,
      "priority": "High/Medium/Low",
      "recommendation": "Action item"
    }}
  ]
}}

Rules: Be precise. If uncertain, set confidence <0.6. Use only English."""

    def _get_optimized_classification_prompt(self) -> str:
        """Optimized classification prompt."""
        return """Classify this clinical document:

{document_text}

Discipline: {discipline}
Entities: {entity_summary}

Output: Document type (Progress Note, Evaluation, Discharge Summary, etc.)"""

    def _get_optimized_fact_check_prompt(self) -> str:
        """Optimized fact-checking prompt."""
        return """Fact Check:

Premise: {document_text}
Hypothesis: {context_summary}

Is the hypothesis supported by the premise? Answer: YES/NO"""

    def _summarize_entities(self, entities: List[Dict[str, Any]]) -> str:
        """Create a concise entity summary."""
        if not entities:
            return "None detected"

        # Group by type
        entity_groups = {}
        for entity in entities:
            entity_type = entity.get('entity_group', 'Other')
            if entity_type not in entity_groups:
                entity_groups[entity_type] = []
            entity_groups[entity_type].append(entity.get('word', ''))

        # Create summary
        summary_parts = []
        for entity_type, words in entity_groups.items():
            unique_words = list(set(words))[:3]  # Top 3 unique words per type
            summary_parts.append(f"{entity_type}: {', '.join(unique_words)}")

        return "; ".join(summary_parts)

    def _summarize_context(self, context_rules: List[str]) -> str:
        """Create a concise context summary."""
        if not context_rules:
            return "No specific guidelines available"

        # Take first few rules and summarize
        summary_rules = context_rules[:3]  # Top 3 most relevant rules

        # Truncate long rules
        summarized_rules = []
        for rule in summary_rules:
            if len(rule) > 200:
                summarized_rules.append(rule[:200] + "...")
            else:
                summarized_rules.append(rule)

        return "\n".join(summarized_rules)
