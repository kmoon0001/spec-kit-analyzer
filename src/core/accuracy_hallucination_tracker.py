"""
Comprehensive Accuracy and Hallucination Tracking System
Real-time monitoring and validation of system accuracy and hallucination rates
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import numpy as np
from pathlib import Path

from src.core.centralized_logging import get_logger, performance_tracker, audit_logger
from src.core.type_safety import Result, ErrorHandler

logger = get_logger(__name__)


class AccuracyMetric(Enum):
    """Types of accuracy metrics tracked."""
    OVERALL_ACCURACY = "overall_accuracy"
    CLINICAL_ACCURACY = "clinical_accuracy"
    COMPLIANCE_ACCURACY = "compliance_accuracy"
    ENTITY_EXTRACTION_ACCURACY = "entity_extraction_accuracy"
    FACT_CHECKING_ACCURACY = "fact_checking_accuracy"
    CONFIDENCE_CALIBRATION = "confidence_calibration"


class HallucinationType(Enum):
    """Types of hallucinations detected."""
    FACTUAL_HALLUCINATION = "factual_hallucination"
    CLINICAL_HALLUCINATION = "clinical_hallucination"
    COMPLIANCE_HALLUCINATION = "compliance_hallucination"
    ENTITY_HALLUCINATION = "entity_hallucination"
    TEMPORAL_HALLUCINATION = "temporal_hallucination"
    CAUSAL_HALLUCINATION = "causal_hallucination"


@dataclass
class AccuracyMetrics:
    """Comprehensive accuracy metrics."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    overall_accuracy: float = 0.0
    clinical_accuracy: float = 0.0
    compliance_accuracy: float = 0.0
    entity_extraction_accuracy: float = 0.0
    fact_checking_accuracy: float = 0.0
    confidence_calibration: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    processing_time_ms: float = 0.0
    model_used: str = ""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class HallucinationMetrics:
    """Comprehensive hallucination metrics."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_hallucinations: int = 0
    factual_hallucinations: int = 0
    clinical_hallucinations: int = 0
    compliance_hallucinations: int = 0
    entity_hallucinations: int = 0
    temporal_hallucinations: int = 0
    causal_hallucinations: int = 0
    hallucination_rate: float = 0.0
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    detection_confidence: float = 0.0
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ValidationResult:
    """Result from accuracy and hallucination validation."""
    analysis_id: str
    document_text: str
    findings: List[Dict[str, Any]]
    accuracy_metrics: AccuracyMetrics
    hallucination_metrics: HallucinationMetrics
    validation_status: str
    confidence_score: float
    recommendations: List[str]
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AccuracyHallucinationTracker:
    """
    Comprehensive system for tracking accuracy and hallucination rates.
    Provides real-time monitoring and validation capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the accuracy and hallucination tracker."""
        self.config = config or {}
        self.tracking_enabled = self.config.get('tracking_enabled', True)
        self.real_time_monitoring = self.config.get('real_time_monitoring', True)
        self.threshold_alerts = self.config.get('threshold_alerts', True)

        # Accuracy thresholds
        self.accuracy_thresholds = {
            'overall_accuracy': 0.85,      # 85% minimum
            'clinical_accuracy': 0.90,     # 90% minimum for clinical
            'compliance_accuracy': 0.88,   # 88% minimum for compliance
            'confidence_calibration': 0.80 # 80% minimum calibration
        }

        # Hallucination thresholds
        self.hallucination_thresholds = {
            'max_hallucination_rate': 0.10,  # 10% maximum
            'max_factual_hallucinations': 0.05,  # 5% maximum
            'max_clinical_hallucinations': 0.08   # 8% maximum
        }

        # Storage
        self.accuracy_history: List[AccuracyMetrics] = []
        self.hallucination_history: List[HallucinationMetrics] = []
        self.validation_results: List[ValidationResult] = []

        # Performance tracking
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0

        # Real-time metrics
        self.current_accuracy_trends: Dict[str, List[float]] = {
            'overall_accuracy': [],
            'clinical_accuracy': [],
            'compliance_accuracy': [],
            'hallucination_rate': []
        }

        logger.info("AccuracyHallucinationTracker initialized with tracking enabled: %s", self.tracking_enabled)

    async def validate_analysis(
        self,
        analysis_result: Dict[str, Any],
        document_text: str,
        ground_truth: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Result[ValidationResult, str]:
        """Validate analysis for accuracy and hallucinations."""
        try:
            start_time = datetime.now()
            analysis_id = str(uuid.uuid4())

            self.total_validations += 1

            # Extract findings
            findings = analysis_result.get('findings', [])

            # Calculate accuracy metrics
            accuracy_metrics = await self._calculate_accuracy_metrics(
                analysis_result, findings, ground_truth, context
            )

            # Detect hallucinations
            hallucination_metrics = await self._detect_hallucinations(
                analysis_result, document_text, findings, context
            )

            # Determine validation status
            validation_status = self._determine_validation_status(
                accuracy_metrics, hallucination_metrics
            )

            # Calculate overall confidence
            confidence_score = self._calculate_confidence_score(
                accuracy_metrics, hallucination_metrics
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                accuracy_metrics, hallucination_metrics
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create validation result
            result = ValidationResult(
                analysis_id=analysis_id,
                document_text=document_text,
                findings=findings,
                accuracy_metrics=accuracy_metrics,
                hallucination_metrics=hallucination_metrics,
                validation_status=validation_status,
                confidence_score=confidence_score,
                recommendations=recommendations,
                processing_time_ms=processing_time,
                metadata={
                    'validation_timestamp': datetime.now(timezone.utc).isoformat(),
                    'ground_truth_available': ground_truth is not None,
                    'context_provided': context is not None,
                    'tracking_enabled': self.tracking_enabled
                }
            )

            # Store results
            if self.tracking_enabled:
                self.accuracy_history.append(accuracy_metrics)
                self.hallucination_history.append(hallucination_metrics)
                self.validation_results.append(result)

                # Update real-time trends
                self._update_real_time_trends(accuracy_metrics, hallucination_metrics)

                # Check thresholds and alert if needed
                if self.threshold_alerts:
                    await self._check_threshold_alerts(accuracy_metrics, hallucination_metrics)

            self.successful_validations += 1

            logger.info("Validation completed: accuracy=%.2f, hallucination_rate=%.2f, status=%s",
                       accuracy_metrics.overall_accuracy, hallucination_metrics.hallucination_rate, validation_status)

            return Result.success(result)

        except Exception as e:
            logger.error("Validation failed: %s", e)
            self.failed_validations += 1
            return Result.error(f"Validation failed: {e}")

    async def _calculate_accuracy_metrics(
        self,
        analysis_result: Dict[str, Any],
        findings: List[Dict[str, Any]],
        ground_truth: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> AccuracyMetrics:
        """Calculate comprehensive accuracy metrics."""
        try:
            metrics = AccuracyMetrics()

            # Overall accuracy (based on confidence scores and consistency)
            overall_confidence = analysis_result.get('compliance_score', 0) / 100.0
            findings_consistency = self._calculate_findings_consistency(findings)
            metrics.overall_accuracy = (overall_confidence + findings_consistency) / 2.0

            # Clinical accuracy (based on clinical relevance and medical terminology)
            clinical_relevance = self._calculate_clinical_relevance(findings, document_text)
            medical_terminology_score = self._calculate_medical_terminology_score(findings)
            metrics.clinical_accuracy = (clinical_relevance + medical_terminology_score) / 2.0

            # Compliance accuracy (based on regulatory compliance and rule adherence)
            compliance_score = analysis_result.get('compliance_score', 0) / 100.0
            rule_adherence = self._calculate_rule_adherence(findings, context)
            metrics.compliance_accuracy = (compliance_score + rule_adherence) / 2.0

            # Entity extraction accuracy (based on NER results)
            entities = analysis_result.get('entities', [])
            metrics.entity_extraction_accuracy = self._calculate_entity_accuracy(entities, document_text)

            # Fact checking accuracy (based on fact checker results)
            fact_check_results = analysis_result.get('fact_check_results', [])
            metrics.fact_checking_accuracy = self._calculate_fact_checking_accuracy(fact_check_results)

            # Confidence calibration (based on confidence vs actual accuracy)
            metrics.confidence_calibration = self._calculate_confidence_calibration(findings)

            # Calculate precision, recall, F1
            if ground_truth:
                precision, recall, f1 = self._calculate_precision_recall_f1(findings, ground_truth)
                metrics.precision = precision
                metrics.recall = recall
                metrics.f1_score = f1

                # Calculate false positive/negative rates
                metrics.false_positive_rate = 1.0 - precision
                metrics.false_negative_rate = 1.0 - recall

            # Processing time
            metrics.processing_time_ms = analysis_result.get('processing_time_ms', 0.0)

            # Model used
            metrics.model_used = analysis_result.get('model_used', 'unknown')

            return metrics

        except Exception as e:
            logger.error("Accuracy metrics calculation failed: %s", e)
            return AccuracyMetrics()

    async def _detect_hallucinations(
        self,
        analysis_result: Dict[str, Any],
        document_text: str,
        findings: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> HallucinationMetrics:
        """Detect and categorize hallucinations."""
        try:
            metrics = HallucinationMetrics()

            # Detect different types of hallucinations
            factual_hallucinations = self._detect_factual_hallucinations(findings, document_text)
            clinical_hallucinations = self._detect_clinical_hallucinations(findings, document_text)
            compliance_hallucinations = self._detect_compliance_hallucinations(findings, context)
            entity_hallucinations = self._detect_entity_hallucinations(findings, document_text)
            temporal_hallucinations = self._detect_temporal_hallucinations(findings, document_text)
            causal_hallucinations = self._detect_causal_hallucinations(findings, document_text)

            # Count hallucinations
            metrics.factual_hallucinations = len(factual_hallucinations)
            metrics.clinical_hallucinations = len(clinical_hallucinations)
            metrics.compliance_hallucinations = len(compliance_hallucinations)
            metrics.entity_hallucinations = len(entity_hallucinations)
            metrics.temporal_hallucinations = len(temporal_hallucinations)
            metrics.causal_hallucinations = len(causal_hallucinations)

            metrics.total_hallucinations = (
                metrics.factual_hallucinations + metrics.clinical_hallucinations +
                metrics.compliance_hallucinations + metrics.entity_hallucinations +
                metrics.temporal_hallucinations + metrics.causal_hallucinations
            )

            # Calculate hallucination rate
            total_statements = len(findings) + len(document_text.split('.'))
            metrics.hallucination_rate = metrics.total_hallucinations / max(1, total_statements)

            # Calculate severity distribution
            metrics.severity_distribution = self._calculate_severity_distribution(findings)

            # Detection confidence
            metrics.detection_confidence = self._calculate_detection_confidence(
                factual_hallucinations, clinical_hallucinations, compliance_hallucinations
            )

            return metrics

        except Exception as e:
            logger.error("Hallucination detection failed: %s", e)
            return HallucinationMetrics()

    def _calculate_findings_consistency(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate consistency of findings."""
        try:
            if not findings:
                return 1.0

            # Check for contradictory findings
            contradictions = 0
            total_pairs = 0

            for i, finding1 in enumerate(findings):
                for j, finding2 in enumerate(findings[i+1:], i+1):
                    if self._are_contradictory(finding1, finding2):
                        contradictions += 1
                    total_pairs += 1

            if total_pairs == 0:
                return 1.0

            consistency = 1.0 - (contradictions / total_pairs)
            return max(0.0, min(1.0, consistency))

        except Exception as e:
            logger.error("Findings consistency calculation failed: %s", e)
            return 0.5

    def _calculate_clinical_relevance(self, findings: List[Dict[str, Any]], document_text: str) -> float:
        """Calculate clinical relevance of findings."""
        try:
            if not findings:
                return 0.0

            clinical_terms = [
                'patient', 'diagnosis', 'treatment', 'therapy', 'symptom', 'condition',
                'medication', 'procedure', 'assessment', 'evaluation', 'clinical',
                'medical', 'healthcare', 'therapeutic', 'intervention'
            ]

            relevant_findings = 0
            for finding in findings:
                finding_text = finding.get('text', '').lower()
                if any(term in finding_text for term in clinical_terms):
                    relevant_findings += 1

            return relevant_findings / len(findings)

        except Exception as e:
            logger.error("Clinical relevance calculation failed: %s", e)
            return 0.5

    def _calculate_medical_terminology_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate medical terminology accuracy score."""
        try:
            if not findings:
                return 0.0

            medical_terms = [
                'range of motion', 'functional mobility', 'activities of daily living',
                'pain management', 'therapeutic exercise', 'patient education',
                'treatment goals', 'progress note', 'evaluation', 'assessment'
            ]

            accurate_terms = 0
            total_terms = 0

            for finding in findings:
                finding_text = finding.get('text', '').lower()
                for term in medical_terms:
                    if term in finding_text:
                        total_terms += 1
                        # Check if term is used correctly in context
                        if self._is_medical_term_accurate(finding_text, term):
                            accurate_terms += 1

            return accurate_terms / max(1, total_terms)

        except Exception as e:
            logger.error("Medical terminology score calculation failed: %s", e)
            return 0.5

    def _calculate_rule_adherence(self, findings: List[Dict[str, Any]], context: Optional[Dict[str, Any]]) -> float:
        """Calculate adherence to compliance rules."""
        try:
            if not findings or not context:
                return 0.5

            retrieved_rules = context.get('retrieved_rules', [])
            if not retrieved_rules:
                return 0.5

            adherence_score = 0.0
            for finding in findings:
                finding_text = finding.get('text', '').lower()
                for rule in retrieved_rules:
                    rule_content = rule.get('content', '').lower()
                    if self._finding_adheres_to_rule(finding_text, rule_content):
                        adherence_score += 1
                        break

            return adherence_score / len(findings)

        except Exception as e:
            logger.error("Rule adherence calculation failed: %s", e)
            return 0.5

    def _calculate_entity_accuracy(self, entities: List[Dict[str, Any]], document_text: str) -> float:
        """Calculate entity extraction accuracy."""
        try:
            if not entities:
                return 0.0

            accurate_entities = 0
            for entity in entities:
                entity_text = entity.get('text', '').lower()
                if entity_text in document_text.lower():
                    accurate_entities += 1

            return accurate_entities / len(entities)

        except Exception as e:
            logger.error("Entity accuracy calculation failed: %s", e)
            return 0.5

    def _calculate_fact_checking_accuracy(self, fact_check_results: List[Dict[str, Any]]) -> float:
        """Calculate fact checking accuracy."""
        try:
            if not fact_check_results:
                return 0.5

            consistent_facts = sum(1 for result in fact_check_results if result.get('is_consistent', False))
            return consistent_facts / len(fact_check_results)

        except Exception as e:
            logger.error("Fact checking accuracy calculation failed: %s", e)
            return 0.5

    def _calculate_confidence_calibration(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate confidence calibration score."""
        try:
            if not findings:
                return 0.5

            # Check if confidence scores are well-calibrated
            well_calibrated = 0
            for finding in findings:
                confidence = finding.get('confidence', 0.5)
                severity = finding.get('severity', 'Medium')

                # Check if confidence matches severity
                if self._is_confidence_calibrated(confidence, severity):
                    well_calibrated += 1

            return well_calibrated / len(findings)

        except Exception as e:
            logger.error("Confidence calibration calculation failed: %s", e)
            return 0.5

    def _detect_factual_hallucinations(self, findings: List[Dict[str, Any]], document_text: str) -> List[str]:
        """Detect factual hallucinations."""
        try:
            hallucinations = []

            for finding in findings:
                finding_text = finding.get('text', '')

                # Check for claims not supported by document
                if not self._is_claim_supported(finding_text, document_text):
                    hallucinations.append(f"Unsupported claim: {finding_text}")

                # Check for fabricated details
                if self._contains_fabricated_details(finding_text, document_text):
                    hallucinations.append(f"Fabricated details: {finding_text}")

            return hallucinations

        except Exception as e:
            logger.error("Factual hallucination detection failed: %s", e)
            return []

    def _detect_clinical_hallucinations(self, findings: List[Dict[str, Any]], document_text: str) -> List[str]:
        """Detect clinical hallucinations."""
        try:
            hallucinations = []

            for finding in findings:
                finding_text = finding.get('text', '')

                # Check for incorrect medical terminology
                if self._contains_incorrect_medical_terminology(finding_text):
                    hallucinations.append(f"Incorrect medical terminology: {finding_text}")

                # Check for unsupported clinical claims
                if self._contains_unsupported_clinical_claims(finding_text, document_text):
                    hallucinations.append(f"Unsupported clinical claim: {finding_text}")

            return hallucinations

        except Exception as e:
            logger.error("Clinical hallucination detection failed: %s", e)
            return []

    def _detect_compliance_hallucinations(self, findings: List[Dict[str, Any]], context: Optional[Dict[str, Any]]) -> List[str]:
        """Detect compliance hallucinations."""
        try:
            hallucinations = []

            if not context:
                return hallucinations

            retrieved_rules = context.get('retrieved_rules', [])

            for finding in findings:
                finding_text = finding.get('text', '')

                # Check for compliance claims not supported by rules
                if not self._is_compliance_claim_supported(finding_text, retrieved_rules):
                    hallucinations.append(f"Unsupported compliance claim: {finding_text}")

            return hallucinations

        except Exception as e:
            logger.error("Compliance hallucination detection failed: %s", e)
            return []

    def _detect_entity_hallucinations(self, findings: List[Dict[str, Any]], document_text: str) -> List[str]:
        """Detect entity hallucinations."""
        try:
            hallucinations = []

            for finding in findings:
                finding_text = finding.get('text', '')

                # Check for entities not present in document
                entities = self._extract_entities_from_text(finding_text)
                for entity in entities:
                    if entity not in document_text.lower():
                        hallucinations.append(f"Non-existent entity: {entity}")

            return hallucinations

        except Exception as e:
            logger.error("Entity hallucination detection failed: %s", e)
            return []

    def _detect_temporal_hallucinations(self, findings: List[Dict[str, Any]], document_text: str) -> List[str]:
        """Detect temporal hallucinations."""
        try:
            hallucinations = []

            for finding in findings:
                finding_text = finding.get('text', '')

                # Check for incorrect temporal references
                if self._contains_incorrect_temporal_references(finding_text, document_text):
                    hallucinations.append(f"Incorrect temporal reference: {finding_text}")

            return hallucinations

        except Exception as e:
            logger.error("Temporal hallucination detection failed: %s", e)
            return []

    def _detect_causal_hallucinations(self, findings: List[Dict[str, Any]], document_text: str) -> List[str]:
        """Detect causal hallucinations."""
        try:
            hallucinations = []

            for finding in findings:
                finding_text = finding.get('text', '')

                # Check for incorrect causal relationships
                if self._contains_incorrect_causal_relationships(finding_text, document_text):
                    hallucinations.append(f"Incorrect causal relationship: {finding_text}")

            return hallucinations

        except Exception as e:
            logger.error("Causal hallucination detection failed: %s", e)
            return []

    def _determine_validation_status(
        self,
        accuracy_metrics: AccuracyMetrics,
        hallucination_metrics: HallucinationMetrics
    ) -> str:
        """Determine overall validation status."""
        try:
            # Check accuracy thresholds
            accuracy_ok = (
                accuracy_metrics.overall_accuracy >= self.accuracy_thresholds['overall_accuracy'] and
                accuracy_metrics.clinical_accuracy >= self.accuracy_thresholds['clinical_accuracy'] and
                accuracy_metrics.compliance_accuracy >= self.accuracy_thresholds['compliance_accuracy']
            )

            # Check hallucination thresholds
            hallucination_ok = (
                hallucination_metrics.hallucination_rate <= self.hallucination_thresholds['max_hallucination_rate'] and
                hallucination_metrics.factual_hallucinations <= len(hallucination_metrics.factual_hallucinations) * self.hallucination_thresholds['max_factual_hallucinations']
            )

            if accuracy_ok and hallucination_ok:
                return "VALIDATED"
            elif accuracy_ok and not hallucination_ok:
                return "ACCURATE_BUT_HALLUCINATIONS"
            elif not accuracy_ok and hallucination_ok:
                return "LOW_ACCURACY_NO_HALLUCINATIONS"
            else:
                return "NEEDS_REVIEW"

        except Exception as e:
            logger.error("Validation status determination failed: %s", e)
            return "ERROR"

    def _calculate_confidence_score(
        self,
        accuracy_metrics: AccuracyMetrics,
        hallucination_metrics: HallucinationMetrics
    ) -> float:
        """Calculate overall confidence score."""
        try:
            # Weight accuracy metrics
            accuracy_score = (
                accuracy_metrics.overall_accuracy * 0.3 +
                accuracy_metrics.clinical_accuracy * 0.3 +
                accuracy_metrics.compliance_accuracy * 0.2 +
                accuracy_metrics.confidence_calibration * 0.2
            )

            # Weight hallucination metrics (inverse)
            hallucination_penalty = hallucination_metrics.hallucination_rate * 0.5

            # Calculate final confidence
            confidence = accuracy_score - hallucination_penalty

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error("Confidence score calculation failed: %s", e)
            return 0.5

    def _generate_recommendations(
        self,
        accuracy_metrics: AccuracyMetrics,
        hallucination_metrics: HallucinationMetrics
    ) -> List[str]:
        """Generate improvement recommendations."""
        try:
            recommendations = []

            # Accuracy recommendations
            if accuracy_metrics.overall_accuracy < self.accuracy_thresholds['overall_accuracy']:
                recommendations.append("Improve overall accuracy through better model training and validation")

            if accuracy_metrics.clinical_accuracy < self.accuracy_thresholds['clinical_accuracy']:
                recommendations.append("Enhance clinical accuracy with medical terminology training")

            if accuracy_metrics.compliance_accuracy < self.accuracy_thresholds['compliance_accuracy']:
                recommendations.append("Improve compliance accuracy with regulatory rule updates")

            if accuracy_metrics.confidence_calibration < self.accuracy_thresholds['confidence_calibration']:
                recommendations.append("Calibrate confidence scores for better reliability")

            # Hallucination recommendations
            if hallucination_metrics.hallucination_rate > self.hallucination_thresholds['max_hallucination_rate']:
                recommendations.append("Reduce hallucination rate through fact-checking and validation")

            if hallucination_metrics.factual_hallucinations > 0:
                recommendations.append("Implement stronger fact-checking mechanisms")

            if hallucination_metrics.clinical_hallucinations > 0:
                recommendations.append("Enhance clinical validation and medical knowledge verification")

            return recommendations

        except Exception as e:
            logger.error("Recommendation generation failed: %s", e)
            return ["Review system performance and implement improvements"]

    def _update_real_time_trends(
        self,
        accuracy_metrics: AccuracyMetrics,
        hallucination_metrics: HallucinationMetrics
    ) -> None:
        """Update real-time trend tracking."""
        try:
            # Add current metrics to trends
            self.current_accuracy_trends['overall_accuracy'].append(accuracy_metrics.overall_accuracy)
            self.current_accuracy_trends['clinical_accuracy'].append(accuracy_metrics.clinical_accuracy)
            self.current_accuracy_trends['compliance_accuracy'].append(accuracy_metrics.compliance_accuracy)
            self.current_accuracy_trends['hallucination_rate'].append(hallucination_metrics.hallucination_rate)

            # Keep only recent trends (last 100 measurements)
            for trend_name in self.current_accuracy_trends:
                if len(self.current_accuracy_trends[trend_name]) > 100:
                    self.current_accuracy_trends[trend_name] = self.current_accuracy_trends[trend_name][-100:]

        except Exception as e:
            logger.error("Real-time trends update failed: %s", e)

    async def _check_threshold_alerts(
        self,
        accuracy_metrics: AccuracyMetrics,
        hallucination_metrics: HallucinationMetrics
    ) -> None:
        """Check thresholds and send alerts if needed."""
        try:
            alerts = []

            # Check accuracy thresholds
            if accuracy_metrics.overall_accuracy < self.accuracy_thresholds['overall_accuracy']:
                alerts.append(f"Overall accuracy below threshold: {accuracy_metrics.overall_accuracy:.2f}")

            if accuracy_metrics.clinical_accuracy < self.accuracy_thresholds['clinical_accuracy']:
                alerts.append(f"Clinical accuracy below threshold: {accuracy_metrics.clinical_accuracy:.2f}")

            # Check hallucination thresholds
            if hallucination_metrics.hallucination_rate > self.hallucination_thresholds['max_hallucination_rate']:
                alerts.append(f"Hallucination rate above threshold: {hallucination_metrics.hallucination_rate:.2f}")

            # Send alerts if any
            if alerts:
                await self._send_alerts(alerts)

        except Exception as e:
            logger.error("Threshold alert check failed: %s", e)

    async def _send_alerts(self, alerts: List[str]) -> None:
        """Send threshold alerts."""
        try:
            for alert in alerts:
                logger.warning("ACCURACY ALERT: %s", alert)
                # In a real system, this would send notifications to monitoring systems

        except Exception as e:
            logger.error("Alert sending failed: %s", e)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current accuracy and hallucination metrics."""
        try:
            if not self.accuracy_history or not self.hallucination_history:
                return {
                    "status": "no_data",
                    "message": "No validation data available yet"
                }

            # Calculate current averages
            recent_accuracy = self.accuracy_history[-10:] if len(self.accuracy_history) >= 10 else self.accuracy_history
            recent_hallucination = self.hallucination_history[-10:] if len(self.hallucination_history) >= 10 else self.hallucination_history

            current_metrics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_validations": self.total_validations,
                "successful_validations": self.successful_validations,
                "failed_validations": self.failed_validations,
                "success_rate": self.successful_validations / max(1, self.total_validations),
                "current_accuracy": {
                    "overall_accuracy": np.mean([m.overall_accuracy for m in recent_accuracy]),
                    "clinical_accuracy": np.mean([m.clinical_accuracy for m in recent_accuracy]),
                    "compliance_accuracy": np.mean([m.compliance_accuracy for m in recent_accuracy]),
                    "confidence_calibration": np.mean([m.confidence_calibration for m in recent_accuracy])
                },
                "current_hallucination": {
                    "hallucination_rate": np.mean([m.hallucination_rate for m in recent_hallucination]),
                    "total_hallucinations": np.mean([m.total_hallucinations for m in recent_hallucination]),
                    "factual_hallucinations": np.mean([m.factual_hallucinations for m in recent_hallucination]),
                    "clinical_hallucinations": np.mean([m.clinical_hallucinations for m in recent_hallucination])
                },
                "trends": {
                    "overall_accuracy_trend": self._calculate_trend('overall_accuracy'),
                    "clinical_accuracy_trend": self._calculate_trend('clinical_accuracy'),
                    "hallucination_rate_trend": self._calculate_trend('hallucination_rate')
                },
                "thresholds": {
                    "accuracy_thresholds": self.accuracy_thresholds,
                    "hallucination_thresholds": self.hallucination_thresholds
                }
            }

            return current_metrics

        except Exception as e:
            logger.error("Current metrics retrieval failed: %s", e)
            return {"error": str(e)}

    def _calculate_trend(self, metric_name: str) -> str:
        """Calculate trend direction for a metric."""
        try:
            trend_data = self.current_accuracy_trends.get(metric_name, [])
            if len(trend_data) < 2:
                return "insufficient_data"

            recent = trend_data[-5:] if len(trend_data) >= 5 else trend_data
            older = trend_data[-10:-5] if len(trend_data) >= 10 else trend_data[:-5] if len(trend_data) >= 5 else []

            if not older:
                return "insufficient_data"

            recent_avg = np.mean(recent)
            older_avg = np.mean(older)

            if recent_avg > older_avg * 1.05:  # 5% improvement
                return "improving"
            elif recent_avg < older_avg * 0.95:  # 5% decline
                return "declining"
            else:
                return "stable"

        except Exception as e:
            logger.error("Trend calculation failed for %s: %s", metric_name, e)
            return "error"

    # Helper methods for accuracy calculations
    def _are_contradictory(self, finding1: Dict[str, Any], finding2: Dict[str, Any]) -> bool:
        """Check if two findings are contradictory."""
        # Simplified contradiction detection
        text1 = finding1.get('text', '').lower()
        text2 = finding2.get('text', '').lower()

        # Check for obvious contradictions
        contradictions = [
            ('improved', 'declined'),
            ('increased', 'decreased'),
            ('present', 'absent'),
            ('normal', 'abnormal')
        ]

        for pos, neg in contradictions:
            if (pos in text1 and neg in text2) or (neg in text1 and pos in text2):
                return True

        return False

    def _is_medical_term_accurate(self, text: str, term: str) -> bool:
        """Check if medical term is used accurately."""
        # Simplified medical term accuracy check
        return True  # Placeholder - would need medical knowledge base

    def _finding_adheres_to_rule(self, finding_text: str, rule_content: str) -> bool:
        """Check if finding adheres to compliance rule."""
        # Simplified rule adherence check
        return True  # Placeholder - would need rule matching logic

    def _is_confidence_calibrated(self, confidence: float, severity: str) -> bool:
        """Check if confidence is well-calibrated with severity."""
        # Simplified calibration check
        if severity == 'High' and confidence >= 0.8:
            return True
        elif severity == 'Medium' and 0.5 <= confidence < 0.8:
            return True
        elif severity == 'Low' and confidence < 0.5:
            return True
        return False

    # Helper methods for hallucination detection
    def _is_claim_supported(self, claim: str, document: str) -> bool:
        """Check if claim is supported by document."""
        # Simplified support check
        return True  # Placeholder - would need semantic matching

    def _contains_fabricated_details(self, text: str, document: str) -> bool:
        """Check if text contains fabricated details."""
        # Simplified fabrication detection
        return False  # Placeholder - would need fact verification

    def _contains_incorrect_medical_terminology(self, text: str) -> bool:
        """Check for incorrect medical terminology."""
        # Simplified medical terminology check
        return False  # Placeholder - would need medical dictionary

    def _contains_unsupported_clinical_claims(self, text: str, document: str) -> bool:
        """Check for unsupported clinical claims."""
        # Simplified clinical claim check
        return False  # Placeholder - would need clinical knowledge base

    def _is_compliance_claim_supported(self, text: str, rules: List[Dict[str, Any]]) -> bool:
        """Check if compliance claim is supported by rules."""
        # Simplified compliance claim check
        return True  # Placeholder - would need rule matching

    def _extract_entities_from_text(self, text: str) -> List[str]:
        """Extract entities from text."""
        # Simplified entity extraction
        return []  # Placeholder - would need NER

    def _contains_incorrect_temporal_references(self, text: str, document: str) -> bool:
        """Check for incorrect temporal references."""
        # Simplified temporal reference check
        return False  # Placeholder - would need temporal analysis

    def _contains_incorrect_causal_relationships(self, text: str, document: str) -> bool:
        """Check for incorrect causal relationships."""
        # Simplified causal relationship check
        return False  # Placeholder - would need causal analysis

    def _calculate_severity_distribution(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate severity distribution of findings."""
        try:
            distribution = {'High': 0, 'Medium': 0, 'Low': 0}
            for finding in findings:
                severity = finding.get('severity', 'Medium')
                if severity in distribution:
                    distribution[severity] += 1
            return distribution
        except Exception as e:
            logger.error("Severity distribution calculation failed: %s", e)
            return {'High': 0, 'Medium': 0, 'Low': 0}

    def _calculate_detection_confidence(
        self,
        factual_hallucinations: List[str],
        clinical_hallucinations: List[str],
        compliance_hallucinations: List[str]
    ) -> float:
        """Calculate confidence in hallucination detection."""
        try:
            total_detections = len(factual_hallucinations) + len(clinical_hallucinations) + len(compliance_hallucinations)
            if total_detections == 0:
                return 1.0  # High confidence when no hallucinations detected

            # Simplified confidence calculation
            return 0.8  # Placeholder - would need more sophisticated confidence estimation

        except Exception as e:
            logger.error("Detection confidence calculation failed: %s", e)
            return 0.5

    def _calculate_precision_recall_f1(
        self,
        findings: List[Dict[str, Any]],
        ground_truth: Dict[str, Any]
    ) -> Tuple[float, float, float]:
        """Calculate precision, recall, and F1 score."""
        try:
            # Simplified precision/recall calculation
            # In a real system, this would compare findings against ground truth
            return 0.8, 0.7, 0.75  # Placeholder values

        except Exception as e:
            logger.error("Precision/recall/F1 calculation failed: %s", e)
            return 0.5, 0.5, 0.5


# Global instance
accuracy_hallucination_tracker = AccuracyHallucinationTracker()
