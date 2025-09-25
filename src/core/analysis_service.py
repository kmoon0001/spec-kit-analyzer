import os
from datetime import datetime
import sqlite3
import json
import yaml
from src.parsing import parse_document_content
from src.guideline_service import GuidelineService
from src.database import DATABASE_PATH
from .compliance_analyzer import ComplianceAnalyzer
from .hybrid_retriever import HybridRetriever

# Get the absolute path to the project's root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AnalysisService:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(ROOT_DIR), "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        guideline_sources = [
            os.path.join(os.path.dirname(ROOT_DIR), "medicare_benefit_policy_manual_chapter_8.txt"),
            os.path.join(os.path.dirname(ROOT_DIR), "_default_medicare_benefit_policy_manual.txt"),
            os.path.join(os.path.dirname(ROOT_DIR), "_default_medicare_part.txt")
        ]
        guideline_service = GuidelineService(sources=guideline_sources)
        retriever = HybridRetriever()
        self.analyzer = ComplianceAnalyzer(
            config=config,
            guideline_service=guideline_service,
            retriever=retriever
        )

    def analyze_document(self, file_path: str, rubric_id: int | None = None, discipline: str | None = None, analysis_mode: str = "rubric") -> str:
        # 1. Parse the document content
        document_chunks = parse_document_content(file_path)
        document_text = " ".join([chunk['sentence'] for chunk in document_chunks])
        doc_name = os.path.basename(file_path)

        # 2. Perform analysis using the ComplianceAnalyzer
        analysis_result = self.analyzer.analyze_document(
            document_text,
            discipline=discipline,
            doc_type="Unknown", # This should be determined from the document
        )

        # 3. Generate the HTML report based on the analysis mode
        if analysis_mode in ["llm_only", "hybrid"]:
            template_path = os.path.join(os.path.dirname(ROOT_DIR), "backend", "app", "templates", "llm_report_template.html")
            with open(template_path, "r") as f:
                template_str = f.read()

            report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
            report_html = report_html.replace("<!-- Placeholder for analysis date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            report_html = report_html.replace("<!-- Placeholder for generation date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Inject the JSON directly into the script tag
            analysis_json_str = json.dumps(analysis_result)
            report_html = report_html.replace("<!-- {{ analysis_result_json | safe }} -->", analysis_json_str)

        else: # Existing rubric-based report
            template_path = os.path.join(os.path.dirname(ROOT_DIR), "src", "resources", "report_template.html")
            with open(template_path, "r") as f:
                template_str = f.read()

            # Populate summary
            report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
            report_html = report_html.replace("<!-- Placeholder for analysis date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            findings = analysis_result.get("findings", [])
            compliance_score = max(0, 100 - (len(findings) * 10)) # Simple scoring
            report_html = report_html.replace("<!-- Placeholder for compliance score -->", str(compliance_score))
            report_html = report_html.replace("<!-- Placeholder for total findings -->", str(len(findings)))

            # Populate findings table
            findings_rows_html = ""
            if findings:
                for finding in findings:
                    findings_rows_html += f"""
                    <tr>
                        <td>{finding.get('rule_id', 'N/A')}</td>
                        <td>{finding.get('risk', 'N/A')}</td>
                        <td>{finding.get('suggestion', 'N/A')}</td>
                        <td>{finding.get('text', 'N/A')}</td>
                    </tr>
                    """
            else:
                findings_rows_html = "<tr><td colspan='4'>No findings.</td></tr>"
            report_html = report_html.replace("<!-- Placeholder for findings rows -->", findings_rows_html)

            # Populate Medicare guidelines
            guidelines_html = "<p>No relevant Medicare guidelines found.</p>" # Placeholder
            report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", guidelines_html)

            # Populate footer
            report_html = report_html.replace("<!-- Placeholder for generation date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return report_html