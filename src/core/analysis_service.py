import os
import yaml
from src.parsing import parse_document_content
from .compliance_analyzer import ComplianceAnalyzer
from .hybrid_retriever import HybridRetriever
from .report_generator import ReportGenerator

# Get the absolute path to the project's root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class AnalysisService:
    def __init__(self):
        config_path = os.path.join(ROOT_DIR, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Initialize the components required by the ComplianceAnalyzer
        retriever = HybridRetriever()
        self.analyzer = ComplianceAnalyzer(
            config=config,
            retriever=retriever
        )
        self.report_generator = ReportGenerator()

    def analyze_document(self, file_path: str, rubric_id: int | None = None, discipline: str | None = None, analysis_mode: str = "rubric") -> str:
        # 1. Parse the document content
        document_chunks = parse_document_content(file_path)
        document_text = " ".join([chunk['sentence'] for chunk in document_chunks])
        doc_name = os.path.basename(file_path)

        # 2. Perform analysis using the ComplianceAnalyzer
        analysis_result = self.analyzer.analyze_document(
            document_text,
            discipline=discipline,
            doc_type="Unknown",  # This should be determined from the document
        )

        # 3. Generate the HTML report
        report_html = self.report_generator.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode
        )

        return report_html
