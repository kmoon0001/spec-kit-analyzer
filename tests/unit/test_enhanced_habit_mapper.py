"""
Unit tests for Enhanced 7 Habits Framework.

Tests all 7 habits mapping, AI-powered features, progression tracking,
and configuration integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.enhanced_habit_mapper import SevenHabitsFramework, get_habit_for_finding


class TestSevenHabitsFramework:
    """Tests for SevenHabitsFramework initialization and configuration."""

    def test_initialization_default(self):
        """Test framework initializes with default settings."""
        framework = SevenHabitsFramework()
        
        assert framework.use_ai_mapping is False
        assert framework.llm_service is None
        assert len(framework.HABITS) == 7

    def test_initialization_with_ai(self):
        """Test framework initializes with AI mapping enabled."""
        mock_llm = MagicMock()
        framework = SevenHabitsFramework(use_ai_mapping=True, llm_service=mock_llm)
        
        assert framework.use_ai_mapping is True
        assert framework.llm_service == mock_llm

    def test_all_seven_habits_present(self):
        """Test all 7 habits are defined."""
        framework = SevenHabitsFramework()
        
        assert "habit_1" in framework.HABITS
        assert "habit_2" in framework.HABITS
        assert "habit_3" in framework.HABITS
        assert "habit_4" in framework.HABITS  # NEW
        assert "habit_5" in framework.HABITS
        assert "habit_6" in framework.HABITS  # NEW
        assert "habit_7" in framework.HABITS  # NEW

    def test_habit_structure_complete(self):
        """Test each habit has all required fields."""
        framework = SevenHabitsFramework()
        
        required_fields = [
            "number", "name", "principle", "clinical_application",
            "description", "keywords", "clinical_examples",
            "improvement_strategies", "common_issues"
        ]
        
        for habit_id, habit in framework.HABITS.items():
            for field in required_fields:
                assert field in habit, f"{habit_id} missing {field}"
                assert habit[field], f"{habit_id} has empty {field}"


class TestRuleBasedMapping:
    """Tests for rule-based habit mapping."""

    def test_habit_1_proactive_mapping(self):
        """Test Habit 1 (Be Proactive) mapping."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Incomplete documentation",
            "text": "Missing required elements"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 1
        assert "Be Proactive" in result["name"]
        assert "proactive" in result["explanation"].lower()

    def test_habit_2_begin_with_end_mapping(self):
        """Test Habit 2 (Begin with the End in Mind) mapping."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Goals not measurable",
            "text": "Patient goals lack specificity"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 2
        assert "Begin with the End" in result["name"]

    def test_habit_3_put_first_things_first_mapping(self):
        """Test Habit 3 (Put First Things First) mapping."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Missing signature",
            "text": "Note not signed timely"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 3
        assert "Put First Things First" in result["name"]

    def test_habit_4_think_win_win_mapping(self):
        """Test Habit 4 (Think Win-Win) mapping - NEW HABIT."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Poor interdisciplinary collaboration",
            "text": "Documentation doesn't support billing"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 4
        assert "Think Win-Win" in result["name"]
        assert "collaboration" in result["explanation"].lower() or "stakeholder" in result["explanation"].lower()

    def test_habit_5_seek_first_to_understand_mapping(self):
        """Test Habit 5 (Seek First to Understand) mapping."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Insufficient justification of medical necessity",
            "text": "Skilled service not clearly documented"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 5
        assert "Seek First to Understand" in result["name"]

    def test_habit_6_synergize_mapping(self):
        """Test Habit 6 (Synergize) mapping - NEW HABIT."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Inconsistency between disciplines",
            "text": "Therapy notes don't align with physician orders"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 6
        assert "Synergize" in result["name"]

    def test_habit_7_sharpen_the_saw_mapping(self):
        """Test Habit 7 (Sharpen the Saw) mapping - NEW HABIT."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Outdated documentation practices",
            "text": "Not following current training guidelines"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 7
        assert "Sharpen the Saw" in result["name"]

    def test_default_to_habit_1_no_matches(self):
        """Test defaults to Habit 1 when no keywords match."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": "Random issue",
            "text": "No matching keywords"
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] == 1  # Default

    def test_confidence_scoring(self):
        """Test confidence scoring based on keyword matches."""
        framework = SevenHabitsFramework()
        
        # Strong match (multiple keywords)
        finding_strong = {
            "issue_title": "Missing signature and date",
            "text": "Note not signed timely"
        }
        
        result_strong = framework.map_finding_to_habit(finding_strong)
        
        # Weak match (no keywords)
        finding_weak = {
            "issue_title": "Random issue",
            "text": "No keywords"
        }
        
        result_weak = framework.map_finding_to_habit(finding_weak)
        
        assert result_strong["confidence"] > result_weak["confidence"]


class TestAIPoweredMapping:
    """Tests for AI-powered habit mapping."""

    @patch('src.core.enhanced_habit_mapper.SevenHabitsFramework._ai_powered_mapping')
    def test_ai_mapping_called_when_enabled(self, mock_ai_mapping):
        """Test AI mapping is used when enabled."""
        mock_llm = MagicMock()
        mock_llm.is_ready.return_value = True
        
        framework = SevenHabitsFramework(use_ai_mapping=True, llm_service=mock_llm)
        
        finding = {"issue_title": "Test", "text": "Test"}
        framework.map_finding_to_habit(finding)
        
        mock_ai_mapping.assert_called_once()

    def test_ai_mapping_fallback_when_llm_not_ready(self):
        """Test falls back to rule-based when LLM not ready."""
        mock_llm = MagicMock()
        mock_llm.is_ready.return_value = False
        
        framework = SevenHabitsFramework(use_ai_mapping=True, llm_service=mock_llm)
        
        finding = {"issue_title": "Missing signature", "text": "Not signed"}
        result = framework.map_finding_to_habit(finding)
        
        # Should still get a result (from rule-based fallback)
        assert result["habit_number"] in range(1, 8)

    def test_ai_mapping_with_context(self):
        """Test AI mapping uses context information."""
        mock_llm = MagicMock()
        mock_llm.is_ready.return_value = True
        mock_llm.generate.return_value = '{"habit_id": "habit_2", "explanation": "Test", "strategies": ["Strategy 1"], "confidence": 0.9}'
        mock_llm.parse_json_output.return_value = {
            "habit_id": "habit_2",
            "explanation": "Test explanation",
            "strategies": ["Strategy 1"],
            "confidence": 0.9
        }
        
        framework = SevenHabitsFramework(use_ai_mapping=True, llm_service=mock_llm)
        
        finding = {"issue_title": "Test", "text": "Test"}
        context = {"document_type": "Progress Note", "discipline": "PT"}
        
        result = framework.map_finding_to_habit(finding, context)
        
        assert result["habit_number"] == 2
        assert result["ai_generated"] is True


class TestHabitDetails:
    """Tests for habit information retrieval."""

    def test_get_habit_details(self):
        """Test retrieving complete habit details."""
        framework = SevenHabitsFramework()
        
        habit = framework.get_habit_details("habit_1")
        
        assert habit["number"] == 1
        assert habit["name"] == "Be Proactive"
        assert "principle" in habit
        assert len(habit["improvement_strategies"]) >= 4

    def test_get_all_habits(self):
        """Test retrieving all habits."""
        framework = SevenHabitsFramework()
        
        all_habits = framework.get_all_habits()
        
        assert len(all_habits) == 7
        assert all(["habit_id" in h for h in all_habits])

    def test_habit_has_clinical_examples(self):
        """Test each habit has clinical examples."""
        framework = SevenHabitsFramework()
        
        for habit_id in framework.HABITS:
            habit = framework.get_habit_details(habit_id)
            assert len(habit["clinical_examples"]) >= 4

    def test_habit_has_improvement_strategies(self):
        """Test each habit has improvement strategies."""
        framework = SevenHabitsFramework()
        
        for habit_id in framework.HABITS:
            habit = framework.get_habit_details(habit_id)
            assert len(habit["improvement_strategies"]) >= 4


class TestHabitProgression:
    """Tests for habit progression tracking."""

    def test_progression_metrics_calculation(self):
        """Test habit progression metrics are calculated correctly."""
        framework = SevenHabitsFramework()
        
        findings_history = [
            {"habit_id": "habit_1"},
            {"habit_id": "habit_1"},
            {"habit_id": "habit_2"},
            {"habit_id": "habit_5"},
            {"habit_id": "habit_5"},
            {"habit_id": "habit_5"},
        ]
        
        metrics = framework.get_habit_progression_metrics(findings_history)
        
        assert metrics["total_findings"] == 6
        assert metrics["habit_breakdown"]["habit_1"]["finding_count"] == 2
        assert metrics["habit_breakdown"]["habit_5"]["finding_count"] == 3

    def test_mastery_level_calculation(self):
        """Test mastery levels are calculated correctly."""
        framework = SevenHabitsFramework()
        
        # Mastered: <5%
        findings_mastered = [{"habit_id": "habit_1"}] + [{"habit_id": "habit_2"}] * 99
        metrics_mastered = framework.get_habit_progression_metrics(findings_mastered)
        assert metrics_mastered["habit_breakdown"]["habit_1"]["mastery_level"] == "Mastered"
        
        # Needs Focus: >25%
        findings_needs_focus = [{"habit_id": "habit_1"}] * 30 + [{"habit_id": "habit_2"}] * 70
        metrics_needs_focus = framework.get_habit_progression_metrics(findings_needs_focus)
        assert metrics_needs_focus["habit_breakdown"]["habit_1"]["mastery_level"] == "Needs Focus"

    def test_focus_areas_identification(self):
        """Test focus areas are identified correctly."""
        framework = SevenHabitsFramework()
        
        findings = [{"habit_id": "habit_5"}] * 30 + [{"habit_id": "habit_1"}] * 70
        metrics = framework.get_habit_progression_metrics(findings)
        
        # Habit 1 should be top focus area (70%)
        assert len(metrics["top_focus_areas"]) > 0
        top_habit_id, top_metrics = metrics["top_focus_areas"][0]
        assert top_habit_id == "habit_1"
        assert top_metrics["needs_focus"] is True

    def test_empty_findings_history(self):
        """Test progression metrics with empty history."""
        framework = SevenHabitsFramework()
        
        metrics = framework.get_habit_progression_metrics([])
        
        assert metrics["total_findings"] == 0
        assert len(metrics["top_focus_areas"]) == 0


class TestBackwardCompatibility:
    """Tests for backward compatibility with legacy code."""

    def test_legacy_function_works(self):
        """Test legacy get_habit_for_finding function still works."""
        finding = {
            "issue_title": "Missing signature",
            "text": "Not signed"
        }
        
        result = get_habit_for_finding(finding)
        
        assert "name" in result
        assert "explanation" in result
        assert "Habit" in result["name"]

    def test_legacy_function_returns_correct_format(self):
        """Test legacy function returns expected format."""
        finding = {"issue_title": "Test", "text": "Test"}
        
        result = get_habit_for_finding(finding)
        
        # Legacy format: {"name": "Habit X: Name", "explanation": "..."}
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "name" in result
        assert "explanation" in result


class TestHabitContent:
    """Tests for habit content quality and completeness."""

    def test_all_habits_have_unique_numbers(self):
        """Test each habit has a unique number 1-7."""
        framework = SevenHabitsFramework()
        
        numbers = [habit["number"] for habit in framework.HABITS.values()]
        
        assert sorted(numbers) == list(range(1, 8))

    def test_all_habits_have_principles(self):
        """Test each habit has Covey's principle defined."""
        framework = SevenHabitsFramework()
        
        for habit in framework.HABITS.values():
            assert habit["principle"]
            assert len(habit["principle"]) > 5

    def test_all_habits_have_clinical_applications(self):
        """Test each habit has clinical application defined."""
        framework = SevenHabitsFramework()
        
        for habit in framework.HABITS.values():
            assert habit["clinical_application"]
            assert "document" in habit["clinical_application"].lower()

    def test_keywords_are_lowercase(self):
        """Test all keywords are lowercase for matching."""
        framework = SevenHabitsFramework()
        
        for habit in framework.HABITS.values():
            for keyword in habit["keywords"]:
                assert keyword == keyword.lower()

    def test_no_empty_strategies(self):
        """Test no habit has empty improvement strategies."""
        framework = SevenHabitsFramework()
        
        for habit in framework.HABITS.values():
            assert len(habit["improvement_strategies"]) > 0
            for strategy in habit["improvement_strategies"]:
                assert strategy.strip()

    def test_no_empty_examples(self):
        """Test no habit has empty clinical examples."""
        framework = SevenHabitsFramework()
        
        for habit in framework.HABITS.values():
            assert len(habit["clinical_examples"]) > 0
            for example in habit["clinical_examples"]:
                assert example.strip()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_finding(self):
        """Test handling of empty finding."""
        framework = SevenHabitsFramework()
        
        finding = {}
        result = framework.map_finding_to_habit(finding)
        
        # Should default to Habit 1
        assert result["habit_number"] == 1

    def test_finding_with_none_values(self):
        """Test handling of None values in finding."""
        framework = SevenHabitsFramework()
        
        finding = {
            "issue_title": None,
            "text": None
        }
        
        result = framework.map_finding_to_habit(finding)
        
        assert result["habit_number"] in range(1, 8)

    def test_invalid_habit_id_in_progression(self):
        """Test progression metrics handles invalid habit IDs."""
        framework = SevenHabitsFramework()
        
        findings = [
            {"habit_id": "habit_1"},
            {"habit_id": "invalid_habit"},
            {"habit_id": "habit_2"}
        ]
        
        # Should not crash
        metrics = framework.get_habit_progression_metrics(findings)
        
        assert metrics["total_findings"] == 3

    def test_get_invalid_habit_details(self):
        """Test getting details for invalid habit ID."""
        framework = SevenHabitsFramework()
        
        # Should return Habit 1 as default
        habit = framework.get_habit_details("invalid_habit")
        
        assert habit["number"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
