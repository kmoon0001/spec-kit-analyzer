import os
from datetime import datetime
import sqlite3
import tempfile
from src.rubric_service import RubricService
from src.parsing import parse_document_content
from src.guideline_service import GuidelineService
from src.database import DATABASE_PATH

class AnalysisService:
    def __init__(self): 
        self.guideline_service = GuidelineService()
        guideline_sources = [
            "_default_medicare_benefit_policy_manual.txt",
            "_default_medicare_part.txt"
        ]
        self.guideline_service.load_and_index_guidelines(sources=guideline_sources)

    def analyze_document(self, file_path: str, rubric_id: int | None = None, discipline: str | None = None) -> str:
        # 1. Parse the document content
        document_chunks = parse_document_content(file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks])
        doc_name = os.path.basename(file_path)

        # 2. Load the rubric
        if rubric_id:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT content FROM rubrics WHERE id = ?", (rubric_id,))
                    result = cur.fetchone()
                if not result:
                    raise ValueError("Selected rubric not found.")
                rubric_content = result[0]

                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".ttl") as temp_rubric_file:
                    temp_rubric_file.write(rubric_content)
                    temp_rubric_path = temp_rubric_file.name

                rubric_service = RubricService(ontology_path=temp_rubric_path)
            finally:
                if 'temp_rubric_path' in locals() and os.path.exists(temp_rubric_path):
                    os.remove(temp_rubric_path)
        else:
            # Default rubric based on discipline or a general one
            # For now, using the hardcoded PT rubric as a default
            rubric_path = os.path.join("src", "resources", "pt_compliance_rubric.ttl")
            rubric_service = RubricService(ontology_path=rubric_path)

        rules = rubric_service.get_rules()

        # 3. Perform analysis
        findings = []
        for rule in rules:
            for keyword in rule.positive_keywords:
                if keyword.lower() in document_text.lower():
                    findings.append(rule)
                    break

        # 4. Calculate compliance score
        compliance_score = max(0, 100 - (len(findings) * 10))

        # 5. Generate the HTML report
        with open(os.path.join("src", "resources", "report_template.html"), "r") as f:
            template_str = f.read()

        # Populate summary
        report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
        report_html = report_html.replace("<!-- Placeholder for analysis date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        report_html = report_html.replace("<!-- Placeholder for compliance score -->", str(compliance_score))
        report_html = report_html.replace("<!-- Placeholder for total findings -->", str(len(findings)))

        # Populate findings table
        findings_rows_html = ""
        if findings:
            for finding in findings:
                # For now, a generic recommendation
                recommendation = "Review the finding and update the document accordingly."
                findings_rows_html += f"""
                <tr>
                    <td>{finding.severity}</td>
                    <td>{finding.issue_category}</td>
                    <td>{finding.issue_detail}</td>
                    <td>{recommendation}</td>
                </tr>
                """
        else:
            findings_rows_html = "<tr><td colspan='4'>No findings.</td></tr>"
        report_html = report_html.replace("<!-- Placeholder for findings rows -->", findings_rows_html)

        # Populate Medicare guidelines
        guidelines_html = ""
        if findings:
            for finding in findings:
                guideline_results = self.guideline_service.search(query=finding.issue_title, top_k=1)
                if guideline_results:
                    guidelines_html += "<div>"
                    guidelines_html += f"<h4>Related to: {finding.issue_title}</h4>"
                    for result in guideline_results:
                        guidelines_html += f"<p><strong>Source:</strong> {result['source']}</p>"
                        guidelines_html += f"<p>{result['text']}</p>"
                    guidelines_html += "</div>"
        if not guidelines_html:
            guidelines_html = "<p>No relevant Medicare guidelines found.</p>"
        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", guidelines_html)

        # Populate footer
        report_html = report_html.replace("<!-- Placeholder for generation date -->", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return report_html
