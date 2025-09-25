import os
import yaml
import logging
from src.parsing import parse_document_content

# Import all the necessary services
from .compliance_analyzer import ComplianceAnalyzer
from .hybrid_retriever import HybridRetriever
from .report_generator import ReportGenerator
from .preprocessing_service import PreprocessingService
from .document_classifier import DocumentClassifier
from .llm_service import LLMService
from .nlg_service import NLGService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

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

            # 1. Initialize the core LLM service first
            llm_service = LLMService(
                model_repo_id=config['models']['generator'],
                model_filename=config['models'].get('generator_filename'),
                llm_settings=config.get('llm_settings', {})
            )

            # 2. Initialize all other services, reusing the LLM service where needed
            retriever = HybridRetriever()
            ner_pipeline = NERPipeline(model_name=config['models']['ner'])
            self.preprocessing_service = PreprocessingService()
            self.report_generator = ReportGenerator()
            explanation_engine = ExplanationEngine()

            self.document_classifier = DocumentClassifier(
                llm_service=llm_service,
                prompt_template_path=os.path.join(ROOT_DIR, config['models']['doc_classifier_prompt'])
            )
            
            nlg_service = NLGService(
                llm_service=llm_service,
                prompt_template_path=os.path.join(ROOT_DIR, config['models']['nlg_prompt_template'])
            )

            analysis_prompt_manager = PromptManager(
                template_path=os.path.join(ROOT_DIR, config['models']['analysis_prompt_template'])
            )

            # 3. Initialize the main analyzer, passing it the pre-loaded components
            self.analyzer = ComplianceAnalyzer(
                retriever=retriever,
                ner_pipeline=ner_pipeline,
                llm_service=llm_service,
                nlg_service=nlg_service,
                explanation_engine=explanation_engine,
                prompt_manager=analysis_prompt_manager
            )
            logger.info("AnalysisService initialized successfully.")

        except Exception as e:
            logger.error(f"FATAL: Failed to initialize AnalysisService: {e}", exc_info=True)
            # In a real application, you might want to handle this more gracefully
            # but for now, we re-raise to make it clear initialization failed.
            raise e

    def analyze_document(self, file_path: str, discipline: str, analysis_mode: str) -> str:
        doc_name = os.path.basename(file_path)
        logger.info(f"Starting analysis for document: {doc_name}")

        # 1. Parse and preprocess the document text
        document_text = " ".join([chunk['sentence'] for chunk in parse_document_content(file_path)])
        corrected_text = self.preprocessing_service.correct_text(document_text)

        # 2. Classify the document type (New Step)
        doc_type = self.document_classifier.classify_document(corrected_text)
        logger.info(f"Document classified as: {doc_type}")

        # 3. Perform the core compliance analysis
        analysis_result = self.analyzer.analyze_document(
            document=corrected_text,
            discipline=discipline,
            doc_type=doc_type # Use the classified type
        )

        # 4. Generate the final HTML report
        report_html = self.report_generator.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode
        )

        logger.info(f"Analysis complete for document: {doc_name}")
        return report_html
