import os
import logging
<<<<<<< HEAD
import pickle
from typing import Dict, Any, List

from src.config import get_config
||||||| 604b275
import pickle
=======
>>>>>>> origin/main
from src.parsing import parse_document_content

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
<<<<<<< HEAD
from .fact_checker_service import FactCheckerService
||||||| 604b275
from .fact_checker_service import FactCheckerService # New Import
=======
from .fact_checker import FactCheckerService # Make sure this import is present
>>>>>>> origin/main
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

            # 1. Initialize the core LLM service first
            llm_service = LLMService(
                model_repo_id=config.models.generator,
                model_filename=config.models.generator_filename,
                llm_settings=config.llm_settings
            )
<<<<<<< HEAD
            fact_checker_service = FactCheckerService(model_name=config.models.fact_checker)
            ner_pipeline = NERPipeline(model_names=config.models.ner_ensemble)
||||||| 604b275
            fact_checker_service = FactCheckerService(model_name=config['models']['fact_checker'])
            ner_pipeline = NERPipeline(model_names=config['models']['ner_ensemble'])
=======

            # 2. Initialize all other services
            fact_checker_service = FactCheckerService(model_name=config['models']['fact_checker'])
            ner_pipeline = NERPipeline(model_names=config['models']['ner_ensemble'])
>>>>>>> origin/main
            self.report_generator = ReportGenerator()
            explanation_engine = ExplanationEngine()

            self.document_classifier = DocumentClassifier(
                llm_service=llm_service,
                prompt_template_path=os.path.join(ROOT_DIR, config.models.doc_classifier_prompt)
            )

            analysis_prompt_manager = PromptManager(
                template_path=os.path.join(ROOT_DIR, config.models.analysis_prompt_template)
            )

            # 3. Initialize the main analyzer, passing it the pre-loaded components
            self.analyzer = ComplianceAnalyzer(
                retriever=self.retriever, # Use the injected retriever
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

    def analyze_document(self, file_path: str, discipline: str, analysis_mode: str) -> str:
        doc_name = os.path.basename(file_path)
        logger.info(f"Starting analysis for document: {doc_name}")

        # 1. Parse and preprocess the document text
        document_text = " ".join([chunk['sentence'] for chunk in parse_document_content(file_path)])

<<<<<<< HEAD
        doc_type = self.document_classifier.classify_document(document_text)
||||||| 604b275
        # Preprocessing step removed as the service is obsolete
        corrected_text = document_text

        doc_type = self.document_classifier.classify_document(corrected_text)
=======
        # Preprocessing step removed as the service is obsolete
        corrected_text = document_text

        # 2. Classify the document type (New Step)
        doc_type = self.document_classifier.classify_document(corrected_text)
>>>>>>> origin/main
        logger.info(f"Document classified as: {doc_type}")

        # 3. Perform the core compliance analysis
        analysis_result = self.analyzer.analyze_document(
<<<<<<< HEAD
            document_text=document_text,
||||||| 604b275
            document_text=corrected_text,
=======
            document=corrected_text,
>>>>>>> origin/main
            discipline=discipline,
            doc_type=doc_type # Use the classified type
        )

<<<<<<< HEAD
        return analysis_result
||||||| 604b275
        return analysis_result
=======
        # 4. Generate the final HTML report
        report_html = self.report_generator.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode
        )

        logger.info(f"Analysis complete for document: {doc_name}")
        return report_html
>>>>>>> origin/main
