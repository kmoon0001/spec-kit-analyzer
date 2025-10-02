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
        
        # Clinical name patterns for regex-based extraction
        self.clinical_patterns = {
            'titles': r'\b(?:Dr\.?|Doctor|PT|OT|SLP|COTA|PTA|RN|LPN|MD|DPT|OTR|CCC-SLP)\b',
            'signature_keywords': r'\b(?:signature|signed|therapist|by|clinician|provider|treating)\b',
            'name_pattern': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*\s+[A-Z][a-z]+\b'
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
            results = self.presidio_analyzer.analyze(text=text, language='en')
            entities = []
            for result in results:
                entities.append({
                    'entity_group': result.entity_type,
                    'score': result.score,
                    'word': text[result.start:result.end],
                    'start': result.start,
                    'end': result.end
                })
            return entities
        except Exception as e:
            logger.warning("Presidio entity extraction failed: %s", str(e))
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
            
            # Method 1: Look for names near clinical keywords
            clinical_keywords_pattern = self.clinical_patterns['signature_keywords']
            name_pattern = self.clinical_patterns['name_pattern']
            
            # Find all clinical keyword positions
            for keyword_match in re.finditer(clinical_keywords_pattern, text, re.IGNORECASE):
                # Look for names within 50 characters of the keyword
                start_pos = max(0, keyword_match.start() - 50)
                end_pos = min(len(text), keyword_match.end() + 50)
                context = text[start_pos:end_pos]
                
                # Find names in this context
                for name_match in re.finditer(name_pattern, context):
                    name = name_match.group().strip()
                    if len(name.split()) >= 2:  # At least first and last name
                        clinician_names.append(name)
            
            # Method 2: Look for names with clinical titles
            title_pattern = self.clinical_patterns['titles']
            title_name_pattern = rf"({title_pattern})\s+({name_pattern})"
            
            for match in re.finditer(title_name_pattern, text, re.IGNORECASE):
                full_name = match.group().strip()
                clinician_names.append(full_name)
            
            # Method 3: Use presidio to find PERSON entities near clinical context
            if self.presidio_analyzer:
                presidio_entities = self._extract_presidio_entities(text)
                for entity in presidio_entities:
                    if entity.get('entity_group') == 'PERSON':
                        # Check if this person is in clinical context
                        start = entity.get('start', 0)
                        end = entity.get('end', 0)
                        context_start = max(0, start - 50)
                        context_end = min(len(text), end + 50)
                        context = text[context_start:context_end]
                        
                        if re.search(clinical_keywords_pattern, context, re.IGNORECASE):
                            clinician_names.append(entity.get('word', ''))
            
            return list(set(clinician_names))  # Remove duplicates
            
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
            'persons': [],
            'other': []
        }
        
        # Map entity labels to categories
        label_mapping = {
            'DISEASE': 'conditions',
            'SYMPTOM': 'conditions',
            'CONDITION': 'conditions',
            'MEDICATION': 'medications',
            'DRUG': 'medications',
            'PROCEDURE': 'procedures',
            'TREATMENT': 'procedures',
            'ANATOMY': 'anatomy',
            'BODY_PART': 'anatomy',
            'MEASUREMENT': 'measurements',
            'DOSAGE': 'measurements',
            'PERSON': 'persons',
            'PHONE_NUMBER': 'other',
            'EMAIL_ADDRESS': 'other',
            'DATE_TIME': 'other'
        }
        
        for entity in entities:
            entity_type = entity.get('entity_group', '').upper()
            category = label_mapping.get(entity_type, 'other')
            entity_text = entity.get('word', '').strip()
            
            if entity_text and entity_text not in categorized[category]:
                categorized[category].append(entity_text)
        
        return categorized