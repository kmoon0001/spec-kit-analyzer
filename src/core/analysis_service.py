import os
import yaml
import logging
import pickle
from typing import Dict, Any, List

from src.parsing import parse_document_content

# Corrected imports to reflect refactoring
from .llm_analyzer import LLMComplianceAnalyzer
from .hybrid_retriever import HybridRetriever
from .report_generator import ReportGenerator
from .document_classifier import DocumentClassifier
from .llm_service import LLMService
from .nlg_service import NLGService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
from .fact_checker_service import FactCheckerService

# Placeholders for services that might be missing files or have constructor mismatches
# This avoids causing immediate new errors and allows us to focus on one problem at a time.
class PreprocessingService:
    def correct_text(self, text): return text

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONFIDENCE_THRESHOLD = 0.7

class AnalysisService:
    """
    The central orchestrator for the entire analysis pipeline.
    Initializes and holds all AI-related services.
    """
    def __init__(self):
        logger.info("Initializing AnalysisService and all sub-components...")
        try:
            config_path = os.path.join(ROOT_DIR, "config.yaml")
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # 1. Initialize services
            llm_service = LLMService(
                model_repo_id=config['models']['generator'],
                model_filename=config['models'].get('generator_filename'),
                llm_settings=config.get('llm_settings', {})
            )
            self.fact_checker_service = FactCheckerService(model_name=config['models']['fact_checker'])
            # Temporarily adjust constructor call to match placeholder
            self.ner_pipeline = NERPipeline(model_name="placeholder_for_ensemble")
            self.retriever = HybridRetriever()
            self.preprocessing_service = PreprocessingService()
            self.report_generator = ReportGenerator()
            self.explanation_engine = ExplanationEngine()

            self.document_classifier = DocumentClassifier(
                llm_service=llm_service,
                prompt_template_path=os.path.join(ROOT_DIR, config['models']['doc_classifier_prompt'])
            )
            # Temporarily adjust constructor call to match placeholder
            self.nlg_service = NLGService(model_name="placeholder_nlg")

            analysis_prompt_manager = PromptManager(
                template_path=os.path.join(ROOT_DIR, config['models']['analysis_prompt_template'])
            )

            # 2. Initialize the new LLM analyzer instead of the old one
            self.llm_analyzer = LLMComplianceAnalyzer(
                llm_service=llm_service,
                prompt_manager=analysis_prompt_manager,
            )
            logger.info("AnalysisService initialized successfully.")

        except Exception as e:
            logger.error(f"FATAL: Failed to initialize AnalysisService: {e}", exc_info=True)
            raise e

    def get_document_embedding(self, text: str) -> bytes:
        if not self.retriever or not self.retriever.dense_retriever:
            raise RuntimeError("Dense retriever is not initialized.")
        embedding = self.retriever.dense_retriever.encode(text)
        return pickle.dumps(embedding)

    def analyze_document(self, file_path: str, discipline: str) -> dict:
        doc_name = os.path.basename(file_path)
        logger.info(f"Starting analysis for document: {doc_name}")

        document_text = " ".join([chunk['sentence'] for chunk in parse_document_content(file_path)])
        corrected_text = self.preprocessing_service.correct_text(document_text)

        doc_type = self.document_classifier.classify_document(corrected_text)
        logger.info(f"Document classified as: {doc_type}")

        entities = self.ner_pipeline.extract_entities(corrected_text)
        entity_list = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities])
        search_query = f"{discipline} {doc_type} {entity_list}"
        retrieved_rules = self.retriever.retrieve(search_query)

        context = self._format_rules_for_prompt(retrieved_rules)

        analysis_result = self.llm_analyzer.analyze_document(document_text=corrected_text, context=context)

        explained_analysis = self.explanation_engine.add_explanations(analysis_result, corrected_text)

        if "findings" in explained_analysis:
            for finding in explained_analysis["findings"]:
                rule_id = finding.get("rule_id")
                associated_rule = next((r for r in retrieved_rules if r.get('id') == rule_id), None)

                if associated_rule:
                    if not self.fact_checker_service.is_finding_plausible(finding, associated_rule):
                        finding['is_disputed'] = True

                confidence = finding.get("confidence", 1.0)
                if isinstance(confidence, (int, float)) and confidence < CONFIDENCE_THRESHOLD:
                    finding['is_low_confidence'] = True

                tip = self.nlg_service.generate_personalized_tip(finding)
                finding['personalized_tip'] = tip

        return explained_analysis

    def _format_rules_for_prompt(self, rules: List[Dict[str, Any]]) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        return "\n".join([f"- Title: {r.get('name', '')}, Content: {r.g_et('content', '')}" for r in rules])