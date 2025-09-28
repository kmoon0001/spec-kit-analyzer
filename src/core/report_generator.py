"""
Clinical Compliance Report Generator

Generates comprehensive HTML reports following the structure defined in REPORT_ELEMENTS.md.
Includes executive summary, detailed findings, AI transparency, and regulatory citations.
"""
import os
import urllib.parse
from datetime import UTC, datetime
from typing import Any, Dict

import markdown

from .habit_mapper import get_habit_for_finding

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ReportGenerator:
    """
    Generates comprehensive clinical compliance reports following REPORT_ELEMENTS.md structure.
    
    Produces HTML reports with executive summary, detailed findings table, AI transparency
    section, regulatory citations, and action planning recommendations.
    """
    
    def __init__(self):
        self.rubric_template_str = self._load_template(
            os.path.join(ROOT_DIR, "src", "resources", "report_template.html")
        )
        self.model_limitations_html = self._load_and_convert_markdown(
            os.path.join(ROOT_DIR, "src", "resources", "model_limitations.md")
        )

    @staticmethod
    def _load_template(template_path: str) -> str:
        try:
            with open(template_path, "r", encoding="utf-8") as handle:
                return handle.read()
        except FileNotFoundError:
            return "<h1>Report</h1><p>Template not found.</p><div>{findings}</div>"

    @staticmethod
    def _load_and_convert_markdown(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                md_text = handle.read()
            return markdown.markdown(md_text, extensions=["tables"])
        except (ImportError, FileNotFoundError):
            return "<p>Could not load model limitations document.</p>"

    def generate_report(
        self,
        analysis_result: Dict[str, Any],
        *,
        document_name: str | None = None,
        analysis_mode: str = "rubric",
    ) -> Dict[str, Any]:
        """Build a normalized payload consumed by higher-level services."""
        doc_name = document_name or analysis_result.get("document_name", "Document")
        report_html = self.generate_html_report(
            analysis_result=analysis_result,
            doc_name=doc_name,
            analysis_mode=analysis_mode,
        )
        findings = analysis_result.get("findings", [])
        return {
            "analysis": analysis_result,
            "findings": findings,
            "summary": analysis_result.get("summary", ""),
            "report_html": report_html,
            "generated_at": datetime.now(tz=UTC).isoformat(),
        }

    def generate_html_report(
        self, analysis_result: dict, doc_name: str, analysis_mode: str = "rubric"
    ) -> str:
        """Generate HTML report based on analysis mode."""
        return self._generate_rubric_report(analysis_result, doc_name)

    def _generate_rubric_report(self, analysis_result: dict, doc_name: str) -> str:
        """Generate comprehensive rubric-based compliance report."""
        template_str = self.rubric_template_str
        
        # Basic report metadata
        report_html = self._populate_basic_metadata(template_str, doc_name, analysis_result)
        
        # Generate findings table
        findings = analysis_result.get("findings", [])
        findings_rows_html = self._generate_findings_table(findings)
        
        report_html = report_html.replace(
            "<!-- Placeholder for findings rows -->", findings_rows_html
        )
        
        # Add AI transparency section
        report_html = report_html.replace(
            "<!-- Placeholder for model limitations -->", self.model_limitations_html
        )
        
        return report_html
    
    def _populate_basic_metadata(self, template_str: str, doc_name: str, analysis_result: dict) -> str:
        """Populate basic report metadata and summary information."""
        report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
        
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_html = report_html.replace("<!-- Placeholder for analysis date -->", analysis_date)
        
        compliance_score = analysis_result.get("compliance_score", "N/A")
        report_html = report_html.replace("<!-- Placeholder for compliance score -->", str(compliance_score))
        
        findings_count = len(analysis_result.get("findings", []))
        report_html = report_html.replace("<!-- Placeholder for total findings -->", str(findings_count))
        
        return report_html
    
    def _generate_findings_table(self, findings: list) -> str:
        """Generate the detailed findings analysis table."""
        if not findings:
            return '<tr><td colspan="6">No compliance findings identified.</td></tr>'
        
        findings_rows_html = ""
        for finding in findings:
            # Determine row styling based on confidence and dispute status
            row_class = self._get_finding_row_class(finding)
            
            # Generate table cells
            risk_cell = self._generate_risk_cell(finding)
            text_cell = self._generate_text_cell(finding)
            issue_cell = self._generate_issue_cell(finding)
            recommendation_cell = self._generate_recommendation_cell(finding)
            prevention_cell = self._generate_prevention_cell(finding)
            confidence_cell = self._generate_confidence_cell(finding)
            
            findings_rows_html += f"""
            <tr {row_class}>
                <td>{risk_cell}</td>
                <td>{text_cell}</td>
                <td>{issue_cell}</td>
                <td>{recommendation_cell}</td>
                <td>{prevention_cell}</td>
                <td>{confidence_cell}</td>
            </tr>
            """
        
        return findings_rows_html
    
    def _get_finding_row_class(self, finding: dict) -> str:
        """Determine CSS class for finding row based on confidence and status."""
        if finding.get("is_disputed"):
            return 'class="disputed"'
        
        confidence = finding.get("confidence", 0)
        if isinstance(confidence, (int, float)):
            if confidence >= 0.8:
                return 'class="high-confidence"'
            elif confidence >= 0.6:
                return 'class="medium-confidence"'
            else:
                return 'class="low-confidence"'
        
        if finding.get("is_low_confidence"):
            return 'class="low-confidence"'
        
        return ""
    
    def _generate_risk_cell(self, finding: dict) -> str:
        """Generate risk level cell with appropriate styling."""
        risk = finding.get("risk", "Unknown").upper()
        risk_class = f"risk-{risk.lower()}" if risk in ["HIGH", "MEDIUM", "LOW"] else ""
        
        risk_html = f'<span class="{risk_class}">{risk}</span>'
        
        # Add financial impact if available
        financial_impact = finding.get("financial_impact")
        if financial_impact:
            risk_html += f'<br><small>Impact: {financial_impact}</small>'
        
        return risk_html
    
    def _generate_text_cell(self, finding: dict) -> str:
        """Generate problematic text cell with highlighting link."""
        problematic_text = finding.get("text", "N/A")
        context_snippet = finding.get("context_snippet", problematic_text)
        
        # Create highlight link for source document navigation
        combined_payload = f"{context_snippet}|||{problematic_text}"
        encoded_payload = urllib.parse.quote(combined_payload)
        
        return f'<a href="highlight://{encoded_payload}" class="highlight-link">{problematic_text}</a>'
    
    def _generate_issue_cell(self, finding: dict) -> str:
        """Generate compliance issue cell with regulatory citations."""
        issue_title = finding.get("issue_title", "Compliance Issue")
        regulation = finding.get("regulation", "")
        
        issue_html = f"<strong>{issue_title}</strong>"
        
        if regulation:
            issue_html += f"<br><small><em>Citation: {regulation}</em></small>"
        
        # Add severity justification if available
        severity_reason = finding.get("severity_reason")
        if severity_reason:
            issue_html += f"<br><small>{severity_reason}</small>"
        
        return issue_html
    
    def _generate_recommendation_cell(self, finding: dict) -> str:
        """Generate actionable recommendations cell."""
        recommendation = finding.get("personalized_tip") or finding.get("suggestion", "Review and update documentation")
        
        # Add priority indicator if available
        priority = finding.get("priority")
        if priority:
            recommendation = f"<strong>Priority {priority}:</strong> {recommendation}"
        
        return recommendation
    
    def _generate_prevention_cell(self, finding: dict) -> str:
        """Generate prevention strategies cell using habit mapper."""
        habit = get_habit_for_finding(finding)
        
        return (
            f'<div class="habit-name">{habit["name"]}</div>'
            f'<div class="habit-explanation">{habit["explanation"]}</div>'
        )
    
    def _generate_confidence_cell(self, finding: dict) -> str:
        """Generate confidence and interactive actions cell."""
        confidence = finding.get("confidence", 0)
        
        # Confidence indicator
        if isinstance(confidence, (int, float)):
            confidence_html = f'<div class="confidence-indicator">{confidence:.0%} confidence</div>'
        else:
            confidence_html = '<div class="confidence-indicator">Confidence: Unknown</div>'
        
        # Chat link for clarification
        problematic_text = finding.get("text", "N/A")
        issue_title = finding.get("issue_title", "N/A")
        
        chat_context = (
            f"Regarding the finding '{issue_title}' with text '{problematic_text}', "
            f"please provide additional clarification and guidance."
        )
        encoded_chat_context = urllib.parse.quote(chat_context)
        chat_link = f'<a href="chat://{encoded_chat_context}" class="chat-link">Ask AI</a>'
        
        # Dispute mechanism
        dispute_link = '<a href="dispute://finding" class="chat-link">Dispute Finding</a>'
        
        return f"{confidence_html}<br>{chat_link}<br>{dispute_link}"
