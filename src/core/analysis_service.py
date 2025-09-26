import os
import yaml
import logging
import pickle
from typing import Dict, Any, List

from src.parsing import parse_document_content

# Corrected imports to reflect refactoring
from .compliance_analyzer import ComplianceAnalyzer
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
            self.ner_pipeline = NERPipeline(model_names=config['models']['ner_ensemble'])
            self.retriever = HybridRetriever()
            self.preprocessing_service = PreprocessingService()
            self.report_generator = ReportGenerator()
            self.explanation_engine = ExplanationEngine()
            self.nlg_service = NLGService()

            self.document_classifier = DocumentClassifier(
                llm_service=llm_service,
                prompt_template_path=os.path.join(ROOT_DIR, config['models']['doc_classifier_prompt'])
            )

            analysis_prompt_manager = PromptManager(
                template_path=os.path.join(ROOT_DIR, config['models']['analysis_prompt_template'])
            )

            # 2. Initialize the compliance analyzer with all its dependencies
            self.analyzer = ComplianceAnalyzer(
                retriever=self.retriever,
                ner_pipeline=self.ner_pipeline,
                llm_service=llm_service,
                explanation_engine=self.explanation_engine,
                prompt_manager=analysis_prompt_manager,
                fact_checker_service=self.fact_checker_service
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
        """
        Performs a compliance analysis on a given document.
        This service acts as a high-level orchestrator, delegating tasks
        to specialized components.
        """
        doc_name = os.path.basename(file_path)
        logger.info(f"Starting analysis for document: {doc_name}")

        # 1. Parse and preprocess the document content
        document_text = " ".join([chunk['sentence'] for chunk in parse_document_content(file_path)])
        corrected_text = self.preprocessing_service.correct_text(document_text)

        # 2. Classify the document to understand its type (e.g., "Progress Note")
        doc_type = self.document_classifier.classify_document(corrected_text)
        logger.info(f"Document classified as: {doc_type}")

        # 3. Delegate the core analysis logic to the ComplianceAnalyzer
        # The analyzer handles NER, rule retrieval, LLM analysis, and fact-checking.
        analysis_result = self.analyzer.analyze_document(
            document_text=corrected_text,
            discipline=discipline,
            doc_type=doc_type
        )

        # 4. Generate a comprehensive report from the analysis findings
        final_report = self.report_generator.generate_report(
            original_text=document_text,
            analysis=analysis_result
        )

        return final_report