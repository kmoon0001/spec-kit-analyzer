import os
import yaml
import logging
from src.parsing import parse_document_content
import pickle

# Import all the necessary services
from .compliance_analyzer import ComplianceAnalyzer
from .retriever import HybridRetriever
from .report_generator import ReportGenerator
from .document_classifier import DocumentClassifier
from .llm_service import LLMService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
<<<<<<< HEAD
from .fact_checker import FactCheckerService
from ..config import get_config
||||||| 278fb88
from .fact_checker import FactCheckerService # Make sure this import is present
=======
from .fact_checker_service import FactCheckerService # Make sure this import is present
>>>>>>> origin/main

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class AnalysisService:
    """
    The central orchestrator for the entire analysis pipeline.
    Initializes and holds all AI-related services.
    """
    def __init__(self, retriever: HybridRetriever):
        logger.info("Initializing AnalysisService with injected retriever...")
        self.retriever = retriever
        try:
            config = get_config()

            # 1. Initialize the core AI models and services
            llm_service = LLMService(
                model_repo_id=config.models.generator,
                model_filename=config.models.generator_filename,
                llm_settings=config.llm_settings
            )
            fact_checker_service = FactCheckerService(model_name=config.models.fact_checker)
            ner_pipeline = NERPipeline(model_names=config.models.ner_ensemble)
            self.report_generator = ReportGenerator()
            explanation_engine = ExplanationEngine()

            self.document_classifier = DocumentClassifier(
                llm_service=llm_service,
                prompt_template_path=os.path.join(ROOT_DIR, config.models.doc_classifier_prompt)
            )

            analysis_prompt_manager = PromptManager(
                template_path=os.path.join(ROOT_DIR, config.models.analysis_prompt_template)
            )

            # 2. Initialize the main analyzer, passing it all the pre-loaded components
            self.analyzer = ComplianceAnalyzer(
                retriever=self.retriever,
                ner_pipeline=ner_pipeline,
                llm_service=llm_service,
                explanation_engine=explanation_engine,
                prompt_manager=analysis_prompt_manager,
                fact_checker_service=fact_checker_service
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

    def analyze_document(self, file_path: str, discipline: str, analysis_mode: str = 'rubric') -> dict:
        doc_name = os.path.basename(file_path)
        logger.info(f"Starting analysis for document: {doc_name}")

        document_text = " ".join([chunk['sentence'] for chunk in parse_document_content(file_path)])

        doc_type = self.document_classifier.classify_document(document_text)
        logger.info(f"Document classified as: {doc_type}")

        analysis_result = self.analyzer.analyze_document(
            document_text=document_text,
            discipline=discipline,
            doc_type=doc_type
        )
        
        # The generation of the HTML report is a presentation-layer concern
        # The service should return the structured data.
        return analysis_result