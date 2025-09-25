import os
from datetime import datetime
import markdown
import urllib.parse

from .risk_scoring_service import RiskScoringService
from .habit_mapper import get_habit_for_finding

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
            with open(file_path, "r") as f:
                md_text = f.read()
            return markdown.markdown(md_text, extensions=['tables'])
        except (ImportError, FileNotFoundError):
            return "<p>Could not load model limitations document.</p>"

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
                # Determine the row class based on flags
                row_class = ''
                if finding.get('is_disputed'):
                    row_class = 'class="disputed"'
                elif finding.get('is_low_confidence'):
                    row_class = 'class="low-confidence"'

# Create the risk/confidence display string
                risk_display = finding.get('risk', 'N/A')
                if finding.get('is_disputed'):
                    risk_display += " <b>(Disputed by Fact-Checker)</b>"
                else:
                    confidence = finding.get('confidence')
                    if isinstance(confidence, (int, float)):
                        risk_display += f" ({confidence:.0%} confidence)"
                    elif finding.get('is_low_confidence'):
                        risk_display += " (Low Confidence)"

                tip_to_display = finding.get('personalized_tip', finding.get('suggestion', 'N/A'))

                problematic_text = finding.get('text', 'N/A')
                context_snippet = finding.get('context_snippet', problematic_text)

                combined_payload = f"{context_snippet}|||{problematic_text}"
                encoded_payload = urllib.parse.quote(combined_payload)
                clickable_text = f'<a href="highlight://{encoded_payload}">{problematic_text}</a>'

                chat_context = f"Regarding the finding titled '{finding.get('issue_title', 'N/A')}', which you identified with the text '{problematic_text}', please explain further."
                encoded_chat_context = urllib.parse.quote(chat_context)
                chat_link = f'<a href="chat://{encoded_chat_context}">Discuss with AI</a>'

                habit = get_habit_for_finding(finding)
                habit_html = f'<div class="habit-name">{habit["name"]}</div><div class="habit-explanation">{habit["explanation"]}</div>'

                findings_rows_html += f"""
                <tr {row_class}>
                    <td>{risk_display}</td>
                    <td>{clickable_text}</td>
                    <td>{tip_to_display}</td>
                    <td>{habit_html}</td>
                    <td>{chat_link}</td>
                </tr>
                """
        else:
            findings_rows_html = "<tr><td colspan='5'>No findings.</td></tr>"
        report_html = report_html.replace("<!-- Placeholder for findings rows -->", findings_rows_html)

        report_html = report_html.replace("<!-- Placeholder for model limitations -->", self.model_limitations_html)

        return report_html
