"""Deterministic checklist heuristics for common compliance requirements."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from .text_utils import sanitize_human_text


@dataclass
class ChecklistItem:
    """Represents a single compliance checklist item with keywords and recommendations.

    Attributes:
        identifier: Unique identifier for the checklist item
        title: Human-readable title describing what is being checked
        keywords: List of keywords/phrases to search for in the document
        recommendation: Actionable recommendation if the item is not found
        optional: Whether this item is optional or required for compliance
        discipline_specific: Optional discipline (PT, OT, SLP) if item is specific
        doc_types: Optional list of document types this item applies to

    """

    identifier: str
    title: str
    keywords: Iterable[str]
    recommendation: str
    optional: bool = False
    discipline_specific: str | None = None
    doc_types: list[str] | None = None


class DeterministicChecklistService:
    """Run lightweight heuristics to highlight must-have documentation elements.

    This service provides deterministic compliance checking using keyword matching
    and pattern recognition. It complements the AI-powered analysis by providing
    fast, reliable checks for common documentation requirements across different
    therapy disciplines (PT, OT, SLP) and document types.
    """

    def __init__(self) -> None:
        # Using simple regex-based sentence splitting instead of spaCy
        self.sentence_pattern = re.compile(r"[.!?]+\s+")
        self._checks = self._initialize_checklist_items()

    def _initialize_checklist_items(self) -> list[ChecklistItem]:
        """Initialize the standard checklist items for compliance checking."""
        return [
            # Core documentation requirements (all disciplines)
            ChecklistItem(
                identifier="treatment_frequency",
                title="Treatment frequency documented",
                keywords=[
                    "frequency",
                    "per week",
                    "times per week",
                    "x/week",
                    "sessions per week",
                    "weekly",
                    "daily",
                    "2x/week",
                    "3x/week",
                ],
                recommendation=("Document the planned visit frequency (e.g., '3 sessions per week for 4 weeks')."),
                doc_types=["progress_note", "evaluation", "treatment_plan"]),
            ChecklistItem(
                identifier="goals_progress",
                title="Goals reviewed or progress documented",
                keywords=[
                    "goal",
                    "progress",
                    "updated goal",
                    "goal status",
                    "short-term goal",
                    "long-term goal",
                    "objective met",
                    "goal achieved",
                    "progress toward",
                    "STG",
                    "LTG",
                ],
                recommendation=("Document progress toward established goals or note if goals require modification."),
                doc_types=["progress_note", "evaluation"]),
            ChecklistItem(
                identifier="medical_necessity",
                title="Medical necessity justified",
                keywords=[
                    "medical necessity",
                    "medically necessary",
                    "skilled care",
                    "clinical rationale",
                    "justification",
                    "requires therapy",
                    "therapeutic intervention",
                    "skilled intervention",
                ],
                recommendation=("Include clear justification for why skilled therapy remains medically necessary.")),
            ChecklistItem(
                identifier="functional_status",
                title="Functional status or limitations described",
                keywords=[
                    "functional",
                    "limitations",
                    "participation",
                    "impact on",
                    "activities of daily living",
                    "ADL",
                    "mobility",
                    "independence",
                    "assistance required",
                    "functional level",
                ],
                recommendation=(
                    "Describe current functional status and how the condition "
                    "affects daily activities or participation."
                ),
                optional=True),
            ChecklistItem(
                identifier="plan_of_care",
                title="Plan of care documented or updated",
                keywords=[
                    "plan of care",
                    "continue",
                    "modify",
                    "change plan",
                    "treatment plan",
                    "intervention",
                    "approach",
                    "discharge planning",
                    "POC",
                ],
                recommendation=("Document the current plan of care or note any changes to the treatment approach."),
                optional=True),
            # Physical Therapy specific items
            ChecklistItem(
                identifier="range_of_motion",
                title="Range of motion assessed (PT)",
                keywords=[
                    "range of motion",
                    "ROM",
                    "flexibility",
                    "joint mobility",
                    "passive ROM",
                    "active ROM",
                    "PROM",
                    "AROM",
                    "degrees",
                ],
                recommendation=("Document range of motion measurements or assessments when relevant to treatment."),
                discipline_specific="PT",
                optional=True),
            ChecklistItem(
                identifier="strength_assessment",
                title="Strength assessment documented (PT)",
                keywords=[
                    "strength",
                    "muscle strength",
                    "MMT",
                    "manual muscle test",
                    "weakness",
                    "strong",
                    "fair",
                    "good",
                    "trace",
                ],
                recommendation=("Document muscle strength assessments using standardized grading when applicable."),
                discipline_specific="PT",
                optional=True),
            # Occupational Therapy specific items
            ChecklistItem(
                identifier="adl_assessment",
                title="ADL performance documented (OT)",
                keywords=[
                    "activities of daily living",
                    "ADL",
                    "self-care",
                    "dressing",
                    "bathing",
                    "grooming",
                    "feeding",
                    "toileting",
                    "transfers",
                ],
                recommendation=("Document performance in activities of daily living and any adaptive strategies used."),
                discipline_specific="OT",
                optional=True),
            # Speech-Language Pathology specific items
            ChecklistItem(
                identifier="speech_intelligibility",
                title="Speech intelligibility documented (SLP)",
                keywords=[
                    "intelligibility",
                    "speech clarity",
                    "articulation",
                    "pronunciation",
                    "understandable",
                    "clear speech",
                    "percent intelligible",
                ],
                recommendation=("Document speech intelligibility levels and any changes in clarity or articulation."),
                discipline_specific="SLP",
                optional=True),
            ChecklistItem(
                identifier="swallowing_safety",
                title="Swallowing safety addressed (SLP)",
                keywords=[
                    "swallowing",
                    "dysphagia",
                    "aspiration",
                    "safe swallow",
                    "diet texture",
                    "thickened liquids",
                    "NPO",
                    "PO intake",
                ],
                recommendation=("Document swallowing safety and any dietary modifications or precautions."),
                discipline_specific="SLP",
                optional=True),
        ]

    def describe_expectations(self) -> str:
        """Return a formatted description of all checklist expectations."""
        lines = []
        for item in self._checks:
            qualifier = "(optional) " if item.optional else ""
            discipline_note = f" [{item.discipline_specific}]" if item.discipline_specific else ""
            keywords = ", ".join(item.keywords)
            lines.append(f"- {qualifier}{item.title}{discipline_note}: {keywords}")
        return "\n".join(lines)

    def _filter_applicable_checks(
        self,
        doc_type: str | None,
        discipline: str | None) -> list[ChecklistItem]:
        """Filter checklist items based on document type and discipline.

        Args:
            doc_type: Document type to filter by (optional)
            discipline: Therapy discipline to filter by (optional)

        Returns:
            List of applicable checklist items

        """
        applicable_checks = []

        for item in self._checks:
            # Check discipline filter
            if item.discipline_specific and discipline:
                if item.discipline_specific.upper() != discipline.upper():
                    continue

            # Check document type filter
            if item.doc_types and doc_type:
                doc_type_normalized = doc_type.lower().replace(" ", "_")
                if doc_type_normalized not in item.doc_types:
                    continue

            applicable_checks.append(item)

        return applicable_checks

    def evaluate(
        self,
        document_text: str,
        *,
        doc_type: str | None = None,
        discipline: str | None = None) -> list[dict[str, str]]:
        """Return checklist results with evidence snippets when available.

        Args:
            document_text: The document content to analyze
            doc_type: Document type (e.g., 'progress_note', 'evaluation')
            discipline: Therapy discipline (e.g., 'PT', 'OT', 'SLP')

        Returns:
            List of dictionaries containing checklist results with status,
            evidence, and recommendations for each applicable item.

        """
        document_text = document_text or ""

        # Filter checklist items based on document type and discipline
        applicable_checks = self._filter_applicable_checks(doc_type, discipline)

        if not document_text.strip():
            return [
                {
                    "id": item.identifier,
                    "title": item.title,
                    "status": "review",
                    "evidence": "",
                    "recommendation": item.recommendation,
                    "optional": "yes" if item.optional else "no",
                    "discipline": item.discipline_specific or "all",
                }
                for item in applicable_checks
            ]

        sentences = self._split_sentences(document_text)
        sentences_lower = [sentence.lower() for sentence in sentences]

        results: list[dict[str, str]] = []
        for item in applicable_checks:
            evidence_sentence = self._locate_sentence(
                sentences,
                sentences_lower,
                item.keywords)
            status = "pass" if evidence_sentence else "review"
            results.append(
                {
                    "id": item.identifier,
                    "title": item.title,
                    "status": status,
                    "evidence": sanitize_human_text(evidence_sentence or ""),
                    "recommendation": item.recommendation,
                    "optional": "yes" if item.optional else "no",
                    "discipline": item.discipline_specific or "all",
                })
        return results

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using regex patterns."""
        # Split on sentence endings followed by whitespace
        sentences = self.sentence_pattern.split(text)
        # Clean up and filter empty sentences
        return [sent.strip() for sent in sentences if sent.strip()]

    def get_checklist_summary(
        self,
        discipline: str | None = None,
        doc_type: str | None = None) -> dict[str, int]:
        """Get a summary of checklist items by category.

        Args:
            discipline: Filter by therapy discipline (optional)
            doc_type: Filter by document type (optional)

        Returns:
            Dictionary with counts of required, optional, and total items

        """
        applicable_checks = self._filter_applicable_checks(doc_type, discipline)

        required_count = sum(1 for item in applicable_checks if not item.optional)
        optional_count = sum(1 for item in applicable_checks if item.optional)

        return {
            "total": len(applicable_checks),
            "required": required_count,
            "optional": optional_count,
            "discipline_specific": sum(1 for item in applicable_checks if item.discipline_specific),
        }

    @staticmethod
    def _locate_sentence(
        sentences: list[str],
        sentences_lower: list[str],
        keywords: Iterable[str]) -> str | None:
        """Locate the first sentence containing any of the specified keywords."""
        keyword_set = [kw.lower() for kw in keywords]
        for original, lowered in zip(sentences, sentences_lower, strict=False):
            if any(keyword in lowered for keyword in keyword_set):
                return original
        return None
