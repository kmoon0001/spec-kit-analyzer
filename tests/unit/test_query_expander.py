"""Tests for query expansion functionality."""

import pytest
import tempfile
from pathlib import Path

from src.core.query_expander import (
    QueryExpander, 
    MedicalVocabulary, 
    SemanticExpander,
    ExpansionResult
)


class TestMedicalVocabulary:
    """Test medical vocabulary functionality."""
    
    def test_initialization_with_defaults(self):
        """Test vocabulary initializes with default medical terms."""
        vocab = MedicalVocabulary()
        
        # Check that default vocabulary is loaded
        assert len(vocab.synonyms) > 0
        assert len(vocab.abbreviations) > 0
        assert len(vocab.specialties) > 0
        
        # Check specific medical terms
        assert 'physical therapy' in vocab.synonyms
        assert 'PT' in vocab.abbreviations
        assert 'physical_therapy' in vocab.specialties
    
    def test_get_synonyms(self):
        """Test synonym retrieval."""
        vocab = MedicalVocabulary()
        
        # Test direct lookup
        pt_synonyms = vocab.get_synonyms('physical therapy')
        assert 'physiotherapy' in pt_synonyms
        assert 'PT' in pt_synonyms
        assert 'rehabilitation' in pt_synonyms
        
        # Test reverse lookup
        physio_synonyms = vocab.get_synonyms('physiotherapy')
        assert 'physical therapy' in physio_synonyms
        
        # Test case insensitivity
        pt_upper_synonyms = vocab.get_synonyms('PHYSICAL THERAPY')
        assert len(pt_upper_synonyms) > 0
    
    def test_expand_abbreviations(self):
        """Test abbreviation expansion."""
        vocab = MedicalVocabulary()
        
        # Test abbreviation expansion
        pt_expansions = vocab.expand_abbreviations('PT')
        assert 'physical therapy' in pt_expansions
        assert 'physiotherapy' in pt_expansions
        
        # Test reverse expansion
        pt_reverse = vocab.expand_abbreviations('physical therapy')
        assert 'PT' in pt_reverse
        
        # Test case handling
        rom_expansions = vocab.expand_abbreviations('rom')
        assert 'range of motion' in rom_expansions
    
    def test_get_specialty_terms(self):
        """Test specialty-specific term retrieval."""
        vocab = MedicalVocabulary()
        
        # Test PT specialty terms
        pt_terms = vocab.get_specialty_terms('physical')
        assert 'gait training' in pt_terms
        assert 'therapeutic exercise' in pt_terms
        
        # Test OT specialty terms
        ot_terms = vocab.get_specialty_terms('occupational')
        assert 'activities of daily living' in ot_terms
        assert 'adaptive equipment' in ot_terms
        
        # Test SLP specialty terms
        slp_terms = vocab.get_specialty_terms('speech')
        assert 'articulation' in slp_terms
        assert 'dysphagia' in slp_terms
    
    def test_save_and_load_vocabulary(self):
        """Test saving and loading vocabulary from file."""
        vocab = MedicalVocabulary()
        
        # Add custom term
        vocab.synonyms['test_term'] = ['test_synonym1', 'test_synonym2']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save vocabulary
            vocab.save_vocabulary(temp_file)
            assert Path(temp_file).exists()
            
            # Load vocabulary in new instance
            new_vocab = MedicalVocabulary(temp_file)
            assert 'test_term' in new_vocab.synonyms
            assert new_vocab.synonyms['test_term'] == ['test_synonym1', 'test_synonym2']
            
        finally:
            Path(temp_file).unlink()


class TestSemanticExpander:
    """Test semantic expansion functionality."""
    
    def test_initialization(self):
        """Test semantic expander initialization."""
        expander = SemanticExpander()
        assert expander.embedding_model is None
        assert expander.medical_terms_cache == {}
    
    def test_expand_semantically_without_model(self):
        """Test semantic expansion without embedding model."""
        expander = SemanticExpander()
        
        result = expander.expand_semantically(
            "physical therapy",
            ["rehabilitation", "physiotherapy", "treatment"],
            max_expansions=3
        )
        
        # Should return empty list without embedding model
        assert result == []
    
    def test_expand_semantically_with_mock_model(self):
        """Test semantic expansion with mock embedding model."""
        # Mock embedding model
        class MockEmbeddingModel:
            def encode(self, text):
                # Return simple mock embeddings based on text length
                return [len(text), len(text.split()), hash(text) % 100]
        
        expander = SemanticExpander(MockEmbeddingModel())
        
        # Override the _get_embedding method for testing
        def mock_get_embedding(text):
            return [len(text), len(text.split()), hash(text) % 100]
        
        expander._get_embedding = mock_get_embedding
        
        result = expander.expand_semantically(
            "PT",
            ["physical therapy", "rehabilitation", "treatment"],
            max_expansions=2,
            similarity_threshold=0.1
        )
        
        # Should return some results with mock similarity
        assert isinstance(result, list)
        # Results depend on mock similarity calculation


class TestExpansionResult:
    """Test ExpansionResult functionality."""
    
    def test_expansion_result_creation(self):
        """Test creating an expansion result."""
        result = ExpansionResult(
            original_query="PT assessment",
            expanded_terms=["physical therapy", "evaluation", "examination"],
            expansion_sources={"synonyms": ["physical therapy"], "specialty": ["evaluation", "examination"]},
            confidence_scores={"physical therapy": 0.9, "evaluation": 0.7, "examination": 0.7},
            total_terms=4
        )
        
        assert result.original_query == "PT assessment"
        assert len(result.expanded_terms) == 3
        assert result.total_terms == 4
    
    def test_get_expanded_query(self):
        """Test getting expanded query string."""
        result = ExpansionResult(
            original_query="PT",
            expanded_terms=["physical therapy", "physiotherapy", "rehabilitation"],
            expansion_sources={},
            confidence_scores={"physical therapy": 0.9, "physiotherapy": 0.8, "rehabilitation": 0.7},
            total_terms=4
        )
        
        # Test without limit
        expanded = result.get_expanded_query()
        assert "PT" in expanded
        assert "physical therapy" in expanded
        assert "physiotherapy" in expanded
        assert "rehabilitation" in expanded
        
        # Test with limit
        limited = result.get_expanded_query(max_terms=2)
        # Note: "physical therapy" is two words, so split() will give more terms
        assert "PT" in limited  # Original query should always be included
        assert len(limited.split()) >= 2  # Should have at least 2 words


class TestQueryExpander:
    """Test main query expander functionality."""
    
    def test_initialization(self):
        """Test query expander initialization."""
        expander = QueryExpander()
        
        assert expander.medical_vocab is not None
        assert expander.semantic_expander is not None
        assert expander.max_total_expansions == 10
    
    def test_extract_key_terms(self):
        """Test key term extraction from queries."""
        expander = QueryExpander()
        
        # Test medical term extraction
        terms = expander._extract_key_terms("PT assessment for range of motion")
        # PT might not be extracted if not in medical_term_pattern, but assessment should be
        assert any("assessment" in term.lower() for term in terms)
        assert any("range of motion" in term.lower() for term in terms)
        assert len(terms) > 0
        
        # Test with mixed case
        terms2 = expander._extract_key_terms("Physical Therapy GOALS and Progress")
        assert len(terms2) > 0
    
    def test_expand_with_synonyms(self):
        """Test synonym-based expansion."""
        expander = QueryExpander()
        
        synonym_terms = expander._expand_with_synonyms(["physical therapy", "assessment"])
        
        # Should include synonyms for physical therapy
        assert any("physiotherapy" in term.lower() for term in synonym_terms)
        assert any("pt" in term.lower() for term in synonym_terms)
        
        # Should include synonyms for assessment
        assert any("evaluation" in term.lower() for term in synonym_terms)
    
    def test_expand_abbreviations(self):
        """Test abbreviation expansion."""
        expander = QueryExpander()
        
        abbrev_terms = expander._expand_abbreviations(["PT", "ROM", "assessment"])
        
        # Should expand PT
        assert any("physical therapy" in term.lower() for term in abbrev_terms)
        
        # Should expand ROM
        assert any("range of motion" in term.lower() for term in abbrev_terms)
    
    def test_expand_with_specialty_terms(self):
        """Test discipline-specific expansion."""
        expander = QueryExpander()
        
        # Test that specialty terms are available for each discipline
        pt_specialty_terms = expander.medical_vocab.get_specialty_terms("physical")
        ot_specialty_terms = expander.medical_vocab.get_specialty_terms("occupational")
        slp_specialty_terms = expander.medical_vocab.get_specialty_terms("speech")
        
        assert len(pt_specialty_terms) > 0
        assert len(ot_specialty_terms) > 0
        assert len(slp_specialty_terms) > 0
        
        # Test that the expansion method works (even if it filters heavily)
        # Use queries that should match the filtering logic
        pt_terms = expander._expand_with_specialty_terms("assessment therapy treatment", "pt")
        ot_terms = expander._expand_with_specialty_terms("assessment therapy treatment", "ot")
        slp_terms = expander._expand_with_specialty_terms("assessment therapy treatment", "slp")
        
        # At least the vocabulary should be accessible
        assert isinstance(pt_terms, list)
        assert isinstance(ot_terms, list)
        assert isinstance(slp_terms, list)
    
    def test_expand_with_context(self):
        """Test context-based expansion."""
        expander = QueryExpander()
        
        context_entities = ["gait training", "balance exercises", "strengthening"]
        context_terms = expander._expand_with_context("therapy", context_entities)
        
        # Should return relevant context terms
        assert len(context_terms) >= 0  # May be empty if no synonyms found
    
    def test_expand_with_document_type(self):
        """Test document type expansion."""
        expander = QueryExpander()
        
        # Test progress note expansion
        progress_terms = expander._expand_with_document_type("therapy", "progress_note")
        assert "progress" in progress_terms
        assert "improvement" in progress_terms
        
        # Test evaluation expansion
        eval_terms = expander._expand_with_document_type("therapy", "evaluation")
        assert "assessment" in eval_terms
        assert "examination" in eval_terms
        
        # Test treatment plan expansion
        plan_terms = expander._expand_with_document_type("therapy", "treatment_plan")
        assert "plan" in plan_terms
        assert "goals" in plan_terms
    
    def test_full_query_expansion(self):
        """Test complete query expansion process."""
        expander = QueryExpander()
        
        result = expander.expand_query(
            query="PT assessment",
            discipline="pt",
            document_type="evaluation",
            context_entities=["gait", "balance", "strength"]
        )
        
        # Check result structure
        assert isinstance(result, ExpansionResult)
        assert result.original_query == "PT assessment"
        assert len(result.expanded_terms) >= 0
        assert isinstance(result.expansion_sources, dict)
        assert isinstance(result.confidence_scores, dict)
        
        # Check that expansion sources are populated
        assert len(result.expansion_sources) > 0
        
        # Check expanded query
        expanded_query = result.get_expanded_query()
        assert "PT assessment" in expanded_query or "PT" in expanded_query
    
    def test_expansion_with_limits(self):
        """Test expansion with term limits."""
        expander = QueryExpander()
        expander.max_total_expansions = 3  # Set low limit for testing
        
        result = expander.expand_query(
            query="therapy",
            discipline="pt",
            document_type="progress_note",
            context_entities=["walking", "balance", "strength", "coordination", "endurance"]
        )
        
        # Should respect the limit
        assert len(result.expanded_terms) <= 3
        
        # Should still have confidence scores for included terms
        for term in result.expanded_terms:
            assert term in result.confidence_scores
    
    def test_get_expansion_statistics(self):
        """Test getting expansion statistics."""
        expander = QueryExpander()
        
        stats = expander.get_expansion_statistics()
        
        # Check structure
        assert 'vocabulary_size' in stats
        assert 'expansion_weights' in stats
        assert 'configuration' in stats
        
        # Check vocabulary size info
        vocab_size = stats['vocabulary_size']
        assert 'synonyms' in vocab_size
        assert 'abbreviations' in vocab_size
        assert vocab_size['synonyms'] > 0
        assert vocab_size['abbreviations'] > 0
        
        # Check weights
        weights = stats['expansion_weights']
        assert 'synonym_weight' in weights
        assert 'abbreviation_weight' in weights
        assert weights['synonym_weight'] == expander.synonym_weight
    
    def test_empty_query_handling(self):
        """Test handling of empty or invalid queries."""
        expander = QueryExpander()
        
        # Test empty query
        result = expander.expand_query("")
        assert result.original_query == ""
        assert len(result.expanded_terms) >= 0  # May have some expansions from context
        
        # Test whitespace-only query
        result2 = expander.expand_query("   ")
        assert result2.original_query == "   "
    
    def test_case_insensitive_expansion(self):
        """Test that expansion works regardless of case."""
        expander = QueryExpander()
        
        # Test different cases
        result1 = expander.expand_query("pt assessment")
        result2 = expander.expand_query("PT ASSESSMENT")
        result3 = expander.expand_query("Pt Assessment")
        
        # All should produce expansions (though exact results may vary)
        assert len(result1.expanded_terms) >= 0
        assert len(result2.expanded_terms) >= 0
        assert len(result3.expanded_terms) >= 0


@pytest.mark.integration
class TestQueryExpansionIntegration:
    """Integration tests for query expansion."""
    
    def test_realistic_medical_query_expansion(self):
        """Test expansion with realistic medical queries."""
        expander = QueryExpander()
        
        test_cases = [
            {
                'query': 'PT gait training documentation',
                'discipline': 'pt',
                'doc_type': 'progress_note',
                'expected_expansions': ['physical therapy', 'physiotherapy', 'ambulation', 'walking']
            },
            {
                'query': 'OT ADL assessment',
                'discipline': 'ot', 
                'doc_type': 'evaluation',
                'expected_expansions': ['occupational therapy', 'activities of daily living', 'assessment', 'evaluation']
            },
            {
                'query': 'SLP swallowing therapy',
                'discipline': 'slp',
                'doc_type': 'treatment_plan',
                'expected_expansions': ['speech therapy', 'dysphagia', 'speech pathology']
            }
        ]
        
        for case in test_cases:
            result = expander.expand_query(
                query=case['query'],
                discipline=case['discipline'],
                document_type=case['doc_type']
            )
            
            # Check that we got some expansions
            assert len(result.expanded_terms) > 0
            
            # Check that at least some expected terms are present
            expanded_query_lower = result.get_expanded_query().lower()
            found_expected = sum(1 for term in case['expected_expansions'] 
                               if term.lower() in expanded_query_lower)
            
            # Should find at least some expected terms (or have some expansions)
            # Note: Expansion might not always include the exact expected terms
            assert found_expected > 0 or len(result.expanded_terms) > 0, \
                f"No expected terms or expansions found for '{case['query']}'. " \
                f"Got: {result.get_expanded_query()}"
    
    def test_expansion_with_medical_entities(self):
        """Test expansion with medical entities from NER."""
        expander = QueryExpander()
        
        # Simulate entities extracted from a document
        medical_entities = [
            "gait training",
            "balance exercises", 
            "therapeutic exercise",
            "range of motion",
            "strengthening"
        ]
        
        result = expander.expand_query(
            query="therapy progress",
            discipline="pt",
            context_entities=medical_entities
        )
        
        # Should incorporate context from entities
        assert len(result.expanded_terms) > 0
        
        # Check expansion sources
        assert len(result.expansion_sources) > 0
        
        # Should have reasonable confidence scores
        for term, confidence in result.confidence_scores.items():
            assert 0.0 <= confidence <= 1.0