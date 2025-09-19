# src/llm_analyzer.py
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def _verify_issue_with_llm(llm, chunk: str, rule: Dict[str, Any], reasoning: str) -> Dict[str, Any]:
    """
    Uses the LLM to verify a potential compliance issue.
    """
    prompt = f"""
You are a meticulous fact-checker. Your task is to verify if a previously identified compliance issue is factually correct based on the provided text.

**Original Finding:**
- **Rule Violated:** "{rule['issue_title']}"
- **Initial Reasoning:** "{reasoning}"

**Text Snippet to Verify Against:**
"{chunk}"

**Your Task:**
1.  Carefully re-read the "Text Snippet".
2.  Determine if the "Original Finding" is a valid and accurate assessment of the text.
3.  Respond with a JSON object containing ONLY the following keys:
    - "is_violation_confirmed": boolean (true if the violation is definitely present, false otherwise)
    - "supporting_quote": string (if true, provide the *exact* quote from the text that proves the violation. If false, provide a brief explanation for why it's not a violation.)

**Your JSON Response:**
"""
    try:
        response = llm(
            prompt,
            max_tokens=256,
            temperature=0.0,  # Be deterministic for fact-checking
            top_p=0.9,
            stop=["}"],
            echo=False,
        )
        response_text = response["choices"][0]["text"].strip() + "}"
        json_match = response_text[response_text.find('{'):response_text.rfind('}')+1]
        return json.loads(json_match)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f"Failed to parse verification LLM response for rule '{rule['issue_title']}'. Response: '{response_text}'. Error: {e}")
        return {"is_violation_confirmed": False, "supporting_quote": "Error during verification."}
    except Exception as e:
        logger.error(f"An unexpected error occurred during verification for rule '{rule['issue_title']}': {e}")
        return {"is_violation_confirmed": False, "supporting_quote": "Unexpected error during verification."}


def run_llm_analysis(llm, chunks: List[str], rules: List[Dict[str, Any]], file_path: str) -> List[Dict[str, Any]]:
    """
    Runs compliance analysis on text chunks using an LLM.

    Args:
        llm: An initialized llama_cpp.Llama instance.
        chunks: A list of text chunks from the document.
        rules: A list of compliance rules (as dictionaries).
        file_path: The path to the file being analyzed.

    Returns:
        A list of dictionaries, where each dictionary represents a detected compliance issue.
    """
    logger.info(f"Starting LLM-based compliance analysis on {len(chunks)} chunks against {len(rules)} rules.")
    all_issues = []

    analysis_date = datetime.now().strftime("%Y-%m-%d")
    file_name = os.path.basename(file_path)

    for rule in rules:
        for chunk in chunks:
            prompt = f"""
You are an expert compliance auditor for clinical documentation. Your task is to determine if a given text snippet violates a specific compliance rule.
Provide your answer in a strict JSON format.

**Document Metadata:**
- **Analysis Date:** "{analysis_date}"
- **Source Filename:** "{file_name}"

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
                    # Verify the finding with a second pass
                    verification_result = _verify_issue_with_llm(llm, chunk, rule, result.get("reasoning", ""))
                    if verification_result.get("is_violation_confirmed"):
                        # Add rule and chunk info for context
                        issue = {**result, **rule, "evidence_chunk": chunk, "supporting_quote": verification_result.get("supporting_quote")}
                        all_issues.append(issue)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"Failed to parse LLM response for rule '{rule['issue_title']}'. Response: '{response_text}'. Error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during LLM analysis for rule '{rule['issue_title']}': {e}")

    logger.info(f"LLM analysis complete. Found {len(all_issues)} potential issues.")

    # Format the output to match the structure expected by the rest of the application
    formatted_issues = []
    for issue in all_issues:
        # Use the more specific supporting quote if available, otherwise fall back to the whole chunk.
        citation_text = issue.get("supporting_quote") or issue.get("evidence_chunk", "")
        formatted_issues.append({
            "severity": issue['severity'],
            "title": issue['issue_title'],
            "detail": issue['issue_detail'],
            "category": issue['issue_category'],
            "confidence": issue.get('confidence', 0.5),
            "reasoning": issue.get('reasoning', 'No reasoning provided.'),
            "citations": [(citation_text, "Document Text")]
        })

    return formatted_issues
