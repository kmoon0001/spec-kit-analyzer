import asyncio
import datetime
import hashlib
import inspect
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
from src.core.document_chunker import get_document_chunker
from src.core.document_classifier import DocumentClassifier
from src.core.explanation import ExplanationEngine
from src.core.fact_checker_service import FactCheckerService
from src.core.file_cleanup_service import get_cleanup_service
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
from src.core.rubric_detector import RubricDetector
from src.core.text_utils import sanitize_human_text
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]


# Constants for better maintainability
class AnalysisConstants:
    """Constants for analysis service configuration."""

    # Timeout values (in seconds)
    COMPLIANCE_ANALYSIS_TIMEOUT = 300.0  # 5 minutes
    REPORT_GENERATION_TIMEOUT = 60.0  # 1 minute

    # Document processing thresholds
    FAST_TRACK_DOCUMENT_LENGTH = 2000
    LIGHT_PREPROCESSING_LENGTH = 5000

    # Default values
    DEFAULT_DISCIPLINE = "pt"
    DEFAULT_DOC_TYPE = "Progress Note"
    DEFAULT_STRICTNESS = "standard"

    # Confidence thresholds
    DISCIPLINE_DETECTION_CONFIDENCE = 0.3

    # Mock analysis parameters
    MOCK_BASE_SCORE = 88
    MOCK_SCORE_VARIATION = 7
    MOCK_MIN_SCORE = 70
    MOCK_MAX_SCORE = 99

    # Strictness score adjustments
    STRICTNESS_OFFSETS = {"lenient": 4, "standard": 0, "strict": -5}


class AnalysisOutput(dict):
    """Dictionary wrapper for consistent analysis output."""


class _MockLLMService:
    """Lightweight mock implementation used when use_ai_mocks is enabled."""

    backend = "mock"

    def is_ready(self) -> bool:
        return True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return "Mock analysis response generated for testing purposes. No real language model invocation occurred."

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


# Remove duplicate get_settings function - use the one from config.py


class AnalysisService:
    """Orchestrates the document analysis process with a best-practices, two-stage pipeline."""

    use_mocks: bool = False  # default for tests that construct via __new__

    def __init__(self, *args, **kwargs):
        settings = _get_settings()
        self._settings = settings
        self.use_mocks = bool(getattr(settings, "use_ai_mocks", False))
        logger.info("AnalysisService initialized with use_mocks=%s", self.use_mocks)

        # Services used across both mocked and full pipelines
        self.checklist_service = kwargs.get("checklist_service") or ChecklistService()
        self.phi_scrubber = kwargs.get("phi_scrubber") or PhiScrubberService()
        self.preprocessing = kwargs.get("preprocessing") or PreprocessingService()
        self.rubric_detector = kwargs.get("rubric_detector") or RubricDetector()

        # Initialize 7 Habits Framework if enabled (works in both mock and real modes)
        self.habits_framework = None
        if settings.habits_framework.enabled:
            try:
                from .enhanced_habit_mapper import SevenHabitsFramework

                self.habits_framework = SevenHabitsFramework()
                logger.info("7 Habits Framework initialized successfully")
            except ImportError as e:
                logger.warning("7 Habits Framework not available: %s", e)

        # Initialize RAG system if enabled
        self.rag_system = None
        if getattr(settings, "rag_system", {}).get("enabled", False):
            try:
                from .rag_database_integration import (
                    RAGDatabaseManager,
                    RAGModelIntegration,
                )

                self.rag_db = RAGDatabaseManager()
                self.rag_system = RAGModelIntegration(self.rag_db)
                logger.info("RAG system initialized successfully")
            except ImportError as e:
                logger.warning("RAG system not available: %s", e)

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
            self.report_generator = kwargs.get("report_generator") or ReportGenerator(
                llm_service=self.llm_service
            )
            return

        repo_id, filename, revision = select_generator_profile(
            settings.models.model_dump()
        )
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
        self.clinical_ner_service = kwargs.get(
            "clinical_ner_service"
        ) or ClinicalNERService(model_names=settings.models.ner_ensemble)
        template_path = Path(settings.models.analysis_prompt_template)
        self.prompt_manager = kwargs.get("prompt_manager") or PromptManager(
            template_name=template_path.name
        )
        self.explanation_engine = (
            kwargs.get("explanation_engine") or ExplanationEngine()
        )
        # Fact checker can use either a small pipeline model or reuse the main LLM
        fc_backend = (
            getattr(settings.models, "fact_checker_backend", "pipeline")
            if hasattr(settings, "models")
            else "pipeline"
        )
        if fc_backend == "llm":
            self.fact_checker_service = kwargs.get("fact_checker_service") or FactCheckerService(
                model_name=settings.models.fact_checker,
                llm_service=self.llm_service,
                backend="llm",
            )
        else:
            self.fact_checker_service = kwargs.get("fact_checker_service") or FactCheckerService(
                model_name=settings.models.fact_checker,
                backend="pipeline",
            )
        self.nlg_service = kwargs.get("nlg_service") or NLGService(
            llm_service=self.llm_service,
            prompt_template_path=settings.models.nlg_prompt_template,
        )
        self.compliance_analyzer = kwargs.get(
            "compliance_analyzer"
        ) or ComplianceAnalyzer(
            retriever=self.retriever,
            ner_service=self.clinical_ner_service,
            llm_service=self.llm_service,
            explanation_engine=self.explanation_engine,
            prompt_manager=self.prompt_manager,
            fact_checker_service=self.fact_checker_service,
            nlg_service=self.nlg_service,
            deterministic_focus=settings.analysis.deterministic_focus,
        )
        self.document_classifier = kwargs.get(
            "document_classifier"
        ) or DocumentClassifier(
            llm_service=self.llm_service,
            prompt_template_path=settings.models.doc_classifier_prompt,
        )
        self.report_generator = kwargs.get("report_generator") or ReportGenerator(
            llm_service=self.llm_service
        )

    async def _maybe_await(self, obj):
        if asyncio.iscoroutine(obj):
            return await obj
        return obj

    def _get_analysis_cache_key(
        self,
        content_hash: str,
        discipline: str,
        analysis_mode: str | None,
        strictness: str | None,
    ) -> str:
        hasher = hashlib.sha256()
        hasher.update(content_hash.encode())
        hasher.update(discipline.encode())
        if analysis_mode:
            hasher.update(analysis_mode.encode())
        if strictness:
            hasher.update(strictness.encode())
        return f"analysis_report_{hasher.hexdigest()}"

    async def analyze_document(
        self,
        discipline: str = "pt",
        analysis_mode: str | None = None,
        strictness: str | None = None,
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

        normalized_strictness = (
            strictness or AnalysisConstants.DEFAULT_STRICTNESS
        ).lower()
        temp_file_path: Path | None = None
        try:
            if file_content:
                content_hash = hashlib.sha256(file_content).hexdigest()
            elif document_text:
                content_hash = hashlib.sha256(document_text.encode()).hexdigest()
            else:
                raise ValueError(
                    "Either file_content or document_text must be provided"
                )

            cache_key = self._get_analysis_cache_key(
                content_hash, discipline, analysis_mode, normalized_strictness
            )
            cached_result = None
            if not self.use_mocks:
                cached_result = cache_service.get_from_disk(cache_key)
            if cached_result is not None:
                logger.info("Full analysis cache hit for key: %s", cache_key)
                _update_progress(50, "Reusing cached analysis results...")
                _update_progress(100, "Analysis completed from cache.")
                return AnalysisOutput(cached_result)

            logger.info(
                "Full analysis cache miss for key: %s. Running analysis.", cache_key
            )

            _update_progress(5, "Parsing document content...")
            if file_content:
                temp_dir = Path(self._settings.paths.temp_upload_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file_path = (
                    temp_dir / f"temp_{uuid.uuid4().hex}_{original_filename or 'file'}"
                )
                try:
                    temp_file_path.write_bytes(file_content)
                    chunks = parse_document_content(str(temp_file_path))
                    text_to_process = " ".join(
                        c.get("sentence", "") for c in chunks if isinstance(c, dict)
                    ).strip()
                except Exception as e:
                    logger.error("Failed to process file content: %s", e)
                    raise ValueError(f"Failed to process file content: {e}")
                finally:
                    # Clean up temp file immediately after parsing
                    try:
                        if temp_file_path.exists():
                            temp_file_path.unlink()
                            logger.info("Cleaned up temporary file: %s", temp_file_path)
                    except Exception as e:
                        logger.warning(
                            "Failed to clean up temp file %s: %s", temp_file_path, e
                        )
            else:  # document_text must exist
                text_to_process = document_text or ""

            if not text_to_process:
                logger.warning("No text content extracted from document")
                raise ValueError(
                    "No text content could be extracted from the document. Please check if the file is readable and contains text."
                )

            logger.info(
                "Successfully extracted %d characters of text for analysis",
                len(text_to_process),
            )
            _update_progress(15, "Document parsing completed successfully...")

            # Check if document needs chunking for large documents
            estimated_tokens = len(text_to_process) // 4  # Rough token estimation
            if estimated_tokens > 2000:  # If document is very large
                _update_progress(18, "Processing large document in chunks...")
                logger.info(
                    "Large document detected (%d estimated tokens), using chunked processing",
                    estimated_tokens,
                )

                # Use document chunker for large documents
                chunker = get_document_chunker(max_tokens=512)
                chunks = chunker.chunk_document_by_sections(text_to_process)
                logger.info("Document split into %d chunks for processing", len(chunks))

                # Process chunks and combine results
                chunk_results = []
                for i, chunk in enumerate(chunks):
                    chunk_progress = 18 + (i / len(chunks)) * 2  # 18-20% for chunking
                    _update_progress(
                        int(chunk_progress), f"Processing chunk {i+1}/{len(chunks)}..."
                    )

                    # Process this chunk (simplified analysis for chunks)
                    chunk_result = await self._analyze_chunk(
                        chunk["text"], discipline, analysis_mode, normalized_strictness
                    )
                    chunk_results.append(
                        {
                            "chunk_index": i,
                            "section": chunk.get("section", "Unknown"),
                            "result": chunk_result,
                        }
                    )

                # Combine chunk results
                combined_result = self._combine_chunk_results(
                    chunk_results, text_to_process
                )
                text_to_process = combined_result.get("combined_text", text_to_process)
                _update_progress(20, "Large document processing completed...")

            # Automatic rubric detection based on content
            _update_progress(20, "Detecting appropriate compliance rubric...")
            detected_rubric, rubric_confidence, rubric_details = (
                self.rubric_detector.detect_rubric(text_to_process, original_filename)
            )
            detected_discipline, discipline_confidence = (
                self.rubric_detector.detect_discipline(text_to_process)
            )

            # Use detected discipline if confidence is high, otherwise use provided discipline
            if discipline_confidence > 0.3:
                discipline = detected_discipline
                logger.info(
                    f"Auto-detected discipline: {discipline} (confidence: {discipline_confidence:.2f})"
                )
            else:
                logger.info(f"Using provided discipline: {discipline}")

            logger.info(
                f"Auto-detected rubric: {detected_rubric} (confidence: {rubric_confidence:.2f})"
            )

            if self.use_mocks:
                logger.info("Using MOCK pipeline for analysis")
                return await self._run_mock_pipeline(
                    text_to_process=text_to_process,
                    discipline=discipline,
                    analysis_mode=analysis_mode,
                    strictness=normalized_strictness,
                    original_filename=original_filename,
                    update_progress=_update_progress,
                )
            else:
                logger.info("Using REAL pipeline for analysis")

            # --- Start of Optimized Two-Stage Pipeline ---

            # Stage 0: Initial text processing (optimized for speed)
            _update_progress(25, "Preprocessing document text...")
            trimmed_text = trim_document_text(text_to_process)
            # Skip heavy preprocessing for faster analysis - basic cleaning only
            corrected_text = (
                trimmed_text.strip()
                if len(trimmed_text) < 5000
                else await self._maybe_await(
                    self.preprocessing.correct_text(trimmed_text)
                )
            )

            # Stage 1: PHI Redaction (Security First)
            _update_progress(35, "Performing PHI redaction...")
            scrubbed_text = self.phi_scrubber.scrub(corrected_text)

            # Stage 2: Clinical Analysis on Anonymized Text (optimized)
            _update_progress(45, "Classifying document type...")
            discipline_clean = sanitize_human_text(discipline or "Unknown")

            # Fast-track for shorter documents (skip heavy classification)
            if len(scrubbed_text) < 2000:
                doc_type_clean = "Progress Note"  # Default for fast processing
                _update_progress(50, "Using fast-track classification...")
            else:
                _update_progress(48, "Running document classification...")
                doc_type_raw = await self._maybe_await(
                    self.document_classifier.classify_document(scrubbed_text)
                )
                doc_type_clean = sanitize_human_text(doc_type_raw or "Progress Note")
                _update_progress(55, "Document classification completed...")

            _update_progress(60, "Running compliance analysis...")
            # Add timeout to the entire compliance analysis
            try:
                logger.info(
                    "Starting compliance analysis with %d characters of scrubbed text",
                    len(scrubbed_text),
                )
                logger.info("Using strictness level: %s", normalized_strictness)

                # Apply strictness level to analysis parameters
                analysis_kwargs = {
                    "document_text": scrubbed_text,
                    "discipline": discipline_clean,
                    "doc_type": doc_type_clean,
                    "strictness": normalized_strictness,
                }

                # Adjust kwargs based on analyzer signature to keep compatibility with custom analyzers
                analyzer_fn = getattr(
                    self.compliance_analyzer, "analyze_document", None
                )
                if analyzer_fn is None:
                    raise ValueError("Compliance analyzer is not configured correctly.")
                try:
                    sig = inspect.signature(analyzer_fn)
                    params = sig.parameters
                except (TypeError, ValueError):
                    params = {}
                if "strictness" not in params:
                    analysis_kwargs.pop("strictness", None)
                if "progress_callback" not in params:
                    analysis_kwargs.pop("progress_callback", None)

                supports_progress = "progress_callback" in params
                if supports_progress:

                    def compliance_progress_callback(
                        progress: int, message: str | None
                    ) -> None:
                        # Map compliance analysis progress (0-100) to overall progress (60-90)
                        overall_progress = 60 + int(progress * 0.3)
                        _update_progress(
                            overall_progress,
                            message or "Running compliance analysis...",
                        )

                    analysis_kwargs["progress_callback"] = compliance_progress_callback

                analysis_result = await asyncio.wait_for(
                    self._maybe_await(
                        self.compliance_analyzer.analyze_document(**analysis_kwargs)
                    ),
                    timeout=120.0,  # 2 minute timeout for entire analysis
                )
                logger.info("Compliance analysis completed successfully")
                logger.info(
                    "Analysis result keys: %s",
                    (
                        list(analysis_result.keys())
                        if isinstance(analysis_result, dict)
                        else "Not a dict"
                    ),
                )
                logger.info(
                    "Compliance score in result: %s",
                    (
                        analysis_result.get("compliance_score")
                        if isinstance(analysis_result, dict)
                        else "N/A"
                    ),
                )
            except TimeoutError:
                logger.error("Compliance analysis timed out after 2 minutes")
                analysis_result = {
                    "findings": [],
                    "summary": "Analysis timed out - document may be too complex or system resources limited.",
                    "error": "Analysis timeout",
                    "exception": True,
                    "compliance_score": 0.0,
                }
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

            # Enhance with RAG if available
            rag_system = getattr(self, "rag_system", None)
            if rag_system:
                try:
                    enriched_result = rag_system.enhance_analysis_with_rag(
                        scrubbed_text, enriched_result
                    )
                    logger.info("Analysis enhanced with RAG system")
                except Exception as e:
                    logger.warning("RAG enhancement failed: %s", e)

            metadata = enriched_result.setdefault("metadata", {})
            if analysis_mode and not metadata.get("analysis_mode"):
                metadata["analysis_mode"] = analysis_mode
            metadata["strictness"] = normalized_strictness

            _update_progress(95, "Generating report...")
            # Add timeout to report generation
            try:
                report = await asyncio.wait_for(
                    self._maybe_await(
                        self.report_generator.generate_report(enriched_result)
                    ),
                    timeout=60.0,  # 1 minute timeout for report generation
                )
                final_report = {
                    "analysis": enriched_result,
                    **(report if isinstance(report, dict) else {}),
                }
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
                should_cache = True
                analysis_section = final_report.get("analysis")
                if isinstance(analysis_section, dict):
                    has_error = bool(analysis_section.get("error")) or bool(
                        analysis_section.get("exception")
                    )
                    if has_error:
                        should_cache = False
                if final_report.get("error") or final_report.get("exception"):
                    should_cache = False
                if should_cache:
                    cache_service.set_to_disk(cache_key, final_report)
                else:
                    logger.info(
                        "Skipping cache for key %s due to incomplete analysis result",
                        cache_key,
                    )
            _update_progress(100, "Analysis complete.")
            return AnalysisOutput(final_report)

        finally:
            if temp_file_path:
                try:
                    if temp_file_path.exists():
                        temp_file_path.unlink()
                        logger.info("Cleaned up temporary file: %s", temp_file_path)
                    else:
                        logger.debug(
                            "Temporary file already removed: %s", temp_file_path
                        )
                except Exception as exc:
                    logger.warning(
                        "Failed to remove temporary file %s: %s", temp_file_path, exc
                    )
            # Clean up task files
            cleanup_service = get_cleanup_service()
            await cleanup_service.cleanup_task_files(
                task_id if "task_id" in locals() else "unknown"
            )

    async def _run_mock_pipeline(
        self,
        *,
        text_to_process: str,
        discipline: str,
        analysis_mode: str | None,
        strictness: str | None,
        original_filename: str | None,
        update_progress: Callable[[int, str], None],
    ) -> AnalysisOutput:
        """Fast-path analysis used when use_ai_mocks is enabled."""

        logger.info(
            "Running mock analysis pipeline with %d characters of text",
            len(text_to_process),
        )

        update_progress(25, "Preprocessing document text...")
        await asyncio.sleep(0.2)
        sanitized_text = (
            sanitize_human_text(text_to_process)
            or "Sample clinical document for compliance analysis. Patient demonstrates improved range of motion and functional mobility. Treatment goals include pain management and functional restoration. Progress noted in activities of daily living."
        )
        doc_length = len(sanitized_text)
        doc_hash = hashlib.sha1(sanitized_text.encode("utf-8")).hexdigest()

        logger.info(
            "Mock pipeline: processed %d characters, discipline: %s",
            doc_length,
            discipline,
        )

        update_progress(45, "Performing PHI redaction (mock)...")
        await asyncio.sleep(0.2)
        discipline_clean = sanitize_human_text(discipline or "unknown").upper()
        doc_type = "Progress Note" if doc_length < 4000 else "Evaluation"

        update_progress(70, "Generating compliance findings (mock)...")
        await asyncio.sleep(0.2)
        base_score = 88 + (int(doc_hash[:2], 16) % 7)
        compliance_score = max(70, min(99, base_score))

        strictness_normalized = (strictness or "balanced").lower()
        offset_map = AnalysisConstants.STRICTNESS_OFFSETS
        compliance_score = max(
            65, min(99, compliance_score + offset_map.get(strictness_normalized, 0))
        )

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

        # Add 7 Habits integration to mock findings
        if self.habits_framework and findings:
            for finding in findings:
                habit_info = self.habits_framework.map_finding_to_habit(finding)
                finding["habit_info"] = habit_info

        # Add RAG enhancement to mock analysis
        rag_enhanced = False
        if self.rag_system:
            try:
                # Mock RAG enhancement
                rag_enhanced = True
                summary += " (Enhanced with RAG knowledge base)"
            except Exception as e:
                logger.warning("Mock RAG enhancement failed: %s", e)

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
            "strictness_level": strictness_normalized,
            "rag_enhanced": rag_enhanced,
            "metadata": {
                "analysis_mode": analysis_mode or "mock",
                "document_name": original_filename or "uploaded_document",
                "stage_flags": {
                    "ingestion": True,
                    "analysis": True,
                    "enrichment": True,
                    "habits_integration": self.habits_framework is not None,
                    "rag_enhancement": rag_enhanced,
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

    async def _analyze_chunk(
        self, chunk_text: str, discipline: str, analysis_mode: str, strictness: str
    ) -> dict[str, Any]:
        """Analyze a single chunk of text."""
        try:
            # Simplified analysis for chunks - focus on key compliance elements
            findings = []

            # Basic compliance checks
            if "patient" in chunk_text.lower():
                findings.append(
                    {
                        "type": "patient_identification",
                        "severity": "low",
                        "message": "Patient identification found in chunk",
                    }
                )

            if "assessment" in chunk_text.lower() or "plan" in chunk_text.lower():
                findings.append(
                    {
                        "type": "clinical_documentation",
                        "severity": "medium",
                        "message": "Clinical assessment/plan documentation found",
                    }
                )

            return {
                "findings": findings,
                "compliance_score": 85.0,  # Default score for chunks
                "chunk_length": len(chunk_text),
            }

        except Exception as e:
            logger.error(f"Error analyzing chunk: {e}")
            return {
                "findings": [],
                "compliance_score": 0.0,
                "chunk_length": len(chunk_text),
                "error": str(e),
            }

    def _combine_chunk_results(
        self, chunk_results: list[dict[str, Any]], original_text: str
    ) -> dict[str, Any]:
        """Combine results from multiple chunks."""
        try:
            all_findings = []
            total_score = 0.0
            valid_chunks = 0

            for chunk_result in chunk_results:
                result = chunk_result["result"]
                if "error" not in result:
                    all_findings.extend(result.get("findings", []))
                    total_score += result.get("compliance_score", 0.0)
                    valid_chunks += 1

            # Calculate average compliance score
            avg_score = total_score / valid_chunks if valid_chunks > 0 else 0.0

            # Deduplicate findings
            unique_findings = []
            seen_types = set()
            for finding in all_findings:
                finding_type = finding.get("type", "unknown")
                if finding_type not in seen_types:
                    unique_findings.append(finding)
                    seen_types.add(finding_type)

            return {
                "combined_text": original_text,
                "findings": unique_findings,
                "compliance_score": avg_score,
                "chunks_processed": len(chunk_results),
                "valid_chunks": valid_chunks,
            }

        except Exception as e:
            logger.error(f"Error combining chunk results: {e}")
            return {
                "combined_text": original_text,
                "findings": [],
                "compliance_score": 0.0,
                "error": str(e),
            }
