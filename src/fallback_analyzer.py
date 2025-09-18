# Python
from __future__ import annotations

import re
from typing import List, Dict, Any

# The 14 nodes provided by the user, structured for the analyzer.
FALLBACK_LOGIC_NODES: List[Dict[str, Any]] = [
    {
        "id": "skilled_need_unjustified",
        "name": "Skilled Need Not Justified",
        "trigger_keywords": [],
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["mbs", "moca", "objective data", "clinical data", "anticipated decline"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Skilled need unclear”",
        "audit_safe_default": "Therapist to clarify skilled need using clinical data or anticipated decline",
        "improvement_prompt": "Add MBS results, cognitive scores, or functional risk if untreated"
    },
    {
        "id": "frequency_exceeds_norms",
        "name": "Frequency Exceeds Norms",
        "trigger_keywords": ["daily"],
        "trigger_logic": lambda text: "daily" in text.lower() and not any(k in text.lower() for k in ["rationale", "justify", "aspiration risk", "decline"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Frequency exceeds norms”",
        "audit_safe_default": "Frequency may be appropriate if aspiration risk or rapid decline is present",
        "improvement_prompt": "Add justification for frequency—e.g., aspiration risk, caregiver training need"
    },
    {
        "id": "safety_not_documented",
        "name": "Safety Not Documented",
        "trigger_keywords": [],
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["supervision", "precaution", "adjustment", "safety"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Safety not addressed”",
        "audit_safe_default": "Therapist to document supervision level and safety precautions",
        "improvement_prompt": "Include aspiration risk mitigation, therapist adjustments, and supervision level"
    },
    {
        "id": "functional_goals_missing",
        "name": "Functional Goals Missing",
        "trigger_keywords": ["goal"],
        "trigger_logic": lambda text: "goal" in text.lower() and not any(k in text.lower() for k in ["functional", "smart", "measurable"]),
        "risk_flag": "🟠 Moderate",
        "fallback_action": "Flag “Goals not functional”",
        "audit_safe_default": "Therapist to revise goals to reflect measurable functional outcomes",
        "improvement_prompt": "Use SMART goals tied to PO intake, medication memory, or ADL participation"
    },
    {
        "id": "therapist_qualification_not_documented",
        "name": "Therapist Qualification Not Documented",
        "trigger_keywords": [],
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["credentials", "licensure", "cbis", "mbsimp"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Therapist role unclear”",
        "audit_safe_default": "Therapist to document licensure and clinical interpretation",
        "improvement_prompt": "Add CBIS/MBSImP credentials and CEU-informed clinical decisions"
    },
    {
        "id": "severity_not_supported",
        "name": "Severity Not Supported",
        "trigger_keywords": [],
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["fois", "slums", "severity scale"]),
        "risk_flag": "🟠 Moderate",
        "fallback_action": "Flag “Severity not documented”",
        "audit_safe_default": "Therapist to include severity scale or patient-centered goal",
        "improvement_prompt": "Use FOIS, SLUMS, or shared decision-making notes"
    },
    {
        "id": "plan_of_care_not_referenced",
        "name": "Plan of Care Not Referenced",
        "trigger_keywords": [],
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["plan of care", "poc", "physician-certified"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Plan of care not referenced”",
        "audit_safe_default": "Therapist to confirm alignment with certified plan",
        "improvement_prompt": "Reference physician orders and plan goals in documentation"
    },
    {
        "id": "progress_not_measured",
        "name": "Progress Not Measured",
        "trigger_keywords": ["progress"],
        "trigger_logic": lambda text: "progress" in text.lower() and not any(k in text.lower() for k in ["measurable change", "response"]),
        "risk_flag": "🟠 Moderate",
        "fallback_action": "Flag “Progress unclear”",
        "audit_safe_default": "Therapist to document patient response and progress toward goals",
        "improvement_prompt": "Include measurable change in function, tolerance, or independence"
    },
    {
        "id": "maintenance_vs_skilled_ambiguity",
        "name": "Maintenance vs Skilled Ambiguity",
        "trigger_keywords": ["routine", "maintenance"],
        "trigger_logic": lambda text: any(k in text.lower() for k in ["routine", "maintenance"]) and not any(k in text.lower() for k in ["skilled", "analysis", "adjustments"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Skilled intervention not evident”",
        "audit_safe_default": "Therapist to clarify skilled oversight and clinical reasoning",
        "improvement_prompt": "Avoid routine phrasing—document skilled analysis and adjustments"
    },
    {
        "id": "interdisciplinary_input_missing",
        "name": "Interdisciplinary Input Missing",
        "trigger_keywords": [],
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["nursing", "pt", "ot", "caregiver", "team", "collaboration"]),
        "risk_flag": "🟠 Moderate",
        "fallback_action": "Flag “Team input missing”",
        "audit_safe_default": "Therapist to document interdisciplinary coordination",
        "improvement_prompt": "Include nursing feedback, PT goals, or caregiver training notes"
    },
    {
        "id": "discharge_planning_absent",
        "name": "Discharge Planning Absent",
        "trigger_keywords": [],
        "trigger_logic": lambda text: not any(k in text.lower() for k in ["discharge", "transition plan"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Discharge planning not addressed”",
        "audit_safe_default": "Therapist to outline criteria for discharge or transition",
        "improvement_prompt": "Add discharge goals, caregiver readiness, or transition barriers"
    },
    {
        "id": "documentation_timing_risk",
        "name": "Documentation Timing Risk",
        "trigger_keywords": ["late", "missing note"],
        "trigger_logic": lambda text: any(k in text.lower() for k in ["late", "missing note"]),
        "risk_flag": "🟠 Moderate",
        "fallback_action": "Flag “Documentation timing risk”",
        "audit_safe_default": "Therapist to confirm timely entry per CMS standards",
        "improvement_prompt": "Ensure notes are entered same day or within 24 hours per policy"
    },
    {
        "id": "skilled_nursing_criteria_not_met",
        "name": "Skilled Nursing Criteria Not Met (Chapter 8 §30.3)",
        "trigger_keywords": [],
        "trigger_logic": lambda text: "nursing" in text.lower() and not any(k in text.lower() for k in ["complexity", "rn", "lpn", "iv care", "wound", "tube feeding"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Nursing skill not justified”",
        "audit_safe_default": "Therapist to document complexity requiring skilled nursing",
        "improvement_prompt": "Include IV care, wound staging, or tube feeding complexity"
    },
    {
        "id": "skilled_therapy_criteria_not_met",
        "name": "Skilled Therapy Criteria Not Met (Chapter 8 §30.4)",
        "trigger_keywords": ["therapy"],
        "trigger_logic": lambda text: "therapy" in text.lower() and not any(k in text.lower() for k in ["skilled technique", "clinical reasoning", "therapist expertise"]),
        "risk_flag": "🔴 High",
        "fallback_action": "Flag “Therapy skill not justified”",
        "audit_safe_default": "Therapist to document skilled techniques and clinical reasoning",
        "improvement_prompt": "Specify skilled interventions and why they require therapist expertise"
    }
]


class FallbackAnalyzer:
    """
    Analyzes document text against a set of fallback logic nodes to identify
    documentation risks and provide actionable feedback.
    """

    def __init__(self):
        self.nodes = FALLBACK_LOGIC_NODES

    def analyze_text(self, full_text: str) -> List[Dict[str, Any]]:
        """
        Runs the analysis on the provided text and returns a list of triggered findings.

        Args:
            full_text: The complete text of the document to be analyzed.

        Returns:
            A list of dictionaries, where each dictionary is a triggered node
            containing the finding's details.
        """
        triggered_findings = []
        for node in self.nodes:
            # The trigger logic is a lambda function that checks for the condition
            if node["trigger_logic"](full_text):
                finding = {
                    "name": node["name"],
                    "risk": node["risk_flag"],
                    "fallback_action": node["fallback_action"],
                    "audit_safe_default": node["audit_safe_default"],
                    "improvement_prompt": node["improvement_prompt"]
                }
                triggered_findings.append(finding)

        return triggered_findings
