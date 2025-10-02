"""
Named Entity Recognition (NER) module for medical document analysis.

This module provides NER capabilities using both spaCy and Hugging Face transformers
for extracting clinical entities from therapy documentation. It includes specialized
functionality for identifying clinician names and medical terminology.
"""

import logging
from typing import List, Dict, Any, Optional

try:
    import spacy
    import spacy.cli
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

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
            "Clinical-AI-Apollo/Medical-NER"
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
                logger.error("Failed to load NER model %s: %s", model_name, str(e), exc_info=True)
    
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
            key = (entity.get('start', 0), entity.get('end', 0), entity.get('word', ''))
            if key not in seen:
                seen.add(key)
                merged.append(entity)
        return merged


class NERAnalyzer:
    """
    Advanced NER analyzer for clinical documents with specialized medical entity extraction.
    
    Combines spaCy's general NER capabilities with specialized biomedical models
    for comprehensive entity recognition in therapy documentation.
    """
    def __init__(self, model_names: Optional[List[str]] = None):
        """
        Initialize the NER analyzer with spaCy and transformer models.
        
        Args:
            model_names: List of Hugging Face model names for biomedical NER.
                        If None, uses default models optimized for clinical text.
        """
        self.spacy_nlp = None
        self.ner_pipeline = None
        
        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            self._initialize_spacy()
        else:
            logger.warning("spaCy not available, some NER features will be limited")
        
        # Initialize transformer-based NER pipeline
        self.ner_pipeline = NERPipeline(model_names)
    
    def _initialize_spacy(self) -> None:
        """Initialize spaCy model with error handling."""
        try:
            self.spacy_nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.warning("en_core_web_sm not found, attempting to download...")
            try:
                spacy.cli.download("en_core_web_sm")
                self.spacy_nlp = spacy.load("en_core_web_sm")
                logger.info("Successfully downloaded and loaded spaCy model")
            except Exception as e:
                logger.error("Failed to download spaCy model: %s", str(e))
                self.spacy_nlp = None

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using both spaCy and transformer models.
        
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
        
        # Extract entities using spaCy (if available)
        if self.spacy_nlp:
            spacy_entities = self._extract_spacy_entities(text)
            entities.extend(spacy_entities)
        
        return self._deduplicate_entities(entities)
    
    def _extract_spacy_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy model."""
        try:
            doc = self.spacy_nlp(text)
            entities = []
            for ent in doc.ents:
                entities.append({
                    'entity_group': ent.label_,
                    'score': 1.0,  # spaCy doesn't provide confidence scores
                    'word': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
            return entities
        except Exception as e:
            logger.warning("spaCy entity extraction failed: %s", str(e))
            return []
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on position and text."""
        seen = set()
        deduplicated = []
        
        for entity in entities:
            key = (entity.get('start', 0), entity.get('end', 0), entity.get('word', ''))
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)
        
        return sorted(deduplicated, key=lambda x: x.get('start', 0))

    def extract_clinician_name(self, text: str) -> List[str]:
        """
        Extract clinician names from text by looking for PERSON entities near clinical keywords.
        
        Args:
            text: Input text to search for clinician names
            
        Returns:
            List of unique clinician names found in the text
        """
        if not text or not self.spacy_nlp:
            return []
        
        try:
            doc = self.spacy_nlp(text)
            clinician_names = []
            clinical_keywords = {
                "signature", "therapist", "by", "dr", "pt", "ot", "slp", 
                "cota", "pta", "signed", "clinician", "provider", "treating"
            }
            
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    # Check surrounding context for clinical keywords
                    context_start = max(0, ent.start - 5)
                    context_end = min(len(doc), ent.end + 5)
                    
                    for token in doc[context_start:context_end]:
                        if token.text.lower().strip(".:,()") in clinical_keywords:
                            clinician_names.append(ent.text)
                            break
            
            return list(set(clinician_names))
            
        except Exception as e:
            logger.warning("Clinician name extraction failed: %s", str(e))
            return []
    
    def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical-specific entities categorized by type.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with entity categories as keys and lists of entities as values
        """
        entities = self.extract_entities(text)
        categorized = {
            'conditions': [],
            'medications': [],
            'procedures': [],
            'anatomy': [],
            'measurements': [],
            'other': []
        }
        
        # Map entity labels to categories
        label_mapping = {
            'DISEASE': 'conditions',
            'SYMPTOM': 'conditions',
            'MEDICATION': 'medications',
            'DRUG': 'medications',
            'PROCEDURE': 'procedures',
            'TREATMENT': 'procedures',
            'ANATOMY': 'anatomy',
            'BODY_PART': 'anatomy',
            'MEASUREMENT': 'measurements',
            'DOSAGE': 'measurements'
        }
        
        for entity in entities:
            entity_type = entity.get('entity_group', '').upper()
            category = label_mapping.get(entity_type, 'other')
            entity_text = entity.get('word', '').strip()
            
            if entity_text and entity_text not in categorized[category]:
                categorized[category].append(entity_text)
        
        return categorized
