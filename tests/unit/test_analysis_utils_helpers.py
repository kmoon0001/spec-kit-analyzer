import pytest

from src.core.analysis_utils import (
    build_bullet_highlights,
    build_narrative_summary,
    build_summary_fallback,
    calculate_overall_confidence,
    enrich_analysis_result,
    trim_document_text,
)


class _StubChecklistService:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def evaluate(self, document_text, doc_type=None, discipline=None):
        self.calls.append((document_text, doc_type, discipline))
        return self.results


def test_trim_document_text_truncates_and_preserves_boundaries():
    long_text = "abc" * 50
    truncated = trim_document_text(long_text, max_chars=100)
    assert truncated.endswith("...")
    assert len(truncated) == 103

    unchanged = trim_document_text("short text", max_chars=100)
    assert unchanged == "short text"


def test_build_summary_fallback_handles_findings_and_flags():
    findings = [
        {"issue_title": "Missing signature", "severity": "high"},
        {"issue_title": "Incomplete plan", "severity": "medium"},
    ]
    checklist = [
        {"status": "review", "title": "Treatment frequency documented"},
        {"status": "pass", "title": "Goals reviewed"},
    ]
    fallback = build_summary_fallback({"findings": findings}, checklist)
    assert "2 findings" in fallback
    assert "Deterministic checks flagged" in fallback

    no_findings = build_summary_fallback({}, [])
    assert "no LLM-generated compliance findings" in no_findings


def test_build_narrative_summary_includes_follow_up_when_flagged():
    base = "Reviewed"
    flagged = [{"status": "review", "title": "Missing vitals"}]
    narrative = build_narrative_summary(base, flagged)
    assert "Immediate follow-up" in narrative

    clean = build_narrative_summary(base, [])
    assert "Core documentation elements were present" in clean


def test_build_bullet_highlights_deduplicates_and_filters_summary_overlap():
    checklist = [
        {
            "status": "review",
            "title": "Treatment plan",
            "recommendation": "Document the plan clearly",
        },
        {"status": "pass", "title": "Goals reviewed", "recommendation": ""},
    ]
    analysis_result = {
        "findings": [
            {"issue_title": "Missing signature", "suggestion": "Add clinician sign-off"},
            {"issue_title": "Late entry", "suggestion": "Record entry time"},
        ]
    }
    summary = "Treatment plan: Document the plan clearly"

    bullets = build_bullet_highlights(analysis_result, checklist, summary)
    assert all("Treatment plan" not in bullet for bullet in bullets)
    assert "Missing signature" in " ".join(bullets)
    assert "Late entry" in " ".join(bullets)


def test_calculate_overall_confidence_penalizes_flags():
    analysis_result = {
        "findings": [
            {"confidence": 0.9},
            {"confidence": 0.8},
        ]
    }
    checklist = [{"status": "review"}, {"status": "pass"}]

    confidence = calculate_overall_confidence(analysis_result, checklist)
    assert pytest.approx(confidence, rel=1e-3) == 0.8


def test_enrich_analysis_result_populates_missing_fields_with_fallbacks():
    checklist_results = [
        {
            "status": "review",
            "title": "Treatment frequency documented",
            "recommendation": "Add planned visits",
        },
        {
            "status": "pass",
            "title": "Goals reviewed",
            "recommendation": "",
        },
    ]
    checklist_service = _StubChecklistService(checklist_results)
    analysis_result = {
        "findings": [
            {"issue_title": "Missing signature", "severity": "high", "confidence": 0.9},
            {"issue_title": "Incomplete plan", "severity": "medium", "confidence": 0.7},
        ],
        "summary": "",
        "compliance_score": None,
    }

    enriched = enrich_analysis_result(
        analysis_result,
        document_text="Short clinical summary",
        discipline="OT",
        doc_type="progress_note",
        checklist_service=checklist_service,
    )

    assert enriched["discipline"] == "OT"
    assert enriched["document_type"] == "progress_note"
    assert enriched["summary"]
    assert "Immediate follow-up" in enriched["narrative_summary"]
    assert enriched["bullet_highlights"]
    assert enriched["compliance_score"] == 70
    assert checklist_service.calls[-1][1:] == ("progress_note", "OT")
