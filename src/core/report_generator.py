"""
Clinical Compliance Report Generator

Generates comprehensive HTML reports following the structure defined in REPORT_ELEMENTS.md.
Includes executive summary, detailed findings, AI transparency, and regulatory citations.
"""

import os
import urllib.parse
from datetime import UTC, datetime
from collections import Counter
from typing import Any, Dict, List

import markdown

from src.core.habit_mapper import get_habit_for_finding
from src.core.text_utils import sanitize_human_text

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
        report_html = self._populate_basic_metadata(
            template_str, doc_name, analysis_result
        )

        # Generate findings table
        findings = analysis_result.get("findings", [])
        findings_rows_html = self._generate_findings_table(findings)

        report_html = report_html.replace(
            "<!-- Placeholder for findings rows -->", findings_rows_html
        )

        report_html = self._inject_summary_sections(report_html, analysis_result)
        report_html = self._inject_checklist(
            report_html, analysis_result.get("deterministic_checks", [])
        )
        report_html = report_html.replace(
            "<!-- Placeholder for pattern analysis -->",
            self._build_pattern_analysis(analysis_result),
        )

        # Add AI transparency section
        report_html = report_html.replace(
            "<!-- Placeholder for model limitations -->", self.model_limitations_html
        )

        # Add analysis disclosures
        disclosures_html = self._generate_analysis_disclosures(analysis_result)
        report_html = report_html.replace(
            "<!-- Placeholder for analysis disclosures -->", disclosures_html
        )

        return report_html

    def _generate_analysis_disclosures(self, analysis_result: dict) -> str:
        """Generates the analysis disclosures section."""
        disclosures = []

        # Bias Analysis
        bias_analysis = analysis_result.get("bias_analysis", [])
        if bias_analysis:
            disclosures.append("<strong>Bias Check:</strong> Potential bias detected in recommendations. Please review carefully.")
        else:
            disclosures.append("<strong>Bias Check:</strong> No potential biases detected in recommendations.")

        # Quality Assurance
        qa_issues = analysis_result.get("qa_issues", [])
        if qa_issues:
            disclosures.append(f"<strong>Quality Assurance:</strong> {len(qa_issues)} potential inconsistency/ies found between clinical findings and recommendations.")
        else:
            disclosures.append("<strong>Quality Assurance:</strong> Recommendations appear consistent with clinical findings.")

        # AI Confidence
        overall_confidence = analysis_result.get("overall_confidence")
        if isinstance(overall_confidence, (int, float)):
            disclosures.append(f"<strong>AI Confidence:</strong> The overall confidence for this analysis is {overall_confidence:.0%}.")

        return "<br>".join(f"<p>{d}</p>" for d in disclosures)

    def _populate_basic_metadata(
        self, template_str: str, doc_name: str, analysis_result: dict
    ) -> str:
        """Populate basic report metadata and summary information."""
        report_html = template_str.replace(
            "<!-- Placeholder for document name -->", doc_name
        )

        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_html = report_html.replace(
            "<!-- Placeholder for analysis date -->", analysis_date
        )

        compliance_score = analysis_result.get("compliance_score", "N/A")
        report_html = report_html.replace(
            "<!-- Placeholder for compliance score -->", str(compliance_score)
        )

        findings_count = len(analysis_result.get("findings", []))
        report_html = report_html.replace(
            "<!-- Placeholder for total findings -->", str(findings_count)
        )

        doc_type = sanitize_human_text(analysis_result.get("document_type", "Unknown"))
        discipline = sanitize_human_text(analysis_result.get("discipline", "Unknown"))
        report_html = report_html.replace(
            "<!-- Placeholder for document type -->", doc_type
        )
        report_html = report_html.replace(
            "<!-- Placeholder for discipline -->", discipline
        )

        overall_confidence = analysis_result.get("overall_confidence")
        if isinstance(overall_confidence, (int, float)):
            confidence_text = f"{overall_confidence:.0%}"
        else:
            confidence_text = "Not reported"
        report_html = report_html.replace(
            "<!-- Placeholder for overall confidence -->", confidence_text
        )

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
        risk = sanitize_human_text(finding.get("risk", "Unknown").upper())
        risk_class = f"risk-{risk.lower()}" if risk in ["HIGH", "MEDIUM", "LOW"] else ""

        risk_html = f'<span class="{risk_class}">{risk}</span>'

        # Add financial impact if available
        financial_impact = finding.get("financial_impact")
        if financial_impact:
            risk_html += f"<br><small>Impact: {financial_impact}</small>"

        return risk_html

    def _generate_text_cell(self, finding: dict) -> str:
        """Generate problematic text cell with highlighting link."""
        problematic_text = sanitize_human_text(finding.get("text", "N/A"))
        context_snippet = sanitize_human_text(
            finding.get("context_snippet", problematic_text)
        )

        # Create highlight link for source document navigation
        combined_payload = f"{context_snippet}|||{problematic_text}"
        encoded_payload = urllib.parse.quote(combined_payload)

        return f'<a href="highlight://{encoded_payload}" class="highlight-link">{problematic_text}</a>'

    def _generate_issue_cell(self, finding: dict) -> str:
        """Generate compliance issue cell with regulatory citations."""
        issue_title = sanitize_human_text(
            finding.get("issue_title", "Compliance Issue")
        )
        regulation = sanitize_human_text(finding.get("regulation", ""))

        issue_html = f"<strong>{issue_title}</strong>"

        if regulation:
            issue_html += f"<br><small><em>Citation: {regulation}</em></small>"

        # Add severity justification if available
        raw_severity = finding.get("severity_reason")
        severity_reason = sanitize_human_text(raw_severity) if raw_severity else None
        if severity_reason:
            issue_html += f"<br><small>{severity_reason}</small>"

        return issue_html

    def _generate_recommendation_cell(self, finding: dict) -> str:
        """Generate actionable recommendations cell."""
        recommendation = sanitize_human_text(
            finding.get("personalized_tip")
            or finding.get("suggestion", "Review and update documentation")
        )

        # Add priority indicator if available
        priority = finding.get("priority")
        if priority:
            recommendation = f"<strong>Priority {sanitize_human_text(str(priority))}:</strong> {recommendation}"

        return recommendation

    def _generate_prevention_cell(self, finding: dict) -> str:
        """Generate prevention strategies cell using habit mapper."""
        habit = get_habit_for_finding(finding)
        habit_name = sanitize_human_text(habit["name"])
        habit_explanation = sanitize_human_text(habit["explanation"])

        return (
            f'<div class="habit-name">{habit_name}</div>'
            f'<div class="habit-explanation">{habit_explanation}</div>'
        )

    def _generate_confidence_cell(self, finding: dict) -> str:
        """Generate confidence and interactive actions cell."""
        confidence = finding.get("confidence", 0)

        # Confidence indicator
        if isinstance(confidence, (int, float)):
            confidence_html = (
                f'<div class="confidence-indicator">{confidence:.0%} confidence</div>'
            )
        else:
            confidence_html = (
                '<div class="confidence-indicator">Confidence: Unknown</div>'
            )

        # Chat link for clarification
        problematic_text = sanitize_human_text(finding.get("text", "N/A"))
        issue_title = sanitize_human_text(finding.get("issue_title", "N/A"))

        chat_context = (
            f"Regarding the finding '{issue_title}' with text '{problematic_text}', "
            f"please provide additional clarification and guidance."
        )
        encoded_chat_context = urllib.parse.quote(chat_context)
        chat_link = (
            f'<a href="chat://{encoded_chat_context}" class="chat-link">Ask AI</a>'
        )

        # Dispute mechanism
        dispute_link = (
            '<a href="dispute://finding" class="chat-link">Dispute Finding</a>'
        )

        return f"{confidence_html}<br>{chat_link}<br>{dispute_link}"

    def _inject_summary_sections(
        self, report_html: str, analysis_result: Dict[str, Any]
    ) -> str:
        narrative = sanitize_human_text(analysis_result.get("narrative_summary", ""))
        if not narrative:
            narrative = "No narrative summary generated."
        report_html = report_html.replace(
            "<!-- Placeholder for narrative summary -->", narrative
        )

        bullet_items = analysis_result.get("bullet_highlights") or []
        if bullet_items:
            bullets_html = "".join(
                f"<li>{sanitize_human_text(item)}</li>" for item in bullet_items
            )
        else:
            bullets_html = "<li>No key highlights available.</li>"
        report_html = report_html.replace(
            "<!-- Placeholder for bullet highlights -->", bullets_html
        )
        return report_html

    def _inject_checklist(
        self, report_html: str, checklist: List[Dict[str, Any]]
    ) -> str:
        if not checklist:
            rows_html = '<tr><td colspan="4">Checklist data was not captured for this analysis.</td></tr>'
        else:
            rows = []
            for item in checklist:
                status = (item.get("status") or "review").lower()
                status_class = (
                    "checklist-status-pass"
                    if status == "pass"
                    else "checklist-status-review"
                )
                status_label = "Pass" if status == "pass" else "Review"
                evidence = (
                    sanitize_human_text(item.get("evidence", ""))
                    or "Not located in document."
                )
                recommendation = sanitize_human_text(item.get("recommendation", ""))
                title = sanitize_human_text(
                    item.get("title", item.get("id", "Checklist item"))
                )
                rows.append(
                    f"<tr><td>{title}</td><td><span class='{status_class}'>{status_label}</span></td><td>{evidence}</td><td>{recommendation}</td></tr>"
                )
            rows_html = "".join(rows)
        return report_html.replace("<!-- Placeholder for checklist rows -->", rows_html)

    def _build_pattern_analysis(self, analysis_result: Dict[str, Any]) -> str:
        findings = analysis_result.get("findings") or []
        if not findings:
            return "<p>No recurring compliance patterns were detected in this document.</p>"
        categories = Counter(
            sanitize_human_text(finding.get("issue_category", "General")) or "General"
            for finding in findings
        )
        top_categories = categories.most_common(3)
        list_items = "".join(
            f"<li>{category}: {count} finding(s)</li>"
            for category, count in top_categories
        )
        return f"<ul>{list_items}</ul>"
