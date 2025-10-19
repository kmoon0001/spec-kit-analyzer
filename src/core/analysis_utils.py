import logging

from src.core.checklist_service import DeterministicChecklistService as ChecklistService
from src.core.text_utils import sanitize_bullets, sanitize_human_text

logger = logging.getLogger(__name__)


def trim_document_text(document_text: str, *, max_chars: int = 12000) -> str:
    return document_text[:max_chars] + "..." if len(document_text) > max_chars else document_text


def enrich_analysis_result(
    analysis_result: dict, *, document_text: str, discipline: str, doc_type: str, checklist_service: ChecklistService
) -> dict:
    result = dict(analysis_result)
    result.setdefault("discipline", discipline)
    result.setdefault("document_type", doc_type)
    checklist = checklist_service.evaluate(document_text, doc_type=doc_type, discipline=discipline)
    result["deterministic_checks"] = checklist
    summary = sanitize_human_text(result.get("summary", "")) or build_summary_fallback(result, checklist)
    result["summary"] = summary
    result["narrative_summary"] = build_narrative_summary(summary, checklist)
    result["bullet_highlights"] = build_bullet_highlights(result, checklist, summary)
    result["overall_confidence"] = calculate_overall_confidence(result, checklist)

    # Ensure compliance score is preserved from analysis result
    if "compliance_score" not in result or result["compliance_score"] is None:
        # Calculate compliance score from findings if not present
        findings = result.get("findings", [])
        if findings:
            high_severity = len([f for f in findings if f.get('severity') == 'high'])
            medium_severity = len([f for f in findings if f.get('severity') == 'medium'])
            low_severity = len([f for f in findings if f.get('severity') == 'low'])

            base_score = 100
            base_score -= high_severity * 20
            base_score -= medium_severity * 10
            base_score -= low_severity * 5
            result["compliance_score"] = max(0, min(100, base_score))
        else:
            result["compliance_score"] = 85.0  # Default score when no findings

    return result


def build_summary_fallback(analysis_result: dict, checklist: list) -> str:
    findings = analysis_result.get("findings") or []
    highlights = ", ".join(sanitize_human_text(f.get("issue_title", "finding")) for f in findings[:3])
    base = (
        f"Reviewed documentation uncovered {len(findings)} findings: {highlights}."
        if findings
        else "Reviewed documentation shows no LLM-generated compliance findings."
    )
    flagged = [item for item in checklist if item.get("status") != "pass"]
    if flagged:
        titles = ", ".join(sanitize_human_text(item.get("title", "")) for item in flagged[:3])
        base += f" Deterministic checks flagged: {titles}."
    return base


def build_narrative_summary(base_summary: str, checklist: list) -> str:
    flagged = [item for item in checklist if item.get("status") != "pass"]
    if not flagged:
        return sanitize_human_text(base_summary + " Core documentation elements were present.")
    focus = ", ".join(sanitize_human_text(item.get("title", "")) for item in flagged[:3])
    return sanitize_human_text(f"{base_summary} Immediate follow-up recommended for: {focus}.")


def build_bullet_highlights(analysis_result: dict, checklist: list, summary: str) -> list[str]:
    bullets = [
        f"{item.get('title')}: {item.get('recommendation')}" for item in checklist if item.get("status") != "pass"
    ]
    findings = analysis_result.get("findings") or []
    for finding in findings[:4]:
        issue = finding.get("issue_title") or finding.get("rule_name")
        suggestion = finding.get("personalized_tip") or finding.get("suggestion")
        if issue and suggestion:
            bullets.append(f"{issue}: {suggestion}")
        elif issue:
            bullets.append(issue)

    summary_lower = summary.lower()
    seen: set[str] = set()
    sanitized: list[str] = []
    for bullet in sanitize_bullets(bullets):
        lowered = bullet.lower()
        if lowered in seen or lowered in summary_lower:
            continue
        seen.add(lowered)
        sanitized.append(bullet)
    return sanitized


def calculate_overall_confidence(analysis_result: dict, checklist: list) -> float:
    findings = analysis_result.get("findings") or []
    conf_values = [float(f.get("confidence")) for f in findings if isinstance(f.get("confidence"), int | float)]
    base_conf = sum(conf_values) / len(conf_values) if conf_values else 0.85
    penalty = 0.05 * sum(1 for item in checklist if item.get("status") != "pass")
    return max(0.0, min(1.0, base_conf - penalty))
