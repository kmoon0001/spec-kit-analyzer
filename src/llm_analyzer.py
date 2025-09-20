# src/llm_analyzer.py
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


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
    logger.info(f"Starting simplified LLM-based compliance analysis on {len(chunks)} chunks against {len(rules)} rules.")
    all_issues = []

    for rule in rules:
        for chunk in chunks:
            prompt = f"""You are a compliance auditor. Does the following text violate the rule provided?
Answer with only "yes" or "no".

Rule: {rule['issue_title']}: {rule['issue_detail']}
Text: "{chunk}"

Answer: """
            try:
                response = llm(
                    prompt,
                    max_tokens=3,
                    temperature=0.0,
                    top_p=0.9,
                    echo=False,
                )
                answer = response["choices"][0]["text"].strip().lower()

                if "yes" in answer:
                    issue = {**rule, "evidence_chunk": chunk}
                    all_issues.append(issue)

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
            "confidence": 0.9,  # High confidence for this simplified approach
            "reasoning": "Violation detected by simplified LLM check.",
            "citations": [(issue.get("evidence_chunk", ""), "Document Text")]
        })

    return formatted_issues
