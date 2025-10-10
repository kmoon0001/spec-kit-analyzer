def get_habit_for_finding(finding: dict) -> dict:
    """Maps a compliance finding to one of the 7 Habits and provides an explanation.

    This is a simplified rule-based mapper. A more advanced version could use
    the AI to generate this mapping dynamically.
    """
    issue_title = finding.get("issue_title", "").lower()

    if "signature" in issue_title or "timely" in issue_title or "date" in issue_title:
        return {
            "name": "Habit 3: Put First Things First",
            "explanation": "This finding relates to prioritizing and executing on critical, time-sensitive tasks. Ensure all documentation is signed and dated promptly.",
        }
    if "goal" in issue_title or "plan of care" in issue_title:
        return {
            "name": "Habit 2: Begin with the End in Mind",
            "explanation": "This finding relates to having a clear vision. Ensure all goals are patient-centered, functional, and clearly defined in the initial plan of care.",
        }
    if "skilled" in issue_title or "medical necessity" in issue_title or "justify" in issue_title:
        return {
            "name": "Habit 5: Seek First to Understand, Then to Be Understood",
            "explanation": "This finding relates to clear communication. First, understand the patient's unique needs, then document them in a way that makes the medical necessity of your skilled service clear to an external reviewer.",
        }
    if "collaboration" in issue_title or "interdisciplinary" in issue_title or "billing" in issue_title:
        return {
            "name": "Habit 6: Synergize",
            "explanation": "This finding relates to creative cooperation. Ensure that documentation and communication between therapy, nursing, and billing are aligned to prevent errors.",
        }
    return {
        "name": "Habit 1: Be Proactive",
        "explanation": "This finding highlights an opportunity to take initiative. Proactively reviewing your documentation for completeness and accuracy can prevent most common compliance issues.",
    }
