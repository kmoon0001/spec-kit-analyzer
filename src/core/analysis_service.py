import asyncio
import hashlib
import logging
import uuid
from pathlib import Path
from typing import Any, Callable

import psutil  # type: ignore[import-untyped]

from src.config import get_settings as _get_settings
from src.core.cache_service import cache_service
from src.core.checklist_service import DeterministicChecklistService as ChecklistService
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.document_classifier import DocumentClassifier
from src.core.explanation import ExplanationEngine
from src.core.fact_checker_service import FactCheckerService
from src.core.hybrid_retriever import HybridRetriever
from src.core.llm_service import LLMService
from src.core.ner import ClinicalNERService
from src.core.nlg_service import NLGService
from src.core.parsing import parse_document_content
from src.core.phi_scrubber import PhiScrubberService
from src.core.preprocessing_service import PreprocessingService
from src.core.report_generator import ReportGenerator
from src.core.text_utils import sanitize_bullets, sanitize_human_text
from src.utils.prompt_manager import PromptManager

from src.core.analysis_utils import (
    build_bullet_highlights,
    build_narrative_summary,
    build_summary_fallback,
    calculate_overall_confidence,
    enrich_analysis_result,
    trim_document_text,
)
from src.core.model_selection_utils import (
    resolve_local_model_path,
    select_generator_profile,
)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]


class AnalysisOutput(dict):
    """Dictionary wrapper for consistent analysis output."""


def get_settings():
    """Legacy helper retained for tests that patch this symbol."""
    return _get_settings()


class AnalysisService:
    """Orchestrates the document analysis process with a best-practices, two-stage pipeline."""

    def __init__(self, *args, **kwargs):
        settings = _get_settings()
        repo_id, filename, revision = select_generator_profile(settings.models.model_dump())
        local_model_path = resolve_local_model_path(settings)

        # Stage 1 Service: Pure PHI Redaction
        self.phi_scrubber = kwargs.get("phi_scrubber") or PhiScrubberService()

        # Stage 2 Services: Clinical Analysis on Anonymized Text
        self.llm_service = kwargs.get("llm_service") or LLMService(
            model_repo_id=repo_id,
            model_filename=filename,
            llm_settings=settings.llm.model_dump(),
            revision=revision,
            local_model_path=local_model_path)
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
            deterministic_focus=settings.analysis.deterministic_focus)
        self.preprocessing = kwargs.get("preprocessing") or PreprocessingService()
        self.document_classifier = kwargs.get("document_classifier") or DocumentClassifier(
            llm_service=self.llm_service, prompt_template_path=settings.models.doc_classifier_prompt
        )
        self.report_generator = kwargs.get("report_generator") or ReportGenerator()
        self.checklist_service = kwargs.get("checklist_service") or ChecklistService()

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
        progress_callback: Callable[[int, str], None] | None = None) -> Any:
        """Analyzes document content for compliance, using a content-aware cache."""

        def _update_progress(percentage: int, message: str) -> None:
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
            cached_result = cache_service.get_from_disk(cache_key)
            if cached_result is not None:
                logger.info("Full analysis cache hit for key: %s", cache_key)
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

            # --- Start of Optimized Two-Stage Pipeline ---

            # Stage 0: Initial text processing (optimized for speed)
            _update_progress(10, "Preprocessing document text...")
            trimmed_text = self._trim_document_text(text_to_process)
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
                            document_text=scrubbed_text,
                            discipline=discipline_clean,
                            doc_type=doc_type_clean)),
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

            enriched_result = self._enrich_analysis_result(
                analysis_result,
                document_text=scrubbed_text,
                discipline=discipline_clean,
                doc_type=doc_type_clean)

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

            cache_service.set_to_disk(cache_key, final_report)
            _update_progress(100, "Analysis complete.")
            return AnalysisOutput(final_report)

        finally:
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
                logger.info("Cleaned up temporary file: %s", temp_file_path)
