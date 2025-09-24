import os
from datetime import datetime
import sqlite3
import tempfile
from src.rubric_service import RubricService
from src.parsing import parse_document_content
from src.guideline_service import GuidelineService
from src.database import DATABASE_PATH
from src.core.document_analysis_service import DocumentAnalysisService
from src.core.llm_analyzer import LLMComplianceAnalyzer

class AnalysisService:
    def __init__(self):  
        guideline_sources = [
            "_default_medicare_benefit_policy_manual.txt",
            "_default_medicare_part.txt"
        ]
        self.guideline_service = GuidelineService(sources=guideline_sources)
        self.llm_analyzer = LLMComplianceAnalyzer(guideline_service=self.guideline_service)

    def analyze_document(self, file_path: str, rubric_id: int | None = None, discipline: str | None = None) -> str:
        # 1. Parse the document content and add discipline metadata
        document_chunks = parse_document_content(file_path)
        if discipline:
            for chunk in document_chunks:
                chunk['metadata']['discipline'] = discipline

        doc_name = os.path.basename(file_path)

        # 2. Create a searchable index of the document
        doc_analysis_service = DocumentAnalysisService(chunks=document_chunks)

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

        # 3. Perform analysis by searching for rule keywords in the document
        findings = []
        for rule in rules:
            all_matches_for_rule = []
            for keyword in rule.positive_keywords:
                # Search for the keyword in the document chunks
                metadata_filter = {'discipline': discipline} if discipline else None
                search_results = doc_analysis_service.search(query=keyword, top_k=3, metadata_filter=metadata_filter)
                if search_results:
                    all_matches_for_rule.extend(search_results)

            if all_matches_for_rule:
                # Remove duplicate chunks if a rule has multiple keywords that match the same chunk
                unique_matches = list({v['sentence']:v for v in all_matches_for_rule}.values())
                findings.append({'rule': rule, 'matches': unique_matches})

        # 4. Perform LLM-based analysis
        document_text = " ".join([chunk['sentence'] for chunk in document_chunks])
        llm_findings = self.llm_analyzer.analyze_document(document_text, discipline)

        # Combine findings
        # For now, we just append them. A more sophisticated approach could be to merge them based on similarity.
        if "findings" in llm_findings:
            for llm_finding in llm_findings["findings"]:
                # Create a dummy rule for the LLM finding
                from src.rubric_service import ComplianceRule
                rule = ComplianceRule(
                    uri='llm_finding',
                    severity='medium',
                    strict_severity='medium',
                    issue_title=llm_finding.get('risk', 'LLM Finding'),
                    issue_detail=llm_finding.get('text', ''),
                    issue_category='LLM',
                    discipline=discipline or 'All',
                    suggestion=llm_finding.get('suggestion', '')
                )
                findings.append({'rule': rule, 'matches': [{'sentence': llm_finding.get('text', ''), 'window': ''}]})

        # 5. Calculate compliance score
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
                rule = finding['rule']
                # Main row for the rule
                findings_rows_html += f"""
                <tr class="finding-rule">
                    <td>{rule.severity}</td>
                    <td>{rule.issue_category}</td>
                    <td colspan="2">{rule.issue_detail}</td>
                </tr>
                """
                # Sub-rows for each piece of evidence (matching chunk)
                for match in finding['matches']:
                    findings_rows_html += f"""
                    <tr class="finding-evidence">
                        <td></td>
                        <td colspan="3">
                            <strong>Evidence:</strong> "{match['sentence']}"
                            <br>
                            <em>Context: "{match['window']}"</em>
                        </td>
                    </tr>
                    """
        else:
            findings_rows_html = "<tr><td colspan='4'>No findings.</td></tr>"
        report_html = report_html.replace("<!-- Placeholder for findings rows -->", findings_rows_html)

        # Populate Medicare guidelines
        guidelines_html = ""
        if findings:
            for finding in findings:
                rule = finding['rule']
                guideline_results = self.guideline_service.search(query=rule.issue_title, top_k=1)
                if guideline_results:
                    guidelines_html += "<div>"
                    guidelines_html += f"<h4>Related to: {rule.issue_title}</h4>"
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
