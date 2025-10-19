"""Automatic Rubric Detection Service

Analyzes document content to automatically determine the most appropriate
compliance rubric based on key terms, document structure, and content patterns.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class RubricDetector:
    """Automatically detects the most appropriate compliance rubric based on document content."""

    def __init__(self):
        """Initialize the rubric detector with predefined patterns and keywords."""
        self.rubric_patterns = self._load_rubric_patterns()
        self.discipline_keywords = self._load_discipline_keywords()
        self.document_type_patterns = self._load_document_type_patterns()

    def _load_rubric_patterns(self) -> dict[str, dict[str, Any]]:
        """Load patterns and keywords for each rubric type."""
        return {
            "medicare_part_b": {
                "keywords": [
                    "outpatient therapy", "part b", "medicare part b", "therapy cap", "therapy services",
                    "skilled therapy", "outpatient rehabilitation", "therapy evaluation", "therapy assessment",
                    "functional improvement", "therapy goals", "treatment plan", "therapy progress"
                ],
                "patterns": [
                    r"outpatient\s+therapy",
                    r"part\s+b\s+therapy",
                    r"therapy\s+cap",
                    r"skilled\s+therapy",
                    r"functional\s+improvement"
                ],
                "weight": 1.0
            },
            "cms_1500": {
                "keywords": [
                    "cms-1500", "claim form", "billing", "cpt codes", "icd-10", "diagnosis codes",
                    "procedure codes", "billing codes", "revenue codes", "claim submission",
                    "insurance billing", "medicare billing", "reimbursement"
                ],
                "patterns": [
                    r"cms-1500",
                    r"claim\s+form",
                    r"cpt\s+codes?",
                    r"icd-10",
                    r"billing\s+codes?"
                ],
                "weight": 1.0
            },
            "therapy_cap": {
                "keywords": [
                    "therapy cap", "cap exception", "exception request", "therapy limits",
                    "annual therapy limit", "therapy threshold", "cap documentation",
                    "exception documentation", "therapy cap exceeded"
                ],
                "patterns": [
                    r"therapy\s+cap",
                    r"cap\s+exception",
                    r"exception\s+request",
                    r"therapy\s+limits?"
                ],
                "weight": 1.0
            },
            "skilled_therapy": {
                "keywords": [
                    "skilled therapy", "skilled services", "medical necessity", "skilled care",
                    "therapy necessity", "skilled intervention", "complex therapy",
                    "skilled assessment", "skilled treatment"
                ],
                "patterns": [
                    r"skilled\s+therapy",
                    r"skilled\s+services",
                    r"medical\s+necessity",
                    r"skilled\s+care"
                ],
                "weight": 1.0
            },
            "apta_pt": {
                "keywords": [
                    "physical therapy", "pt", "apta", "physical therapist", "mobility", "strength",
                    "range of motion", "gait", "balance", "coordination", "muscle strength",
                    "joint mobility", "functional mobility", "ambulation", "transfer"
                ],
                "patterns": [
                    r"physical\s+therapy",
                    r"pt\s+services?",
                    r"range\s+of\s+motion",
                    r"muscle\s+strength",
                    r"functional\s+mobility"
                ],
                "weight": 1.0
            },
            "aota_ot": {
                "keywords": [
                    "occupational therapy", "ot", "aota", "occupational therapist", "adl", "activities of daily living",
                    "fine motor", "gross motor", "sensory", "cognitive", "adaptive equipment",
                    "home modifications", "work therapy", "leisure activities"
                ],
                "patterns": [
                    r"occupational\s+therapy",
                    r"ot\s+services?",
                    r"activities\s+of\s+daily\s+living",
                    r"fine\s+motor",
                    r"adaptive\s+equipment"
                ],
                "weight": 1.0
            },
            "asha_slp": {
                "keywords": [
                    "speech therapy", "slp", "asha", "speech language pathologist", "swallowing", "dysphagia",
                    "communication", "language", "articulation", "voice", "fluency", "cognitive communication",
                    "aphasia", "dysarthria", "speech production"
                ],
                "patterns": [
                    r"speech\s+therapy",
                    r"slp\s+services?",
                    r"speech\s+language",
                    r"swallowing",
                    r"communication"
                ],
                "weight": 1.0
            },
            "default": {
                "keywords": [
                    "medicare", "compliance", "documentation", "medical services", "healthcare",
                    "clinical", "patient care", "medical record", "health record"
                ],
                "patterns": [
                    r"medicare",
                    r"compliance",
                    r"medical\s+services?",
                    r"clinical"
                ],
                "weight": 0.5
            }
        }

    def _load_discipline_keywords(self) -> dict[str, list[str]]:
        """Load discipline-specific keywords for detection."""
        return {
            "pt": [
                "physical therapy", "pt", "physical therapist", "mobility", "strength", "range of motion",
                "gait", "balance", "coordination", "muscle strength", "joint mobility", "functional mobility",
                "ambulation", "transfer", "walking", "standing", "sitting", "lifting"
            ],
            "ot": [
                "occupational therapy", "ot", "occupational therapist", "adl", "activities of daily living",
                "fine motor", "gross motor", "sensory", "cognitive", "adaptive equipment", "home modifications",
                "work therapy", "leisure activities", "dressing", "feeding", "bathing", "toileting"
            ],
            "slp": [
                "speech therapy", "slp", "speech language pathologist", "swallowing", "dysphagia",
                "communication", "language", "articulation", "voice", "fluency", "cognitive communication",
                "aphasia", "dysarthria", "speech production", "speaking", "listening", "reading", "writing"
            ]
        }

    def _load_document_type_patterns(self) -> dict[str, list[str]]:
        """Load document type patterns for better rubric selection."""
        return {
            "evaluation": [
                "evaluation", "assessment", "initial evaluation", "comprehensive evaluation",
                "therapy evaluation", "functional evaluation", "clinical evaluation"
            ],
            "progress_note": [
                "progress note", "therapy note", "treatment note", "visit note", "session note",
                "progress report", "therapy progress", "treatment progress"
            ],
            "discharge": [
                "discharge", "discharge summary", "discharge planning", "discharge note",
                "final report", "completion", "therapy completion"
            ],
            "plan_of_care": [
                "plan of care", "treatment plan", "therapy plan", "care plan", "intervention plan",
                "goals", "therapy goals", "treatment goals", "outcome goals"
            ]
        }

    def detect_rubric(self, document_text: str, filename: str | None = None) -> tuple[str, float, dict[str, Any]]:
        """
        Detect the most appropriate rubric based on document content.

        Args:
            document_text: The full text content of the document
            filename: Optional filename for additional context

        Returns:
            Tuple of (rubric_id, confidence_score, detection_details)
        """
        if not document_text or not document_text.strip():
            return "default", 0.0, {"reason": "empty_document"}

        # Normalize text for analysis
        text_lower = document_text.lower()
        text_words = set(re.findall(r'\b\w+\b', text_lower))

        # Calculate scores for each rubric
        rubric_scores = {}
        detection_details = {
            "document_length": len(document_text),
            "word_count": len(text_words),
            "filename": filename,
            "matches": {}
        }

        for rubric_id, rubric_config in self.rubric_patterns.items():
            score = 0.0
            matches = []

            # Check keyword matches
            for keyword in rubric_config["keywords"]:
                keyword_lower = keyword.lower()
                if keyword_lower in text_lower:
                    # Weight by keyword frequency and importance
                    frequency = text_lower.count(keyword_lower)
                    weight = rubric_config["weight"]
                    keyword_score = min(frequency * weight, 5.0)  # Cap at 5 points per keyword
                    score += keyword_score
                    matches.append({
                        "type": "keyword",
                        "text": keyword,
                        "frequency": frequency,
                        "score": keyword_score
                    })

            # Check pattern matches
            for pattern in rubric_config["patterns"]:
                pattern_matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if pattern_matches:
                    frequency = len(pattern_matches)
                    weight = rubric_config["weight"]
                    pattern_score = min(frequency * weight * 2, 10.0)  # Patterns worth more
                    score += pattern_score
                    matches.append({
                        "type": "pattern",
                        "pattern": pattern,
                        "matches": pattern_matches,
                        "frequency": frequency,
                        "score": pattern_score
                    })

            # Apply document type bonus
            doc_type_bonus = self._calculate_document_type_bonus(text_lower, rubric_id)
            score += doc_type_bonus

            # Apply filename bonus
            filename_bonus = self._calculate_filename_bonus(filename, rubric_id)
            score += filename_bonus

            rubric_scores[rubric_id] = score
            detection_details["matches"][rubric_id] = {
                "score": score,
                "matches": matches,
                "doc_type_bonus": doc_type_bonus,
                "filename_bonus": filename_bonus
            }

        # Find the best rubric
        if not rubric_scores:
            return "default", 0.0, detection_details

        best_rubric = max(rubric_scores.items(), key=lambda x: x[1])
        best_rubric_id, best_score = best_rubric

        # Calculate confidence (0-1 scale)
        total_possible_score = sum(config["weight"] * 10 for config in self.rubric_patterns.values())
        confidence = min(best_score / max(total_possible_score, 1), 1.0)

        # If confidence is very low, default to general Medicare rubric
        if confidence < 0.1:
            best_rubric_id = "default"
            confidence = 0.1

        detection_details["best_rubric"] = best_rubric_id
        detection_details["confidence"] = confidence
        detection_details["all_scores"] = rubric_scores

        logger.info(f"Detected rubric: {best_rubric_id} (confidence: {confidence:.2f})")

        return best_rubric_id, confidence, detection_details

    def _calculate_document_type_bonus(self, text_lower: str, rubric_id: str) -> float:
        """Calculate bonus score based on document type patterns."""
        bonus = 0.0

        # Document type specific bonuses
        if rubric_id in ["apta_pt", "aota_ot", "asha_slp"]:
            # Therapy-specific rubrics get bonus for evaluation/assessment documents
            for doc_type, patterns in self.document_type_patterns.items():
                if doc_type in ["evaluation", "assessment"]:
                    for pattern in patterns:
                        if pattern in text_lower:
                            bonus += 2.0
                            break

        elif rubric_id in ["medicare_part_b", "therapy_cap"]:
            # Medicare rubrics get bonus for progress notes and plans of care
            for doc_type, patterns in self.document_type_patterns.items():
                if doc_type in ["progress_note", "plan_of_care"]:
                    for pattern in patterns:
                        if pattern in text_lower:
                            bonus += 1.5
                            break

        return bonus

    def _calculate_filename_bonus(self, filename: str | None, rubric_id: str) -> float:
        """Calculate bonus score based on filename patterns."""
        if not filename:
            return 0.0

        filename_lower = filename.lower()
        bonus = 0.0

        # Filename pattern bonuses
        filename_patterns = {
            "apta_pt": ["pt", "physical", "therapy", "mobility", "strength"],
            "aota_ot": ["ot", "occupational", "adl", "fine motor", "adaptive"],
            "asha_slp": ["slp", "speech", "language", "swallowing", "communication"],
            "medicare_part_b": ["part b", "outpatient", "therapy", "medicare"],
            "cms_1500": ["cms", "1500", "claim", "billing"],
            "therapy_cap": ["cap", "exception", "limit"],
            "skilled_therapy": ["skilled", "necessity", "complex"]
        }

        patterns = filename_patterns.get(rubric_id, [])
        for pattern in patterns:
            if pattern in filename_lower:
                bonus += 1.0

        return bonus

    def detect_discipline(self, document_text: str) -> tuple[str, float]:
        """
        Detect the therapy discipline based on document content.

        Args:
            document_text: The full text content of the document

        Returns:
            Tuple of (discipline, confidence_score)
        """
        if not document_text:
            return "pt", 0.0

        text_lower = document_text.lower()
        discipline_scores = {}

        for discipline, keywords in self.discipline_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    frequency = text_lower.count(keyword)
                    score += frequency

            discipline_scores[discipline] = score

        if not discipline_scores:
            return "pt", 0.0

        best_discipline = max(discipline_scores.items(), key=lambda x: x[1])
        discipline, score = best_discipline

        # Calculate confidence
        total_keywords = sum(len(keywords) for keywords in self.discipline_keywords.values())
        confidence = min(score / max(total_keywords, 1), 1.0)

        return discipline, confidence

    def get_rubric_suggestions(self, document_text: str, filename: str | None = None) -> list[dict[str, Any]]:
        """
        Get multiple rubric suggestions ranked by confidence.

        Args:
            document_text: The full text content of the document
            filename: Optional filename for additional context

        Returns:
            List of rubric suggestions with scores and details
        """
        if not document_text:
            return [{"rubric_id": "default", "confidence": 0.0, "reason": "empty_document"}]

        rubric_id, confidence, details = self.detect_rubric(document_text, filename)

        # Get all scores and sort them
        all_scores = details.get("all_scores", {})
        sorted_suggestions = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

        suggestions = []
        for rubric_id, score in sorted_suggestions[:5]:  # Top 5 suggestions
            rubric_confidence = min(score / max(sum(all_scores.values()), 1), 1.0)
            suggestions.append({
                "rubric_id": rubric_id,
                "confidence": rubric_confidence,
                "score": score,
                "matches": details["matches"].get(rubric_id, {}).get("matches", [])
            })

        return suggestions
