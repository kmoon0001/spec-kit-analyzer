from types import SimpleNamespace

import pytest

from src.core.analysis_service import AnalysisService


@pytest.mark.asyncio
async def test_analysis_service_uses_analysis_utils(monkeypatch):
    service = AnalysisService.__new__(AnalysisService)

    phi_calls = {}
    compliance_calls = {}
    trim_calls = {}
    enrich_calls = {}
    cache_calls = {}

    def fake_trim(text: str) -> str:
        trim_calls["text"] = text
        return "trimmed-text"

    async def fake_analyze_document(document_text: str, discipline: str, doc_type: str):
        compliance_calls["document_text"] = document_text
        compliance_calls["discipline"] = discipline
        compliance_calls["doc_type"] = doc_type
        return {"findings": [], "summary": "ok"}

    def fake_scrub(text: str) -> str:
        phi_calls["text"] = text
        return text

    def fake_checklist(document_text: str, *, doc_type: str, discipline: str):
        return [{"title": "Checklist", "status": "pass", "recommendation": "ok"}]

    def fake_enrich(result, *, document_text: str, discipline: str, doc_type: str, checklist_service):
        enrich_calls["result"] = result
        enrich_calls["document_text"] = document_text
        enrich_calls["discipline"] = discipline
        enrich_calls["doc_type"] = doc_type
        enrich_calls["checklist_service"] = checklist_service
        return {"enriched": True, "summary": result.get("summary", "")}

    async def fake_generate_report(enriched):
        cache_calls["report_input"] = enriched
        return {"report_html": "<p>report</p>"}

    def fake_cache_set(key, value):
        cache_calls["set_key"] = key
        cache_calls["set_value"] = value

    monkeypatch.setattr("src.core.analysis_service.trim_document_text", fake_trim)
    monkeypatch.setattr("src.core.analysis_service.enrich_analysis_result", fake_enrich)
    monkeypatch.setattr("src.core.analysis_service.cache_service.get_from_disk", lambda key: None)
    monkeypatch.setattr("src.core.analysis_service.cache_service.set_to_disk", fake_cache_set)

    service.phi_scrubber = SimpleNamespace(scrub=fake_scrub)
    service.preprocessing = SimpleNamespace()
    service.document_classifier = SimpleNamespace(classify_document=lambda _: "DocType")
    service.compliance_analyzer = SimpleNamespace(analyze_document=fake_analyze_document)
    service.report_generator = SimpleNamespace(generate_report=fake_generate_report)
    service.checklist_service = SimpleNamespace(evaluate=fake_checklist)

    result = await service.analyze_document(document_text="original text", discipline="PT")

    assert trim_calls["text"] == "original text"
    assert phi_calls["text"] == "trimmed-text"
    assert compliance_calls["document_text"] == "trimmed-text"
    assert enrich_calls["checklist_service"] is service.checklist_service
    assert enrich_calls["document_text"] == "trimmed-text"
    assert result["analysis"]["enriched"] is True
    assert result["report_html"] == "<p>report</p>"
    assert cache_calls["set_value"]["analysis"]["enriched"] is True
