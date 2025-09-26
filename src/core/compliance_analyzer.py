<<<<<<< HEAD
import logging
import json
from typing import Dict, Any, List

from .llm_service import LLMService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
from .fact_checker_service import FactCheckerService

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.7

class ComplianceAnalyzer:
    """
    The core logic unit for analyzing a document against a set of compliance rules.
    It receives pre-initialized components and does not load models itself.
    """

    def __init__(self, retriever: Any, ner_pipeline: NERPipeline, llm_service: LLMService, explanation_engine: ExplanationEngine, prompt_manager: PromptManager, fact_checker_service: FactCheckerService):
        self.retriever = retriever
        self.ner_pipeline = ner_pipeline
        self.llm_service = llm_service
        self.explanation_engine = explanation_engine
        self.prompt_manager = prompt_manager
        self.fact_checker_service = fact_checker_service

    def analyze_document(self, document_text: str, discipline: str, doc_type: str) -> dict:
        """
        Orchestrates the analysis of a single document.
        """
        logger.info(f"Analyzing document. Discipline: {discipline}, Type: {doc_type}")

        # 1. Use NER to find key terms
        entities = self.ner_pipeline.extract_entities(document_text)
        entity_list = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities])

        # 2. Build a search query and retrieve relevant rules
        search_query = f"{discipline} {doc_type} {entity_list}"
        retrieved_rules = self.retriever.retrieve(search_query)

        # 3. Build the prompt and get the raw analysis from the LLM
        context = self._format_rules_for_prompt(retrieved_rules)
        prompt = self.prompt_manager.build_prompt(context=context, document_text=document_text)
        raw_analysis = self.llm_service.generate_analysis(prompt)

        # 4. Post-process the analysis
        explained_analysis = self.explanation_engine.add_explanations(raw_analysis, document_text)

        if "findings" in explained_analysis:
            for finding in explained_analysis["findings"]:
                # a. Fact-check the finding against the retrieved rule
                rule_id = finding.get("rule_id")
                associated_rule = next((r for r in retrieved_rules if r.get('id') == rule_id), None)
                if associated_rule:
                    if not self.fact_checker_service.is_finding_plausible(finding, associated_rule):
                        finding['is_disputed'] = True

                # b. Flag low-confidence findings
                confidence = finding.get("confidence", 1.0)
                if isinstance(confidence, (int, float)) and confidence < CONFIDENCE_THRESHOLD:
                    finding['is_low_confidence'] = True

                # c. Generate personalized tip
                tip = self.llm_service.generate_personalized_tip(finding)
                finding['personalized_tip'] = tip

        return explained_analysis

    @staticmethod
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        return "\\n".join([f"- Title: {r.get('name', '')}, Content: {r.get('content', '')}" for r in rules])
||||||| c46cdd8
# This file is intentionally left blank for now.
# The logic has been refactored into llm_analyzer.py
pass
=======
import logging
import json
from typing import Dict, Any, List

from .llm_service import LLMService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
from .fact_checker_service import FactCheckerService

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7

class ComplianceAnalyzer:
    """
    A service that orchestrates the core compliance analysis of a document.
    It receives pre-initialized components and does not load models itself.
    """

    def __init__(self, retriever: Any, ner_pipeline: NERPipeline, llm_service: LLMService, explanation_engine: ExplanationEngine, prompt_manager: PromptManager, fact_checker_service: FactCheckerService):
        self.retriever = retriever
        self.ner_pipeline = ner_pipeline
        self.llm_service = llm_service
        self.explanation_engine = explanation_engine
        self.prompt_manager = prompt_manager
        self.fact_checker_service = fact_checker_service

    def analyze_document(self, document_text: str, discipline: str, doc_type: str) -> Dict[str, Any]:
        """
        Analyzes a document, generates tips, and flags low-confidence or disputed findings.
        """
        entities = self.ner_pipeline.extract_entities(document_text)
        entity_list = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities])
        search_query = f"{discipline} {doc_type} {entity_list}"
        retrieved_rules = self.retriever.retrieve(search_query)

        context = self._format_rules_for_prompt(retrieved_rules)
        prompt = self.prompt_manager.build_prompt(context=context, document_text=document_text)

        raw_analysis = self._generate_analysis(prompt)

        explained_analysis = self.explanation_engine.add_explanations(raw_analysis, document_text)

        if "findings" in explained_analysis:
            for finding in explained_analysis["findings"]:
                # Find the rule that this finding is associated with
                rule_id = finding.get("rule_id")
                associated_rule = next((r for r in retrieved_rules if r.get('id') == rule_id), None)

                # a. Fact-check the finding if a rule was found
                if associated_rule:
                    if not self.fact_checker_service.is_finding_plausible(finding, associated_rule):
                        finding['is_disputed'] = True

                # b. Check for low confidence
                confidence = finding.get("confidence", 1.0)
                if isinstance(confidence, (int, float)) and confidence < CONFIDENCE_THRESHOLD:
                    finding['is_low_confidence'] = True

                # c. Generate personalized tip
                tip = self.llm_service.generate_personalized_tip(finding)
                finding['personalized_tip'] = tip

        return explained_analysis

    @staticmethod
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
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
            raise json.JSONDecodeError("No JSON object found in the output.", raw_output, 0)
        except json.JSONDecodeError:
            logger.error("Failed to decode LLM output into JSON.")
            return {"error": "Invalid JSON output from LLM", "raw_output": raw_output}
>>>>>>> origin/main
