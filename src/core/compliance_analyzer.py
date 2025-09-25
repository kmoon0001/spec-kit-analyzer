import logging
import json
from typing import Dict, Any, List

from .llm_service import LLMService
from .nlg_service import NLGService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7

class ComplianceAnalyzer:
    """
    A service that orchestrates the core compliance analysis of a document.
    It receives pre-initialized components and does not load models itself.
    """

    def __init__(self, retriever: Any, ner_pipeline: NERPipeline, llm_service: LLMService, nlg_service: NLGService, explanation_engine: ExplanationEngine, prompt_manager: PromptManager):
        self.retriever = retriever
        self.ner_pipeline = ner_pipeline
        self.llm_service = llm_service
        self.nlg_service = nlg_service
        self.explanation_engine = explanation_engine
        self.prompt_manager = prompt_manager

    def analyze_document(self, document_text: str, discipline: str, doc_type: str) -> Dict[str, Any]:
        """
        Analyzes a document, generates tips, and flags low-confidence findings.
        """
        # 1. Retrieve relevant guidelines
        entities = self.ner_pipeline.extract_entities(document_text)
        entity_list = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities])
        search_query = f"{discipline} {doc_type} {entity_list}"
        retrieved_rules = self.retriever.retrieve(search_query)

        # 2. Build the main analysis prompt
        context = self._format_rules_for_prompt(retrieved_rules)
        prompt = self.prompt_manager.build_prompt(context=context, document_text=document_text)

        # 3. Generate the core analysis from the LLM
        raw_analysis = self._generate_analysis(prompt)

        # 4. Post-process for explanations, now with full document context
        explained_analysis = self.explanation_engine.add_explanations(raw_analysis, document_text)

        # 5. Process findings for uncertainty and generate personalized tips
        if "findings" in explained_analysis:
            for finding in explained_analysis["findings"]:
                confidence = finding.get("confidence", 1.0)
                if isinstance(confidence, (int, float)) and confidence < CONFIDENCE_THRESHOLD:
                    finding['is_low_confidence'] = True
                
                tip = self.nlg_service.generate_personalized_tip(finding)
                finding['personalized_tip'] = tip

        return explained_analysis

    def _format_rules_for_prompt(self, rules: List[Dict[str, Any]]) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        return "\n".join([f"- Title: {r.get('name', '')}, Content: {r.get('content', '')}" for r in rules])

    def _generate_analysis(self, prompt: str) -> Dict[str, Any]:
        raw_output = self.llm_service.generate_analysis(prompt)
        try:
            start = raw_output.find('{')
            end = raw_output.rfind('}')
            if start != -1 and end != -1:
                json_str = raw_output[start:end+1]
                return json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON object found in the output.", raw_output, 0)
        except json.JSONDecodeError:
            logger.error("Failed to decode LLM output into JSON.")
            return {"error": "Invalid JSON output from LLM", "raw_output": raw_output}
