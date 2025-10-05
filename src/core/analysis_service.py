
import asyncio
import hashlib
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from src.config import get_settings as _get_settings
from src.core.cache_service import cache_service
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.document_classifier import DocumentClassifier
from src.core.hybrid_retriever import HybridRetriever
from src.core.llm_service import LLMService
from src.core.report_generator import ReportGenerator
from src.core.parsing import parse_document_content
from src.core.phi_scrubber import PhiScrubberService
from src.core.preprocessing_service import PreprocessingService
from src.core.text_utils import sanitize_bullets, sanitize_human_text
from src.core.ner import ClinicalNERService
from src.utils.prompt_manager import PromptManager
from src.core.explanation import ExplanationEngine
from src.core.fact_checker_service import FactCheckerService
from src.core.nlg_service import NLGService
from src.core.checklist_service import DeterministicChecklistService as ChecklistService

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]

class AnalysisOutput(dict):
    """Dictionary wrapper for consistent analysis output."""
    pass

def get_settings():
    """Legacy helper retained for tests that patch this symbol."""
    return _get_settings()

class AnalysisService:
    """Orchestrates the document analysis process with a best-practices, two-stage pipeline."""

    def __init__(self, *args, **kwargs):
        settings = _get_settings()
        repo_id, filename, revision = self._select_generator_profile(settings.models.model_dump())
        local_model_path = self._resolve_local_model_path(settings)

        # Stage 1 Service: Pure PHI Redaction
        self.phi_scrubber = kwargs.get('phi_scrubber') or PhiScrubberService()

        # Stage 2 Services: Clinical Analysis on Anonymized Text
        self.llm_service = kwargs.get('llm_service') or LLMService(
            model_repo_id=repo_id, model_filename=filename,
            llm_settings=settings.llm.model_dump(), revision=revision,
            local_model_path=local_model_path,
        )
        self.retriever = kwargs.get('retriever') or HybridRetriever()
        self.clinical_ner_service = kwargs.get('clinical_ner_service') or ClinicalNERService(model_names=settings.models.ner_ensemble)
        template_path = Path(settings.models.analysis_prompt_template)
        self.prompt_manager = kwargs.get('prompt_manager') or PromptManager(template_name=template_path.name)
        self.explanation_engine = kwargs.get('explanation_engine') or ExplanationEngine()
        self.fact_checker_service = kwargs.get('fact_checker_service') or FactCheckerService(model_name=settings.models.fact_checker)
        self.nlg_service = kwargs.get('nlg_service') or NLGService(llm_service=self.llm_service, prompt_template_path=settings.models.nlg_prompt_template)
        self.compliance_analyzer = kwargs.get('compliance_analyzer') or ComplianceAnalyzer(
            retriever=self.retriever, ner_service=self.clinical_ner_service, llm_service=self.llm_service,
            explanation_engine=self.explanation_engine, prompt_manager=self.prompt_manager,
            fact_checker_service=self.fact_checker_service, nlg_service=self.nlg_service,
            deterministic_focus=settings.analysis.deterministic_focus,
        )
        self.preprocessing = kwargs.get('preprocessing') or PreprocessingService()
        self.document_classifier = kwargs.get('document_classifier') or DocumentClassifier(llm_service=self.llm_service, prompt_template_path=settings.models.doc_classifier_prompt)
        self.report_generator = kwargs.get('report_generator') or ReportGenerator()
        self.checklist_service = kwargs.get('checklist_service') or ChecklistService()

    def _get_analysis_cache_key(self, content_hash: str, discipline: str, analysis_mode: Optional[str]) -> str:
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
        document_text: Optional[str] = None,
        file_content: Optional[bytes] = None,
        original_filename: Optional[str] = None,
    ) -> Any:
        """Analyzes document content for compliance, using a content-aware cache."""
        temp_file_path: Optional[Path] = None
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
                logger.info(f"Full analysis cache hit for key: {cache_key}")
                return AnalysisOutput(cached_result)

            logger.info(f"Full analysis cache miss for key: {cache_key}. Running analysis.")

            if file_content:
                temp_dir = Path(_get_settings().paths.temp_upload_dir)
                temp_dir.mkdir(exist_ok=True)
                temp_file_path = temp_dir / f"temp_{uuid.uuid4().hex}_{original_filename or 'file'}"
                temp_file_path.write_bytes(file_content)
                chunks = parse_document_content(str(temp_file_path))
                text_to_process = " ".join(c.get("sentence", "") for c in chunks if isinstance(c, dict)).strip()
            else: # document_text must exist
                text_to_process = document_text

            if not text_to_process:
                raise ValueError("Could not extract any text from the provided document.")

            # --- Start of Optimized Two-Stage Pipeline ---

            # Stage 0: Initial text processing
            trimmed_text = self._trim_document_text(text_to_process)
            corrected_text = await self._maybe_await(self.preprocessing.correct_text(trimmed_text))

            # Stage 1: PHI Redaction (Security First)
            scrubbed_text = self.phi_scrubber.scrub(corrected_text)

            # Stage 2: Clinical Analysis on Anonymized Text
            discipline_clean = sanitize_human_text(discipline or "Unknown")
            doc_type_raw = await self._maybe_await(self.document_classifier.classify_document(scrubbed_text))
            doc_type_clean = sanitize_human_text(doc_type_raw or "Unknown")

            analysis_result = await self._maybe_await(
                self.compliance_analyzer.analyze_document(
                    document_text=scrubbed_text, discipline=discipline_clean, doc_type=doc_type_clean
                )
            )

            # --- End of Pipeline ---

            enriched_result = self._enrich_analysis_result(
                analysis_result, document_text=scrubbed_text, discipline=discipline_clean, doc_type=doc_type_clean
            )

            report = await self._maybe_await(self.report_generator.generate_report(enriched_result))
            final_report = {"analysis": enriched_result, **(report if isinstance(report, dict) else {})}

            cache_service.set_to_disk(cache_key, final_report)
            return AnalysisOutput(final_report)

        finally:
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file_path}")

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        return await value if asyncio.iscoroutine(value) or asyncio.isfuture(value) else value

    @staticmethod
    def _trim_document_text(document_text: str, *, max_chars: int = 12000) -> str:
        return document_text[:max_chars] + "..." if len(document_text) > max_chars else document_text

    def _enrich_analysis_result(self, analysis_result: Dict, *, document_text: str, discipline: str, doc_type: str) -> Dict:
        result = dict(analysis_result)
        result.setdefault("discipline", discipline)
        result.setdefault("document_type", doc_type)
        checklist = self.checklist_service.evaluate(document_text, doc_type=doc_type, discipline=discipline)
        result["deterministic_checks"] = checklist
        summary = sanitize_human_text(result.get("summary", "")) or self._build_summary_fallback(result, checklist)
        result["summary"] = summary
        result["narrative_summary"] = self._build_narrative_summary(summary, checklist)
        result["bullet_highlights"] = self._build_bullet_highlights(result, checklist, summary)
        result["overall_confidence"] = self._calculate_overall_confidence(result, checklist)
        return result

    @staticmethod
    def _build_summary_fallback(analysis_result: Dict, checklist: List) -> str:
        findings = analysis_result.get("findings") or []
        highlights = ", ".join(sanitize_human_text(f.get("issue_title", "finding")) for f in findings[:3])
        base = f"Reviewed documentation uncovered {len(findings)} findings: {highlights}." if findings else "Reviewed documentation shows no LLM-generated compliance findings."
        flagged = [item for item in checklist if item.get("status") != "pass"]
        if flagged:
            titles = ", ".join(sanitize_human_text(item.get("title", "")) for item in flagged[:3])
            base += f" Deterministic checks flagged: {titles}."
        return base

    def _build_narrative_summary(self, base_summary: str, checklist: List) -> str:
        flagged = [item for item in checklist if item.get("status") != "pass"]
        if not flagged:
            return sanitize_human_text(base_summary + " Core documentation elements were present.")
        focus = ", ".join(sanitize_human_text(item.get("title", "")) for item in flagged[:3])
        return sanitize_human_text(f"{base_summary} Immediate follow-up recommended for: {focus}.")

    @staticmethod
    def _build_bullet_highlights(analysis_result: Dict, checklist: List, summary: str) -> List[str]:
        bullets = [
            f"{item.get('title')}: {item.get('recommendation')}"
            for item in checklist
            if item.get("status") != "pass"
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
        sanitized: List[str] = []
        for bullet in sanitize_bullets(bullets):
            lowered = bullet.lower()
            if lowered in seen or lowered in summary_lower:
                continue
            seen.add(lowered)
            sanitized.append(bullet)
        return sanitized


    @staticmethod
    def _calculate_overall_confidence(analysis_result: Dict, checklist: List) -> float:
        findings = analysis_result.get("findings") or []
        conf_values = [float(f.get("confidence")) for f in findings if isinstance(f.get("confidence"), (int, float))]
        base_conf = sum(conf_values) / len(conf_values) if conf_values else 0.85
        penalty = 0.05 * sum(1 for item in checklist if item.get("status") != "pass")
        return max(0.0, min(1.0, base_conf - penalty))

    def _select_generator_profile(self, models_cfg: Dict) -> tuple[str, str, Optional[str]]:
        profiles = models_cfg.get("generator_profiles") or {}
        if isinstance(profiles, dict) and profiles:
            mem_gb = self._system_memory_gb()
            name, profile = self._find_best_profile(profiles, mem_gb) or next(iter(profiles.items()), (None, None))
            if profile:
                logger.info(f"Selected generator profile {name} (system memory {mem_gb:.1f} GB)")
                return profile.get("repo", ""), profile.get("filename", ""), profile.get("revision")
        return models_cfg.get("generator", ""), models_cfg.get("generator_filename", ""), models_cfg.get("generator_revision")

    def _find_best_profile(self, profiles: Dict, mem_gb: float) -> Optional[tuple[str, Dict]]:
        best_fit = None
        for name, profile in profiles.items():
            if not (profile.get("repo") and profile.get("filename")):
                continue
            min_gb, max_gb = profile.get("min_system_gb"), profile.get("max_system_gb")
            if (min_gb and mem_gb < float(min_gb)) or (max_gb and mem_gb > float(max_gb)):
                continue
            if best_fit is None or (profile.get("min_system_gb") or 0.0) >= (best_fit[1].get("min_system_gb") or 0.0):
                best_fit = (name, profile)
        return best_fit

    def _resolve_local_model_path(self, settings) -> Optional[str]:
        path_str = getattr(settings.models, "generator_local_path", None)
        if not path_str:
            return None

        candidate = Path(path_str)
        path = candidate if candidate.is_absolute() else (ROOT_DIR / path_str).resolve()
        if path.exists():
            return str(path)

        logger.warning(f"Configured generator_local_path does not exist: {path}")
        return None


    @staticmethod
    def _system_memory_gb() -> float:
        try:
            return psutil.virtual_memory().total / (1024**3)
        except Exception:
            # Fallback to a conservative default when system inspection fails
            return 16.0

__all__ = ["AnalysisService", "AnalysisOutput", "get_settings"]

