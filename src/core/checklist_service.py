"""Deterministic checklist heuristics for common compliance requirements."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

try:
    import spacy
    from spacy.language import Language
except Exception:  # pragma: no cover - spaCy is optional at runtime
    spacy = None
    Language = None  # type: ignore[assignment]

from .text_utils import sanitize_human_text


@dataclass
class ChecklistItem:
    identifier: str
    title: str
    keywords: Iterable[str]
    recommendation: str
    optional: bool = False


class DeterministicChecklistService:
    """Run lightweight heuristics to highlight must-have documentation elements."""

    def __init__(self) -> None:
        self._nlp: Optional[Language]
        if spacy is None:
            self._nlp = None
        else:
            self._nlp = spacy.blank("en")
            if "sentencizer" not in self._nlp.pipe_names:
                self._nlp.add_pipe("sentencizer")

        self._checks: List[ChecklistItem] = [
            ChecklistItem(
                identifier="treatment_frequency",
                title="Treatment frequency documented",
                keywords=("frequency", "per week", "times per week", "x/week", "sessions per week"),
                recommendation="Document the planned visit frequency (for example, '3 sessions per week').",
            ),
            ChecklistItem(
                identifier="goals_adjusted",
                title="Goals reviewed or adjusted",
                keywords=("goal", "progress", "updated goal", "goal status", "short-term goal"),
                recommendation="State whether established goals were met, progressed, or require adjustment.",
            ),
            ChecklistItem(
                identifier="medical_necessity",
                title="Medical necessity justified",
                keywords=("medical necessity", "medically necessary", "justified", "clinical rationale"),
                recommendation="Add a sentence that justifies why skilled therapy remains medically necessary.",
            ),
            ChecklistItem(
                identifier="functional_impact",
                title="Functional impact described",
                keywords=("functional", "limitations", "participation", "impact on"),
                recommendation="Describe how the condition affects functional activities or participation.",
                optional=True,
            ),
            ChecklistItem(
                identifier="plan_changes",
                title="Plan of care or interventions updated",
                keywords=("plan of care", "continue", "upgrade", "downgrade", "modify treatment"),
                recommendation="Note any change to the plan of care or affirm that the current plan continues.",
                optional=True,
            ),
        ]


    def describe_expectations(self) -> str:
        lines = []
        for item in self._checks:
            qualifier = "(optional) " if item.optional else ""
            keywords = ", ".join(item.keywords)
            lines.append(f"- {qualifier}{item.title}: {keywords}")
        return "\n".join(lines)

    def evaluate(
        self,
        document_text: str,
        *,
        doc_type: Optional[str] = None,
        discipline: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Return checklist results with evidence snippets when available."""
        document_text = document_text or ""
        if not document_text.strip():
            return [
                {
                    "id": item.identifier,
                    "title": item.title,
                    "status": "review",
                    "evidence": "",
                    "recommendation": item.recommendation,
                    "optional": "yes" if item.optional else "no",
                }
                for item in self._checks
            ]

        sentences = self._split_sentences(document_text)
        sentences_lower = [sentence.lower() for sentence in sentences]

        results: List[Dict[str, str]] = []
        for item in self._checks:
            evidence_sentence = self._locate_sentence(sentences, sentences_lower, item.keywords)
            status = "pass" if evidence_sentence else "review"
            results.append(
                {
                    "id": item.identifier,
                    "title": item.title,
                    "status": status,
                    "evidence": sanitize_human_text(evidence_sentence or ""),
                    "recommendation": item.recommendation,
                    "optional": "yes" if item.optional else "no",
                }
            )
        return results

    def _split_sentences(self, text: str) -> List[str]:
        if self._nlp is None:
            return [segment.strip() for segment in text.split('.') if segment.strip()]
        doc = self._nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    @staticmethod
    def _locate_sentence(
        sentences: List[str], sentences_lower: List[str], keywords: Iterable[str]
    ) -> Optional[str]:
        keyword_set = [kw.lower() for kw in keywords]
        for original, lowered in zip(sentences, sentences_lower):
            if any(keyword in lowered for keyword in keyword_set):
                return original
        return None
