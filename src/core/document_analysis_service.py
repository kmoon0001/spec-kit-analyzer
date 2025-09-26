import logging
import pickle
import numpy as np

from src.core.parsing import DocumentParser
from src.core.document_classifier import DocumentClassifier
from src.core.guideline_service import GuidelineService
from src.core.llm_analyzer import LLMAnalyzer
from src.core.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentAnalysisService:
    """
    This service class orchestrates the entire document analysis pipeline.
    It integrates various components like parsing, classification, analysis, and reporting.
    """
    def __init__(self):
        """
        Initializes all the necessary components for the analysis pipeline.
        This follows a Singleton-like pattern where services are initialized once.
        """
        logger.info("Initializing DocumentAnalysisService and its components...")
        self.parser = DocumentParser()
        self.classifier = DocumentClassifier()
        self.guideline_service = GuidelineService()
        self.llm_analyzer = LLMAnalyzer()
        self.report_generator = ReportGenerator()
        logger.info("DocumentAnalysisService initialized successfully.")

    def get_document_embedding(self, text: str) -> bytes:
        """
        Generates a semantic embedding for the given text.
        This is used for caching and similarity checks.
        """
        return self.llm_analyzer.get_embedding(text)

    def analyze_document(self, doc_content: str, doc_name: str) -> tuple[dict, list]:
        """
        Runs the full analysis pipeline on a given document.
        """
        logger.info(f"Starting analysis for document: {doc_name}")

        # 1. Parse the document content to extract text
        # This step is simplified as we assume text is already extracted.
        # In a real scenario, this would handle different file formats.
        parsed_text = doc_content # In a real system, parser.parse(doc_content)

        # 2. Classify the document type (e.g., "Progress Note")
        doc_type = self.classifier.classify_document(parsed_text)
        logger.info(f"Classified document as: {doc_type}")

        # 3. Retrieve relevant guidelines using the RAG pipeline
        relevant_guidelines = self.guideline_service.get_relevant_guidelines(parsed_text)
        logger.info(f"Retrieved {len(relevant_guidelines)} relevant guidelines.")

        # 4. Perform the core analysis using the LLM
        analysis_result = self.llm_analyzer.analyze(parsed_text, relevant_guidelines)
        logger.info("LLM analysis complete.")

        # 5. Generate the final report data
        report_data, findings_data = self.report_generator.generate_report(
            doc_name=doc_name,
            analysis_result=analysis_result
        )
        logger.info("Report generation complete.")

        return report_data, findings_data