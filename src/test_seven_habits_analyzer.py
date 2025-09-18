# Python
from __future__ import annotations

import unittest
from typing import List, Dict, Any

# Local
from .seven_habits_analyzer import SevenHabitsAnalyzer


class TestSevenHabitsAnalyzer(unittest.TestCase):

    def setUp(self):
        """Set up an instance of the SevenHabitsAnalyzer for testing."""
        self.analyzer = SevenHabitsAnalyzer()

    def test_proactive_habit_triggers_on_missing_risk(self):
        """
        Test that the 'Be Proactive' habit triggers when anticipated risks
        are not mentioned.
        """
        # Arrange
        text = "The patient was seen for a swallowing evaluation. The plan is to continue with therapy."

        # Act
        findings = self.analyzer.analyze_text(text)

        # Assert
        self.assertGreater(len(findings), 0, "No findings were triggered.")

        # Find the specific finding we expect
        proactive_finding = next((f for f in findings if f["name"] == "Anticipate Risks"), None)

        self.assertIsNotNone(proactive_finding, "The 'Anticipate Risks' finding was not triggered.")
        self.assertEqual(proactive_finding["habit"], "Habit 1: Be Proactive")
        self.assertEqual(proactive_finding["risk_flag"], "🔴 High – Skilled need may be denied")

    def test_begin_with_end_in_mind_triggers_on_missing_discharge_goals(self):
        """
        Test that Habit 2 triggers when discharge criteria are missing from goals.
        """
        # Arrange
        text = "The patient's goal is to improve swallowing."

        # Act
        findings = self.analyzer.analyze_text(text)

        # Assert
        discharge_finding = next((f for f in findings if f["name"] == "Align with Discharge Goals"), None)

        self.assertIsNotNone(discharge_finding, "The 'Align with Discharge Goals' finding was not triggered.")
        self.assertEqual(discharge_finding["habit"], "Habit 2: Begin with the End in Mind")

    def test_no_triggers_on_compliant_text(self):
        """
        Test that no findings are triggered for a compliant piece of text
        that addresses multiple habits.
        """
        # Arrange
        text = """
        The patient was seen for a swallowing evaluation due to aspiration risk.
        Objective findings from the MBS support the need for skilled intervention.
        The long-term goal is for the patient to return to their prior level of function,
        and discharge criteria have been established. Safety precautions were taken.
        The patient's goals were discussed (shared decision-making).
        Therapy will be provided daily due to the high aspiration risk, which provides a clear rationale for frequency.
        The plan aligns with the PT goals for improved functional mobility.
        This analysis is provided by a licensed therapist with credentials.
        Skilled interpretation of the assessment data was performed.
        """

        # Act
        findings = self.analyzer.analyze_text(text)

        # Assert
        self.assertEqual(len(findings), 0, f"Expected no findings, but got: {[f['name'] for f in findings]}")


if __name__ == '__main__':
    unittest.main()
