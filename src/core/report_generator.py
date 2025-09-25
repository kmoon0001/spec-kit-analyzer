import os
import json
from datetime import datetime

# Get the absolute path to the project's root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ReportGenerator:
    def __init__(self):
        # Pre-load templates
        self.llm_template_str = self._load_template(os.path.join(os.path.dirname(ROOT_DIR), "backend", "app", "templates", "llm_report_template.html"))
        self.rubric_template_str = self._load_template(os.path.join(os.path.dirname(ROOT_DIR), "src", "resources", "report_template.html"))

    @staticmethod
    def _load_template(template_path: str) -> str:
        try:
            with open(template_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to a default simple template if a specific one is not found
            return "<h1>Report</h1><p>Template not found.</p><div>{findings}</div>"

    def generate_html_report(self, analysis_result: dict, doc_name: str, analysis_mode: str) -> str:
        if analysis_mode in ["llm_only", "hybrid"]:
            return self._generate_llm_report(analysis_result, doc_name)
        else:
            return self._generate_rubric_report(analysis_result, doc_name)

    def _generate_llm_report(self, analysis_result: dict, doc_name: str) -> str:
        template_str = self.llm_template_str
        report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
        report_html = report_html.replace("<!-- Placeholder for analysis date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        report_html = report_html.replace("<!-- Placeholder for generation date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        analysis_json_str = json.dumps(analysis_result)
        report_html = report_html.replace("<!-- {{ analysis_result_json | safe }} -->", analysis_json_str)
        return report_html

    def _generate_rubric_report(self, analysis_result: dict, doc_name: str) -> str:
        template_str = self.rubric_template_str
        report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
        report_html = report_html.replace("<!-- Placeholder for analysis date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        findings = analysis_result.get("findings", [])
        compliance_score = max(0, 100 - (len(findings) * 10))  # Simple scoring
        report_html = report_html.replace("<!-- Placeholder for compliance score -->", str(compliance_score))
        report_html = report_html.replace("<!-- Placeholder for total findings -->", str(len(findings)))

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

        guidelines_html = "<p>No relevant Medicare guidelines found.</p>"  # Placeholder
        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", guidelines_html)

        report_html = report_html.replace("<!-- Placeholder for generation date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return report_html
