import logging
import json
from typing import Dict, Any

from src.core.ner import NERPipeline
from src.core.prompt_manager import PromptManager
from src.core.explanation import ExplanationEngine
from transformers import AutoModelForCausalLM, AutoTokenizer

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
        self.ner_pipeline = NERPipeline(
            model_name=self.config['models']['ner_model'],
            quantization=self.config.get('quantization', 'none'),
            performance_profile=self.config.get('performance_profile', 'medium')
        )
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
        retrieved_rules = self.retriever.search(query=search_query, discipline=discipline, doc_type=doc_type)

        # 3. Generate analysis
        analysis = self._generate_analysis(
            document, entity_list, retrieved_rules
        )

        # 4. Post-process for explanations
        explained_analysis = self.explanation_engine.add_explanations(analysis)

        return explained_analysis

    def _generate_analysis(self, document: str, entity_list: str, retrieved_rules: list) -> Dict[str, Any]:
        """
        Generates a compliance analysis for a given document.
        """
        prompt = self.prompt_manager.build_prompt(
            document=document,
            entity_list=entity_list,
            context=self._format_rules_for_prompt(retrieved_rules)
        )
        raw_analysis = self._generate_analysis_from_prompt(prompt)
        return self._parse_json_output(raw_analysis)

    def _format_rules_for_prompt(self, rules: list) -> str:
        """
        Formats retrieved rules for inclusion in the prompt.
        """
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."

        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {rule.issue_title}\n"
                f"  **Detail:** {rule.issue_detail}\n"
                f"  **Suggestion:** {rule.suggestion}"
            )
        return "\\n".join(formatted_rules)

    def _generate_analysis_from_prompt(self, prompt: str) -> str:
        """
        Placeholder for the actual LLM call.
        """
        logger.info("Generating analysis with prompt:\\n%s", prompt)
        # In a real implementation, this would call the LLM
        return """
{
    "findings": [
        {
            "text": "Sample finding text",
            "risk": "Sample risk description",
            "suggestion": "Sample suggestion for mitigation"
        }
    ]
}
"""

    def _parse_json_output(self, result: str) -> dict:
        """
        Parses JSON output from the model with robust error handling.
        """
        try:
            json_start = result.find('```json')
            if json_start != -1:
                json_str = result[json_start + 7:].strip()
                json_end = json_str.rfind('```')
                if json_end != -1:
                    json_str = json_str[:json_end].strip()
            else:
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                json_str = result[json_start:json_end]

            analysis = json.loads(json_str)
            return analysis

        except (json.JSONDecodeError, IndexError, ValueError) as e:
            logger.error(f"Error parsing JSON output: {e}\\nRaw model output:\\n{result}")
            analysis = {"error": "Failed to parse JSON output from model."}
            return analysis