import os
from src.parsing import parse_document_content
from src.guideline_service import GuidelineService
from src.core.llm_analyzer import LLMComplianceAnalyzer

class AnalysisService:
    def __init__(self):
        # GuidelineService is initialized first, as it's a dependency for the analyzer
        self.guideline_service = GuidelineService()
        guideline_sources = [
            "_default_medicare_benefit_policy_manual.txt",
            "_default_medicare_part.txt"
        ]
        # Load and index guidelines upon initialization
        self.guideline_service.load_and_index_guidelines(sources=guideline_sources)

        # Now initialize the analyzer, passing the ready guideline service
        self.llm_analyzer = LLMComplianceAnalyzer(guideline_service=self.guideline_service)

    def analyze_document(self, file_path: str) -> str:
        """
        Analyzes a document using the LLM-based RAG pipeline and generates an HTML report.
        """
        # 1. Parse the document content
        document_chunks = parse_document_content(file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks])

        # 2. Perform analysis using the LLM analyzer
        llm_analysis_text = self.llm_analyzer.analyze_document(document_text)

        # 3. Generate the HTML report
        with open(os.path.join("src", "resources", "report_template.html"), "r") as f:
            template_str = f.read()

        # Populate the analysis placeholder
        report_html = template_str.replace("<!-- Placeholder for LLM analysis -->", llm_analysis_text)

        return report_html
