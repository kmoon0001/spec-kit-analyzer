import logging
from typing import Dict, Any, List

from .llm_service import LLMService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
from .fact_checker_service import FactCheckerService

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.7  # Confidence score below which a finding is flagged

class ComplianceAnalyzer:
    """
    Orchestrates the core compliance analysis of a document by coordinating various services.
    It receives pre-initialized components and does not load models itself.
    """

    def __init__(self, retriever: Any, ner_pipeline: NERPipeline, llm_service: LLMService, 
                 explanation_engine: ExplanationEngine, prompt_manager: PromptManager, 
                 fact_checker_service: FactCheckerService):
        self.retriever = retriever
        self.ner_pipeline = ner_pipeline
        self.llm_service = llm_service
        self.explanation_engine = explanation_engine
        self.prompt_manager = prompt_manager
        self.fact_checker_service = fact_checker_service
        logger.info("ComplianceAnalyzer initialized with all services.")

    def analyze_document(self, document_text: str, discipline: str, doc_type: str) -> Dict[str, Any]:
        """Analyzes a document for compliance risks using a multi-step pipeline."""
        logger.info(f"Starting compliance analysis for document type: {doc_type}")

        # 1. Use NER to find key terms
        entities = self.ner_pipeline.extract_entities(document_text)
        entity_list_str = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities]) if entities else "No specific entities extracted."

        # 2. Build a search query and retrieve relevant rules
        search_query = f"{discipline} {doc_type} {entity_list_str}"
        retrieved_rules = self.retriever.retrieve(search_query)
        logger.info(f"Retrieved {len(retrieved_rules)} rules for analysis.")

        # 3. Build the prompt for the LLM
        formatted_rules = self._format_rules_for_prompt(retrieved_rules)
        prompt = self.prompt_manager.build_prompt(
            document=document_text,
            entity_list=entity_list_str,
            context=formatted_rules
        )

        # 4. Get initial analysis from the LLM
        raw_analysis_result = self.llm_service.generate_analysis(prompt)
        initial_analysis = self.llm_service.parse_json_output(raw_analysis_result)

        # 5. Add explanations to the findings
        explained_analysis = self.explanation_engine.add_explanations(initial_analysis, document_text)

        # 6. Post-process findings (fact-checking, confidence, tips)
        final_analysis = self._post_process_findings(explained_analysis, retrieved_rules)
        logger.info("Compliance analysis complete.")

        return final_analysis

    def _post_process_findings(self, explained_analysis: Dict[str, Any], retrieved_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adds flags for disputed findings, low confidence, and generates personalized tips."""
        if "findings" in explained_analysis:
            for finding in explained_analysis["findings"]:
                rule_id = finding.get("rule_id")
                associated_rule = next((r for r in retrieved_rules if r.get('id') == rule_id), None)

                # Fact-check the finding
                if associated_rule and not self.fact_checker_service.is_finding_plausible(finding, associated_rule):
                    finding['is_disputed'] = True

                # Check for low confidence
                confidence = finding.get("confidence", 1.0)
                if isinstance(confidence, (float, int)) and confidence < CONFIDENCE_THRESHOLD:
                    finding['is_low_confidence'] = True
                
                # Generate a personalized tip (assuming llm_service has this method as per the merge)
                try:
                    tip = self.llm_service.generate_personalized_tip(finding)
                    finding['personalized_tip'] = tip
                except AttributeError:
                     finding['personalized_tip'] = "Tip generation is currently unavailable."

        return explained_analysis

    @staticmethod
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
        """Formats a list of rule dictionaries into a string for the LLM prompt."""
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        
        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {rule.get('issue_title', 'N/A')}\n"
                f"  **Detail:** {rule.get('issue_detail', 'N/A')}\n"
                f"  **Suggestion:** {rule.get('suggestion', 'N/A')}"
            )
        return "\n".join(formatted_rules)
