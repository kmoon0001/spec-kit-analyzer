# Standard library
import logging
import os
import re
import html
from typing import List, Tuple, Callable, Optional, Dict

# Third-party
import pandas as pd

# Local imports
from .rubric_service import RubricService
from .guideline_service import GuidelineService
from .database import get_bool_setting, get_str_setting, set_bool_setting, add_recent_file, set_str_setting, _file_fingerprint, _settings_fingerprint, _load_cached_outputs, _load_last_snapshot, persist_analysis_run, _save_snapshot, _compute_recent_trends, get_int_setting
from .utils import parse_document_content, scrub_phi, collapse_similar_sentences_tfidf, collapse_similar_sentences_simple, build_rich_summary, count_categories, _now_iso
from .reporting import generate_report_paths, export_report_json, export_report_pdf

logger = logging.getLogger(__name__)

def _get_analysis_parameters(scrub_override: Optional[bool], review_mode_override: Optional[str], dedup_method_override: Optional[str]) -> Dict:
    scrub_enabled = scrub_override if scrub_override is not None else get_bool_setting("scrub_phi", True)
    if scrub_override is not None: set_bool_setting("scrub_phi", scrub_override)

    CURRENT_REVIEW_MODE = "Moderate"
    if review_mode_override in ("Moderate", "Strict"):
        CURRENT_REVIEW_MODE = review_mode_override

    DEDUP_DEFAULTS = {"Moderate": {"method": "tfidf", "threshold": 0.50},
                      "Strict": {"method": "tfidf", "threshold": 0.70}}

    def get_similarity_threshold() -> float:
        raw = get_str_setting("dup_threshold", "")
        if raw:
            try: return float(raw)
            except (ValueError, TypeError):
                logger.warning(f"Invalid similarity threshold value: {raw}")
        return float(DEDUP_DEFAULTS.get(CURRENT_REVIEW_MODE, {"threshold": 0.50})["threshold"])

    threshold = get_similarity_threshold()
    dedup_method = (dedup_method_override or get_str_setting("dedup_method", "tfidf")).lower()
    if dedup_method_override: set_str_setting("dedup_method", dedup_method)

    return {
        "scrub_enabled": scrub_enabled,
        "review_mode": CURRENT_REVIEW_MODE,
        "dedup_method": dedup_method,
        "similarity_threshold": threshold
    }

def _process_document(file_path: str, params: Dict, report_cb: Callable) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    report_cb(10, "Parsing document")
    original = parse_document_content(file_path, get_str_setting("ocr_lang", "eng"))
    if len(original) == 1 and original[0][0].startswith(("Error:", "Info:")):
        raise ValueError(f"{original[0][1]}: {original[0][0]}")

    report_cb(30, "Scrubbing PHI" if params["scrub_enabled"] else "Skipping PHI scrubbing")
    processed = [(scrub_phi(t) if params["scrub_enabled"] else t, s) for (t, s) in original]

    report_cb(50, f"Reducing near-duplicates ({params['dedup_method']})")
    if params["dedup_method"] == "tfidf":
        collapsed = collapse_similar_sentences_tfidf(processed, params["similarity_threshold"])
    else:
        collapsed = collapse_similar_sentences_simple(processed, params["similarity_threshold"])

    return processed, list(collapsed)

def _perform_compliance_analysis(collapsed: List[Tuple[str, str]], params: Dict, guideline_service: Optional[GuidelineService]) -> Dict:
    full_text = "\n".join(t for t, _ in collapsed)
    strict_flag = (params["review_mode"] == "Strict")
    issues_base = _audit_from_rubric(full_text, params["selected_disciplines"], strict=strict_flag)
    issues_scored = _score_issue_confidence(_attach_issue_citations(issues_base, collapsed), collapsed)

    return {"issues": issues_scored, "full_text": full_text}

def _generate_reports(file_path: str, analysis_data: Dict, params: Dict, report_cb: Callable) -> Dict:
    report_cb(86, "Writing JSON/PDF")
    pdf_path, csv_path = generate_report_paths()
    json_path = pdf_path[:-4] + ".json"

    export_report_json(analysis_data, json_path)

    meta = {"file_name": os.path.basename(file_path), "run_time": _now_iso(),
            "risk_label": analysis_data["risk_label"], "risk_color": analysis_data["risk_color"]}
    export_report_pdf(
        lines=analysis_data["narrative_lines"],
        pdf_path=pdf_path,
        meta=meta,
        chart_data=analysis_data["sev_counts"],
        sev_counts=analysis_data["sev_counts"],
        cat_counts=analysis_data["cat_counts"]
    )

    flat = {
        "file_name": os.path.basename(file_path),
        "generated": _now_iso(),
        "review_mode": params["review_mode"],
        "dup_threshold": params["similarity_threshold"],
        "dedup_method": params["dedup_method"],
        "pages_est": analysis_data["metrics"]["pages"],
        "flags": analysis_data["sev_counts"]["flag"],
        "wobblers": analysis_data["sev_counts"]["wobbler"],
        "suggestions": analysis_data["sev_counts"]["suggestion"],
        "notes": analysis_data["sev_counts"]["auditor_note"],
        "sentences_raw": analysis_data["summary"]["total_sentences_raw"],
        "sentences_final": analysis_data["summary"]["total_sentences_final"],
        "dedup_removed": analysis_data["summary"]["dedup_removed"],
        "compliance_score": analysis_data["compliance"]["score"],
        "risk_label": analysis_data["risk_label"],
    }
    df = pd.DataFrame([flat])
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    return {"json": json_path, "pdf": pdf_path, "csv": csv_path}

def _generate_risk_dashboard(compliance_score: float, sev_counts: dict) -> list[str]:
    lines = ["--- Risk Dashboard ---"]
    score = compliance_score
    flags = sev_counts.get("flag", 0)
    wobblers = sev_counts.get("wobbler", 0)

    if score >= 90 and flags == 0: risk = "Low"; summary = "Good compliance posture."
    elif score >= 70 and flags <= 1: risk = "Medium"; summary = "Some areas need review."
    else: risk = "High"; summary = "Critical issues require attention."

    lines.append(f"Overall Risk: {risk}")
    lines.append(f"Compliance Score: {score:.1f}/100")
    lines.append(f"Summary: {summary}")
    lines.append(f"Critical Findings (Flags): {flags}")
    lines.append(f"Areas of Concern (Wobblers): {wobblers}")
    lines.append("")
    return lines

def _generate_compliance_checklist(strengths: list[str], weaknesses: list[str]) -> list[str]:
    lines = ["<h3>Compliance Checklist</h3>"]
    checklist_items = {
        "Provider Authentication": "Provider authentication (signature/date)",
        "Measurable Goals": "Goals appear to be measurable",
        "Medical Necessity": "Medical necessity is explicitly discussed",
        "Assistant Supervision": "Assistant involvement includes supervision context",
        "Plan/Certification": "Plan/certification is referenced"
    }

    def get_status_icon(key, text):
        if any(text in s for s in strengths): return "<span style='color: #28a745; font-weight: bold;'>✔</span>"
        elif any(text in w for w in weaknesses): return "<span style='color: #dc3545; font-weight: bold;'>❌</span>"
        else:
            simplified_weakness_text = text.split('(')[0].strip()
            if any(simplified_weakness_text in w for w in weaknesses): return "<span style='color: #dc3545; font-weight: bold;'>❌</span>"
            else: return "<span style='color: #6c757d; font-weight: bold;'>○</span>"

    lines.append("<table>")
    for key, text in checklist_items.items():
        icon = get_status_icon(key, text)
        lines.append(f"<tr><td style='padding-right: 10px;'>{icon}</td><td>{key}</td></tr>")
    lines.append("</table>")
    lines.append("")
    return lines

def _generate_suggested_questions(issues: list) -> list[str]:
    """Generates a list of suggested questions based on high-priority findings."""
    suggestions = []

    QUESTION_MAP = {
        "Provider signature/date possibly missing": "Why are signatures and dates important for compliance?",
        "Goals may not be measurable/time-bound": "What makes a therapy goal 'measurable' and 'time-bound'?",
        "Medical necessity not explicitly supported": "Can you explain 'Medical Necessity' in the context of a therapy note?",
        "Assistant supervision context unclear": "What are the supervision requirements for therapy assistants?",
        "Plan/Certification not clearly referenced": "How should the Plan of Care be referenced in a note?",
    }

    # Prioritize flags, then wobblers
    sorted_issues = sorted(issues, key=lambda x: ({"flag": 0, "wobbler": 1}.get(x.get('severity'), 2)))

    for issue in sorted_issues:
        if len(suggestions) >= 3:
            break

        title = issue.get('title')
        if title in QUESTION_MAP and QUESTION_MAP[title] not in suggestions:
            suggestions.append(QUESTION_MAP[title])

    logger.info(f"Generated {len(suggestions)} suggested questions.")
    return suggestions

def run_analyzer(file_path: str,
                 selected_disciplines: List[str],
                 scrub_override: Optional[bool] = None,
                 review_mode_override: Optional[str] = None,
                 dedup_method_override: Optional[str] = None,
                 progress_cb: Optional[Callable[[int, str], None]] = None,
                 cancel_cb: Optional[Callable[[], bool]] = None,
                 guideline_service: Optional[GuidelineService] = None) -> dict:

    def report(pct: int, msg: str):
        if progress_cb:
            try: progress_cb(max(0, min(100, int(pct))), msg)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def check_cancel():
        if cancel_cb:
            try:
                if cancel_cb(): raise KeyboardInterrupt("Operation cancelled")
            except KeyboardInterrupt: raise
            except Exception as e:
                logger.warning(f"Cancel callback failed: {e}")

    result_info = {"csv": None, "html": None, "json": None, "pdf": None, "summary": None}
    try:
        params = _get_analysis_parameters(scrub_override, review_mode_override, dedup_method_override)
        params["selected_disciplines"] = selected_disciplines

        set_bool_setting("last_analysis_from_cache", False)
        add_recent_file(file_path)

        processed, collapsed = _process_document(file_path, params, report)

        analysis_results = _perform_compliance_analysis(collapsed, params, guideline_service)

        summary = build_rich_summary(processed, collapsed)

        issues = analysis_results.get("issues", [])
        sev_counts = {
            "flag": sum(1 for i in issues if i.get("severity") == "flag"),
            "wobbler": sum(1 for i in issues if i.get("severity") == "wobbler"),
            "suggestion": sum(1 for i in issues if i.get("severity") == "suggestion"),
            "auditor_note": sum(1 for i in issues if i.get("severity") == "auditor_note"),
        }
        cat_counts = count_categories(issues)

        # Calculate compliance score
        compliance_score = 100
        compliance_score -= sev_counts["flag"] * 15
        compliance_score -= sev_counts["wobbler"] * 5
        compliance_score -= sev_counts["suggestion"] * 1
        compliance_score = max(0, compliance_score)

        # Determine risk level
        risk_label = "Low"
        risk_color = "#28a745"  # green
        if compliance_score < 70 or sev_counts["flag"] > 0:
            risk_label = "High"
            risk_color = "#dc3545"  # red
        elif compliance_score < 90 or sev_counts["wobbler"] > 0:
            risk_label = "Medium"
            risk_color = "#ffc107"  # yellow

        narrative_lines = _generate_risk_dashboard(compliance_score, sev_counts)

        analysis_data = {
            "issues": issues,
            "summary": summary,
            "metrics": {
                "pages": 1 # Placeholder
            },
            "risk_label": risk_label,
            "risk_color": risk_color,
            "narrative_lines": narrative_lines,
            "sev_counts": sev_counts,
            "cat_counts": cat_counts,
            "compliance": {"score": float(compliance_score)}
        }

        reports = _generate_reports(file_path, analysis_data, params, report)
        result_info.update(reports)

        report(100, "Done")
        return result_info

    except (ValueError, KeyboardInterrupt) as e:
        logger.warning(f"Analysis stopped: {e}")
        return result_info
    except FileNotFoundError as e:
        logger.error(f"File not found during analysis: {e}")
        return result_info
    except Exception as e:
        logger.exception(f"An unexpected error occurred in the analyzer: {e}")
        return result_info

def _audit_from_rubric(text: str, selected_disciplines: List[str], strict: bool | None = None) -> list[dict]:
    if not selected_disciplines: return []

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    rubric_map = {
        "pt": os.path.join(BASE_DIR, "pt_compliance_rubric.json"),
        "ot": os.path.join(BASE_DIR, "ot_compliance_rubric.json"),
        "slp": os.path.join(BASE_DIR, "slp_compliance_rubric.json"),
    }

    all_rules = []
    for discipline in selected_disciplines:
        path = rubric_map.get(discipline)
        if path and os.path.exists(path):
            try:
                service = RubricService(path)
                all_rules.extend(service.get_rules())
            except Exception as e:
                logger.warning(f"Failed to load rubric for {discipline}", exc_info=True)

    seen_titles = set()
    unique_rules = []
    for rule in all_rules:
        if rule.issue_title not in seen_titles:
            unique_rules.append(rule)
            seen_titles.add(rule.issue_title)

    t_lower = text.lower()
    issues = []
    s = bool(strict)

    for rule in unique_rules:
        positive_kws = [kw.lower() for kw in rule.positive_keywords]
        negative_kws = [kw.lower() for kw in rule.negative_keywords]

        triggered = False
        if rule.positive_keywords and rule.negative_keywords:
            if any(kw in t_lower for kw in positive_kws) and not any(kw in t_lower for kw in negative_kws):
                triggered = True
        elif rule.positive_keywords and not rule.negative_keywords:
            if any(kw in t_lower for kw in positive_kws):
                triggered = True
        elif not rule.positive_keywords and rule.negative_keywords:
            if not any(kw in t_lower for kw in negative_kws):
                triggered = True

        if triggered:
            severity = rule.strict_severity if s else rule.severity
            issues.append({
                "severity": severity, "title": rule.issue_title, "detail": rule.issue_detail,
                "category": rule.issue_category, "trigger_keywords": rule.positive_keywords
            })
    return issues

def _attach_issue_citations(issues_in: list[dict], records: list[tuple[str, str]], cap: int = 3) -> list[dict]:
    out: list[dict] = []
    for it in issues_in:
        q = (it.get("title", "") + " " + it.get("detail", "")).lower()
        tok = [w for w in re.findall(r"[a-z]{4,}", q)]
        cites: list[tuple[str, str]] = []
        trigger_keywords = it.get("trigger_keywords")

        for (text, src) in records:
            tl = text.lower()
            score = sum(1 for w in tok if w in tl)

            is_citation = score >= max(1, len(tok) // 4)
            if not is_citation and trigger_keywords:
                if any(kw.lower() in tl for kw in trigger_keywords):
                    is_citation = True

            if is_citation:
                text_to_cite = text.strip()
                if trigger_keywords:
                    sorted_kws = sorted(trigger_keywords, key=len, reverse=True)
                    pattern = r'(' + '|'.join(r'\b' + re.escape(kw) + r'\b' for kw in sorted_kws) + r')'
                    parts = re.split(pattern, text_to_cite, flags=re.IGNORECASE)
                    result_parts = [f"<b>{html.escape(p)}</b>" if i % 2 == 1 else html.escape(p) for i, p in enumerate(parts)]
                    final_text = "".join(result_parts)
                    cites.append((final_text, src))
                else:
                    cites.append((html.escape(text_to_cite), src))

            if len(cites) >= cap: break
        out.append({**it, "citations": cites})
    return out

def _score_issue_confidence(issues_in: list[dict], records: list[tuple[str, str]]) -> list[dict]:
    all_text = " ".join(t for t, _ in records).lower()
    doc_tok = set(re.findall(r"[a-z]{4,}", all_text))
    out: list[dict] = []
    for it in issues_in:
        q = (it.get("title", "") + " " + it.get("detail", "")).lower()
        q_tok = set(re.findall(r"[a-z]{4,}", q))
        conf = 0.3 if not q_tok else 0.25 + 0.75 * min(1.0, len(q_tok & doc_tok) / max(1, len(q_tok)))
        if it.get("citations"): conf = min(1.0, conf + 0.15)
        out.append({**it, "confidence": round(float(conf), 2)})
    return out
