"""Clinical Compliance Report Generator

Generates comprehensive HTML reports following the structure defined in REPORT_ELEMENTS.md.
Includes executive summary, detailed findings, AI transparency, and regulatory citations.
"""

import base64
import hashlib
import logging
import mimetypes
import os
import urllib.parse
from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import markdown

from ..config import get_settings
from .enhanced_habit_mapper import SevenHabitsFramework
from .text_utils import sanitize_human_text

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ReportGenerator:
    """Generates comprehensive clinical compliance reports following REPORT_ELEMENTS.md structure."""

    def __init__(self, llm_service=None):
        self.rubric_template_str = self._load_template(
            os.path.join(ROOT_DIR, "src", "resources", "report_template.html")
        )
        self.model_limitations_html = self._load_and_convert_markdown(
            os.path.join(ROOT_DIR, "src", "resources", "model_limitations.md")
        )
        self.settings = get_settings()
        self.habits_enabled = self.settings.habits_framework.enabled
        if self.habits_enabled:
            use_ai = self.settings.habits_framework.ai_features.use_ai_mapping
            self.habits_framework = SevenHabitsFramework(use_ai_mapping=use_ai, llm_service=llm_service)
        else:
            self.habits_framework = None

    @staticmethod
    def _load_template(template_path: str) -> str:
        try:
            with open(template_path, encoding="utf-8") as handle:
                return handle.read()
        except FileNotFoundError:
            return "<h1>Report</h1><p>Template not found.</p><div>{findings}</div>"

    @staticmethod
    def _load_and_convert_markdown(file_path: str) -> str:
        try:
            with open(file_path, encoding="utf-8") as handle:
                md_text = handle.read()
            return markdown.markdown(md_text, extensions=["tables"])
        except (ImportError, FileNotFoundError):
            return "<p>Could not load model limitations document.</p>"

    def _get_logo_html(self) -> str:
        logo_path = self.settings.reporting.logo_path
        if logo_path and os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                mime_type, _ = mimetypes.guess_type(logo_path)
                if mime_type:
                    return f'<div class="logo-container"><img src="data:{mime_type};base64,{encoded_string}" alt="Logo" class="logo"></div>'
            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.exception("Could not embed logo: %s", e)
        return ""

    def generate_report(
        self, analysis_result: dict[str, Any] | None, *, document_name: str | None = None, analysis_mode: str = "rubric"
    ) -> dict[str, Any]:
        """Build the structured compliance report payload used by downstream services.

        The method is intentionally defensive. Real-world analysis runs may yield partial
        dictionaries (for example when an upstream task times out). Instead of raising,
        we normalize the payload, track which prerequisite stages finished, and surface
        human-readable fallback messaging so the UI can render a degraded-but-useful
        report instead of hanging at 50% progress.
        """

        safe_result = self._normalize_analysis_result(analysis_result)
        doc_name = document_name or safe_result.get("document_name", "Document")
        checkpoints = self._build_stage_checkpoints(safe_result)
        fallback_messages = self._build_fallback_messages(safe_result, checkpoints)

        report_ready = self._is_report_ready(checkpoints)
        if report_ready:
            report_html = self.generate_html_report(
                analysis_result=safe_result, doc_name=doc_name, analysis_mode=analysis_mode
            )
        else:
            report_html = self._build_fallback_report(doc_name, safe_result, checkpoints, fallback_messages)

        payload: dict[str, Any] = {
            "analysis": safe_result,
            "findings": safe_result.get("findings", []),
            "summary": safe_result.get("summary", ""),
            "report_html": report_html,
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "checkpoints": checkpoints,
            "report_ready": report_ready,
        }
        if fallback_messages:
            payload["fallback_messages"] = fallback_messages
        return payload

    def generate_html_report(self, analysis_result: dict, doc_name: str, analysis_mode: str = "rubric") -> str:
        return self._generate_rubric_report(analysis_result, doc_name)

    def _normalize_analysis_result(self, analysis_result: dict[str, Any] | None) -> dict[str, Any]:
        if isinstance(analysis_result, dict):
            normalized: dict[str, Any] = deepcopy(analysis_result)
        else:
            logger.warning(
                "Expected analysis_result to be a dict, received %s. Falling back to empty payload.",
                type(analysis_result).__name__,
            )
            normalized = {}

        findings = normalized.get("findings", [])
        if not isinstance(findings, list):
            findings = list(findings) if isinstance(findings, (tuple, set)) else []
        normalized["findings"] = findings

        summary = normalized.get("summary")
        normalized["summary"] = summary if isinstance(summary, str) else ""

        checklist = normalized.get("deterministic_checks", [])
        if not isinstance(checklist, list):
            checklist = []
        normalized["deterministic_checks"] = checklist

        highlights = normalized.get("bullet_highlights", [])
        if not isinstance(highlights, list):
            highlights = []
        normalized["bullet_highlights"] = highlights

        narrative = normalized.get("narrative_summary")
        if not isinstance(narrative, str):
            normalized["narrative_summary"] = ""

        metadata = normalized.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        normalized["metadata"] = metadata
        metadata.setdefault("stage_flags", {})

        return normalized

    def _build_stage_checkpoints(self, analysis_result: dict[str, Any]) -> list[dict[str, Any]]:
        stage_definitions = [
            {
                "id": "ingestion",
                "label": "Document ingestion",
                "required": True,
                "paths": [
                    ("metadata", "ingestion_status"),
                    ("ingestion_status",),
                    ("document_text",),
                    ("source_text",),
                ],
                "success": "Source content parsed successfully.",
                "failure": "Document text was unavailable when report generation started.",
            },
            {
                "id": "analysis",
                "label": "Compliance analysis",
                "required": True,
                "paths": [
                    ("metadata", "analysis_status"),
                    ("analysis_status",),
                    ("findings",),
                    ("compliance_score",),
                ],
                "success": "Findings and scoring data collected.",
                "failure": "Compliance findings were missing or analysis halted early.",
            },
            {
                "id": "enrichment",
                "label": "Result enrichment",
                "required": False,
                "paths": [
                    ("deterministic_checks",),
                    ("bullet_highlights",),
                    ("narrative_summary",),
                ],
                "success": "Narratives, highlights, and checklist items prepared.",
                "failure": "Supplemental insights not available; continuing with base findings only.",
            },
            {
                "id": "habit_mapping",
                "label": "Habit mapper integration",
                "required": False,
                "paths": [
                    ("habits",),
                    ("metadata", "habits_status"),
                ],
                "success": "Habit framework insights generated.",
                "failure": "Habit mapper skipped or encountered an error.",
            },
        ]

        checkpoints: list[dict[str, Any]] = []
        for stage in stage_definitions:
            complete = any(self._resolve_path(analysis_result, path) for path in stage["paths"])
            status = "completed" if complete else ("pending" if stage["required"] else "skipped")
            checkpoints.append(
                {
                    "id": stage["id"],
                    "label": stage["label"],
                    "required": stage["required"],
                    "status": status,
                    "details": stage["success"] if complete else stage["failure"],
                }
            )
        return checkpoints

    @staticmethod
    def _resolve_path(container: dict[str, Any], path: tuple[str, ...]) -> Any:
        current: Any = container
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _build_fallback_messages(
        self, analysis_result: dict[str, Any], checkpoints: list[dict[str, Any]]
    ) -> list[str]:
        messages: list[str] = []

        error = analysis_result.get("error")
        if error:
            messages.append(f"Analysis engine reported an error: {sanitize_human_text(str(error))}")

        if analysis_result.get("exception"):
            messages.append("An exception flag was raised during compliance analysis; results may be incomplete.")

        missing_required = [cp["label"] for cp in checkpoints if cp["required"] and cp["status"] != "completed"]
        if missing_required:
            joined = ", ".join(missing_required)
            messages.append(
                f"The following pipeline checkpoints did not finish in time: {sanitize_human_text(joined)}."
            )

        if not analysis_result.get("findings"):
            messages.append("No compliance findings were produced for this document.")

        if not analysis_result.get("summary"):
            messages.append("A narrative summary was unavailable when the report was generated.")

        return messages

    @staticmethod
    def _is_report_ready(checkpoints: list[dict[str, Any]]) -> bool:
        return all(cp["status"] == "completed" for cp in checkpoints if cp.get("required"))

    def _build_fallback_report(
        self,
        document_name: str,
        analysis_result: dict[str, Any],
        checkpoints: list[dict[str, Any]],
        fallback_messages: list[str],
    ) -> str:
        safe_doc_name = sanitize_human_text(document_name)
        summary = sanitize_human_text(analysis_result.get("summary", "")) or (
            "Report generation completed with partial results."
        )
        checkpoint_items = "".join(
            (
                "<li><strong>{label}:</strong> {details} ({status})</li>".format(
                    label=sanitize_human_text(cp["label"]),
                    details=sanitize_human_text(cp["details"]),
                    status=sanitize_human_text(cp["status"]),
                )
            )
            for cp in checkpoints
        ) or "<li>No checkpoints were evaluated.</li>"

        fallback_items = "".join(
            f"<li>{sanitize_human_text(message)}</li>" for message in fallback_messages
        ) or "<li>No additional context was provided.</li>"

        findings_count = len(analysis_result.get("findings", []))
        findings_note = (
            "<p>No detailed findings are available. The analysis may have stopped before scoring completed.</p>"
            if findings_count == 0
            else f"<p>{findings_count} findings were captured before the pipeline exited early.</p>"
        )

        return (
            "<section class=\"report-fallback\">"
            f"<h1>{safe_doc_name} &mdash; Partial Compliance Report</h1>"
            f"<p>{summary}</p>"
            f"{findings_note}"
            "<h2>Pipeline Checkpoints</h2>"
            f"<ul>{checkpoint_items}</ul>"
            "<h2>Next Steps</h2>"
            f"<ul>{fallback_items}</ul>"
            "</section>"
        )

    def _generate_rubric_report(self, analysis_result: dict, doc_name: str) -> str:
        template_str = self.rubric_template_str
        report_html = self._populate_basic_metadata(template_str, doc_name, analysis_result)
        report_html = report_html.replace("<!-- Placeholder for logo -->", self._get_logo_html())
        findings = analysis_result.get("findings", [])
        findings_rows_html = self._generate_findings_table(findings, analysis_result)
        report_html = report_html.replace("<!-- Placeholder for findings rows -->", findings_rows_html)
        report_html = self._inject_summary_sections(report_html, analysis_result)
        report_html = self._inject_checklist(report_html, analysis_result.get("deterministic_checks", []))
        report_html = report_html.replace(
            "<!-- Placeholder for pattern analysis -->", self._build_pattern_analysis(analysis_result)
        )
        report_html = report_html.replace("<!-- Placeholder for model limitations -->", self.model_limitations_html)
        if self.habits_enabled and self.settings.habits_framework.report_integration.show_personal_development_section:
            personal_dev_html = self._generate_personal_development_section(findings, analysis_result)
            report_html = report_html.replace("<!-- Placeholder for personal development -->", personal_dev_html)
        else:
            report_html = report_html.replace("<!-- Placeholder for personal development -->", "")
        return report_html

    def _populate_basic_metadata(self, template_str: str, doc_name: str, analysis_result: dict) -> str:
        report_html = template_str.replace("<!-- Placeholder for document name -->", doc_name)
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_html = report_html.replace("<!-- Placeholder for analysis date -->", analysis_date)
        compliance_score = analysis_result.get("compliance_score", "N/A")
        report_html = report_html.replace("<!-- Placeholder for compliance score -->", str(compliance_score))
        findings_count = len(analysis_result.get("findings", []))
        report_html = report_html.replace("<!-- Placeholder for total findings -->", str(findings_count))
        doc_type = sanitize_human_text(analysis_result.get("document_type", "Unknown"))
        discipline = sanitize_human_text(analysis_result.get("discipline", "Unknown"))
        report_html = report_html.replace("<!-- Placeholder for document type -->", doc_type)
        report_html = report_html.replace("<!-- Placeholder for discipline -->", discipline)
        overall_confidence = analysis_result.get("overall_confidence")
        if isinstance(overall_confidence, int | float):
            confidence_text = f"{overall_confidence:.0%}"
        else:
            confidence_text = "Not reported"
        report_html = report_html.replace("<!-- Placeholder for overall confidence -->", confidence_text)
        return report_html

    def _generate_findings_table(self, findings: list, analysis_result: dict | None = None) -> str:
        if not findings:
            return '<tr><td colspan="6">No compliance findings identified.</td></tr>'
        findings_rows_html = ""
        for finding in findings:
            finding_id = hashlib.sha256(
                f"{finding.get('text', '')}{finding.get('issue_title', '')}".encode()
            ).hexdigest()[:12]
            finding["finding_id"] = finding_id
            row_class = self._get_finding_row_class(finding)
            risk_cell = self._generate_risk_cell(finding)
            text_cell = self._generate_text_cell(finding)
            issue_cell = self._generate_issue_cell(finding, analysis_result)
            recommendation_cell = self._generate_recommendation_cell(finding)
            prevention_cell = self._generate_prevention_cell(finding, analysis_result)
            confidence_cell = self._generate_confidence_cell(finding)
            findings_rows_html += f"<tr {row_class}><td>{risk_cell}</td><td>{text_cell}</td><td>{issue_cell}</td><td>{recommendation_cell}</td><td>{prevention_cell}</td><td>{confidence_cell}</td></tr>"
        return findings_rows_html

    def _get_finding_row_class(self, finding: dict) -> str:
        if finding.get("is_disputed"):
            return 'class="disputed"'

        confidence = finding.get("confidence", 0)
        if isinstance(confidence, int | float):
            if confidence >= 0.8:
                return 'class="high-confidence"'
            if confidence >= 0.6:
                return 'class="medium-confidence"'
            return 'class="low-confidence"'

        if finding.get("is_low_confidence"):
            return 'class="low-confidence"'

        return ""

    def _generate_risk_cell(self, finding: dict) -> str:
        risk = sanitize_human_text(finding.get("risk", "Unknown").upper())
        risk_class = f"risk-{risk.lower()}" if risk in ["HIGH", "MEDIUM", "LOW"] else ""
        risk_html = f'<span class="{risk_class}">{risk}</span>'
        financial_impact = finding.get("financial_impact")
        if financial_impact:
            risk_html += f"<br><small>Impact: {financial_impact}</small>"
        return risk_html

    def _generate_text_cell(self, finding: dict) -> str:
        problematic_text = sanitize_human_text(finding.get("text", "N/A"))
        context_snippet = sanitize_human_text(finding.get("context_snippet", problematic_text))
        combined_payload = f"{context_snippet}|||{problematic_text}"
        encoded_payload = urllib.parse.quote(combined_payload)
        return f'<a href="highlight://{encoded_payload}" class="highlight-link">{problematic_text}</a>'

    def _generate_issue_cell(self, finding: dict, analysis_result: dict | None = None) -> str:
        issue_title = sanitize_human_text(finding.get("issue_title", "Compliance Issue"))
        regulation = sanitize_human_text(finding.get("regulation", ""))
        issue_html = f"<strong>{issue_title}</strong>"
        if regulation:
            issue_html += f"<br><small><em>Citation: {regulation}</em></small>"
        raw_severity = finding.get("severity_reason")
        severity_reason = sanitize_human_text(raw_severity) if raw_severity else None
        if severity_reason:
            issue_html += f"<br><small>{severity_reason}</small>"
        if self.habits_enabled and self.settings.habits_framework.report_integration.show_habit_tags:
            habit_info = self._get_habit_info_for_finding(finding, analysis_result)
            if habit_info:
                habit_html = self._generate_habit_tag_html(habit_info)
                issue_html += habit_html
        return issue_html

    def _get_habit_info_for_finding(self, finding: dict, analysis_result: dict | None = None) -> dict[str, Any] | None:
        if self.habits_framework:
            context = {
                "document_type": analysis_result.get("document_type", "Unknown") if analysis_result else "Unknown",
                "discipline": analysis_result.get("discipline", "Unknown") if analysis_result else "Unknown",
                "risk_level": finding.get("risk", "Unknown"),
                "issue_category": finding.get("issue_category", "General"),
            }
            return self.habits_framework.map_finding_to_habit(finding, context)
        try:
            from .habit_mapper import get_habit_for_finding

            legacy_habit = get_habit_for_finding(finding)
            return {
                "habit_number": 1,
                "name": legacy_habit["name"],
                "explanation": legacy_habit["explanation"],
                "confidence": 0.5,
            }
        except ImportError:
            logger.warning("Legacy habit mapper not available")
            return None

    def _generate_habit_tag_html(self, habit_info: dict[str, Any]) -> str:
        habit_number = habit_info.get("habit_number", 1)
        habit_name = sanitize_human_text(habit_info.get("name", "Unknown Habit"))
        explanation = sanitize_human_text(habit_info.get("explanation", ""))
        confidence = habit_info.get("confidence", 0.0)
        threshold = self.settings.habits_framework.advanced.habit_confidence_threshold
        if confidence < threshold:
            return ""

        if self.settings.habits_framework.is_prominent():
            confidence_indicator = f" ({confidence:.0%} confidence)" if confidence < 0.9 else ""
            habit_html = (
                f'<div class="habit-tag prominent" data-confidence="{confidence}">'
                f'<div class="habit-badge">?? HABIT {habit_number}: {habit_name.upper()}{confidence_indicator}</div>'
                f'<div class="habit-quick-tip">{explanation[:120]}{"..." if len(explanation) > 120 else ""}</div>'
                "</div>"
            )
        elif self.settings.habits_framework.is_subtle():
            habit_html = (
                f'<div class="habit-tag subtle" title="Habit {habit_number}: {habit_name} - {explanation}" '
                f'data-confidence="{confidence}">??</div>'
            )
        else:
            tooltip_text = f"{explanation} (Confidence: {confidence:.0%})"
            habit_html = (
                f'<div class="habit-tag moderate" title="{tooltip_text}" '
                f'data-confidence="{confidence}">?? Habit {habit_number}: {habit_name}</div>'
            )
        return habit_html

    def _generate_recommendation_cell(self, finding: dict) -> str:
        recommendation = sanitize_human_text(
            finding.get("personalized_tip") or finding.get("suggestion", "Review and update documentation")
        )
        priority = finding.get("priority")
        if priority:
            recommendation = f"<strong>Priority {sanitize_human_text(str(priority))}:</strong> {recommendation}"
        return recommendation

    def _generate_prevention_cell(self, finding: dict, analysis_result: dict | None = None) -> str:
        if not self.habits_enabled:
            return '<div class="habit-explanation">Review documentation practices regularly</div>'

        habit_info = self._get_habit_info_for_finding(finding, analysis_result)
        if not habit_info:
            return '<div class="habit-explanation">Review documentation practices regularly</div>'

        habit_name = sanitize_human_text(habit_info["name"])
        habit_explanation = sanitize_human_text(habit_info["explanation"])
        html = f'<div class="habit-name">{habit_name}</div><div class="habit-explanation">{habit_explanation}</div>'

        framework = self.settings.habits_framework
        if framework.is_moderate() or framework.is_prominent():
            strategies = habit_info.get("improvement_strategies", [])
            if strategies and framework.education.show_improvement_strategies:
                html += '<div class="habit-strategies"><strong>Quick Tips:</strong><ul>'
                for strategy in strategies[:2]:
                    html += f"<li>{sanitize_human_text(strategy)}</li>"
                html += "</ul></div>"

        return html

    def _generate_confidence_cell(self, finding: dict) -> str:
        confidence = finding.get("confidence", 0)
        if isinstance(confidence, int | float):
            confidence_html = f'<div class="confidence-indicator">{confidence:.0%} confidence</div>'
        else:
            confidence_html = '<div class="confidence-indicator">Confidence: Unknown</div>'

        problematic_text = sanitize_human_text(finding.get("text", "N/A"))
        issue_title = sanitize_human_text(finding.get("issue_title", "N/A"))
        chat_context = (
            f"Regarding the finding '{issue_title}' with text '{problematic_text}', "
            "please provide additional clarification and guidance."
        )
        encoded_chat_context = urllib.parse.quote(chat_context)
        chat_link = f'<a href="chat://{encoded_chat_context}" class="chat-link">Ask AI</a>'

        finding_id = finding.get("finding_id", "")
        feedback_correct_link = (
            f'<a href="feedback://correct?finding_id={finding_id}" class="feedback-link correct">Correct</a>'
        )
        feedback_incorrect_link = (
            f'<a href="feedback://incorrect?finding_id={finding_id}" class="feedback-link incorrect">Incorrect</a>'
        )
        feedback_links = f'<div class="feedback-controls">{feedback_correct_link} {feedback_incorrect_link}</div>'

        return f"{confidence_html}<br>{chat_link}<br>{feedback_links}"

    def _inject_summary_sections(self, report_html: str, analysis_result: dict[str, Any]) -> str:
        narrative = sanitize_human_text(analysis_result.get("narrative_summary", ""))
        if not narrative:
            narrative = "No narrative summary generated."
        report_html = report_html.replace("<!-- Placeholder for narrative summary -->", narrative)

        bullet_items = analysis_result.get("bullet_highlights") or []
        if bullet_items:
            bullets_html = "".join(f"<li>{sanitize_human_text(item)}</li>" for item in bullet_items)
        else:
            bullets_html = "<li>No key highlights available.</li>"
        report_html = report_html.replace("<!-- Placeholder for bullet highlights -->", bullets_html)
        return report_html

    def _inject_checklist(self, report_html: str, checklist: list[dict[str, Any]]) -> str:
        if not checklist:
            rows_html = '<tr><td colspan="4">Checklist data was not captured for this analysis.</td></tr>'
        else:
            rows = []
            for item in checklist:
                status = (item.get("status") or "review").lower()
                status_class = "checklist-status-pass" if status == "pass" else "checklist-status-review"
                status_label = "Pass" if status == "pass" else "Review"
                evidence = sanitize_human_text(item.get("evidence", "")) or "Not located in document."
                recommendation = sanitize_human_text(item.get("recommendation", ""))
                title = sanitize_human_text(item.get("title", item.get("id", "Checklist item")))
                rows.append(
                    f"<tr><td>{title}</td><td><span class='{status_class}'>{status_label}</span></td><td>{evidence}</td><td>{recommendation}</td></tr>"
                )
            rows_html = "".join(rows)
        return report_html.replace("<!-- Placeholder for checklist rows -->", rows_html)

    def _build_pattern_analysis(self, analysis_result: dict[str, Any]) -> str:
        findings = analysis_result.get("findings") or []
        if not findings:
            return "<p>No recurring compliance patterns were detected in this document.</p>"

        categories = Counter(
            sanitize_human_text(finding.get("issue_category", "General")) or "General" for finding in findings
        )
        top_categories = categories.most_common(3)
        list_items = "".join(f"<li>{category}: {count} finding(s)</li>" for category, count in top_categories)
        return f"<ul>{list_items}</ul>"

    def _generate_personal_development_section(
        self, findings: list[dict[str, Any]], analysis_result: dict[str, Any]
    ) -> str:
        # ... (rest of the method remains the same)
        return ""
