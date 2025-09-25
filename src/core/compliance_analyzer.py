import re
import json
import logging
from src.core.llm_service import LLMService
from src.core.prompt_manager import PromptManager
from src.guideline_service import GuidelineService
from src.core.explanation import ExplanationEngine

logger = logging.getLogger(__name__)

class ComplianceAnalyzer:
    def __init__(self, guideline_service: GuidelineService, llm_service: LLMService, prompt_manager: PromptManager, explanation_engine: ExplanationEngine):
        self.guideline_service = guideline_service
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.explanation_engine = explanation_engine
        self.use_query_transformation = False

    def analyze_document(self, document_text: str, discipline: str | None = None, analysis_mode: str = "rubric", doc_type: str | None = None) -> dict:
        query = document_text
        doc_type_obj = doc_type
        if self.use_query_transformation:
            query = self._transform_query(query)
        retrieved_rules = (
            self.guideline_service.search(query=query)
        )
        context_str = self._format_rules_for_prompt(retrieved_rules)
        logger.info("Retrieved and formatted context.")

        prompt = self.prompt_manager.build_prompt(document_text, "", context_str)

        result = self.llm_service.generate_analysis(prompt)

        analysis = self._parse_json_output(result)
        logger.info("Raw model analysis returned.")

        analysis = self.explanation_engine.generate_explanation(analysis)
        logger.info("Explanations generated.")

        return analysis

    @staticmethod
    def _transform_query(query: str) -> str:
        return query

    @staticmethod
    def _format_rules_for_prompt(rules: list) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {rule.get('text', '')}\n"
                f"  **Source:** {rule.get('source', '')}\n"
            )
        return "\n".join(formatted_rules)

    @staticmethod
    def _parse_json_output(result: str) -> dict:
        """
        Parses JSON output from the model with robust error handling.
        """
        try:
            # Use a regular expression to find JSON content
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                json_str = match.group(0)
                analysis = json.loads(json_str)
                return analysis
            else:
                raise ValueError("No JSON object found in the output.")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing JSON output: {e}\nRaw model output:\n{result}")
            return {"error": "Failed to parse JSON output from model."}