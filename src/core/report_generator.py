import os
import json
from datetime import datetime

from .risk_scoring_service import RiskScoringService

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class ReportGenerator:
    def __init__(self):
        self.rubric_template_str = self._load_template(os.path.join(ROOT_DIR, "src", "resources", "report_template.html"))
        self.model_limitations_html = self._load_and_convert_markdown(os.path.join(ROOT_DIR, "src", "resources", "model_limitations.md"))
        self.risk_scoring_service = RiskScoringService()

    @staticmethod
    def _load_template(template_path: str) -> str:
        try:
            with open(template_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return "<h1>Report</h1><p>Template not found.</p><div>{findings}</div>"

    @staticmethod
    def _load_and_convert_markdown(file_path: str) -> str:
        try:
            import markdown
            with open(file_path, "r") as f:
                md_text = f.read()
            return markdown.markdown(md_text, extensions=['tables'])
        except (ImportError, FileNotFoundError):
            return "<p>Could not load model limitations document. Please ensure the 'markdown' library is installed.</p>"

    def generate_html_report(self, analysis_result: dict, doc_name: str, analysis_mode: str) -> str:
        return self._generate_rubric_report(analysis_result, doc_name)

    def _generate_rubric_report(self, analysis_result: dict, doc_name: str) -> str:
        template_str = self.rubric_template_str
        report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
        report_html = report_html.replace("<!-- Placeholder for analysis date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        findings = analysis_result.get("findings", [])
        
        compliance_score = self.risk_scoring_service.calculate_compliance_score(findings)
        
        report_html = report_html.replace("<!-- Placeholder for compliance score -->", str(compliance_score))
        report_html = report_html.replace("<!-- Placeholder for total findings -->", str(len(findings)))

        findings_rows_html = ""
        if findings:
            for finding in findings:
                # Check for the low confidence flag
                row_class = 'class="low-confidence"' if finding.get('is_low_confidence') else ''
                risk_display = finding.get('risk', 'N/A')
                if finding.get('is_low_confidence'):
                    risk_display += " (Low Confidence)"

                tip_to_display = finding.get('personalized_tip', finding.get('suggestion', 'N/A'))
                
                findings_rows_html += f"""
                <tr {row_class}>
                    <td>{finding.get('rule_id', 'N/A')}</td>
                    <td>{risk_display}</td>
                    <td>{tip_to_display}</td>
                    <td>{finding.get('text', 'N/A')}</td>
                </tr>
                """
        else:
            findings_rows_html = "<tr><td colspan='4'>No findings.</td></tr>"
        report_html = report_html.replace("<!-- Placeholder for findings rows -->", findings_rows_html)

        report_html = report_html.replace("<!-- Placeholder for model limitations -->", self.model_limitations_html)

        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", "<p>Feature not yet implemented.</p>")
        report_html = report_html.replace("<!-- Placeholder for LLM analysis -->", "<p>Feature not yet implemented.</p>")

        report_html = report_html.replace("<!-- Placeholder for generation date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return report_html
