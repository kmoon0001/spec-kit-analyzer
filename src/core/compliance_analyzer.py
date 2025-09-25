import logging
import json
from typing import Dict, Any, List
from src.core.hybrid_retriever import HybridRetriever
from src.guideline_service import GuidelineService
from src.core.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class ComplianceAnalyzer:
    def __init__(self, config: Dict[str, Any], guideline_service: GuidelineService, retriever: HybridRetriever, use_query_transformation: bool = False):
        self.config = config
        self.guideline_service = guideline_service
        self.retriever = retriever
        self.prompt_manager = PromptManager()
        # Mocked generator model and tokenizer
        self.generator_model = None
        self.generator_tokenizer = None
        self.use_query_transformation = use_query_transformation
        self.explanation_engine = None

    def analyze_document(self, document: str, discipline: str, doc_type: str) -> Dict[str, Any]:
        logger.info(f"Analyzing document for discipline '{discipline}' and doc_type '{doc_type}'.")
        # This is a mock implementation.
        # In a real implementation, this would involve NER, retrieval, and generation.
        return {"analysis": "mock analysis"}

    def _transform_query(self, query: str) -> str:
        return query

    def _format_rules_for_prompt(self, rules: list) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {rule.get('text', '')}\n"
                f"  **Source:** {rule.get('source', '')}\n"
            )
        return "\n".join(formatted_rules)

    def _parse_json_output(self, result: str) -> dict:
        """
        Parses JSON output from the model with robust error handling.
        """
        try:
            # First try to find JSON wrapped in code blocks
            json_start = result.find('```json')
            if json_start != -1:
                json_str = result[json_start + 7:].strip()
                json_end = json_str.rfind('```')
                if json_end != -1:
                    json_str = json_str[:json_end].strip()
            else:
                # Fall back to finding raw JSON braces
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                json_str = result[json_start:json_end]

            analysis = json.loads(json_str)
            return analysis

        except (json.JSONDecodeError, IndexError, ValueError) as e:
            logger.error(f"Error parsing JSON output: {e}\nRaw model output:\n{result}")
            analysis = {"error": "Failed to parse JSON output from model."}
            return analysis