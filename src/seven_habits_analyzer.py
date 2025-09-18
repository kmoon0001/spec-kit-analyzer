# Python
from __future__ import annotations

import re
from typing import List, Dict, Any

# The 14 nodes for the 7 Habits, structured for the analyzer.
SEVEN_HABITS_NODES: List[Dict[str, Any]] = [
    # Habit 1: Be Proactive
    {
        "habit": "Habit 1: Be Proactive",
        "name": "Anticipate Risks",
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["anticipate", "complications", "risk of non-treatment"]),
        "improvement_prompt": "Include clinical risks of non-treatment to justify skilled oversight.",
        "audit_safe_default": "Therapist to document anticipated decline or safety risk without intervention.",
        "risk_flag": "🔴 High – Skilled need may be denied"
    },
    {
        "habit": "Habit 1: Be Proactive",
        "name": "Proactive Justification",
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["objective findings", "mbs", "moca", "medical necessity"]),
        "improvement_prompt": "Add objective findings (e.g., MBS, MoCA) to support medical necessity.",
        "audit_safe_default": "Therapist to cite clinical data supporting skilled intervention.",
        "risk_flag": "🔴 High – Skilled need not supported"
    },
    # Habit 2: Begin with the End in Mind
    {
        "habit": "Habit 2: Begin with the End in Mind",
        "name": "Align with Discharge Goals",
        "trigger_logic": lambda text: "goal" in text.lower() and not any(k in text.lower() for k in ["discharge criteria", "prior level of function"]),
        "improvement_prompt": "Add long-term goals tied to baseline function and discharge readiness.",
        "audit_safe_default": "Therapist to clarify functional outcomes and discharge plan.",
        "risk_flag": "🟠 Moderate – Goals may appear task-focused"
    },
    {
        "habit": "Habit 2: Begin with the End in Mind",
        "name": "Link to Measurable Outcomes",
        "trigger_logic": lambda text: "intervention" in text.lower() and not any(k in text.lower() for k in ["measurable outcome", "po intake", "med management"]),
        "improvement_prompt": "Link skilled techniques to functional goals (e.g., PO intake, med management).",
        "audit_safe_default": "Therapist to align interventions with SMART goals.",
        "risk_flag": "🟠 Moderate – Outcome defensibility weak"
    },
    # Habit 3: Put First Things First
    {
        "habit": "Habit 3: Put First Things First",
        "name": "Prioritize Safety",
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["safety precaution", "aspiration risk mitigation", "supervision level"]),
        "improvement_prompt": "Include aspiration risk mitigation and supervision level.",
        "audit_safe_default": "Therapist to document safety measures and clinical reasoning.",
        "risk_flag": "🔴 High – Safety not addressed"
    },
    {
        "habit": "Habit 3: Put First Things First",
        "name": "Justify Sequencing",
        "trigger_logic": lambda text: "session" in text.lower() and not any(k in text.lower() for k in ["task sequencing", "cognitive tasks precede"]),
        "improvement_prompt": "Explain why cognitive tasks precede swallowing or vice versa.",
        "audit_safe_default": "Therapist to justify treatment order based on patient response.",
        "risk_flag": "🟠 Moderate – Skilled oversight unclear"
    },
    # Habit 4: Think Win-Win
    {
        "habit": "Habit 4: Think Win-Win",
        "name": "Incorporate Patient Priorities",
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["shared decision-making", "patient goals", "caregiver input"]),
        "improvement_prompt": "Document patient goals or caregiver input to support individualized care.",
        "audit_safe_default": "Therapist to include patient-centered rationale.",
        "risk_flag": "🟠 Moderate – May appear generic"
    },
    {
        "habit": "Habit 4: Think Win-Win",
        "name": "Align Goals with Severity",
        "trigger_logic": lambda text: "goal" in text.lower() and not any(k in text.lower() for k in ["fois", "slums", "align with severity"]),
        "improvement_prompt": "Align goals with clinical severity using FOIS, SLUMS, or other scales.",
        "audit_safe_default": "Therapist to reconcile goals with documented impairments.",
        "risk_flag": "🔴 High – Medical necessity mismatch"
    },
    # Habit 5: Seek First to Understand, Then to Be Understood
    {
        "habit": "Habit 5: Seek First to Understand, Then to Be Understood",
        "name": "Justify Frequency/Duration",
        "trigger_logic": lambda text: "daily" in text.lower() and not any(k in text.lower() for k in ["rationale for frequency", "aspiration risk", "rapid decline"]),
        "improvement_prompt": "Add rationale for frequency—e.g., aspiration risk, rapid decline.",
        "audit_safe_default": "Therapist to document clinical need for visit intensity.",
        "risk_flag": "🔴 High – Frequency may be denied"
    },
    {
        "habit": "Habit 5: Seek First to Understand, Then to Be Understood",
        "name": "Reflect Team Input",
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["caregiver feedback", "team feedback", "interdisciplinary input"]),
        "improvement_prompt": "Include interdisciplinary input to support care plan.",
        "audit_safe_default": "Therapist to document team coordination.",
        "risk_flag": "🟠 Moderate – May appear siloed"
    },
    # Habit 6: Synergize
    {
        "habit": "Habit 6: Synergize",
        "name": "Integrate Team Goals",
        "trigger_logic": lambda text: "goal" in text.lower() and not any(k in text.lower() for k in ["nursing goals", "pt goals", "team-based goals"]),
        "improvement_prompt": "Reference team-based goals (e.g., diet trials, fall prevention).",
        "audit_safe_default": "Therapist to document collaborative strategies.",
        "risk_flag": "🟠 Moderate – Team synergy unclear"
    },
    {
        "habit": "Habit 6: Synergize",
        "name": "Link to Interdisciplinary Progress",
        "trigger_logic": lambda text: "functional outcome" in text.lower() and not any(k in text.lower() for k in ["nursing documentation", "ot/pt documentation"]),
        "improvement_prompt": "Align SLP goals with nursing/OT/PT documentation.",
        "audit_safe_default": "Therapist to cross-reference team progress.",
        "risk_flag": "🟠 Moderate – Functional impact may be underrepresented"
    },
    # Habit 7: Sharpen the Saw
    {
        "habit": "Habit 7: Sharpen the Saw",
        "name": "Emphasize Qualifications",
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["credentials", "cbis", "mbsimp", "ceu-informed"]),
        "improvement_prompt": "Add CBIS, MBSImP, or CEU-informed techniques.",
        "audit_safe_default": "Therapist to document licensure and clinical expertise.",
        "risk_flag": "🔴 High – Skilled provider role not evident"
    },
    {
        "habit": "Habit 7: Sharpen the Saw",
        "name": "Show Skilled Analysis",
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["analysis of", "skilled interpretation"]),
        "improvement_prompt": "Include analysis of swallow physiology or cognitive performance.",
        "audit_safe_default": "Therapist to document skilled interpretation of assessment data.",
        "risk_flag": "🔴 High – Skilled intervention may be denied"
    }
]


class SevenHabitsAnalyzer:
    """
    Analyzes document text against the 7 Habits framework to promote
    highly effective documentation.
    """

    def __init__(self):
        self.nodes = SEVEN_HABITS_NODES

    def analyze_text(self, full_text: str) -> List[Dict[str, Any]]:
        """
        Runs the 7 Habits analysis on the provided text.

        Args:
            full_text: The complete text of the document to be analyzed.

        Returns:
            A list of dictionaries, where each dictionary is a triggered habit node.
        """
        triggered_findings = []
        for node in self.nodes:
            if node["trigger_logic"](full_text):
                finding = {
                    "habit": node["habit"],
                    "name": node["name"],
                    "risk": node["risk_flag"],
                    "improvement_prompt": node["improvement_prompt"],
                    "audit_safe_default": node["audit_safe_default"]
                }
                triggered_findings.append(finding)

        return triggered_findings
