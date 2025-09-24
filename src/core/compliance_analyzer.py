import os
import json
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from .hybrid_retriever import HybridRetriever
from .phi_scrubber import scrub_phi

logger = logging.getLogger(__name__)

class ComplianceAnalyzer:
    def __init__(self, generator_model_name="nabilfaieaz/tinyllama-med-full"):
        """
        Initializes the ComplianceAnalyzer.
        """
        logger.info("Initializing ComplianceAnalyzer...")
        self.retriever = HybridRetriever()

        logger.info(f"Loading generator LLM '{generator_model_name}'...")
        self.generator_tokenizer = AutoTokenizer.from_pretrained(generator_model_name, revision="f9e026b")
        self.generator_model = AutoModelForCausalLM.from_pretrained(
            generator_model_name,
            revision="f9e026b",
            load_in_4bit=True,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        logger.info(f"Generator LLM '{generator_model_name}' loaded successfully.")

    def analyze_document(self, document_text: str, discipline: str, analysis_mode: str) -> dict:
        """
        Analyzes a document for compliance.
        """
        # This is a placeholder implementation.
        # The original implementation was likely more complex.
        return {"findings": []}

    def _transform_query(self, query: str) -> str:
        return query

    def _format_rules_for_prompt(self, rules: list) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {getattr(rule, 'issue_title', '')}\n"
                f"  **Detail:** {getattr(rule, 'issue_detail', '')}\n"
                f"  **Suggestion:** {getattr(rule, 'suggestion', '')}"
            )
        return "\n".join(formatted_rules)

    def _build_prompt(self, document: str, entity_list: str, context: str) -> str:
        """
        Builds the prompt for the LLM.
        """
        return f"""
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
            logger.error(f"Error parsing JSON output: {e}\\nRaw model output:\\n{result}")
            analysis = {"error": "Failed to parse JSON output from model."}
            return analysis