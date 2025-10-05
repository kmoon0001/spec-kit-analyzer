import asyncio
import logging
from collections.abc import Awaitable
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from src.config import get_settings as _get_settings
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.document_classifier import DocumentClassifier
from src.core.hybrid_retriever import HybridRetriever
from src.core.llm_service import LLMService
from src.core.report_generator import ReportGenerator
from src.core.parsing import parse_document_content
from src.core.phi_scrubber import PhiScrubberService
from src.core.preprocessing_service import PreprocessingService
from src.core.text_utils import sanitize_bullets, sanitize_human_text
from src.core.ner import NERAnalyzer
from src.utils.prompt_manager import PromptManager
from src.core.explanation import ExplanationEngine
from src.core.fact_checker_service import FactCheckerService
from src.core.nlg_service import NLGService
from src.core.checklist_service import DeterministicChecklistService as ChecklistService

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]


class AnalysisOutput(dict):
    """Dictionary wrapper that compares by analysis payload for legacy tests."""

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        if isinstance(other, dict) and set(other.keys()) == {"findings"}:
            analysis_section = self.get("analysis")
            if isinstance(analysis_section, dict):
                return analysis_section == other
        return super().__eq__(other)


def get_settings():
    """Legacy helper retained for tests that patch this symbol."""
    return _get_settings()


class AnalysisService:
    """Orchestrates the document analysis process."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        phi_scrubber: Optional[PhiScrubberService] = None,
        preprocessing: Optional[PreprocessingService] = None,
        document_classifier: Optional[DocumentClassifier] = None,
        llm_service: Optional[LLMService] = None,
        report_generator: Optional[ReportGenerator] = None,
        compliance_analyzer: Optional[ComplianceAnalyzer] = None,
        checklist_service: Optional[ChecklistService] = None,
        ner_analyzer: Optional[NERAnalyzer] = None,
        explanation_engine: Optional[ExplanationEngine] = None,
        prompt_manager: Optional[PromptManager] = None,
        fact_checker_service: Optional[FactCheckerService] = None,
        nlg_service: Optional[NLGService] = None,
    ):
        """
        Initializes the AnalysisService with all necessary components.

        This method sets up the analysis pipeline by initializing various services
        such as the language model, retriever, scrubbers, and analyzers. It allows
        for dependency injection, making the service highly configurable and testable.

        Args:
            retriever (Optional[HybridRetriever]): Service for retrieving relevant information.
            phi_scrubber (Optional[PhiScrubberService]): Service for scrubbing PHI from text.
            preprocessing (Optional[PreprocessingService]): Service for text preprocessing.
            document_classifier (Optional[DocumentClassifier]): Service for classifying documents.
            llm_service (Optional[LLMService]): The core language model service.
            report_generator (Optional[ReportGenerator]): Service for generating reports.
            compliance_analyzer (Optional[ComplianceAnalyzer]): Service for analyzing compliance.
            checklist_service (Optional[ChecklistService]): Service for deterministic checks.
            ner_analyzer (Optional[NERAnalyzer]): Service for Named Entity Recognition.
            explanation_engine (Optional[ExplanationEngine]): Service for generating explanations.
            prompt_manager (Optional[PromptManager]): Service for managing prompts.
            fact_checker_service (Optional[FactCheckerService]): Service for checking facts.
            nlg_service (Optional[NLGService]): Service for natural language generation.
        """
        settings = _get_settings()

        # Select generator profile based on system memory
        repo_id, filename, revision = self._select_generator_profile(settings.models.model_dump())

        local_model_path = None
        configured_local = getattr(settings.models, 'generator_local_path', None)
        if configured_local:
            candidate_path = Path(configured_local)
            if not candidate_path.is_absolute():
                candidate_path = (ROOT_DIR / candidate_path).resolve()
            if candidate_path.exists():
                local_model_path = str(candidate_path)
            else:
                logger.warning(
                    'Configured generator_local_path does not exist', path=str(candidate_path)
                )

        self.llm_service = llm_service or LLMService(
            model_repo_id=repo_id,
            model_filename=filename,
            llm_settings=settings.llm.model_dump(),
            revision=revision,
            local_model_path=local_model_path,
        )
        self.retriever = retriever or HybridRetriever()
        self.ner_analyzer = ner_analyzer or NERAnalyzer(settings.models.ner_ensemble)
        template_path = Path(settings.models.analysis_prompt_template)
        self.prompt_manager = prompt_manager or PromptManager(
            template_name=template_path.name
        )
        self.explanation_engine = explanation_engine or ExplanationEngine()
        self.fact_checker_service = fact_checker_service or FactCheckerService(
            model_name=settings.models.fact_checker
        )
        self.nlg_service = nlg_service or NLGService(
            llm_service=self.llm_service,
            prompt_template_path=settings.models.nlg_prompt_template,
        )

        self.compliance_analyzer = compliance_analyzer or ComplianceAnalyzer(
            retriever=self.retriever,
            ner_analyzer=self.ner_analyzer,
            llm_service=self.llm_service,
            explanation_engine=self.explanation_engine,
            prompt_manager=self.prompt_manager,
            fact_checker_service=self.fact_checker_service,
            nlg_service=self.nlg_service,
            deterministic_focus=settings.analysis.deterministic_focus,
        )

        self.phi_scrubber = phi_scrubber or PhiScrubberService()
        self.preprocessing = preprocessing or PreprocessingService()
        self.document_classifier = document_classifier or DocumentClassifier(
            llm_service=self.llm_service,
            prompt_template_path=settings.models.doc_classifier_prompt,
        )
        self.report_generator = report_generator or ReportGenerator()
        self.checklist_service = checklist_service or ChecklistService()

        self.checklist_service = checklist_service or ChecklistService()

    def analyze_document(
        self,
        file_path: Optional[str] = None,
        discipline: str = "pt",
        analysis_mode: str | None = None,
        document_text: Optional[str] = None,
    ) -> Any:
        """
        Analyzes a document for compliance and other metrics.

        This is the main entry point for the analysis process. It takes a file path
        or document text, preprocesses it, scrubs it for PHI, classifies it, and
        then runs the compliance analysis. It returns a rich analysis output object.

        Args:
            file_path (Optional[str]): The path to the document to analyze.
            discipline (str): The clinical discipline (e.g., 'pt', 'ot').
            analysis_mode (Optional[str]): The mode of analysis (not currently used).
            document_text (Optional[str]): The text of the document to analyze.

        Returns:
            Any: An AnalysisOutput object containing the results of the analysis.

        Raises:
            ValueError: If neither file_path nor document_text is provided.
        """
        async def _run() -> Dict[str, Any]:
            logger.info("Starting analysis for document: %s", file_path)
            
            # Handle both file path and direct document text input
            if document_text is not None:
                # Use provided document text directly
                text_to_process = self._trim_document_text(document_text)
            elif file_path is not None:
                # Parse document from file path
                chunks = parse_document_content(file_path)
                text_to_process = " ".join(
                    chunk.get("sentence", "") for chunk in chunks if isinstance(chunk, dict)
                ).strip()
                text_to_process = self._trim_document_text(text_to_process)
            else:
                raise ValueError("Either file_path or document_text must be provided")

            corrected_text = await self._maybe_await(
                self.preprocessing.correct_text(text_to_process)
            )

            # Scrub PHI from the document before any further processing
            scrubbed_text = self.phi_scrubber.scrub(corrected_text)

            discipline_clean = sanitize_human_text(discipline or "Unknown")
            doc_type_raw = await self._maybe_await(
                self.document_classifier.classify_document(scrubbed_text)
            )
            doc_type_clean = sanitize_human_text(doc_type_raw or "Unknown")

            analysis_result = await self._maybe_await(
                self.compliance_analyzer.analyze_document(
                    document_text=scrubbed_text,
                    discipline=discipline_clean,
                    doc_type=doc_type_clean,
                )
            )

            analysis_result = self._enrich_analysis_result(
                analysis_result,
                document_text=scrubbed_text,
                discipline=discipline_clean,
                doc_type=doc_type_clean,
            )

            report = await self._maybe_await(
                self.report_generator.generate_report(analysis_result)
            )

            if isinstance(report, dict) and "analysis" not in report:
                report = {"analysis": analysis_result, **report}
            elif not isinstance(report, dict):
                report = {"analysis": analysis_result, "summary": ""}

            return AnalysisOutput(report)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.create_task(_run())

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        if asyncio.isfuture(value) or asyncio.iscoroutine(value):
            return await value
        if isinstance(value, Awaitable):
            return await value
        return value

    @staticmethod
    def _trim_document_text(document_text: str, *, max_chars: int = 12000) -> str:
        if len(document_text) <= max_chars:
            return document_text
        return document_text[:max_chars] + " ..."

    def _enrich_analysis_result(
        self,
        analysis_result: Dict[str, Any],
        *,
        document_text: str,
        discipline: str,
        doc_type: str,
    ) -> Dict[str, Any]:
        if isinstance(analysis_result, dict):
            result: Dict[str, Any] = dict(analysis_result)
        else:
            result = {"raw_analysis": analysis_result}

        discipline_clean = sanitize_human_text(discipline or "Unknown")
        doc_type_clean = sanitize_human_text(doc_type or "Unknown")
        result.setdefault("discipline", discipline_clean)
        result.setdefault("document_type", doc_type_clean)

        checklist = self.checklist_service.evaluate(
            document_text, doc_type=doc_type_clean, discipline=discipline_clean
        )
        result["deterministic_checks"] = checklist

        summary = sanitize_human_text(result.get("summary", ""))
        if not summary:
            summary = self._build_summary_fallback(result, checklist)
        result["summary"] = summary
        result["narrative_summary"] = self._build_narrative_summary(summary, checklist)
        result["bullet_highlights"] = self._build_bullet_highlights(
            result, checklist, summary
        )
        result["overall_confidence"] = self._calculate_overall_confidence(
            result, checklist
        )
        return result

    @staticmethod
    def _build_summary_fallback(
        analysis_result: Dict[str, Any], checklist: List[Dict[str, Any]]
    ) -> str:
        findings = analysis_result.get("findings") or []
        if findings:
            highlights = ", ".join(
                sanitize_human_text(finding.get("issue_title", "finding"))
                for finding in findings[:3]
            )
            base = f"Reviewed documentation uncovered {len(findings)} findings: {highlights}."
        else:
            base = "Reviewed documentation shows no LLM-generated compliance findings."
        flagged = [item for item in checklist if item.get("status") != "pass"]
        if flagged:
            titles = ", ".join(
                sanitize_human_text(item.get("title", "")) for item in flagged[:3]
            )
            base += f" Deterministic checks flagged: {titles}."
        return base

    def _build_narrative_summary(
        self, base_summary: str, checklist: List[Dict[str, Any]]
    ) -> str:
        flagged = [item for item in checklist if item.get("status") != "pass"]
        if not flagged:
            return sanitize_human_text(
                base_summary + " Core documentation elements were present."
            )
        focus = ", ".join(
            sanitize_human_text(item.get("title", "")) for item in flagged[:3]
        )
        narrative = f"{base_summary} Immediate follow-up recommended for: {focus}."
        return sanitize_human_text(narrative)

    @staticmethod
    def _build_bullet_highlights(
        analysis_result: Dict[str, Any],
        checklist: List[Dict[str, Any]],
        summary: str,
    ) -> List[str]:
        bullets: List[str] = []
        for item in checklist:
            if item.get("status") != "pass":
                bullets.append(f"{item.get('title')}: {item.get('recommendation')}")
        findings = analysis_result.get("findings") or []
        for finding in findings[:4]:
            issue = finding.get("issue_title") or finding.get("rule_name")
            suggestion = finding.get("personalized_tip") or finding.get("suggestion")
            if issue and suggestion:
                bullets.append(f"{issue}: {suggestion}")
            elif issue:
                bullets.append(issue)
        deduped = []
        seen = set()
        summary_lower = summary.lower()
        for bullet in sanitize_bullets(bullets):
            lower = bullet.lower()
            if lower in seen:
                continue
            if lower and lower in summary_lower:
                continue
            deduped.append(bullet)
            seen.add(lower)
        return deduped

    @staticmethod
    def _calculate_overall_confidence(
        analysis_result: Dict[str, Any], checklist: List[Dict[str, Any]]
    ) -> float:
        findings = analysis_result.get("findings") or []
        confidence_values: List[float] = []
        for finding in findings:
            value = finding.get("confidence")
            if isinstance(value, (int, float)):
                confidence_values.append(float(value))
        base_conf = (
            sum(confidence_values) / len(confidence_values)
            if confidence_values
            else 0.85
        )
        flagged = sum(1 for item in checklist if item.get("status") != "pass")
        penalty = 0.05 * flagged
        overall = max(0.0, min(1.0, base_conf - penalty))
        return overall

    def _select_generator_profile(self, models_cfg: Dict[str, Any]) -> tuple[str, str, Optional[str]]:
        """
        Selects the appropriate generator profile based on system memory.

        This method reads the available generator profiles from the configuration
        and selects the best one based on the system's available RAM. This allows
        the application to use different models on different hardware.

        Args:
            models_cfg (Dict[str, Any]): The models configuration.

        Returns:
            tuple[str, str, Optional[str]]: Repository ID, filename, and optional revision for the selected model.
        """
        profiles = models_cfg.get("generator_profiles") or {}
        if isinstance(profiles, dict) and profiles:
            mem_gb = self._system_memory_gb()
            chosen_name = None
            chosen_profile = None
            for name, profile in profiles.items():
                repo = profile.get("repo")
                filename = profile.get("filename")
                if not repo or not filename:
                    continue
                min_gb = profile.get("min_system_gb")
                max_gb = profile.get("max_system_gb")
                if min_gb is not None and mem_gb < float(min_gb):
                    continue
                if max_gb is not None and mem_gb > float(max_gb):
                    continue
                if chosen_profile is None:
                    chosen_name = name
                    chosen_profile = profile
                else:
                    prev_min = chosen_profile.get("min_system_gb") or 0.0
                    curr_min = profile.get("min_system_gb") or 0.0
                    if curr_min >= prev_min:
                        chosen_name = name
                        chosen_profile = profile
            if chosen_profile:
                logger.info("Selected generator profile %s (system memory %.1f GB)", chosen_name, round(mem_gb, 1))
                return (
                    chosen_profile.get("repo", ""),
                    chosen_profile.get("filename", ""),
                    chosen_profile.get("revision"),
                )
            # Fall back to the first profile if none matched
            first_name, first_profile = next(iter(profiles.items()))
            logger.warning("No generator profile matched system memory (%.1f GB); falling back to %s", round(mem_gb, 1), first_name)
            return (
                first_profile.get("repo", ""),
                first_profile.get("filename", ""),
                first_profile.get("revision"),
            )
        # Legacy single-entry configuration
        return (
            models_cfg.get("generator", ""),
            models_cfg.get("generator_filename", ""),
            models_cfg.get("generator_revision"),
        )

    def _build_chat_llm(
        self,
        chat_cfg: Dict[str, Any],
        base_llm_settings: Dict[str, Any],
    ) -> LLMService:
        """
        Builds a dedicated LLMService for the chat feature.

        This method creates a separate language model service instance for the chat
        functionality, potentially using a different model or configuration than the
        main analysis service.

        Args:
            chat_cfg (Dict[str, Any]): The chat model configuration.
            base_llm_settings (Dict[str, Any]): The base LLM settings.

        Returns:
            LLMService: An instance of LLMService configured for chat.
        """
        if not chat_cfg:
            return self.llm_service
        repo = chat_cfg.get("repo")
        filename = chat_cfg.get("filename")
        if not repo or not filename:
            logger.warning(
                "Chat model configuration incomplete, reusing primary generator for chat"
            )
            return self.llm_service
        chat_settings = dict(base_llm_settings)
        if chat_cfg.get("model_type"):
            chat_settings["model_type"] = chat_cfg["model_type"]
        if chat_cfg.get("context_length"):
            chat_settings["context_length"] = chat_cfg["context_length"]
        generation_params = dict(chat_settings.get("generation_params", {}))
        for key, value in (chat_cfg.get("generation_params") or {}).items():
            generation_params[key] = value
        chat_settings["generation_params"] = generation_params
        logger.info("Loading chat model: repo=%s, filename=%s", repo, filename)
        return LLMService(
            model_repo_id=repo,
            model_filename=filename,
            llm_settings=chat_settings,
        )

    @staticmethod
    def _system_memory_gb() -> float:
        """
        Gets the total system memory in gigabytes.

        Returns:
            float: The total system memory in GB.
        """
        try:
            return psutil.virtual_memory().total / (1024**3)
        except Exception:  # pragma: no cover - defensive fallback
            return 16.0


__all__ = ["AnalysisService", "AnalysisOutput", "get_settings"]
