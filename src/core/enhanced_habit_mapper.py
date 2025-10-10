"""
Enhanced 7 Habits Framework for Clinical Compliance.

Maps compliance findings to Stephen Covey's 7 Habits of Highly Effective People,
providing personalized coaching and improvement strategies for clinical documentation.

This enhanced version includes:
- All 7 habits (previously only 5)
- AI-powered contextual mapping
- Detailed habit resources and explanations
- Progression tracking support
- Personalized coaching recommendations
"""

import logging
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class HabitDefinition(TypedDict):
    """Structured definition for a single habit."""

    number: int
    name: str
    principle: str
    clinical_application: str
    description: str
    keywords: list[str]
    clinical_examples: list[str]
    improvement_strategies: list[str]
    common_issues: list[str]


class HabitMetrics(TypedDict):
    """Metrics describing habit prevalence and focus."""

    habit_number: int
    habit_name: str
    finding_count: int
    percentage: float
    needs_focus: bool
    mastery_level: str


class SevenHabitsFramework:
    """
    Complete implementation of Stephen Covey's 7 Habits framework
    applied to clinical documentation compliance.
    """

    # Complete 7 Habits definitions with clinical applications
    HABITS: dict[str, HabitDefinition] = {
        "habit_1": {
            "number": 1,
            "name": "Be Proactive",
            "principle": "Personal Responsibility",
            "clinical_application": "Take initiative in documentation quality",
            "description": """
            Being proactive means taking responsibility for your documentation quality
            before issues arise. Instead of reacting to compliance findings, proactively
            review your work, stay current with guidelines, and anticipate reviewer needs.
            """,
            "keywords": [
                "incomplete",
                "missing",
                "omitted",
                "forgot",
                "overlooked",
                "general",
                "vague",
                "unclear",
            ],
            "clinical_examples": [
                "Proactively reviewing documentation before submission",
                "Staying current with Medicare guidelines",
                "Using checklists to ensure completeness",
                "Self-auditing documentation regularly",
            ],
            "improvement_strategies": [
                "Create a personal documentation checklist",
                "Set aside time for daily documentation review",
                "Subscribe to compliance update newsletters",
                "Conduct monthly self-audits",
            ],
            "common_issues": [
                "Incomplete documentation",
                "Missing required elements",
                "Vague or unclear descriptions",
                "Reactive rather than proactive approach",
            ],
        },
        "habit_2": {
            "number": 2,
            "name": "Begin with the End in Mind",
            "principle": "Personal Vision",
            "clinical_application": "Document with clear goals and outcomes",
            "description": """
            Begin with the end in mind means having a clear vision of what you want to
            achieve. In clinical documentation, this means establishing clear, measurable,
            functional goals from the start and documenting progress toward those goals
            in every note.
            """,
            "keywords": [
                "goal",
                "objective",
                "outcome",
                "plan of care",
                "discharge",
                "prognosis",
                "functional",
                "measurable",
            ],
            "clinical_examples": [
                "Writing SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)",
                "Documenting clear discharge criteria",
                "Establishing functional outcomes from day one",
                "Aligning treatment with patient's life goals",
            ],
            "improvement_strategies": [
                "Use SMART goal framework for all goals",
                "Document patient's functional baseline and target",
                "Include patient's personal goals in plan of care",
                "Review and update goals regularly",
            ],
            "common_issues": [
                "Goals not measurable or functional",
                "Missing discharge criteria",
                "Goals not aligned with medical necessity",
                "Lack of clear treatment outcomes",
            ],
        },
        "habit_3": {
            "number": 3,
            "name": "Put First Things First",
            "principle": "Personal Management",
            "clinical_application": "Prioritize critical documentation tasks",
            "description": """
            Put first things first means prioritizing what's most important. In clinical
            documentation, this means completing time-sensitive tasks (signatures, dates,
            certifications) promptly and ensuring critical compliance elements are never
            overlooked due to time pressure.
            """,
            "keywords": [
                "signature",
                "signed",
                "date",
                "dated",
                "timely",
                "certification",
                "recertification",
                "deadline",
                "overdue",
                "late",
            ],
            "clinical_examples": [
                "Signing notes within required timeframes",
                "Completing certifications before deadlines",
                "Prioritizing documentation of skilled services",
                "Managing time effectively during patient care",
            ],
            "improvement_strategies": [
                "Sign notes immediately after treatment",
                "Set calendar reminders for certification deadlines",
                "Use time-blocking for documentation",
                "Prioritize high-risk documentation elements",
            ],
            "common_issues": [
                "Missing or late signatures",
                "Missed certification deadlines",
                "Incomplete time-sensitive documentation",
                "Poor time management affecting quality",
            ],
        },
        "habit_4": {
            "number": 4,
            "name": "Think Win-Win",
            "principle": "Interpersonal Leadership",
            "clinical_application": "Create documentation that serves all stakeholders",
            "description": """
            Think win-win means seeking mutual benefit in all interactions. In clinical
            documentation, this means creating notes that serve multiple purposes: excellent
            patient care, clear communication with the team, compliance with regulations,
            and appropriate reimbursement. Good documentation benefits everyone.
            """,
            "keywords": [
                "collaboration",
                "team",
                "interdisciplinary",
                "coordination",
                "communication",
                "billing",
                "reimbursement",
                "stakeholder",
            ],
            "clinical_examples": [
                "Writing notes that inform the entire care team",
                "Documenting in ways that support appropriate billing",
                "Coordinating care through clear communication",
                "Balancing patient care with compliance needs",
            ],
            "improvement_strategies": [
                "Consider all readers when documenting (team, reviewers, auditors)",
                "Coordinate documentation with billing staff",
                "Participate in interdisciplinary team meetings",
                "Document collaboration and coordination efforts",
            ],
            "common_issues": [
                "Documentation doesn't support billing",
                "Poor interdisciplinary communication",
                "Lack of coordination documentation",
                "Missing stakeholder perspectives",
            ],
        },
        "habit_5": {
            "number": 5,
            "name": "Seek First to Understand, Then to Be Understood",
            "principle": "Empathic Communication",
            "clinical_application": "Understand requirements, then document clearly",
            "description": """
            Seek first to understand means truly comprehending before communicating. In
            clinical documentation, this means first understanding the patient's unique
            needs and the reviewer's perspective, then documenting in a way that clearly
            communicates medical necessity and skilled service provision.
            """,
            "keywords": [
                "skilled",
                "medical necessity",
                "justify",
                "rationale",
                "clinical reasoning",
                "complexity",
                "unique",
                "specialized",
            ],
            "clinical_examples": [
                "Understanding patient's unique clinical presentation",
                "Documenting why skilled therapy is necessary",
                "Explaining clinical reasoning clearly",
                "Anticipating reviewer questions",
            ],
            "improvement_strategies": [
                "Document the 'why' not just the 'what'",
                "Explain complexity and skilled nature of services",
                "Use clinical reasoning in every note",
                "Put yourself in the reviewer's shoes",
            ],
            "common_issues": [
                "Insufficient justification of medical necessity",
                "Missing clinical reasoning",
                "Unclear skilled service documentation",
                "Failure to explain complexity",
            ],
        },
        "habit_6": {
            "number": 6,
            "name": "Synergize",
            "principle": "Creative Cooperation",
            "clinical_application": "Integrate documentation across disciplines",
            "description": """
            Synergize means the whole is greater than the sum of its parts. In clinical
            documentation, this means ensuring therapy, nursing, physician, and billing
            documentation work together seamlessly. When all disciplines document
            consistently, compliance and patient care both improve.
            """,
            "keywords": [
                "consistency",
                "alignment",
                "integration",
                "multidisciplinary",
                "physician",
                "nursing",
                "discrepancy",
                "conflict",
            ],
            "clinical_examples": [
                "Aligning therapy goals with physician orders",
                "Ensuring consistency across disciplines",
                "Integrating billing and clinical documentation",
                "Coordinating discharge planning",
            ],
            "improvement_strategies": [
                "Review physician orders before documenting",
                "Coordinate with nursing on patient status",
                "Ensure billing codes match documentation",
                "Participate in care coordination meetings",
            ],
            "common_issues": [
                "Inconsistencies between disciplines",
                "Documentation doesn't match orders",
                "Billing and clinical documentation misaligned",
                "Poor interdisciplinary coordination",
            ],
        },
        "habit_7": {
            "number": 7,
            "name": "Sharpen the Saw",
            "principle": "Continuous Improvement",
            "clinical_application": "Continuously improve documentation skills",
            "description": """
            Sharpen the saw means continuous renewal and improvement. In clinical
            documentation, this means regularly updating your knowledge, learning from
            feedback, attending training, and continuously refining your documentation
            practices. Excellence in documentation is a journey, not a destination.
            """,
            "keywords": [
                "training",
                "education",
                "improvement",
                "quality",
                "review",
                "audit",
                "feedback",
                "learning",
                "development",
                "update",
            ],
            "clinical_examples": [
                "Attending documentation training regularly",
                "Learning from audit feedback",
                "Staying current with guideline changes",
                "Seeking mentorship and peer review",
            ],
            "improvement_strategies": [
                "Schedule regular training and education",
                "Review audit findings and learn from them",
                "Join professional documentation communities",
                "Set personal improvement goals",
            ],
            "common_issues": [
                "Outdated documentation practices",
                "Not learning from past mistakes",
                "Lack of ongoing education",
                "Resistance to change and improvement",
            ],
        },
    }

    def __init__(self, use_ai_mapping: bool = False, llm_service=None):
        """
        Initialize the 7 Habits framework.

        Args:
            use_ai_mapping: Whether to use AI for contextual habit mapping
            llm_service: Optional LLM service for AI-powered mapping
        """
        self.use_ai_mapping = use_ai_mapping
        self.llm_service = llm_service

    def map_finding_to_habit(
        self, finding: dict[str, Any], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Map a compliance finding to the most appropriate habit.

        Args:
            finding: Compliance finding dictionary
            context: Optional context (document type, discipline, etc.)

        Returns:
            Dict with habit information and personalized guidance
        """
        if self.use_ai_mapping and self.llm_service:
            return self._ai_powered_mapping(finding, context)
        else:
            return self._rule_based_mapping(finding)

    def _rule_based_mapping(self, finding: dict[str, Any]) -> dict[str, Any]:
        """
        Map finding to habit using keyword-based rules.

        Args:
            finding: Compliance finding dictionary

        Returns:
            Dict with habit information
        """
        issue_title = (finding.get("issue_title") or "").lower()
        issue_text = (finding.get("text") or "").lower()
        combined_text = f"{issue_title} {issue_text}"

        # Score each habit based on keyword matches (using word boundaries)
        import re
        habit_scores: dict[str, int] = {}
        for habit_id, habit_info in self.HABITS.items():
            score = sum(
                1 for keyword in habit_info["keywords"]
                if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text)
            )
            habit_scores[habit_id] = score

        # Get habit with highest score (default to Habit 1 if no matches)
        best_habit_id = max(habit_scores, key=lambda habit_id: habit_scores[habit_id])
        if habit_scores[best_habit_id] == 0:
            best_habit_id = "habit_1"  # Default to Be Proactive

        habit = self.HABITS[best_habit_id]

        return {
            "habit_id": best_habit_id,
            "habit_number": habit["number"],
            "name": habit["name"],
            "principle": habit["principle"],
            "explanation": habit["clinical_application"],
            "detailed_description": habit["description"].strip(),
            "improvement_strategies": habit["improvement_strategies"],
            "clinical_examples": habit["clinical_examples"],
            "common_issues": habit["common_issues"],
            "confidence": min(habit_scores[best_habit_id] / 3.0, 1.0),  # Normalize
        }

    def _ai_powered_mapping(
        self, finding: dict[str, Any], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Use AI to map finding to habit with contextual understanding.

        Args:
            finding: Compliance finding dictionary
            context: Optional context information

        Returns:
            Dict with habit information and AI-generated insights
        """
        if not self.llm_service or not self.llm_service.is_ready():
            logger.warning("AI mapping requested but LLM not available, using rules")
            return self._rule_based_mapping(finding)

        # Build prompt for AI
        prompt = self._build_ai_mapping_prompt(finding, context)

        try:
            response = self.llm_service.generate(prompt)
            result = self.llm_service.parse_json_output(response)

            # Validate and enrich with habit details
            habit_id = result.get("habit_id", "habit_1")
            if habit_id not in self.HABITS:
                habit_id = "habit_1"

            habit = self.HABITS[habit_id]

            return {
                "habit_id": habit_id,
                "habit_number": habit["number"],
                "name": habit["name"],
                "principle": habit["principle"],
                "explanation": result.get("explanation", habit["clinical_application"]),
                "detailed_description": habit["description"].strip(),
                "improvement_strategies": result.get(
                    "strategies", habit["improvement_strategies"]
                ),
                "clinical_examples": habit["clinical_examples"],
                "common_issues": habit["common_issues"],
                "confidence": result.get("confidence", 0.8),
                "ai_generated": True,
            }

        except Exception as e:
            logger.exception(f"AI mapping failed: {e}")
            return self._rule_based_mapping(finding)

    def _build_ai_mapping_prompt(
        self, finding: dict[str, Any], context: dict[str, Any] | None = None
    ) -> str:
        """Build prompt for AI-powered habit mapping."""
        habits_summary = "\n".join(
            [
                f"- Habit {h['number']}: {h['name']} - {h['clinical_application']}"
                for h in self.HABITS.values()
            ]
        )

        context_str = ""
        if context:
            context_str = f"\n**Context:** Document Type: {context.get('document_type', 'Unknown')}, Discipline: {context.get('discipline', 'Unknown')}"

        prompt = f"""
You are an expert in clinical documentation and Stephen Covey's 7 Habits framework.

**Compliance Finding:**
- Issue: {finding.get("issue_title", "Unknown")}
- Text: {finding.get("text", "N/A")}
- Risk: {finding.get("risk", "Unknown")}
{context_str}

**7 Habits Framework:**
{habits_summary}

**Task:**
Map this compliance finding to the most appropriate habit and provide personalized guidance.

Return a JSON object:
{{
  "habit_id": "habit_X",
  "explanation": "Brief explanation of why this habit applies (2-3 sentences)",
  "strategies": ["Specific strategy 1", "Specific strategy 2", "Specific strategy 3"],
  "confidence": 0.0-1.0
}}
"""
        return prompt

    def get_habit_details(self, habit_id: str) -> HabitDefinition:
        """
        Get complete details for a specific habit.

        Args:
            habit_id: Habit identifier (e.g., "habit_1")

        Returns:
            Complete habit information
        """
        return self.HABITS.get(habit_id, self.HABITS["habit_1"])

    def get_all_habits(self) -> list[dict[str, Any]]:
        """
        Get information for all 7 habits.

        Returns:
            List of all habit dictionaries
        """
        return [
            {**habit, "habit_id": habit_id} for habit_id, habit in self.HABITS.items()
        ]

    def get_habit_progression_metrics(
        self, findings_history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calculate habit progression metrics from historical findings.

        Args:
            findings_history: List of historical findings with habit mappings

        Returns:
            Dict with progression metrics for each habit
        """
        habit_counts = {habit_id: 0 for habit_id in self.HABITS.keys()}
        total_findings = len(findings_history)

        for finding in findings_history:
            habit_id = finding.get("habit_id", "habit_1")
            if habit_id in habit_counts:
                habit_counts[habit_id] += 1

        # Calculate percentages and identify focus areas
        habit_metrics: dict[str, HabitMetrics] = {}
        for habit_id, count in habit_counts.items():
            habit = self.HABITS[habit_id]
            percentage = (count / total_findings * 100) if total_findings > 0 else 0

            habit_metrics[habit_id] = {
                "habit_number": habit["number"],
                "habit_name": habit["name"],
                "finding_count": count,
                "percentage": round(percentage, 1),
                "needs_focus": percentage > 20,  # More than 20% of issues
                "mastery_level": self._calculate_mastery_level(percentage),
            }

        top_focus_areas: list[tuple[str, HabitMetrics]] = sorted(
            [
                (hid, metrics)
                for hid, metrics in habit_metrics.items()
                if metrics["needs_focus"]
            ],
            key=lambda item: item[1]["percentage"],
            reverse=True,
        )[:3]

        return {
            "total_findings": total_findings,
            "habit_breakdown": habit_metrics,
            "top_focus_areas": top_focus_areas,
        }

    def _calculate_mastery_level(self, percentage: float) -> str:
        """Calculate mastery level based on finding percentage."""
        if percentage < 5:
            return "Mastered"
        elif percentage < 15:
            return "Proficient"
        elif percentage < 25:
            return "Developing"
        else:
            return "Needs Focus"


# Backward compatibility function
def get_habit_for_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """
    Legacy function for backward compatibility.

    Maps a finding to a habit using the enhanced framework.
    """
    framework = SevenHabitsFramework(use_ai_mapping=False)
    result = framework.map_finding_to_habit(finding)

    # Return in legacy format
    return {
        "name": f"Habit {result['habit_number']}: {result['name']}",
        "explanation": result["explanation"],
    }
