import json
import logging
import asyncio
from typing import Any, Dict, List, Optional

from src.core.llm_service import LLMService
from src.core.nlg_service import NLGService
from src.core.ner import NERPipeline
from src.core.explanation import ExplanationEngine
from src.core.prompt_manager import PromptManager
from src.core.fact_checker_service import FactCheckerService
from src.core.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.7


class ComplianceAnalyzer:
    """Coordinate retrieval, LLM scoring, and post-processing for compliance."""

    def __init__(
        self,
        retriever: HybridRetriever,
        ner_pipeline: NERPipeline,
        llm_service: LLMService,
        explanation_engine: ExplanationEngine,
        prompt_manager: PromptManager,
        fact_checker_service: FactCheckerService,
        nlg_service: Optional[NLGService] = None,
        deterministic_focus: Optional[str] = None,
    ) -> None:
        self.retriever = retriever
        self.ner_pipeline = ner_pipeline
        self.llm_service = llm_service
        self.explanation_engine = explanation_engine
        self.prompt_manager = prompt_manager
        self.fact_checker_service = fact_checker_service
        self.nlg_service = nlg_service
        default_focus = "\n".join(
            [
                "- Treatment frequency documented",
                "- Goals reviewed or adjusted",
                "- Medical necessity justified",
            ]
        )
        self.deterministic_focus = deterministic_focus or default_focus
        logger.info("ComplianceAnalyzer initialized with all services.")

    async def analyze_document(
        self, document_text: str, discipline: str, doc_type: str
    ) -> Dict[str, Any]:
        logger.info("Starting compliance analysis for document type: %s", doc_type)

        entities = self.ner_pipeline.extract_entities(document_text)
        entity_list_str = (
            ", ".join(
                f"{entity['entity_group']}: {entity['word']}" for entity in entities
            )
            if entities
            else "No specific entities extracted."
        )

        search_query = f"{discipline} {doc_type} {entity_list_str}"
        retrieved_rules = await self.retriever.retrieve(
            search_query, category_filter=discipline
        )
        logger.info("Retrieved %d rules for analysis.", len(retrieved_rules))

        formatted_rules = self._format_rules_for_prompt(retrieved_rules)
        prompt = self.prompt_manager.build_prompt(
            document_text=document_text,
            entity_list=entity_list_str,
            context=formatted_rules,
            discipline=discipline,
            doc_type=doc_type,
            deterministic_focus=self.deterministic_focus,
        )

        raw_analysis_result = await asyncio.to_thread(
            self.llm_service.generate, prompt
        )
        try:
            initial_analysis = json.loads(raw_analysis_result)
        except json.JSONDecodeError:
            logger.error("LLM returned non-JSON payload: %s", raw_analysis_result)
            initial_analysis = {"raw_output": raw_analysis_result}

        explained_analysis = self.explanation_engine.add_explanations(
            initial_analysis, document_text
        )

        final_analysis = await self._post_process_findings(
            explained_analysis, retrieved_rules
        )
        logger.info("Compliance analysis complete.")
        return final_analysis


    async def _post_process_findings(
        self, explained_analysis: Dict[str, Any], retrieved_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        findings = explained_analysis.get("findings")
        if not isinstance(findings, list):
            return explained_analysis

        for finding in findings:
            rule_id = finding.get("rule_id")
            associated_rule = next(
                (r for r in retrieved_rules if r.get("id") == rule_id), None
            )

            if associated_rule and not self.fact_checker_service.is_finding_plausible(
                finding, associated_rule
            ):
                finding["is_disputed"] = True

            confidence = finding.get("confidence", 1.0)
            if (
                isinstance(confidence, (float, int))
                and confidence < CONFIDENCE_THRESHOLD
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

            rule_text = f"- **Rule:** {rule_name}\n  **Detail:** {rule_detail}"
            if rule_suggestion:
                rule_text += f"\n  **Suggestion:** {rule_suggestion}"

            formatted_rules.append(rule_text)
        return "\n".join(formatted_rules)
