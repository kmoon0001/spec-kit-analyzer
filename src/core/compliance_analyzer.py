import logging
import json
from typing import Dict, Any, List

from src.core.ner import NERPipeline
from src.core.prompt_manager import PromptManager
from src.core.explanation import ExplanationEngine
from src.core.llm_service import LLMService

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
        self.llm_service = LLMService(
            model_repo_id=self.config['models']['llm_repo_id'],
            model_filename=self.config['models']['llm_filename']
        )

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
            document_text=document,
            entity_list=entity_list,
            context=self._format_rules_for_prompt(retrieved_rules)
        )

        # 4. Generate analysis (placeholder for actual model call)
        raw_analysis = self._generate_analysis(prompt)

        # 5. Post-process for explanations
        explained_analysis = self.explanation_engine.add_explanations(raw_analysis, retrieved_rules)

        return explained_analysis

    @staticmethod
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved rules for inclusion in the prompt.
        """
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."

        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule ID:** {rule.get('id', '')}\n"
                f"  **Title:** {rule.get('issue_title', '')}\n"
                f"  **Detail:** {rule.get('issue_detail', '')}\n"
                f"  **Suggestion:** {rule.get('suggestion', '')}"
            )
        return "\n".join(formatted_rules)

    def _generate_analysis(self, prompt: str) -> Dict[str, Any]:
        """
        Generates the analysis by calling the LLM service and parsing the output.
        """
        raw_output = self.llm_service.generate_analysis(prompt)

        # Basic parsing of the raw output.
        # This assumes the LLM returns a JSON string.
        try:
            # A more robust cleanup to handle cases where the model wraps the JSON in markdown
            # or adds extra text. We'll find the first '{' and the last '}'
            start = raw_output.find('{')
            end = raw_output.rfind('}')
            if start != -1 and end != -1:
                json_str = raw_output[start:end+1]
                analysis_result = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON object found in the output.", raw_output, 0)
        except json.JSONDecodeError:
            logger.error("Failed to decode LLM output into JSON.")
            analysis_result = {"error": "Invalid JSON output from LLM", "raw_output": raw_output}

        return analysis_result