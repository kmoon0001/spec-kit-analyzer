import logging
import asyncio
import json
from typing import Any, Dict, List, Optional

from .llm_service import LLMService
from .nlg_service import NLGService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
from .fact_checker_service import FactCheckerService
from .hybrid_retriever import HybridRetriever

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
        retrieved_rules = self.retriever.retrieve(
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
        initial_analysis = self._parse_llm_output(raw_analysis_result)

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

    def _parse_llm_output(self, llm_output: str) -> Dict[str, Any]:
        """
        Parses the raw string output from the LLM, which is expected to be a JSON object.
        """
        try:
            # The LLM output is often wrapped in markdown-style code blocks.
            if "```json" in llm_output:
                llm_output = llm_output.split("```json")[1].split("```")[0]

            return json.loads(llm_output)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse LLM JSON output: {e}\nOutput: {llm_output}")
            return {"error": "Failed to parse LLM output", "raw_output": llm_output}

    @staticmethod
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
        if not rules:
            return (
                "No specific compliance rules were retrieved. Analyze based on general "
                "Medicare principles."
            )

        formatted_rules = []
        for rule in rules[:8]:  # Limit to top 8 rules to keep prompt concise
            rule_name = rule.get("name", "N/A")
            regulation = rule.get("regulation", "N/A")
            pitfalls = rule.get("common_pitfalls", "N/A")
            best_practice = rule.get("best_practice", "N/A")

            rule_text = (
                f"- **Rule:** {rule_name}\n"
                f"  - **Regulation:** {regulation}\n"
                f"  - **Common Pitfalls:** {pitfalls}\n"
                f"  - **Best Practice:** {best_practice}"
            )
            formatted_rules.append(rule_text)
        return "\n\n".join(formatted_rules)
