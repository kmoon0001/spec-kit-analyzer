158

159     return analysis
160
161 def _transform_query(self, query: str) -> str:
162     return query
163
164 def _format_rules_for_prompt(self, rules: list) -> str:
165     if not rules:
166         return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
167     formatted_rules = []
168     for rule in rules:
169         formatted_rules.append(
170             f"- **Rule:** {getattr(rule, 'issue_title', '')}\n"
171             f"  **Detail:** {getattr(rule, 'issue_detail', '')}\n"
172             f"  **Suggestion:** {getattr(rule, 'suggestion', '')}"
173         )
174     return "\n".join(formatted_rules)
175
176 def _build_prompt(self, document: str, entity_list: str, context: str) -> str:
177     """
178     Builds the prompt for the LLM.
179     """
180     return f"""
You are an expert Medicare compliance officer for a Skilled Nursing Facility (SNF). Your task is to analyze a clinical therapy document for potential compliance risks based on the provided Medicare guidelines.

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

 def _parse_json_output(self, result: str) -> dict:
     """
     Parses JSON output from the model with robust error handling.
     """
     try:
         # First try to find JSON wrapped in code blocks
         json_start = result.find('```json')
         if json_start != -1:
             json_str = result[json_start + 7:].strip()
             json_end = json_str.rfind('```')
             if json_end != -1:
                 json_str = json_str[:json_end].strip()
         else:
             # Fall back to finding raw JSON braces
             json_start = result.find('{')
             json_end = result.rfind('}') + 1
             json_str = result[json_start:json_end]
         
         analysis = json.loads(json_str)
         return analysis
         
     except (json.JSONDecodeError, IndexError, ValueError) as e:
         logger.error(f"Error parsing JSON output: {e}\nRaw model output:\n{result}")
         analysis = {"error": "Failed to parse JSON output from model."}
         return analysis