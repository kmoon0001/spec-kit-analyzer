import json
import os
from typing import Any

from jinja2 import Template
from PySide6.QtWidgets import QFileDialog
from xhtml2pdf import pisa  # type: ignore[import-untyped]

DEFAULT_LIMITATIONS_TEXT = "This AI-generated report should be reviewed by a clinical compliance expert before use."


def _load_template(template_path: str) -> Template:
    with open(template_path, encoding="utf-8") as handle:
        return Template(handle.read())


def _normalize_finding(raw_finding: dict[str, Any]) -> dict[str, Any]:
    habit = raw_finding.get("habit") or {}
    return {
        "risk_level": raw_finding.get("risk") or raw_finding.get("risk_level") or "Unknown",
        "problematic_text": raw_finding.get("problematic_text") or raw_finding.get("text") or "",
        "personalized_tip": raw_finding.get("personalized_tip") or raw_finding.get("suggestion") or "",
        "habit": {
            "name": habit.get("name") or raw_finding.get("habit_name") or "General Habit",
            "explanation": habit.get("explanation") or raw_finding.get("habit_explanation") or "",
        },
        "low_confidence": bool(raw_finding.get("low_confidence", False)),
        "disputed": bool(raw_finding.get("disputed", False)),
        "disputable": bool(raw_finding.get("disputable", False)),
    }


def _build_analysis_context(payload: dict[str, Any]) -> dict[str, Any]:
    if "analysis" in payload and isinstance(payload["analysis"], dict):
        analysis_ctx = dict(payload["analysis"])
    else:
        analysis_ctx = {
            "document_name": payload.get("document_name", "Unknown Document"),
            "analysis_date": payload.get("analysis_date") or payload.get("generated_at") or "",
            "generation_date": payload.get("generation_date") or payload.get("analysis_date") or "",
            "compliance_score": payload.get("compliance_score", 0),
            "total_findings": payload.get("total_findings"),
            "findings": payload.get("findings", []),
            "limitations_text": payload.get(
                "limitations_text",
                DEFAULT_LIMITATIONS_TEXT),
        }

    findings: list[dict[str, Any]] = []
    for finding in analysis_ctx.get("findings", []):
        if isinstance(finding, dict):
            findings.append(_normalize_finding(finding))

    analysis_ctx["findings"] = findings
    analysis_ctx.setdefault("document_name", "Unknown Document")
    analysis_ctx.setdefault("analysis_date", "")
    analysis_ctx.setdefault("generation_date", analysis_ctx.get("analysis_date", ""))
    analysis_ctx.setdefault("compliance_score", 0)
    analysis_ctx.setdefault("limitations_text", DEFAULT_LIMITATIONS_TEXT)
    analysis_ctx["total_findings"] = analysis_ctx.get("total_findings", len(findings))

    return analysis_ctx


def generate_pdf_report(analysis_results_str: str, parent=None):
    """Generates a PDF report from serialized analysis results."""
    try:
        analysis_results = json.loads(analysis_results_str)
    except json.JSONDecodeError:
        return False, "Failed to decode analysis results."

    template_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "resources",
            "report_template.html"))

    if not os.path.exists(template_path):
        return False, f"Report template not found at {template_path}"

    template = _load_template(template_path)
    analysis_ctx = _build_analysis_context(analysis_results)

    html_content = template.render(
        analysis=analysis_ctx,
        guidelines=analysis_results.get("guidelines", []))

    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Report as PDF",
        "",
        "PDF Files (*.pdf)")

    if not file_path:
        return False, "File save cancelled."

    try:
        with open(file_path, "w+b") as handle:
            pisa_status = pisa.CreatePDF(html_content, dest=handle)
        if getattr(pisa_status, "err", 0):
            return False, f"PDF generation failed: {pisa_status.err}"
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return False, f"An error occurred while saving the PDF: {exc}"

    return True, file_path
