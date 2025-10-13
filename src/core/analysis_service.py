import asyncio
import datetime
import hashlib
import json
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.config import get_settings as _get_settings
from src.core.analysis_utils import enrich_analysis_result, trim_document_text
from src.core.cache_service import cache_service
from src.core.checklist_service import DeterministicChecklistService as ChecklistService
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.document_classifier import DocumentClassifier
from src.core.explanation import ExplanationEngine
from src.core.fact_checker_service import FactCheckerService
from src.core.hybrid_retriever import HybridRetriever
from src.core.llm_service import LLMService
from src.core.model_selection_utils import (
    resolve_local_model_path,
    select_generator_profile,
)
from src.core.ner import ClinicalNERService
from src.core.nlg_service import NLGService
from src.core.parsing import parse_document_content
from src.core.phi_scrubber import PhiScrubberService
from src.core.preprocessing_service import PreprocessingService
from src.core.report_generator import ReportGenerator
from src.core.text_utils import sanitize_human_text
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]


class AnalysisOutput(dict):
    """Dictionary wrapper for consistent analysis output."""



class _MockLLMService:
    """Lightweight mock implementation used when USE_AI_MOCKS is enabled."""

    backend = "mock"

    def is_ready(self) -> bool:
        return True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return (
            "Mock analysis response generated for testing purposes. "
            "No real language model invocation occurred."
        )

    def generate_analysis(self, prompt: str, **kwargs: Any) -> str:
        return self.generate(prompt, **kwargs)

    def parse_json_output(self, raw: str | bytes) -> dict[str, Any]:
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            return json.loads(raw)
        except Exception:
            return {"text": raw}


class _MockRetriever:
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        **_: Any,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "mock-rule-1",
                "name": "Comprehensive Documentation",
                "content": "Include subjective, objective, assessment, and plan sections.",
                "category": "Default",
                "relevance_score": 0.95,
            }
        ]


def get_settings():
    """Legacy helper retained for tests that patch this symbol."""
    return _get_settings()


class AnalysisService:
    """Orchestrates the document analysis process with a best-practices, two-stage pipeline."""

    use_mocks: bool = False  # default for tests that construct via __new__

    def __init__(self, *args, **kwargs):
        settings = _get_settings()
        self._settings = settings
        self.use_mocks = bool(getattr(settings, "use_ai_mocks", False))

        # Services used across both mocked and full pipelines
        self.checklist_service = kwargs.get("checklist_service") or ChecklistService()
        self.phi_scrubber = kwargs.get("phi_scrubber") or PhiScrubberService()
        self.preprocessing = kwargs.get("preprocessing") or PreprocessingService()

        if self.use_mocks:
            # Lightweight substitutes to avoid heavyweight model loading during tests/CI runs.
            self.llm_service = kwargs.get("llm_service") or _MockLLMService()
            self.retriever = kwargs.get("retriever") or _MockRetriever()
            self.clinical_ner_service = kwargs.get("clinical_ner_service")
            self.document_classifier = kwargs.get("document_classifier")
            self.prompt_manager = kwargs.get("prompt_manager") or None
            self.explanation_engine = kwargs.get("explanation_engine") or None
            self.fact_checker_service = kwargs.get("fact_checker_service") or None
            self.nlg_service = kwargs.get("nlg_service") or None
            self.compliance_analyzer = kwargs.get("compliance_analyzer") or None
            self.report_generator = kwargs.get("report_generator") or None
            return

        repo_id, filename, revision = select_generator_profile(settings.models.model_dump())
        local_model_path = resolve_local_model_path(settings)

        # Stage 2 Services: Clinical Analysis on Anonymized Text
        self.llm_service = kwargs.get("llm_service") or LLMService(
            model_repo_id=repo_id,
            model_filename=filename,
            llm_settings=settings.llm.model_dump(),
            revision=revision,
            local_model_path=local_model_path,
        )
        self.retriever = kwargs.get("retriever") or HybridRetriever()
        self.clinical_ner_service = kwargs.get("clinical_ner_service") or ClinicalNERService(
            model_names=settings.models.ner_ensemble
        )
        template_path = Path(settings.models.analysis_prompt_template)
        self.prompt_manager = kwargs.get("prompt_manager") or PromptManager(template_name=template_path.name)
        self.explanation_engine = kwargs.get("explanation_engine") or ExplanationEngine()
        self.fact_checker_service = kwargs.get("fact_checker_service") or FactCheckerService(
            model_name=settings.models.fact_checker
        )
        self.nlg_service = kwargs.get("nlg_service") or NLGService(
            llm_service=self.llm_service, prompt_template_path=settings.models.nlg_prompt_template
        )
        self.compliance_analyzer = kwargs.get("compliance_analyzer") or ComplianceAnalyzer(
            retriever=self.retriever,
            ner_service=self.clinical_ner_service,
            llm_service=self.llm_service,
            explanation_engine=self.explanation_engine,
            prompt_manager=self.prompt_manager,
            fact_checker_service=self.fact_checker_service,
            nlg_service=self.nlg_service,
            deterministic_focus=settings.analysis.deterministic_focus,
        )
        self.document_classifier = kwargs.get("document_classifier") or DocumentClassifier(
            llm_service=self.llm_service, prompt_template_path=settings.models.doc_classifier_prompt
        )
        self.report_generator = kwargs.get("report_generator") or ReportGenerator()

    async def _maybe_await(self, obj):
        if asyncio.iscoroutine(obj):
            return await obj
        return obj

    def _get_analysis_cache_key(self, content_hash: str, discipline: str, analysis_mode: str | None) -> str:
        hasher = hashlib.sha256()
        hasher.update(content_hash.encode())
        hasher.update(discipline.encode())
        if analysis_mode:
            hasher.update(analysis_mode.encode())
        return f"analysis_report_{hasher.hexdigest()}"

    async def analyze_document(
        self,
        discipline: str = "pt",
        analysis_mode: str | None = None,
        document_text: str | None = None,
        file_content: bytes | None = None,
        original_filename: str | None = None,
        progress_callback: Callable[[int, str | None], None] | None = None,
    ) -> Any:
        """Analyzes document content for compliance, using a content-aware cache."""

        def _update_progress(percentage: int, message: str | None) -> None:
            if progress_callback:
                progress_callback(percentage, message)

        _update_progress(0, "Starting analysis pipeline...")

        temp_file_path: Path | None = None
        try:
            if file_content:
                content_hash = hashlib.sha256(file_content).hexdigest()
            elif document_text:
                content_hash = hashlib.sha256(document_text.encode()).hexdigest()
            else:
                raise ValueError("Either file_content or document_text must be provided")

            cache_key = self._get_analysis_cache_key(content_hash, discipline, analysis_mode)
            cached_result = None
            if not self.use_mocks:
                cached_result = cache_service.get_from_disk(cache_key)
            if cached_result is not None:
                logger.info("Full analysis cache hit for key: %s", cache_key)
                _update_progress(50, "Reusing cached analysis results...")
                _update_progress(100, "Analysis completed from cache.")
                return AnalysisOutput(cached_result)

            logger.info("Full analysis cache miss for key: %s. Running analysis.", cache_key)

            _update_progress(5, "Parsing document content...")
            if file_content:
                temp_dir = Path(_get_settings().paths.temp_upload_dir)
                temp_dir.mkdir(exist_ok=True)
                temp_file_path = temp_dir / f"temp_{uuid.uuid4().hex}_{original_filename or 'file'}"
                temp_file_path.write_bytes(file_content)
                chunks = parse_document_content(str(temp_file_path))
                text_to_process = " ".join(c.get("sentence", "") for c in chunks if isinstance(c, dict)).strip()
            else:  # document_text must exist
                text_to_process = document_text or ""

            if not text_to_process:
                raise ValueError("Could not extract any text from the provided document.")


            if self.use_mocks:
                return await self._run_mock_pipeline(
                    text_to_process=text_to_process,
                    discipline=discipline,
                    analysis_mode=analysis_mode,
                    original_filename=original_filename,
                    update_progress=_update_progress,
                )

            # --- Start of Optimized Two-Stage Pipeline ---

            # Stage 0: Initial text processing (optimized for speed)
            _update_progress(10, "Preprocessing document text...")
            trimmed_text = trim_document_text(text_to_process)
            # Skip heavy preprocessing for faster analysis - basic cleaning only
            corrected_text = (
                trimmed_text.strip()
                if len(trimmed_text) < 5000
                else await self._maybe_await(self.preprocessing.correct_text(trimmed_text))
            )

            # Stage 1: PHI Redaction (Security First)
            _update_progress(30, "Performing PHI redaction...")
            scrubbed_text = self.phi_scrubber.scrub(corrected_text)

            # Stage 2: Clinical Analysis on Anonymized Text (optimized)
            _update_progress(50, "Classifying document type...")
            discipline_clean = sanitize_human_text(discipline or "Unknown")

            # Fast-track for shorter documents (skip heavy classification)
            if len(scrubbed_text) < 2000:
                doc_type_clean = "Progress Note"  # Default for fast processing
            else:
                doc_type_raw = await self._maybe_await(self.document_classifier.classify_document(scrubbed_text))
                doc_type_clean = sanitize_human_text(doc_type_raw or "Progress Note")

            _update_progress(60, "Running compliance analysis...")
            # Add timeout to the entire compliance analysis
            try:
                analysis_result = await asyncio.wait_for(
                    self._maybe_await(
                        self.compliance_analyzer.analyze_document(
                            document_text=scrubbed_text, discipline=discipline_clean, doc_type=doc_type_clean
                        )
                    ),
                    timeout=600.0,  # 10 minute timeout for entire analysis
                )
            except Exception as e:
                logger.exception("Compliance analysis failed: %s", e)
                analysis_result = {
                    "findings": [],
                    "summary": f"Analysis failed due to an error: {e!s}",
                    "error": str(e),
                    "exception": True,
                    "compliance_score": 0.0,
                }

            _update_progress(85, "Enriching analysis results...")
            # --- End of Pipeline ---

            enriched_result = enrich_analysis_result(
                analysis_result,
                document_text=scrubbed_text,
                discipline=discipline_clean,
                doc_type=doc_type_clean,
                checklist_service=self.checklist_service,
            )

            _update_progress(95, "Generating report...")
            # Add timeout to report generation
            try:
                report = await asyncio.wait_for(
                    self._maybe_await(self.report_generator.generate_report(enriched_result)),
                    timeout=60.0,  # 1 minute timeout for report generation
                )
                final_report = {"analysis": enriched_result, **(report if isinstance(report, dict) else {})}
            except TimeoutError:
                logger.exception("Report generation timed out after 1 minute")
                final_report = {
                    "analysis": enriched_result,
                    "report_html": "<h1>Report Generation Timeout</h1><p>The analysis completed but report generation timed out. Please try again.</p>",
                    "error": "Report generation timeout",
                }
            except Exception as e:
                logger.exception("Report generation failed: %s", e)
                final_report = {
                    "analysis": enriched_result,
                    "report_html": f"<h1>Report Generation Error</h1><p>The analysis completed but report generation failed: {e!s}</p>",
                    "error": f"Report generation failed: {e!s}",
                }

            if not self.use_mocks:
                cache_service.set_to_disk(cache_key, final_report)
            _update_progress(100, "Analysis complete.")
            return AnalysisOutput(final_report)

        finally:
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()

            logger.info("Cleaned up temporary file: %s", temp_file_path)


    async def _run_mock_pipeline(
        self,
        *,
        text_to_process: str,
        discipline: str,
        analysis_mode: str | None,
        original_filename: str | None,
        update_progress: Callable[[int, str], None],
    ) -> AnalysisOutput:
        """Fast-path analysis used when USE_AI_MOCKS is enabled."""
    
        update_progress(10, "Preprocessing document text...")
        await asyncio.sleep(0.2)
        sanitized_text = sanitize_human_text(text_to_process) or "Clinical document"
        doc_length = len(sanitized_text)
        doc_hash = hashlib.sha1(sanitized_text.encode("utf-8")).hexdigest()
    
        update_progress(30, "Performing PHI redaction (mock)...")
        await asyncio.sleep(0.2)
        discipline_clean = sanitize_human_text(discipline or "unknown").upper()
        doc_type = "Progress Note" if doc_length < 4000 else "Evaluation"
    
        update_progress(60, "Generating compliance findings (mock)...")
        await asyncio.sleep(0.2)
        base_score = 88 + (int(doc_hash[:2], 16) % 7)
        compliance_score = max(70, min(99, base_score))
    
        findings = [
            {
                "id": "mock-finding-1",
                "title": "Goal documentation needs clarity",
                "issue_title": "Document could benefit from clearer measurable goals",
                "description": "Consider adding objective measurements to support progress reporting.",
                "severity": "medium",
                "confidence": 0.82,
                "suggestion": "Add quantifiable functional goals tied to patient outcomes.",
                "rule_name": "Goal Specificity",
                "rule_id": "mock-rule-1",
            }
        ]
    
        deterministic_checks = [
            {
                "id": "deterministic-soap",
                "title": "SOAP structure present",
                "status": "pass",
                "recommendation": "Ensure each section is updated for every visit.",
            },
            {
                "id": "deterministic-plan",
                "title": "Plan of Care references goals",
                "status": "attention",
                "recommendation": "Tie interventions directly to functional goals.",
            },
        ]
    
        summary = (
            "Automated compliance mock analysis completed successfully. "
            "One improvement opportunity identified for measurable goals."
        )
    
        highlights = [
            "Maintain detailed objective measures to support progress.",
            "Ensure plan of care references functional goals explicitly.",
        ]
    
        generated_at = datetime.datetime.now(datetime.UTC).isoformat()
    
        analysis_payload = {
            "status": "completed",
            "discipline": discipline_clean,
            "document_type": doc_type,
            "summary": summary,
            "narrative_summary": summary,
            "bullet_highlights": highlights,
            "overall_confidence": 0.9,
            "compliance_score": float(compliance_score),
            "findings": findings,
            "deterministic_checks": deterministic_checks,
            "metadata": {
                "analysis_mode": analysis_mode or "mock",
                "document_name": original_filename or "uploaded_document",
                "stage_flags": {
                    "ingestion": True,
                    "analysis": True,
                    "enrichment": True,
                },
            },
        }
    
        report_html = (
            "<h1>Mock Compliance Report</h1>"
            f"<p>Discipline: {discipline_clean}</p>"
            f"<p>Document Type: {doc_type}</p>"
            f"<p>Overall Score: {compliance_score}</p>"
            f"<p>{summary}</p>"
        )
    
        update_progress(90, "Synthesizing final report (mock)...")
        await asyncio.sleep(0.2)
    
        payload = AnalysisOutput(
            {
                "analysis": analysis_payload,
                "report_html": report_html,
                "generated_at": generated_at,
            }
        )
    
        update_progress(100, "Analysis complete (mock).")
        return payload

