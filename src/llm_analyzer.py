# src/llm_analyzer.py
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def run_llm_analysis(llm, chunks: List[str], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs compliance analysis on text chunks using an LLM.

    Args:
        llm: An initialized llama_cpp.Llama instance.
        chunks: A list of text chunks from the document.
        rules: A list of compliance rules (as dictionaries).

    Returns:
        A list of dictionaries, where each dictionary represents a detected compliance issue.
    """
    logger.info(f"Starting LLM-based compliance analysis on {len(chunks)} chunks against {len(rules)} rules.")
    all_issues = []

    for rule in rules:
        for chunk in chunks:
            prompt = f"""
You are an expert compliance auditor for clinical documentation. Your task is to determine if a given text snippet violates a specific compliance rule.
Provide your answer in a strict JSON format.

**Compliance Rule:**
- **Title:** "{rule['issue_title']}"
- **Detail:** "{rule['issue_detail']}"
- **Category:** "{rule['issue_category']}"

**Text Snippet to Analyze:**
"{chunk}"

**Your Task:**
Carefully analyze the text snippet based on the compliance rule. Respond with a JSON object containing ONLY the following keys:
- "violates_rule": boolean (true if the snippet violates the rule, false otherwise)
- "confidence": float (your confidence in the decision, from 0.0 to 1.0)
- "reasoning": string (a brief, one-sentence explanation for your decision)

**Your JSON Response:**
"""
            try:
                response = llm(
                    prompt,
                    max_tokens=256,
                    temperature=0.1,
                    top_p=0.9,
                    stop=["}"],
                    echo=False,
                )
                response_text = response["choices"][0]["text"].strip() + "}"
                json_match = response_text[response_text.find('{'):response_text.rfind('}')+1]
                result = json.loads(json_match)

                if result.get("violates_rule") is True:
                    # Add rule and chunk info for context
                    issue = {**result, **rule, "evidence_chunk": chunk}
                    all_issues.append(issue)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"Failed to parse LLM response for rule '{rule['issue_title']}'. Response: '{response_text}'. Error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during LLM analysis for rule '{rule['issue_title']}': {e}")

    logger.info(f"LLM analysis complete. Found {len(all_issues)} potential issues.")

    # Format the output to match the structure expected by the rest of the application
    formatted_issues = []
    for issue in all_issues:
        formatted_issues.append({
            "severity": issue['severity'],
            "title": issue['issue_title'],
            "detail": issue['issue_detail'],
            "category": issue['issue_category'],
            "confidence": issue.get('confidence', 0.5),
            "reasoning": issue.get('reasoning', 'No reasoning provided.'),
            "citations": [(issue['evidence_chunk'], "Document Text")]
        })

    return formatted_issues
