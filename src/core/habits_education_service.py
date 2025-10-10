"""7 Habits Educational Service.

Provides educational content and guidance for the 7 Habits framework
in clinical documentation compliance.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HabitsEducationService:
    """Service for providing educational content about the 7 Habits framework."""

    def __init__(self):
        """Initialize the habits education service."""
        logger.info("Initializing HabitsEducationService")

    def get_habit_education(self, habit_number: int) -> dict[str, Any]:
        """Get educational content for a specific habit.

        Args:
            habit_number: The habit number (1-7)

        Returns:
            Educational content for the habit

        """
        habits_content = {
            1: {
                "title": "Be Proactive",
                "description": "Take responsibility for your documentation quality",
                "clinical_application": "Proactively ensure all required elements are documented",
                "tips": [
                    "Review documentation requirements before writing",
                    "Use templates and checklists",
                    "Double-check compliance before submitting",
                ],
            },
            2: {
                "title": "Begin with the End in Mind",
                "description": "Document with compliance goals in mind",
                "clinical_application": "Structure notes to meet regulatory requirements",
                "tips": [
                    "Start with compliance objectives",
                    "Use clear, measurable goals",
                    "Document outcomes and progress",
                ],
            },
            3: {
                "title": "Put First Things First",
                "description": "Prioritize essential documentation elements",
                "clinical_application": "Focus on critical compliance areas first",
                "tips": [
                    "Document medical necessity first",
                    "Ensure skilled therapy is clearly described",
                    "Include functional outcomes",
                ],
            },
            4: {
                "title": "Think Win-Win",
                "description": "Balance patient care with compliance requirements",
                "clinical_application": "Document in ways that serve both patient and regulatory needs",
                "tips": [
                    "Use patient-centered language",
                    "Show clear benefit to patient",
                    "Demonstrate skilled intervention",
                ],
            },
            5: {
                "title": "Seek First to Understand, Then to Be Understood",
                "description": "Understand compliance requirements before documenting",
                "clinical_application": "Learn regulations before applying them",
                "tips": [
                    "Study Medicare guidelines",
                    "Understand discipline-specific requirements",
                    "Ask questions when uncertain",
                ],
            },
            6: {
                "title": "Synergize",
                "description": "Combine clinical expertise with compliance knowledge",
                "clinical_application": "Integrate clinical reasoning with regulatory requirements",
                "tips": [
                    "Connect clinical findings to functional goals",
                    "Show interdisciplinary collaboration",
                    "Demonstrate comprehensive care",
                ],
            },
            7: {
                "title": "Sharpen the Saw",
                "description": "Continuously improve documentation skills",
                "clinical_application": "Ongoing education and skill development",
                "tips": [
                    "Attend compliance training",
                    "Review feedback and improve",
                    "Stay updated on regulation changes",
                ],
            },
        }

        return habits_content.get(
            habit_number,
            {
                "title": "Unknown Habit",
                "description": "Habit not found",
                "clinical_application": "",
                "tips": [],
            })

    def get_all_habits_overview(self) -> list[dict[str, Any]]:
        """Get overview of all 7 habits.

        Returns:
            List of all habits with basic information

        """
        return [self.get_habit_education(i) for i in range(1, 8)]

    def get_habit_resources(self, habit_number: int) -> dict[str, Any]:
        """Get additional resources for a specific habit.

        Args:
            habit_number: The habit number (1-7)

        Returns:
            Additional resources and references

        """
        return {
            "habit_number": habit_number,
            "resources": [
                "Medicare Guidelines Reference",
                "Discipline-Specific Documentation Standards",
                "Compliance Best Practices Guide",
            ],
            "examples": [
                "Sample compliant documentation",
                "Common compliance issues to avoid",
                "Improvement strategies",
            ],
        }
