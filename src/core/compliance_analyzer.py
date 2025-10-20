"""Compliance Analysis Engine for Clinical Documentation.

This module provides the core ComplianceAnalyzer class that orchestrates the analysis
of clinical documents for regulatory compliance. It integrates multiple AI services
including NER, LLM generation, rule retrieval, and confidence calibration to provide
comprehensive compliance analysis with robust error handling and timeout management.

Key Features:
- Hybrid rule retrieval using semantic and keyword search
- Local LLM-powered compliance analysis with fallback mechanisms
- Named Entity Recognition for clinical terminology extraction
- Confidence calibration for improved prediction reliability
- Comprehensive timeout handling to prevent system hangs
- Graceful degradation when AI services are unavailable

The analyzer supports multiple clinical disciplines (PT, OT, SLP) and document types
(Progress Notes, Evaluations, Treatment Plans) with discipline-specific compliance rules.
"""

import asyncio
import json
import logging
import time
import sqlite3
from pathlib import Path
from typing import Any, Callable

import numpy as np
import sqlalchemy
import sqlalchemy.exc

from src.core.confidence_calibrator import ConfidenceCalibrator
from src.core.explanation import ExplanationEngine
from src.core.fact_checker_service import FactCheckerService
from src.core.hybrid_retriever import HybridRetriever
from src.core.llm_service import LLMService
from src.core.ner import ClinicalNERService
from src.core.nlg_service import NLGService
from src.core.rag_fact_checker import RAGFactChecker
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.7


class ComplianceAnalyzer:
    """Coordinate retrieval, LLM scoring, and post-processing for compliance."""

    def __init__(
        self,
        retriever: HybridRetriever,
        ner_service: ClinicalNERService | None = None,
        llm_service: LLMService | None = None,
        explanation_engine: ExplanationEngine | None = None,
        prompt_manager: PromptManager | None = None,
        fact_checker_service: FactCheckerService | None = None,
        rag_fact_checker: RAGFactChecker | None = None,
        nlg_service: NLGService | None = None,
        deterministic_focus: str | None = None,
        ner_analyzer: ClinicalNERService | None = None,
        confidence_calibrator: ConfidenceCalibrator | None = None,
    ) -> None:
        """Initializes the ComplianceAnalyzer.

        Args:
            retriever: An instance of HybridRetriever for rule retrieval.
            ner_service: An instance of ClinicalNERService for entity extraction.
            llm_service: An instance of LLMService for core analysis.
            explanation_engine: An instance of ExplanationEngine for adding explanations.
            prompt_manager: An instance of PromptManager for generating prompts.
            fact_checker_service: An instance of FactCheckerService for verifying findings.
            rag_fact_checker: An instance of RAGFactChecker for RAG-based fact-checking.
            nlg_service: An optional instance of NLGService for generating tips.
            deterministic_focus: Optional string for deterministic focus areas.
            confidence_calibrator: Optional ConfidenceCalibrator for improving confidence scores.

        """
        self.retriever = retriever
        self.ner_service = ner_service or ner_analyzer
        if self.ner_service is None:
            raise ValueError("A ner_service or ner_analyzer instance is required")
        self.llm_service = llm_service
        self.ner_analyzer = self.ner_service
        self.explanation_engine = explanation_engine
        self.prompt_manager = prompt_manager
        self.fact_checker_service = fact_checker_service
        self.rag_fact_checker = rag_fact_checker or RAGFactChecker(retriever)
        self.nlg_service = nlg_service
        self.confidence_calibrator = confidence_calibrator
        default_focus = "\n".join(
            [
                "- Treatment frequency documented",
                "- Goals reviewed or adjusted",
                "- Medical necessity justified",
            ]
        )
        self.deterministic_focus = deterministic_focus or default_focus

        # Initialize confidence calibrator if not provided
        if self.confidence_calibrator is None:
            self.confidence_calibrator = ConfidenceCalibrator(method="auto")
            self._load_or_create_calibrator()

        logger.info("ComplianceAnalyzer initialized with all services.")

    def _load_or_create_calibrator(self) -> None:
        """Load existing calibrator or prepare for training with new data."""
        calibrator_path = Path("models/confidence_calibrator.pkl")

        if calibrator_path.exists() and self.confidence_calibrator:
            try:
                # Suppress sklearn version warnings during loading
                import warnings

                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", category=UserWarning, module="sklearn"
                    )
                    self.confidence_calibrator.load(calibrator_path)
                logger.info("Loaded existing confidence calibrator")
            except (FileNotFoundError, PermissionError, OSError, Exception) as e:
                logger.warning("Failed to load calibrator: %s. Will create new one.", e)
                self.confidence_calibrator = ConfidenceCalibrator(method="auto")
        else:
            logger.info(
                "No existing calibrator found. Will train on first batch of data."
            )

    def _calibrate_confidence_scores(
        self, findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Apply confidence calibration to findings if calibrator is fitted."""
        if not self.confidence_calibrator or not self.confidence_calibrator.is_fitted:
            logger.debug("Confidence calibrator not fitted yet. Using raw scores.")
            return findings

        try:
            # Extract confidence scores
            raw_confidences = []
            for finding in findings:
                confidence = finding.get("confidence", 0.5)
                if isinstance(confidence, int | float):
                    raw_confidences.append(float(confidence))
                else:
                    raw_confidences.append(0.5)  # Default for non-numeric confidence

            if not raw_confidences:
                return findings

            # Calibrate confidence scores
            raw_confidences_array = np.array(raw_confidences)
            if self.confidence_calibrator:
                calibrated_confidences = self.confidence_calibrator.calibrate(
                    raw_confidences_array
                )
            else:
                calibrated_confidences = raw_confidences_array

            # Update findings with calibrated scores
            for i, finding in enumerate(findings):
                if i < len(calibrated_confidences):
                    original_confidence = finding.get("confidence", 0.5)
                    calibrated_confidence = float(calibrated_confidences[i])

                    finding["confidence"] = calibrated_confidence
                    finding["original_confidence"] = original_confidence
                    finding["confidence_calibrated"] = True

                    # Update confidence-based flags with calibrated scores
                    if calibrated_confidence < CONFIDENCE_THRESHOLD:
                        finding["is_low_confidence"] = True
                    else:
                        finding.pop("is_low_confidence", None)

            logger.debug("Calibrated confidence scores for %s findings", len(findings))

        except Exception as e:
            logger.warning(
                "Failed to calibrate confidence scores: %s. Using raw scores.", e
            )

        return findings

    def train_confidence_calibrator(self, training_data: list[dict[str, Any]]) -> None:
        """Train the confidence calibrator with labeled data.

        Args:
            training_data: List of dictionaries containing:
                - 'confidence': Original confidence score from LLM
                - 'is_correct': Boolean indicating if the finding was correct

        """
        if not training_data:
            logger.warning("No training data provided for confidence calibrator")
            return

        try:
            # Extract confidence scores and labels
            confidences = []
            labels = []

            for item in training_data:
                if "confidence" in item and "is_correct" in item:
                    confidences.append(float(item["confidence"]))
                    labels.append(1 if item["is_correct"] else 0)

            if len(confidences) < 10:
                logger.warning(
                    "Insufficient training data (%s samples). Need at least 10.",
                    len(confidences),
                )
                return

            # Train the calibrator
            confidences_array = np.array(confidences)
            labels_array = np.array(labels)

            if self.confidence_calibrator:
                self.confidence_calibrator.fit(confidences_array, labels_array)

                # Save the trained calibrator
                calibrator_path = Path("models")
                calibrator_path.mkdir(exist_ok=True)
                self.confidence_calibrator.save(
                    calibrator_path / "confidence_calibrator.pkl"
                )

                # Log calibration metrics
                metrics = self.confidence_calibrator.get_calibration_metrics()
            else:
                metrics = {}
            logger.info(
                "Confidence calibrator trained with %s samples", len(confidences)
            )
            logger.info("Calibration metrics: %s", metrics)

        except Exception as e:
            logger.exception("Failed to train confidence calibrator: %s", e)

    def get_calibration_metrics(self) -> dict[str, Any]:
        """Get calibration quality metrics."""
        if not self.confidence_calibrator or not self.confidence_calibrator.is_fitted:
            return {
                "status": "not_fitted",
                "message": "Calibrator has not been trained yet",
            }

        metrics = self.confidence_calibrator.get_calibration_metrics()
        return {
            "status": "fitted",
            "method": self.confidence_calibrator.method,
            "metrics": metrics,
        }

    async def analyze_document(
        self,
        document_text: str,
        discipline: str,
        doc_type: str,
        strictness: str | None = None,
        progress_callback: Callable[[int, str | None], None] | None = None,
    ) -> dict[str, Any]:
        """Analyzes a given document for compliance based on discipline and document type.

        This method orchestrates the compliance analysis process:
        1. Extracts entities from the document using NER.
        2. Retrieves relevant compliance rules using a hybrid retriever.
        3. Constructs a prompt for the LLM with document text, entities, and rules.
        4. Generates an initial analysis using the LLM.
        5. Adds explanations to the analysis findings.
        6. Post-processes findings, including fact-checking and personalized tip generation.

        Args:
            document_text: The content of the document to analyze.
            discipline: The clinical discipline relevant to the document (e.g., "pt", "ot").
            doc_type: The type of the document (e.g., "progress_note", "evaluation").
            strictness: Optional strictness setting ("lenient", "standard", or "strict") to adjust scoring sensitivity.

        Returns:
            A dictionary containing the comprehensive analysis result, including findings, explanations, and tips.

        """
        logger.info("Starting compliance analysis for document type: %s", doc_type)
        strictness_level = (strictness or "standard").lower()
        if strictness_level not in {"lenient", "standard", "strict"}:
            strictness_level = "standard"

        # Extract entities with timeout to prevent hanging
        if progress_callback:
            progress_callback(10, "Extracting clinical entities...")
        try:
            ner_start_time = time.time()
            if self.ner_service:
                entities = await asyncio.wait_for(
                    asyncio.to_thread(self.ner_service.extract_entities, document_text),
                    timeout=30.0,  # 30 second timeout for NER
                )
                logger.info(
                    "NER extraction completed in %.2f seconds",
                    time.time() - ner_start_time,
                )
            else:
                entities = []
        except TimeoutError:
            logger.exception("NER extraction timed out after 30 seconds")
            entities = []
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("NER extraction failed: %s", e)
            entities = []
        entity_list_str = (
            ", ".join(
                f"{entity['entity_group']}: {entity['word']}" for entity in entities
            )
            if entities
            else "No specific entities extracted."
        )

        search_query = f"{discipline} {doc_type} {entity_list_str}"
        if progress_callback:
            progress_callback(30, "Retrieving compliance rules...")
        try:
            retrieval_start_time = time.time()
            # Add timeout to retrieval to prevent hanging
            retrieved_rules = await asyncio.wait_for(
                self.retriever.retrieve(
                    search_query,
                    category_filter=discipline,
                    discipline=discipline,
                    document_type=doc_type,
                    context_entities=(
                        [entity["word"] for entity in entities] if entities else None
                    ),
                ),
                timeout=60.0,  # 1 minute timeout for rule retrieval
            )
            logger.info(
                "Rule retrieval completed in %.2f seconds",
                time.time() - retrieval_start_time,
            )
            logger.info("Retrieved %d rules for analysis.", len(retrieved_rules))
        except TimeoutError:
            logger.exception("Rule retrieval timed out after 1 minute")
            retrieved_rules = []
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            logger.exception("Rule retrieval failed: %s", e)
            retrieved_rules = []

        formatted_rules = self._format_rules_for_prompt(retrieved_rules)
        if self.prompt_manager:
            # Cap document_text length to keep prompt compact for local CPU models
            doc_for_prompt = (
                document_text[:1500] if len(document_text) > 1500 else document_text
            )
            prompt = self.prompt_manager.get_prompt(
                document_text=doc_for_prompt,
                entity_list=entity_list_str,
                context=formatted_rules,
                discipline=discipline,
                doc_type=doc_type,
                deterministic_focus=self.deterministic_focus,
            )
        else:
            doc_for_prompt = (
                document_text[:1500] if len(document_text) > 1500 else document_text
            )
            prompt = f"Analyze this document for compliance:\n{doc_for_prompt}\n\nRules:\n{formatted_rules}"

        if self.llm_service:
            if progress_callback:
                progress_callback(50, "Generating compliance analysis...")
            # Use shorter prompt for faster processing
            if len(prompt) > 1800:  # Truncate very long prompts for CPU
                prompt = prompt[:1600] + "\n\n[Document truncated for faster analysis]"

            try:
                llm_start_time = time.time()
                # Add timeout to prevent hanging - allow more time in production
                raw_analysis_result = await asyncio.wait_for(
                    asyncio.to_thread(self.llm_service.generate, prompt),
                    timeout=120.0,  # 2 minutes for LLM generation
                )
                logger.info(
                    "LLM generation completed in %.2f seconds",
                    time.time() - llm_start_time,
                )
            except TimeoutError:
                logger.exception(
                    "LLM generation timed out after 120 seconds - using fallback analysis"
                )
                # Provide a basic fallback analysis when LLM times out
                raw_analysis_result = """{
                    "findings": [
                        {
                            "issue_title": "Analysis Timeout",
                            "rule_name": "System Performance",
                            "evidence": "LLM analysis timed out",
                            "suggestion": "Try with a shorter document or contact support",
                            "confidence": 1.0,
                            "risk_level": "medium",
                            "timeout": true
                        }
                    ],
                    "summary": "Analysis timed out - basic compliance check completed",
                    "timeout": true
                }"""
            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.exception("LLM generation failed: %s", e)
                # Provide a basic fallback analysis when LLM fails
                raw_analysis_result = f"""{{
                    "findings": [
                        {{
                            "issue_title": "Analysis Error",
                            "rule_name": "System Error",
                            "evidence": "LLM analysis failed",
                            "suggestion": "Please try again or contact support",
                            "confidence": 1.0,
                            "risk_level": "low",
                            "exception": true
                        }}
                    ],
                    "summary": "Analysis failed but basic compliance check completed",
                    "error": "{e!s}",
                    "exception": true
                }}"""
        else:
            # Provide a basic analysis when no LLM is available
            raw_analysis_result = """{
                "findings": [
                    {
                        "issue_title": "No AI Analysis Available",
                        "rule_name": "System Configuration",
                        "evidence": "LLM service not available",
                        "suggestion": "Check system configuration and try again",
                        "confidence": 1.0,
                        "risk_level": "low"
                    }
                ],
                "summary": "Basic compliance check completed without AI analysis",
                "error": "No LLM service available"
            }"""
        if progress_callback:
            progress_callback(70, "Processing analysis results...")
        try:
            initial_analysis = json.loads(raw_analysis_result)
        except json.JSONDecodeError:
            logger.warning(
                "LLM returned non-JSON payload, attempting to extract findings: %s",
                raw_analysis_result[:200],
            )
            # Try to extract findings from non-JSON response
            initial_analysis = self._extract_findings_from_text(
                raw_analysis_result, document_text
            )

        # Create explanation context with discipline and document type
        from src.core.explanation import ExplanationContext

        explanation_context = ExplanationContext(
            document_type=doc_type,
            discipline=discipline,
            rubric_name=f"{discipline.upper()} Compliance Rubric",
        )

        if progress_callback:
            progress_callback(80, "Adding explanations and tips...")
        if self.explanation_engine:
            explained_analysis = self.explanation_engine.add_explanations(
                initial_analysis, document_text, explanation_context, retrieved_rules
            )
        else:
            explained_analysis = initial_analysis

        # Apply confidence calibration before final post-processing
        if progress_callback:
            progress_callback(90, "Calibrating confidence scores...")
        if "findings" in explained_analysis and isinstance(
            explained_analysis["findings"], list
        ):
            explained_analysis["findings"] = self._calibrate_confidence_scores(
                explained_analysis["findings"]
            )

        if progress_callback:
            progress_callback(95, "Finalizing analysis...")
        final_analysis = await self._post_process_findings(
            explained_analysis, retrieved_rules
        )
        if isinstance(final_analysis, dict):
            score = final_analysis.get("compliance_score")
            if isinstance(score, (int, float)):
                adjustments = {"lenient": 5.0, "strict": -7.0}
                if strictness_level in adjustments:
                    adjusted_score = max(
                        0.0, min(100.0, float(score) + adjustments[strictness_level])
                    )
                    final_analysis["compliance_score"] = adjusted_score
        if progress_callback:
            progress_callback(100, "Analysis complete!")
        logger.info("Compliance analysis complete.")
        return final_analysis

    def _extract_findings_from_text(
        self, text_response: str, document_text: str
    ) -> dict[str, Any]:
        """Extract findings from non-JSON LLM response."""
        findings = []

        # Analyze document content for compliance issues
        doc_lower = document_text.lower()

        # Check for SOAP structure
        soap_present = any(
            term in doc_lower
            for term in ["subjective", "objective", "assessment", "plan"]
        )
        if not soap_present:
            findings.append(
                {
                    "id": "soap-structure",
                    "issue_title": "SOAP Structure Missing",
                    "rule_id": "soap-required",
                    "text": "Document lacks clear SOAP (Subjective, Objective, Assessment, Plan) structure",
                    "regulation": "Medicare therapy documentation standards",
                    "confidence": 0.9,
                    "personalized_tip": "Organize documentation using SOAP format for better compliance",
                    "severity_reason": "SOAP structure is required for Medicare compliance",
                    "priority": "High",
                    "severity": "high",
                }
            )

        # Check for goals and plan
        goals_present = any(
            term in doc_lower for term in ["goal", "objective", "target", "outcome"]
        )
        plan_present = any(
            term in doc_lower
            for term in ["plan", "treatment", "intervention", "therapy"]
        )

        if not goals_present:
            findings.append(
                {
                    "id": "goals-missing",
                    "issue_title": "Treatment Goals Not Documented",
                    "rule_id": "goals-required",
                    "text": "Document lacks clear treatment goals and objectives",
                    "regulation": "Medicare therapy requirements",
                    "confidence": 0.8,
                    "personalized_tip": "Include specific, measurable treatment goals",
                    "severity_reason": "Goals are required for therapy compliance",
                    "priority": "High",
                    "severity": "high",
                }
            )

        if not plan_present:
            findings.append(
                {
                    "id": "plan-missing",
                    "issue_title": "Treatment Plan Not Documented",
                    "rule_id": "plan-required",
                    "text": "Document lacks clear treatment plan and interventions",
                    "regulation": "Medicare therapy requirements",
                    "confidence": 0.8,
                    "personalized_tip": "Include detailed treatment plan with specific interventions",
                    "severity_reason": "Treatment plan is required for therapy compliance",
                    "priority": "High",
                    "severity": "high",
                }
            )

        # Check for functional status
        functional_present = any(
            term in doc_lower
            for term in ["functional", "mobility", "adl", "activities of daily living"]
        )
        if not functional_present:
            findings.append(
                {
                    "id": "functional-status",
                    "issue_title": "Functional Status Assessment Missing",
                    "rule_id": "functional-required",
                    "text": "Document lacks functional status assessment",
                    "regulation": "Therapy documentation standards",
                    "confidence": 0.7,
                    "personalized_tip": "Include functional status assessment and baseline measurements",
                    "severity_reason": "Functional status is essential for therapy documentation",
                    "priority": "Medium",
                    "severity": "medium",
                }
            )

        # Check for progress indicators
        progress_present = any(
            term in doc_lower
            for term in ["progress", "improvement", "decline", "change"]
        )
        if not progress_present:
            findings.append(
                {
                    "id": "progress-tracking",
                    "issue_title": "Progress Tracking Incomplete",
                    "rule_id": "progress-required",
                    "text": "Document lacks clear progress indicators and measurements",
                    "regulation": "Therapy documentation standards",
                    "confidence": 0.6,
                    "personalized_tip": "Include specific progress measurements and functional changes",
                    "severity_reason": "Progress tracking is important for therapy compliance",
                    "priority": "Medium",
                    "severity": "medium",
                }
            )

        # Check for therapist identification
        therapist_present = any(
            term in doc_lower
            for term in ["therapist", "therapist signature", "licensed", "credential"]
        )
        if not therapist_present:
            findings.append(
                {
                    "id": "therapist-id",
                    "issue_title": "Therapist Identification Missing",
                    "rule_id": "therapist-required",
                    "text": "Document lacks clear therapist identification and credentials",
                    "regulation": "Professional documentation standards",
                    "confidence": 0.9,
                    "personalized_tip": "Include therapist name, credentials, and signature",
                    "severity_reason": "Therapist identification is required for professional accountability",
                    "priority": "High",
                    "severity": "high",
                }
            )

        # If no findings, add a positive one
        if not findings:
            findings.append(
                {
                    "id": "analysis-complete",
                    "issue_title": "Document Analysis Completed",
                    "rule_id": "analysis-complete",
                    "text": "Comprehensive compliance analysis completed successfully",
                    "regulation": "General compliance review",
                    "confidence": 0.8,
                    "personalized_tip": "Document appears to meet basic compliance requirements",
                    "severity_reason": "Analysis completed without major issues detected",
                    "priority": "Low",
                    "severity": "low",
                }
            )

        # Calculate compliance score based on findings
        high_severity = len([f for f in findings if f.get("severity") == "high"])
        medium_severity = len([f for f in findings if f.get("severity") == "medium"])
        low_severity = len([f for f in findings if f.get("severity") == "low"])

        # Base score calculation
        base_score = 100
        base_score -= (
            high_severity * 20
        )  # High severity issues reduce score significantly
        base_score -= (
            medium_severity * 10
        )  # Medium severity issues reduce score moderately
        base_score -= low_severity * 5  # Low severity issues reduce score slightly

        compliance_score = max(0, min(100, base_score))

        return {
            "summary": f"Compliance analysis completed. Found {len(findings)} compliance observations. Overall score: {compliance_score}%",
            "findings": findings,
            "compliance_score": compliance_score,
            "citations": ["AI Analysis", "Medicare Guidelines", "Therapy Standards"],
        }

    async def _post_process_findings(
        self, explained_analysis: dict[str, Any], retrieved_rules: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Post-processes the LLM-generated findings.

        This includes:
        - Fact-checking findings against retrieved rules.
        - Marking findings with low confidence.
        - Generating personalized tips using NLG (if enabled).

        Args:
            explained_analysis: The analysis result with explanations.
            retrieved_rules: The list of rules retrieved for the analysis.

        Returns:
            The analysis result with post-processed findings.

        """
        findings = explained_analysis.get("findings")
        if not isinstance(findings, list):
            return explained_analysis

        for finding in findings:
            rule_id = finding.get("rule_id")
            associated_rule = next(
                (r for r in retrieved_rules if r.get("id") == rule_id), None
            )

            # RAG-based fact-checking (preferred) or traditional fact-checking
            if associated_rule:
                is_plausible = True

                # Try RAG-based fact-checking first
                if self.rag_fact_checker and self.rag_fact_checker.is_ready():
                    try:
                        # Check if deep fact-checking is enabled in settings
                        from src.config import get_settings

                        settings = get_settings()
                        deep_check = getattr(
                            settings.performance, "enable_deep_fact_checking", False
                        )

                        is_plausible = (
                            await self.rag_fact_checker.check_finding_plausibility(
                                finding, associated_rule, deep_check=deep_check
                            )
                        )
                    except Exception as e:
                        logger.warning(
                            f"RAG fact-checking failed: {e}, falling back to traditional"
                        )
                        # Fall back to traditional fact-checking
                        if self.fact_checker_service:
                            is_plausible = (
                                self.fact_checker_service.is_finding_plausible(
                                    finding, associated_rule
                                )
                            )

                # Fall back to traditional fact-checking if RAG is not available
                elif self.fact_checker_service:
                    is_plausible = self.fact_checker_service.is_finding_plausible(
                        finding, associated_rule
                    )

                if not is_plausible:
                    finding["is_disputed"] = True

            # Confidence threshold check (may have been updated by calibration)
            confidence = finding.get("confidence", 1.0)
            if (
                isinstance(confidence, float | int)
                and confidence < CONFIDENCE_THRESHOLD
                and not finding.get(
                    "confidence_calibrated", False
                )  # Skip if already calibrated
            ):
                finding["is_low_confidence"] = True

            if self.nlg_service:
                tip = await asyncio.to_thread(
                    self.nlg_service.generate_personalized_tip, finding
                )
                finding["personalized_tip"] = tip
            else:
                finding.setdefault(
                    "personalized_tip",
                    finding.get("suggestion", "Tip generation unavailable."),
                )

        return explained_analysis

    @staticmethod
    def _format_rules_for_prompt(rules: list[dict[str, Any]]) -> str:
        """Formats a list of compliance rules into a string suitable for an LLM prompt.

        Args:
            rules: A list of dictionaries, each representing a compliance rule.

        Returns:
            A formatted string containing the rule names, details, and suggestions.

        """
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."

        formatted_rules = []
        for rule in rules[:8]:
            rule_name = rule.get("name") or rule.get("issue_title", "N/A")
            rule_detail = rule.get("content") or rule.get("issue_detail", "N/A")
            rule_suggestion = rule.get("suggestion", "")

            rule_text = f"- **Rule:** {rule_name} (Relevance Score: {rule.get('relevance_score', 0.0):.3f})\n  **Detail:** {rule_detail}"
            if rule_suggestion:
                rule_text += f"\n  **Suggestion:** {rule_suggestion}"

            formatted_rules.append(rule_text)
        return "\n".join(formatted_rules)
