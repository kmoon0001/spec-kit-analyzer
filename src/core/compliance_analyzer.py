import logging
import json
from typing import Dict, Any, List

from .ner import NERPipeline
from .explanation import ExplanationEngine
from .llm_service import LLMService
from .nlg_service import NLGService

logger = logging.getLogger(__name__)

# Define a threshold for what is considered a low-confidence finding
CONFIDENCE_THRESHOLD = 0.7

class ComplianceAnalyzer:
    """
    An all-in-one, extensible class for the ComplianceAnalyzer system.
    """

    def __init__(self, config: Dict[str, Any], retriever: Any):
        """
        Initializes the ComplianceAnalyzer with config-driven components.
        """
        self.config = config
        self.retriever = retriever

        # Initialize components from the updated config
        self.ner_pipeline = NERPipeline(model_name=self.config['models']['ner'])
        self.explanation_engine = ExplanationEngine()
        
        self.llm_service = LLMService(
            model_repo_id=self.config['models']['generator'],
            model_filename=None, 
            llm_settings=self.config.get('llm_settings', {})
        )

        self.nlg_service = NLGService(
            llm_service=self.llm_service, 
            prompt_template_path=self.config['models']['nlg_prompt_template']
        )

    def analyze_document(self, document: str, discipline: str, doc_type: str) -> Dict[str, Any]:
        """
        Analyzes a document, generates tips, and flags low-confidence findings.
        """
        # Steps 1-3: Retrieve context and build the main analysis prompt
        entities = self.ner_pipeline.extract_entities(document)
        entity_list = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities])
        search_query = f"{discipline} {doc_type} {entity_list}"
        retrieved_rules = self.retriever.retrieve(search_query)
        context = self._format_rules_for_prompt(retrieved_rules)
        prompt = f"Analyze the following document for compliance based on these rules:\n\nContext:\n{context}\n\nDocument:\n{document}"

        # 4. Generate the core analysis from the LLM
        raw_analysis = self._generate_analysis(prompt)

        # 5. Post-process for explanations
        explained_analysis = self.explanation_engine.add_explanations(raw_analysis, retrieved_rules)

        # 6. Process findings for uncertainty and generate personalized tips
        if "findings" in explained_analysis:
            for finding in explained_analysis["findings"]:
                # a. Check for low confidence
                confidence = finding.get("confidence", 1.0) # Default to 1.0 if not provided
                if isinstance(confidence, (int, float)) and confidence < CONFIDENCE_THRESHOLD:
                    finding['is_low_confidence'] = True
                
                # b. Generate personalized tip
                tip = self.nlg_service.generate_personalized_tip(finding)
                finding['personalized_tip'] = tip

        return explained_analysis

    def _format_rules_for_prompt(self, rules: List[Dict[str, Any]]) -> str:
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
