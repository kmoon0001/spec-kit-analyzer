import json
import logging
import asyncio
import numpy as np
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.llm_service import LLMService
from src.core.nlg_service import NLGService
from src.core.ner import ClinicalNERService
from src.core.explanation import ExplanationEngine
from src.utils.prompt_manager import PromptManager
from src.core.fact_checker_service import FactCheckerService
from src.core.hybrid_retriever import HybridRetriever
from src.core.confidence_calibrator import ConfidenceCalibrator

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.7


class ComplianceAnalyzer:
    """Coordinate retrieval, LLM scoring, and post-processing for compliance."""

    def __init__(
        self,
        retriever: HybridRetriever,
        ner_service: Optional[ClinicalNERService] = None,
        llm_service: Optional[LLMService] = None,
        explanation_engine: Optional[ExplanationEngine] = None,
        prompt_manager: Optional[PromptManager] = None,
        fact_checker_service: Optional[FactCheckerService] = None,
        nlg_service: Optional[NLGService] = None,
        deterministic_focus: Optional[str] = None,
        ner_analyzer: Optional[ClinicalNERService] = None,
        confidence_calibrator: Optional[ConfidenceCalibrator] = None,
    ) -> None:
        """Initializes the ComplianceAnalyzer.

        Args:
            retriever: An instance of HybridRetriever for rule retrieval.
            ner_service: An instance of ClinicalNERService for entity extraction.
            llm_service: An instance of LLMService for core analysis.
            explanation_engine: An instance of ExplanationEngine for adding explanations.
            prompt_manager: An instance of PromptManager for generating prompts.
            fact_checker_service: An instance of FactCheckerService for verifying findings.
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
            self.confidence_calibrator = ConfidenceCalibrator(method='auto')
            self._load_or_create_calibrator()
        
        logger.info("ComplianceAnalyzer initialized with all services.")

    def _load_or_create_calibrator(self) -> None:
        """Load existing calibrator or prepare for training with new data."""
        calibrator_path = Path("models/confidence_calibrator.pkl")
        
        if calibrator_path.exists() and self.confidence_calibrator:
            try:
                self.confidence_calibrator.load(calibrator_path)
                logger.info("Loaded existing confidence calibrator")
            except Exception as e:
                logger.warning(f"Failed to load calibrator: {e}. Will create new one.")
                self.confidence_calibrator = ConfidenceCalibrator(method='auto')
        else:
            logger.info("No existing calibrator found. Will train on first batch of data.")

    def _calibrate_confidence_scores(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply confidence calibration to findings if calibrator is fitted."""
        if not self.confidence_calibrator or not self.confidence_calibrator.is_fitted:
            logger.debug("Confidence calibrator not fitted yet. Using raw scores.")
            return findings
        
        try:
            # Extract confidence scores
            raw_confidences = []
            for finding in findings:
                confidence = finding.get("confidence", 0.5)
                if isinstance(confidence, (int, float)):
                    raw_confidences.append(float(confidence))
                else:
                    raw_confidences.append(0.5)  # Default for non-numeric confidence
            
            if not raw_confidences:
                return findings
            
            # Calibrate confidence scores
            raw_confidences_array = np.array(raw_confidences)
            if self.confidence_calibrator:
                calibrated_confidences = self.confidence_calibrator.calibrate(raw_confidences_array)
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
            
            logger.debug(f"Calibrated confidence scores for {len(findings)} findings")
            
        except Exception as e:
            logger.warning(f"Failed to calibrate confidence scores: {e}. Using raw scores.")
        
        return findings

    def train_confidence_calibrator(self, training_data: List[Dict[str, Any]]) -> None:
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
                if 'confidence' in item and 'is_correct' in item:
                    confidences.append(float(item['confidence']))
                    labels.append(1 if item['is_correct'] else 0)
            
            if len(confidences) < 10:
                logger.warning(f"Insufficient training data ({len(confidences)} samples). Need at least 10.")
                return
            
            # Train the calibrator
            confidences_array = np.array(confidences)
            labels_array = np.array(labels)
            
            if self.confidence_calibrator:
                self.confidence_calibrator.fit(confidences_array, labels_array)
                
                # Save the trained calibrator
                calibrator_path = Path("models")
                calibrator_path.mkdir(exist_ok=True)
                self.confidence_calibrator.save(calibrator_path / "confidence_calibrator.pkl")
                
                # Log calibration metrics
                metrics = self.confidence_calibrator.get_calibration_metrics()
            else:
                metrics = {}
            logger.info(f"Confidence calibrator trained with {len(confidences)} samples")
            logger.info(f"Calibration metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Failed to train confidence calibrator: {e}")

    def get_calibration_metrics(self) -> Dict[str, Any]:
        """Get calibration quality metrics."""
        if not self.confidence_calibrator or not self.confidence_calibrator.is_fitted:
            return {"status": "not_fitted", "message": "Calibrator has not been trained yet"}
        
        metrics = self.confidence_calibrator.get_calibration_metrics()
        return {
            "status": "fitted",
            "method": self.confidence_calibrator.method,
            "metrics": metrics
        }

    async def analyze_document(
        self, document_text: str, discipline: str, doc_type: str
    ) -> Dict[str, Any]:
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

        Returns:
            A dictionary containing the comprehensive analysis result, including findings, explanations, and tips.
        """
        logger.info("Starting compliance analysis for document type: %s", doc_type)

        entities = self.ner_service.extract_entities(document_text) if self.ner_service else []
        entity_list_str = (
            ", ".join(
                f"{entity['entity_group']}: {entity['word']}" for entity in entities
            )
            if entities
            else "No specific entities extracted."
        )

        search_query = f"{discipline} {doc_type} {entity_list_str}"
        try:
            # Add timeout to retrieval to prevent hanging
            retrieved_rules = await asyncio.wait_for(
                self.retriever.retrieve(
                    search_query, 
                    category_filter=discipline,
                    discipline=discipline,
                    document_type=doc_type,
                    context_entities=[entity['word'] for entity in entities] if entities else None
                ),
                timeout=60.0  # 1 minute timeout for rule retrieval
            )
            logger.info("Retrieved %d rules for analysis.", len(retrieved_rules))
        except asyncio.TimeoutError:
            logger.error("Rule retrieval timed out after 1 minute")
            retrieved_rules = []
        except Exception as e:
            logger.error(f"Rule retrieval failed: {e}")
            retrieved_rules = []

        formatted_rules = self._format_rules_for_prompt(retrieved_rules)
        if self.prompt_manager:
            prompt = self.prompt_manager.get_prompt(
                document_text=document_text,
                entity_list=entity_list_str,
                context=formatted_rules,
                discipline=discipline,
                doc_type=doc_type,
                deterministic_focus=self.deterministic_focus,
            )
        else:
            prompt = f"Analyze this document for compliance:\n{document_text}\n\nRules:\n{formatted_rules}"

        if self.llm_service:
            # Use shorter prompt for faster processing
            if len(prompt) > 4000:  # Truncate very long prompts
                prompt = prompt[:3500] + "\n\n[Document truncated for faster analysis]"
            
            try:
                # Add timeout to prevent hanging
                raw_analysis_result = await asyncio.wait_for(
                    asyncio.to_thread(self.llm_service.generate, prompt),
                    timeout=300.0  # 5 minute timeout for LLM generation
                )
            except asyncio.TimeoutError:
                logger.error("LLM generation timed out after 5 minutes")
                raw_analysis_result = '{"findings": [], "error": "Analysis timed out - LLM took too long to respond", "timeout": true}'
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                raw_analysis_result = f'{{"findings": [], "error": "LLM generation failed: {str(e)}", "exception": true}}'
        else:
            raw_analysis_result = '{"findings": [], "error": "No LLM service available"}'
        try:
            initial_analysis = json.loads(raw_analysis_result)
        except json.JSONDecodeError:
            logger.error("LLM returned non-JSON payload: %s", raw_analysis_result)
            initial_analysis = {"raw_output": raw_analysis_result}

        # Create explanation context with discipline and document type
        from src.core.explanation import ExplanationContext

        explanation_context = ExplanationContext(
            document_type=doc_type,
            discipline=discipline,
            rubric_name=f"{discipline.upper()} Compliance Rubric",
        )

        if self.explanation_engine:
            explained_analysis = self.explanation_engine.add_explanations(
                initial_analysis, document_text, explanation_context, retrieved_rules
            )
        else:
            explained_analysis = initial_analysis

        # Apply confidence calibration before final post-processing
        if "findings" in explained_analysis and isinstance(explained_analysis["findings"], list):
            explained_analysis["findings"] = self._calibrate_confidence_scores(
                explained_analysis["findings"]
            )

        final_analysis = await self._post_process_findings(
            explained_analysis, retrieved_rules
        )
        logger.info("Compliance analysis complete.")
        return final_analysis

    async def _post_process_findings(
        self, explained_analysis: Dict[str, Any], retrieved_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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

            if associated_rule and self.fact_checker_service and not self.fact_checker_service.is_finding_plausible(
                finding, associated_rule
            ):
                finding["is_disputed"] = True

            # Confidence threshold check (may have been updated by calibration)
            confidence = finding.get("confidence", 1.0)
            if (
                isinstance(confidence, (float, int))
                and confidence < CONFIDENCE_THRESHOLD
                and not finding.get("confidence_calibrated", False)  # Skip if already calibrated
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
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
        """Formats a list of compliance rules into a string suitable for an LLM prompt.

        Args:
            rules: A list of dictionaries, each representing a compliance rule.

        Returns:
            A formatted string containing the rule names, details, and suggestions.
        """
        if not rules:
            return (
                "No specific compliance rules were retrieved. Analyze based on general "
                "Medicare principles."
            )

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
