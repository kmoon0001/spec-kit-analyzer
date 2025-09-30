import json
import logging
import asyncio
from typing import Any, Dict, List, Optional

from ..config import get_settings
from .llm_service import LLMService
from .nlg_service import NLGService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
from .fact_checker_service import FactCheckerService
from .hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class ComplianceAnalyzer:
    """
    Coordinates a sophisticated RAG pipeline for clinical compliance analysis.

    This service integrates rule retrieval, LLM-based scoring, and multi-stage
    post-processing to deliver accurate, explainable, and robust compliance checks.
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        ner_pipeline: NERPipeline,
        llm_service: LLMService,
        explanation_engine: ExplanationEngine,
        prompt_manager: PromptManager,
        fact_checker_service: FactCheckerService,
        nlg_service: Optional[NLGService] = None,
    ) -> None:
        """Initializes the analyzer with all necessary service dependencies."""
        self.retriever = retriever
        self.ner_pipeline = ner_pipeline
        self.llm_service = llm_service
        self.explanation_engine = explanation_engine
        self.prompt_manager = prompt_manager
        self.fact_checker_service = fact_checker_service
        self.nlg_service = nlg_service
        self.settings = get_settings().analysis
        logger.info(
            "ComplianceAnalyzer initialized with confidence threshold: %.2f",
            self.settings.confidence_threshold,
        )

    async def analyze_document(
        self, document_text: str, discipline: str, doc_type: str
    ) -> Dict[str, Any]:
        """
        Executes the full compliance analysis pipeline for a given document.
        """
        logger.info("Starting compliance analysis for document type: %s", doc_type)

        # 1. Hybrid Retrieval: Get the most relevant compliance rules.
        entities = self.ner_pipeline.extract_entities(document_text)
        entity_list_str = ", ".join(
            f"{e['entity_group']}: {e['word']}" for e in entities
        ) or "No specific entities extracted."

        search_query = f"{discipline} {doc_type} {entity_list_str}"
        retrieved_rules = await self.retriever.retrieve(
            search_query, category_filter=discipline
        )
        logger.info("Retrieved %d rules for analysis.", len(retrieved_rules))
        # Create a map for efficient O(1) lookups during post-processing.
        retrieved_rules_map = {rule["id"]: rule for rule in retrieved_rules}

        # 2. Prompt Engineering: Build a detailed prompt for the LLM.
        formatted_rules = self._format_rules_for_prompt(retrieved_rules)
        prompt = self.prompt_manager.build_prompt(
            document_text=document_text,
            entity_list=entity_list_str,
            context=formatted_rules,
            discipline=discipline,
            doc_type=doc_type,
            deterministic_focus=self.settings.deterministic_focus,
        )

        # 3. LLM Inference: Get the initial analysis from the language model.
        raw_analysis_result = await asyncio.to_thread(
            self.llm_service.generate, prompt
        )
        try:
            initial_analysis = json.loads(raw_analysis_result)
        except json.JSONDecodeError:
            logger.error(
                "LLM returned a non-JSON payload: %s", raw_analysis_result, exc_info=True
            )
            # Return a structured error to be handled by the caller.
            return {
                "error": "LLM_RESPONSE_INVALID_JSON",
                "details": "The language model returned a malformed response.",
                "raw_output": raw_analysis_result,
            }

        # 4. Post-processing: Refine, verify, and enhance the initial findings.
        explained_analysis = self.explanation_engine.add_explanations(
            initial_analysis, document_text
        )
        final_analysis = await self._post_process_findings(
            explained_analysis, retrieved_rules_map
        )

        logger.info("Compliance analysis complete.")
        return final_analysis

    async def _post_process_findings(
        self,
        explained_analysis: Dict[str, Any],
        retrieved_rules_map: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Refines and validates findings from the LLM.
        """
        findings = explained_analysis.get("findings")
        if not isinstance(findings, list):
            return explained_analysis

        for finding in findings:
            rule_id = finding.get("rule_id")
            # Efficient O(1) lookup.
            associated_rule = retrieved_rules_map.get(rule_id)

            # Fact-checking and confidence scoring.
            if associated_rule and not self.fact_checker_service.is_finding_plausible(
                finding, associated_rule
            ):
                finding["is_disputed"] = True

            confidence = finding.get("confidence", 1.0)
            if confidence < self.settings.confidence_threshold:
                finding["is_low_confidence"] = True

            # Generate personalized tips using the NLG service.
            if self.nlg_service:
                tip = await asyncio.to_thread(
                    self.nlg_service.generate_personalized_tip, finding
                )
                finding["personalized_tip"] = tip
            else:
                finding.setdefault("personalized_tip", "Tip generation unavailable.")

        return explained_analysis

    @staticmethod
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved rules for the LLM prompt, including their relevance scores.
        """
        if not rules:
            return "No specific compliance rules retrieved. Analyze based on general principles."

        formatted_rules = []
        # Limit to the top 8 most relevant rules to keep the prompt concise.
        for rule in rules[:8]:
            rule_name = rule.get("name", "N/A")
            rule_detail = rule.get("content", "N/A")
            score = rule.get("relevance_score", 0.0)

            # Inform the LLM of the rule's importance via its relevance score.
            rule_text = (
                f"- **Rule:** {rule_name} (Relevance Score: {score:.3f})\n"
                f"  **Detail:** {rule_detail}"
            )
            formatted_rules.append(rule_text)

        return "\n".join(formatted_rules)
