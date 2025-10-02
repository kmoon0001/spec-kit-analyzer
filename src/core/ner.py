"""
Named Entity Recognition (NER) module for medical document analysis.

This module provides NER capabilities using Hugging Face transformers and presidio
for extracting clinical entities from therapy documentation. It includes specialized
functionality for identifying clinician names and medical terminology without spaCy.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

try:
    from presidio_analyzer import AnalyzerEngine

    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class NERPipeline:
    """
    A pipeline for Named Entity Recognition that uses an ensemble of models
    to achieve higher accuracy and recall for medical document analysis.
    """

    def __init__(self, model_names: Optional[List[str]] = None):
        """
        Initializes the NER ensemble.

        Args:
            model_names: A list of model names from the Hugging Face Hub.
                        If None, uses default biomedical models.
        """
        self.pipelines = []
        self.model_names = model_names or [
            "d4data/biomedical-ner-all",
            "Clinical-AI-Apollo/Medical-NER",
        ]
        self._initialize_pipelines()

    def _initialize_pipelines(self) -> None:
        """Initialize the NER pipelines with error handling."""
        for model_name in self.model_names:
            try:
                logger.info("Loading NER model: %s", model_name)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForTokenClassification.from_pretrained(model_name)
                self.pipelines.append(
                    pipeline(
                        "ner",
                        model=model,
                        tokenizer=tokenizer,
                        aggregation_strategy="simple",
                    )
                )
                logger.info("Successfully loaded NER model: %s", model_name)
            except Exception as e:
                logger.error(
                    "Failed to load NER model %s: %s", model_name, str(e), exc_info=True
                )

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using the ensemble of models.

        Args:
            text: Input text to analyze

        Returns:
            List of entity dictionaries with labels, scores, and positions
        """
        if not self.pipelines or not text:
            return []

        all_entities = []
        for pipe in self.pipelines:
            try:
                entities = pipe(text)
                all_entities.extend(entities)
            except Exception as e:
                logger.warning("NER pipeline failed: %s", str(e))

        return self._merge_entities(all_entities)

    def _merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping entities from multiple models."""
        # Simple deduplication - can be enhanced with more sophisticated merging
        seen = set()
        merged = []
        for entity in entities:
            key = (entity.get("start", 0), entity.get("end", 0), entity.get("word", ""))
            if key not in seen:
                seen.add(key)
                merged.append(entity)
        return merged


class NERAnalyzer:
    """
    Advanced NER analyzer for clinical documents with specialized medical entity extraction.

    Uses Hugging Face transformers, presidio, and regex patterns for comprehensive
    entity recognition in therapy documentation without spaCy dependencies.
    """

    def __init__(self, model_names: Optional[List[str]] = None):
        """
        Initialize the NER analyzer with transformer models and presidio.

        Args:
            model_names: List of Hugging Face model names for biomedical NER.
                        If None, uses default models optimized for clinical text.
        """
        self.ner_pipeline = NERPipeline(model_names)
        self.presidio_analyzer = None

        # Initialize presidio if available
        if PRESIDIO_AVAILABLE:
            try:
                self.presidio_analyzer = AnalyzerEngine()
                logger.info("Successfully initialized Presidio analyzer")
            except Exception as e:
                logger.warning("Failed to initialize Presidio: %s", str(e))

        # Enhanced clinical patterns for regex-based extraction
        self.clinical_patterns = {
            "titles": r"\b(?:Dr\.?|Doctor|PT|OT|SLP|COTA|PTA|RN|LPN|MD|DPT|OTR|CCC-SLP|RPT|LOTR|CFY|CCC)\b",
            "signature_keywords": r"\b(?:signature|signed|therapist|by|clinician|provider|treating|evaluated|assessed|documented|supervised)\b",
            "name_pattern": r"\b[A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+\b",
            "medical_conditions": r"\b(?:arthritis|pain|weakness|spasticity|contracture|edema|inflammation|dysfunction|impairment|deficit|limitation|restriction)\b",
            "body_parts": r"\b(?:shoulder|elbow|wrist|hand|finger|hip|knee|ankle|foot|toe|neck|back|spine|arm|leg|joint|muscle|tendon|ligament)\b",
            "therapy_terms": r"\b(?:exercise|therapy|treatment|intervention|modality|technique|protocol|program|plan|goal|objective|outcome)\b",
            "measurements": r"\b(?:\d+(?:\.\d+)?\s*(?:degrees?|°|inches?|in\.?|centimeters?|cm|millimeters?|mm|pounds?|lbs?|kilograms?|kg|repetitions?|reps?|sets?|minutes?|min\.?|seconds?|sec\.?))\b",
        }

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using transformer models and presidio.

        Args:
            text: Input text to analyze for named entities

        Returns:
            List of entity dictionaries with labels, positions, and confidence scores
        """
        if not text or not text.strip():
            return []

        entities = []

        # Extract entities using transformer models
        if self.ner_pipeline:
            transformer_entities = self.ner_pipeline.extract_entities(text)
            entities.extend(transformer_entities)

        # Extract entities using presidio (if available)
        if self.presidio_analyzer:
            presidio_entities = self._extract_presidio_entities(text)
            entities.extend(presidio_entities)

        return self._deduplicate_entities(entities)

    def _extract_presidio_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using Presidio analyzer."""
        try:
            results = self.presidio_analyzer.analyze(text=text, language="en")
            entities = []
            for result in results:
                entities.append(
                    {
                        "entity_group": result.entity_type,
                        "score": result.score,
                        "word": text[result.start : result.end],
                        "start": result.start,
                        "end": result.end,
                    }
                )
            return entities
        except Exception as e:
            logger.warning("Presidio entity extraction failed: %s", str(e))
            return []

    def _deduplicate_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on position and text."""
        seen = set()
        deduplicated = []

        for entity in entities:
            key = (entity.get("start", 0), entity.get("end", 0), entity.get("word", ""))
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)

        return sorted(deduplicated, key=lambda x: x.get("start", 0))

    def extract_clinician_name(self, text: str) -> List[str]:
        """
        Extract clinician names from text using regex patterns and context analysis.

        Args:
            text: Input text to search for clinician names

        Returns:
            List of unique clinician names found in the text
        """
        if not text:
            return []

        try:
            clinician_names = []

            # Method 1: Look for names with clinical titles (most reliable)
            title_pattern = self.clinical_patterns["titles"]
            name_pattern = self.clinical_patterns["name_pattern"]

            # Pattern: Title + Name (e.g., "Dr. John Smith", "PT Jane Doe")
            title_name_pattern = rf"({title_pattern})\s+({name_pattern})"
            for match in re.finditer(title_name_pattern, text, re.IGNORECASE):
                # Extract just the name part (remove title)
                name_part = match.group(2).strip()
                if len(name_part.split()) >= 2:  # At least first and last name
                    clinician_names.append(name_part)

            # Pattern: Name + Title (e.g., "John Smith, PT", "Jane Doe, DPT")
            name_title_pattern = rf"({name_pattern}),?\s*({title_pattern})"
            for match in re.finditer(name_title_pattern, text, re.IGNORECASE):
                name_part = match.group(1).strip()
                if len(name_part.split()) >= 2:
                    clinician_names.append(name_part)

            # Method 2: Look for names near clinical keywords
            clinical_keywords_pattern = self.clinical_patterns["signature_keywords"]

            # Find all clinical keyword positions
            for keyword_match in re.finditer(
                clinical_keywords_pattern, text, re.IGNORECASE
            ):
                # Look for names within 30 characters of the keyword
                start_pos = max(0, keyword_match.start() - 30)
                end_pos = min(len(text), keyword_match.end() + 30)
                context = text[start_pos:end_pos]

                # Find names in this context
                for name_match in re.finditer(name_pattern, context):
                    name = name_match.group().strip()
                    # Filter out common false positives
                    if (
                        len(name.split()) >= 2
                        and not self._is_likely_patient_name(name, text)
                        and self._is_likely_clinician_name(name, context)
                    ):
                        clinician_names.append(name)

            # Method 3: Use presidio to find PERSON entities near clinical context
            if self.presidio_analyzer:
                presidio_entities = self._extract_presidio_entities(text)
                for entity in presidio_entities:
                    if entity.get("entity_group") == "PERSON":
                        # Check if this person is in clinical context
                        start = entity.get("start", 0)
                        end = entity.get("end", 0)
                        context_start = max(0, start - 50)
                        context_end = min(len(text), end + 50)
                        context = text[context_start:context_end]

                        name = entity.get("word", "").strip()
                        if re.search(
                            clinical_keywords_pattern, context, re.IGNORECASE
                        ) and not self._is_likely_patient_name(name, text):
                            clinician_names.append(name)

            # Clean and deduplicate names
            cleaned_names = []
            for name in clinician_names:
                cleaned = self._clean_clinician_name(name)
                if cleaned and cleaned not in cleaned_names:
                    cleaned_names.append(cleaned)

            return cleaned_names

        except Exception as e:
            logger.warning("Clinician name extraction failed: %s", str(e))
            return []

    def _is_likely_patient_name(self, name: str, full_text: str) -> bool:
        """Check if a name is likely a patient name rather than clinician."""
        # Look for patient indicators near the name
        patient_indicators = (
            r"\b(?:patient|pt\.?|client|individual|person|mr\.?|mrs\.?|ms\.?)\b"
        )

        # Find name position in text
        name_pos = full_text.lower().find(name.lower())
        if name_pos == -1:
            return False

        # Check context around the name
        context_start = max(0, name_pos - 50)
        context_end = min(len(full_text), name_pos + len(name) + 50)
        context = full_text[context_start:context_end]

        return bool(re.search(patient_indicators, context, re.IGNORECASE))

    def _is_likely_clinician_name(self, name: str, context: str) -> bool:
        """Check if a name is likely a clinician based on context."""
        # Look for clinician indicators
        clinician_indicators = (
            r"\b(?:dr\.?|doctor|therapist|clinician|provider|signed|signature|by)\b"
        )
        return bool(re.search(clinician_indicators, context, re.IGNORECASE))

    def _clean_clinician_name(self, name: str) -> str:
        """Clean and normalize clinician names."""
        if not name:
            return ""

        # Remove common prefixes/suffixes that might be included
        name = re.sub(r"^(?:dr\.?|doctor)\s+", "", name, flags=re.IGNORECASE)
        name = re.sub(
            r",?\s*(?:pt|ot|slp|dpt|otr|ccc-slp|md|rn|lpn)\.?$",
            "",
            name,
            flags=re.IGNORECASE,
        )

        # Clean up whitespace and punctuation
        name = re.sub(r"\s+", " ", name).strip()
        name = name.strip(".,;:")

        # Ensure proper capitalization
        words = name.split()
        if len(words) >= 2:
            return " ".join(word.capitalize() for word in words)

        return ""

    def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical-specific entities categorized by type.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with entity categories as keys and lists of entities as values
        """
        if not text:
            return self._empty_medical_categories()

        # Get entities from transformer models
        entities = self.extract_entities(text)
        categorized = self._empty_medical_categories()

        # Map entity labels to categories (expanded mapping)
        label_mapping = {
            "DISEASE": "conditions",
            "SYMPTOM": "conditions",
            "CONDITION": "conditions",
            "DISORDER": "conditions",
            "DIAGNOSIS": "conditions",
            "MEDICATION": "medications",
            "DRUG": "medications",
            "MEDICINE": "medications",
            "PROCEDURE": "procedures",
            "TREATMENT": "procedures",
            "THERAPY": "procedures",
            "INTERVENTION": "procedures",
            "ANATOMY": "anatomy",
            "BODY_PART": "anatomy",
            "ORGAN": "anatomy",
            "MEASUREMENT": "measurements",
            "DOSAGE": "measurements",
            "QUANTITY": "measurements",
            "PERSON": "persons",
            "CLINICIAN": "clinicians",
            "THERAPIST": "clinicians",
            "PHONE_NUMBER": "contact_info",
            "EMAIL_ADDRESS": "contact_info",
            "DATE_TIME": "temporal",
            "DATE": "temporal",
            "TIME": "temporal",
        }

        # Process transformer-detected entities
        for entity in entities:
            entity_type = entity.get("entity_group", "").upper()
            category = label_mapping.get(entity_type, "other")
            entity_text = entity.get("word", "").strip()

            if entity_text and entity_text not in categorized[category]:
                categorized[category].append(entity_text)

        # Add regex-based extraction for clinical patterns
        self._extract_regex_entities(text, categorized)

        # Extract clinician names separately
        clinician_names = self.extract_clinician_name(text)
        for name in clinician_names:
            if name not in categorized["clinicians"]:
                categorized["clinicians"].append(name)

        return categorized

    def _empty_medical_categories(self) -> Dict[str, List[str]]:
        """Return empty medical entity categories."""
        return {
            "conditions": [],
            "medications": [],
            "procedures": [],
            "anatomy": [],
            "measurements": [],
            "persons": [],
            "clinicians": [],
            "contact_info": [],
            "temporal": [],
            "other": [],
        }

    def _extract_regex_entities(
        self, text: str, categorized: Dict[str, List[str]]
    ) -> None:
        """Extract entities using regex patterns for clinical terms."""
        try:
            # Extract medical conditions
            for match in re.finditer(
                self.clinical_patterns["medical_conditions"], text, re.IGNORECASE
            ):
                condition = match.group().strip().lower()
                if condition not in [c.lower() for c in categorized["conditions"]]:
                    categorized["conditions"].append(condition.capitalize())

            # Extract body parts/anatomy
            for match in re.finditer(
                self.clinical_patterns["body_parts"], text, re.IGNORECASE
            ):
                body_part = match.group().strip().lower()
                if body_part not in [b.lower() for b in categorized["anatomy"]]:
                    categorized["anatomy"].append(body_part.capitalize())

            # Extract therapy procedures
            for match in re.finditer(
                self.clinical_patterns["therapy_terms"], text, re.IGNORECASE
            ):
                procedure = match.group().strip().lower()
                if procedure not in [p.lower() for p in categorized["procedures"]]:
                    categorized["procedures"].append(procedure.capitalize())

            # Extract measurements
            for match in re.finditer(
                self.clinical_patterns["measurements"], text, re.IGNORECASE
            ):
                measurement = match.group().strip()
                if measurement not in categorized["measurements"]:
                    categorized["measurements"].append(measurement)

            # Extract dates (simple pattern)
            date_pattern = (
                r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"
            )
            for match in re.finditer(date_pattern, text):
                date = match.group().strip()
                if date not in categorized["temporal"]:
                    categorized["temporal"].append(date)

            # Extract phone numbers
            phone_pattern = (
                r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
            )
            for match in re.finditer(phone_pattern, text):
                phone = match.group().strip()
                if phone not in categorized["contact_info"]:
                    categorized["contact_info"].append(phone)

        except Exception as e:
            logger.warning("Regex entity extraction failed: %s", str(e))
