"""Query Expansion Service for Enhanced Compliance Rule Retrieval.

This module implements intelligent query expansion techniques to improve
the retrieval of relevant compliance rules by expanding search queries
with related medical terms, synonyms, and contextual information.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExpansionResult:
    """Result of query expansion containing original and expanded terms."""

    original_query: str
    expanded_terms: list[str]
    expansion_sources: dict[str, list[str]]  # source -> terms mapping
    confidence_scores: dict[str, float]  # term -> confidence mapping
    total_terms: int

    def get_expanded_query(self, max_terms: int | None = None) -> str:
        """Get the expanded query string with optional term limit."""
        all_terms = [self.original_query] + self.expanded_terms

        if max_terms and len(all_terms) > max_terms:
            # Keep original query and top-confidence expanded terms
            sorted_expanded = sorted(
                self.expanded_terms,
                key=lambda t: self.confidence_scores.get(t, 0.0),
                reverse=True,
            )
            all_terms = [self.original_query] + sorted_expanded[:max_terms-1]

        return " ".join(all_terms)


class MedicalVocabulary:
    """Medical terminology and synonym management."""

    def __init__(self, vocab_file: str | None = None):
        """Initialize medical vocabulary.

        Args:
            vocab_file: Path to medical vocabulary JSON file

        """
        self.synonyms: dict[str, list[str]] = {}
        self.abbreviations: dict[str, list[str]] = {}
        self.specialties: dict[str, list[str]] = {}
        self.treatments: dict[str, list[str]] = {}

        if vocab_file and Path(vocab_file).exists():
            self._load_vocabulary(vocab_file)
        else:
            self._initialize_default_vocabulary()

    def _load_vocabulary(self, vocab_file: str) -> None:
        """Load vocabulary from JSON file."""
        try:
            with open(vocab_file, encoding="utf-8") as f:
                vocab_data = json.load(f)

            self.synonyms = vocab_data.get("synonyms", {})
            self.abbreviations = vocab_data.get("abbreviations", {})
            self.specialties = vocab_data.get("specialties", {})
            self.treatments = vocab_data.get("treatments", {})

            logger.info("Loaded medical vocabulary from %s", vocab_file)

        except Exception as e:
            logger.warning("Failed to load vocabulary file %s: {e}", vocab_file)
            self._initialize_default_vocabulary()

    def _initialize_default_vocabulary(self) -> None:
        """Initialize with default medical vocabulary."""
        # Common medical synonyms
        self.synonyms = {
            "physical therapy": ["physiotherapy", "PT", "rehabilitation", "rehab"],
            "occupational therapy": ["OT", "occupational rehab", "work therapy"],
            "speech therapy": ["speech pathology", "SLP", "speech language pathology"],
            "patient": ["client", "individual", "person", "resident"],
            "treatment": ["intervention", "therapy", "care", "management"],
            "assessment": ["evaluation", "exam", "examination", "screening"],
            "goals": ["objectives", "targets", "outcomes", "aims"],
            "progress": ["improvement", "advancement", "development", "gains"],
            "function": ["ability", "capacity", "performance", "functioning"],
            "mobility": ["movement", "ambulation", "locomotion", "walking"],
            "strength": ["power", "force", "muscle strength", "muscular strength"],
            "range of motion": ["ROM", "flexibility", "joint mobility", "movement range"],
            "balance": ["stability", "equilibrium", "postural control"],
            "coordination": ["motor control", "dexterity", "fine motor skills"],
            "pain": ["discomfort", "ache", "soreness", "tenderness"],
            "discharge": ["dismissal", "release", "completion", "termination"],
        }

        # Medical abbreviations
        self.abbreviations = {
            "PT": ["physical therapy", "physiotherapy"],
            "OT": ["occupational therapy"],
            "SLP": ["speech language pathology", "speech therapy"],
            "ROM": ["range of motion"],
            "ADL": ["activities of daily living"],
            "IADL": ["instrumental activities of daily living"],
            "MMT": ["manual muscle testing"],
            "PROM": ["passive range of motion"],
            "AROM": ["active range of motion"],
            "FIM": ["functional independence measure"],
            "SOAP": ["subjective objective assessment plan"],
            "POC": ["plan of care"],
            "LOS": ["length of stay"],
            "D/C": ["discharge"],
            "Dx": ["diagnosis"],
            "Rx": ["prescription", "treatment"],
            "Hx": ["history"],
            "c/o": ["complains of", "complaint of"],
            "w/c": ["wheelchair"],
            "amb": ["ambulation", "ambulate"],
            "indep": ["independent"],
            "assist": ["assistance"],
            "min": ["minimal"],
            "mod": ["moderate"],
            "max": ["maximum"],
            "CGA": ["contact guard assist"],
            "SBA": ["standby assist"],
            "WFL": ["within functional limits"],
            "WNL": ["within normal limits"],
        }

        # Specialty-specific terms
        self.specialties = {
            "physical_therapy": [
                "gait training", "therapeutic exercise", "manual therapy",
                "modalities", "strengthening", "stretching", "endurance",
                "balance training", "transfer training", "mobility training",
            ],
            "occupational_therapy": [
                "activities of daily living", "instrumental activities",
                "cognitive rehabilitation", "adaptive equipment",
                "work hardening", "sensory integration", "fine motor skills",
                "visual perceptual skills", "home safety", "driving assessment",
            ],
            "speech_therapy": [
                "articulation", "phonology", "fluency", "voice therapy",
                "language therapy", "swallowing therapy", "dysphagia",
                "aphasia", "dysarthria", "apraxia", "cognitive communication",
            ],
        }

        # Treatment-related terms
        self.treatments = {
            "therapeutic_exercise": [
                "strengthening exercises", "range of motion exercises",
                "flexibility training", "endurance training", "conditioning",
            ],
            "manual_therapy": [
                "joint mobilization", "soft tissue mobilization",
                "massage", "myofascial release", "trigger point therapy",
            ],
            "modalities": [
                "heat therapy", "cold therapy", "electrical stimulation",
                "ultrasound", "laser therapy", "TENS", "biofeedback",
            ],
        }

        logger.info("Initialized default medical vocabulary")

    def get_synonyms(self, term: str) -> list[str]:
        """Get synonyms for a medical term."""
        term_lower = term.lower()
        synonyms = []

        # Direct lookup
        if term_lower in self.synonyms:
            synonyms.extend(self.synonyms[term_lower])

        # Reverse lookup (if term is a synonym, find the main term)
        for main_term, syn_list in self.synonyms.items():
            if term_lower in [s.lower() for s in syn_list]:
                synonyms.append(main_term)
                synonyms.extend([s for s in syn_list if s.lower() != term_lower])

        return list(set(synonyms))  # Remove duplicates

    def expand_abbreviations(self, term: str) -> list[str]:
        """Expand medical abbreviations."""
        term_upper = term.upper()
        expansions = []

        if term_upper in self.abbreviations:
            expansions.extend(self.abbreviations[term_upper])

        # Also check if term is an expansion of an abbreviation
        for abbrev, expansions_list in self.abbreviations.items():
            if term.lower() in [e.lower() for e in expansions_list]:
                expansions.append(abbrev)

        return expansions

    def get_specialty_terms(self, discipline: str) -> list[str]:
        """Get specialty-specific terms for a discipline."""
        discipline_key = f"{discipline.lower()}_therapy"
        if discipline_key in self.specialties:
            return self.specialties[discipline_key].copy()
        return []

    def save_vocabulary(self, vocab_file: str) -> None:
        """Save current vocabulary to JSON file."""
        vocab_data = {
            "synonyms": self.synonyms,
            "abbreviations": self.abbreviations,
            "specialties": self.specialties,
            "treatments": self.treatments,
        }

        try:
            Path(vocab_file).parent.mkdir(parents=True, exist_ok=True)
            with open(vocab_file, "w", encoding="utf-8") as f:
                json.dump(vocab_data, f, indent=2, ensure_ascii=False)
            logger.info("Saved medical vocabulary to %s", vocab_file)
        except Exception as e:
            logger.exception("Failed to save vocabulary to %s: {e}", vocab_file)


class SemanticExpander:
    """Semantic query expansion using embeddings and similarity."""

    def __init__(self, embedding_model=None):
        """Initialize semantic expander.

        Args:
            embedding_model: Pre-trained embedding model (optional)

        """
        self.embedding_model = embedding_model
        self.medical_terms_cache: dict[str, list[tuple[str, float]]] = {}

    def expand_semantically(self,
                          query: str,
                          context_terms: list[str],
                          max_expansions: int = 5,
                          similarity_threshold: float = 0.7) -> list[tuple[str, float]]:
        """Expand query using semantic similarity.

        Args:
            query: Original query string
            context_terms: Available terms for expansion
            max_expansions: Maximum number of expansions to return
            similarity_threshold: Minimum similarity score for inclusion

        Returns:
            List of (term, similarity_score) tuples

        """
        if not self.embedding_model or not context_terms:
            return []

        try:
            # Get embeddings for query and context terms
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                return []

            similarities = []
            for term in context_terms:
                if term.lower() == query.lower():
                    continue  # Skip identical terms

                term_embedding = self._get_embedding(term)
                if term_embedding is not None:
                    similarity = self._cosine_similarity(query_embedding, term_embedding)
                    if similarity >= similarity_threshold:
                        similarities.append((term, similarity))

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:max_expansions]

        except Exception as e:
            logger.warning("Semantic expansion failed: %s", e)
            return []

    def _get_embedding(self, text: str):
        """Get embedding for text (placeholder for actual implementation)."""
        # This would use the actual embedding model
        # For now, return None to indicate no semantic expansion
        return None

    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


class QueryExpander:
    """Main query expansion service combining multiple expansion strategies."""

    def __init__(self,
                 medical_vocab: MedicalVocabulary | None = None,
                 semantic_expander: SemanticExpander | None = None):
        """Initialize query expander.

        Args:
            medical_vocab: Medical vocabulary for synonym expansion
            semantic_expander: Semantic expander for similarity-based expansion

        """
        self.medical_vocab = medical_vocab or MedicalVocabulary()
        self.semantic_expander = semantic_expander or SemanticExpander()

        # Expansion configuration
        self.max_total_expansions = 10
        self.synonym_weight = 0.9
        self.abbreviation_weight = 0.8
        self.specialty_weight = 0.7
        self.semantic_weight = 0.6

        # Term extraction patterns
        self.medical_term_pattern = re.compile(
            r"\b(?:PT|OT|SLP|ROM|ADL|IADL|therapy|treatment|assessment|goals?|progress|function|mobility|strength|pain|discharge)\b",
            re.IGNORECASE,
        )

    def expand_query(self,
                    query: str,
                    discipline: str | None = None,
                    document_type: str | None = None,
                    context_entities: list[str] | None = None) -> ExpansionResult:
        """Expand a query using multiple expansion strategies.

        Args:
            query: Original search query
            discipline: Clinical discipline (pt, ot, slp)
            document_type: Type of document being analyzed
            context_entities: Named entities from the document

        Returns:
            ExpansionResult with expanded terms and metadata

        """
        logger.debug(f"Expanding query: '{query}' for discipline: {discipline}")

        expanded_terms = []
        expansion_sources = {}
        confidence_scores = {}

        # Extract key terms from the original query
        key_terms = self._extract_key_terms(query)

        # 1. Synonym expansion
        synonym_terms = self._expand_with_synonyms(key_terms)
        if synonym_terms:
            expanded_terms.extend(synonym_terms)
            expansion_sources["synonyms"] = synonym_terms
            for term in synonym_terms:
                confidence_scores[term] = self.synonym_weight

        # 2. Abbreviation expansion
        abbrev_terms = self._expand_abbreviations(key_terms)
        if abbrev_terms:
            expanded_terms.extend(abbrev_terms)
            expansion_sources["abbreviations"] = abbrev_terms
            for term in abbrev_terms:
                confidence_scores[term] = self.abbreviation_weight

        # 3. Discipline-specific expansion
        if discipline:
            specialty_terms = self._expand_with_specialty_terms(query, discipline)
            if specialty_terms:
                expanded_terms.extend(specialty_terms)
                expansion_sources["specialty"] = specialty_terms
                for term in specialty_terms:
                    confidence_scores[term] = self.specialty_weight

        # 4. Context-based expansion
        if context_entities:
            context_terms = self._expand_with_context(query, context_entities)
            if context_terms:
                expanded_terms.extend(context_terms)
                expansion_sources["context"] = context_terms
                for term in context_terms:
                    confidence_scores[term] = self.semantic_weight

        # 5. Document type expansion
        if document_type:
            doc_type_terms = self._expand_with_document_type(query, document_type)
            if doc_type_terms:
                expanded_terms.extend(doc_type_terms)
                expansion_sources["document_type"] = doc_type_terms
                for term in doc_type_terms:
                    confidence_scores[term] = self.specialty_weight

        # Remove duplicates while preserving order and confidence
        unique_terms = []
        seen = set()
        for term in expanded_terms:
            term_lower = term.lower()
            if term_lower not in seen and term_lower != query.lower():
                unique_terms.append(term)
                seen.add(term_lower)

        # Limit total expansions
        if len(unique_terms) > self.max_total_expansions:
            # Sort by confidence and keep top terms
            unique_terms.sort(key=lambda t: confidence_scores.get(t, 0.0), reverse=True)
            unique_terms = unique_terms[:self.max_total_expansions]

        result = ExpansionResult(
            original_query=query,
            expanded_terms=unique_terms,
            expansion_sources=expansion_sources,
            confidence_scores=confidence_scores,
            total_terms=len(unique_terms) + 1,  # +1 for original query
        )

        logger.debug("Query expansion complete: %s terms added", len(unique_terms))
        return result

    def _extract_key_terms(self, query: str) -> list[str]:
        """Extract key medical terms from the query."""
        # Simple tokenization and medical term extraction
        words = re.findall(r"\b\w+\b", query.lower())

        # Filter for medical terms and important words
        key_terms = []
        for word in words:
            if (len(word) > 2 and  # Skip very short words
                (self.medical_term_pattern.search(word) or
                 word in self.medical_vocab.synonyms or
                 word.upper() in self.medical_vocab.abbreviations)):
                key_terms.append(word)

        # Also include multi-word medical phrases
        medical_phrases = [
            "physical therapy", "occupational therapy", "speech therapy",
            "range of motion", "activities of daily living", "manual muscle testing",
            "plan of care", "medical necessity", "treatment frequency",
        ]

        query_lower = query.lower()
        for phrase in medical_phrases:
            if phrase in query_lower:
                key_terms.append(phrase)

        return list(set(key_terms))  # Remove duplicates

    def _expand_with_synonyms(self, key_terms: list[str]) -> list[str]:
        """Expand terms using medical synonyms."""
        synonym_terms = []
        for term in key_terms:
            synonyms = self.medical_vocab.get_synonyms(term)
            synonym_terms.extend(synonyms)
        return synonym_terms

    def _expand_abbreviations(self, key_terms: list[str]) -> list[str]:
        """Expand medical abbreviations."""
        abbrev_terms = []
        for term in key_terms:
            expansions = self.medical_vocab.expand_abbreviations(term)
            abbrev_terms.extend(expansions)
        return abbrev_terms

    def _expand_with_specialty_terms(self, query: str, discipline: str) -> list[str]:
        """Add discipline-specific terms relevant to the query."""
        specialty_terms = self.medical_vocab.get_specialty_terms(discipline)

        # Filter specialty terms that might be relevant to the query
        query_words = set(query.lower().split())
        relevant_terms = []

        for term in specialty_terms:
            term_words = set(term.lower().split())
            # Include if there's word overlap or if it's a common term for the discipline
            if (term_words & query_words or
                any(word in query.lower() for word in ["assessment", "treatment", "therapy", "goals", "progress"])):
                relevant_terms.append(term)

        return relevant_terms[:3]  # Limit to top 3 specialty terms

    def _expand_with_context(self, query: str, context_entities: list[str]) -> list[str]:
        """Expand using context entities from the document."""
        context_terms = []

        # Use entities that might be relevant to compliance
        relevant_entities = []
        for entity in context_entities:
            entity_lower = entity.lower()
            # Include medical terms, treatments, and assessments
            if (any(keyword in entity_lower for keyword in
                   ["therapy", "treatment", "assessment", "exercise", "training", "intervention"]) or
                len(entity) > 3):  # Include longer entities
                relevant_entities.append(entity)

        # Get synonyms for relevant entities
        for entity in relevant_entities[:5]:  # Limit to top 5 entities
            synonyms = self.medical_vocab.get_synonyms(entity)
            context_terms.extend(synonyms[:2])  # Max 2 synonyms per entity

        return context_terms

    def _expand_with_document_type(self, query: str, document_type: str) -> list[str]:
        """Add terms specific to the document type."""
        doc_type_terms = {
            "progress_note": ["progress", "status", "improvement", "response", "continuation"],
            "evaluation": ["assessment", "examination", "baseline", "initial", "screening"],
            "treatment_plan": ["plan", "goals", "objectives", "intervention", "strategy"],
            "discharge_summary": ["discharge", "completion", "outcomes", "final", "summary"],
        }

        doc_type_key = document_type.lower().replace(" ", "_")
        return doc_type_terms.get(doc_type_key, [])

    def get_expansion_statistics(self) -> dict[str, Any]:
        """Get statistics about query expansion performance."""
        return {
            "vocabulary_size": {
                "synonyms": len(self.medical_vocab.synonyms),
                "abbreviations": len(self.medical_vocab.abbreviations),
                "specialties": sum(len(terms) for terms in self.medical_vocab.specialties.values()),
                "treatments": sum(len(terms) for terms in self.medical_vocab.treatments.values()),
            },
            "expansion_weights": {
                "synonym_weight": self.synonym_weight,
                "abbreviation_weight": self.abbreviation_weight,
                "specialty_weight": self.specialty_weight,
                "semantic_weight": self.semantic_weight,
            },
            "configuration": {
                "max_total_expansions": self.max_total_expansions,
            },
        }
