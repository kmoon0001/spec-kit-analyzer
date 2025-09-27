import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """A service for generating compliance analysis for a given document."""

    def __init__(self, config: Dict[str, Any]):
        """Initializes the DocumentAnalysisService with a configuration."""
        self.config = config

    def generate_analysis(
        self, document: str, entity_list: str, retrieved_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generates a compliance analysis for a given document."""
        prompt = self._build_prompt(
            document, entity_list, self._format_rules_for_prompt(retrieved_rules)
        )
        raw_analysis = self._generate_analysis_from_prompt(prompt)
        return self._parse_json_output(raw_analysis)

    def _build_prompt(self, document: str, entity_list: str, context: str) -> str:
        """Builds the prompt for the LLM."""
        if self.config.get("reviewer_difficulty") == "strict":
            difficulty_instruction = "Your analysis should be strict and identify even minor potential compliance risks."
        else:
            difficulty_instruction = "Your analysis should be moderate and focus on significant compliance risks."

        return f"""
You are an expert Medicare compliance officer for a Skilled Nursing Facility (SNF). Your task is to analyze a clinical therapy document for potential compliance risks based on the provided Medicare guidelines.

{difficulty_instruction}

**Clinical Document:**
---
{document}
---

**Extracted Clinical Entities:**
---
{entity_list}
---

**Relevant Medicare Guidelines:**
---
{context}
---

**Your Task:**
Based on all the information above, provide a detailed compliance analysis. Identify any potential risks, explain why they are risks according to the retrieved rules, and suggest specific actions to mitigate them. If no risks are found, state that the document appears to be compliant.

**Output Format:**
Return the analysis as a JSON object with the following structure:
{{
  "findings": [
    {{
      "text": "<original text from document that contains the finding>",
      "risk": "<description of the compliance risk based on retrieved rules>",
      "suggestion": "<suggestion to mitigate the risk>"
    }}
  ]
}}

**Compliance Analysis:**
"""

    @staticmethod
    def _format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
        """Formats retrieved rules for inclusion in the prompt."""
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."

        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {rule.get('issue_title', '')}\\n"
                f"  **Detail:** {rule.get('issue_detail', '')}\\n"
                f"  **Suggestion:** {rule.get('suggestion', '')}"
            )
        return "\\n".join(formatted_rules)

    @staticmethod
    def _generate_analysis_from_prompt(prompt: str) -> str:
        """Placeholder for the actual LLM call."""
        logger.info("Generating analysis with prompt:\\n%s", prompt)
        # In a real implementation, this would call the LLM
        return """
{
    "findings": [
        {
            "text": "Sample finding text",
            "risk": "Sample risk description",
            "suggestion": "Sample suggestion for mitigation"
        }
    ]
}
"""

    @staticmethod
    def _parse_json_output(result: str) -> dict:
        """Parses JSON output from the model with robust error handling."""
        try:
            json_start = result.find("```json")
            if json_start != -1:
                json_str = result[json_start + 7 :].strip()
                json_end = json_str.rfind("```")
                if json_end != -1:
                    json_str = json_str[:json_end].strip()
            else:
                json_start = result.find("{")
                json_end = result.rfind("}") + 1
                json_str = result[json_start:json_end]

            analysis = json.loads(json_str)
            return analysis

        except (json.JSONDecodeError, IndexError, ValueError) as e:
            logger.error(
                f"Error parsing JSON output: {e}\\nRaw model output:\\n{result}"
            )
            analysis = {"error": "Failed to parse JSON output from model."}
            return analysis
