import logging
import json
from typing import Dict, Any, List

from src.core.ner import NERPipeline
from src.core.prompt_manager import PromptManager
from src.core.explanation import ExplanationEngine

logger = logging.getLogger(__name__)

class ComplianceAnalyzer:
    """
    An all-in-one, extensible class for the ComplianceAnalyzer system.
    """

    def __init__(self, config: Dict[str, Any], guideline_service: Any, retriever: Any):
        """
        Initializes the ComplianceAnalyzer with config-driven components.
        """
        self.config = config
        self.guideline_service = guideline_service
        self.retriever = retriever

        # Initialize components from config
        self.ner_pipeline = NERPipeline(model_name=self.config['models']['ner_model'])
        self.prompt_manager = PromptManager(template_path=self.config['models']['prompt_template'])
        self.explanation_engine = ExplanationEngine()

    def analyze_document(self, document: str, discipline: str, doc_type: str) -> Dict[str, Any]:
        """
        Analyzes a single document for compliance.
        """
        # 1. Extract entities
        entities = self.ner_pipeline.extract_entities(document)
        entity_list = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities])

        # 2. Retrieve relevant guidelines
        search_query = f"{discipline} {doc_type} {entity_list}"
        retrieved_rules = self.retriever.retrieve(search_query)

        # 3. Build the prompt
        prompt = self.prompt_manager.build_prompt(
            document=document,
            entity_list=entity_list,
            context=self._format_rules_for_prompt(retrieved_rules)
        )

        # 4. Generate analysis (placeholder for actual model call)
        raw_analysis = self._generate_analysis(prompt)

        # 5. Post-process for explanations
        explained_analysis = self.explanation_engine.add_explanations(raw_analysis)

        return explained_analysis

    def _format_rules_for_prompt(self, rules: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved rules for inclusion in the prompt.
        """
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."

        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {rule.get('issue_title', '')}\n"
                f"  **Detail:** {rule.get('issue_detail', '')}\n"
                f"  **Suggestion:** {rule.get('suggestion', '')}"
            )
        return "\n".join(formatted_rules)

    def _generate_analysis(self, prompt: str) -> Dict[str, Any]:
        """
        Placeholder for the actual LLM call.
        """
        logger.info("Generating analysis with prompt:\n%s", prompt)
        # In a real implementation, this would call the LLM
        return {
            "findings": [
                {
                    "text": "Sample finding text",
                    "risk": "Sample risk description",
                    "suggestion": "Sample suggestion for mitigation"
                }
            ]
        }