import os
import re
from typing import List, Dict

import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import pandas as pd
import yaml
import logging

from src.core.smart_chunker import sentence_window_chunker

logger = logging.getLogger(__name__)

def parse_document_content(file_path: str) -> List[Dict[str, str]]:
    """Parses the content of a document (PDF, TXT, DOCX) into text chunks.

    Args:
        file_path: The full path to the document file.

    Returns:
        A list of dictionaries, where each dictionary represents a chunk of text.
        Returns an error message in the same format if parsing fails.
    """
    logger.info(f"Parsing document: {file_path}")

    supported_extensions = ['.pdf', '.txt', '.docx']
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in supported_extensions:
        error_message = f"Error: Unsupported file type '{file_ext}'. Only PDF, TXT, and DOCX are supported."
        logger.warning(error_message)
        return [{'sentence': error_message, 'source': 'parser'}]

    try:
        chunks = []
        if file_ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        chunks.append({'sentence': text, 'source': f'{os.path.basename(file_path)} (Page {i+1})'})

        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            if text.strip():
                chunks.append({'sentence': text, 'source': os.path.basename(file_path)})

        elif file_ext == '.docx':
            doc = Document(file_path)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            if full_text.strip():
                chunks.append({'sentence': full_text, 'source': os.path.basename(file_path)})

        return chunks

    except FileNotFoundError:
        error_message = f"Error: File not found at {file_path}"
        logger.error(error_message)
        return [{'sentence': error_message, 'source': 'parser'}]
    except Exception as e:
        error_message = f"Error parsing document '{os.path.basename(file_path)}': {e}"
        logger.error(error_message, exc_info=True)
        return [{'sentence': error_message, 'source': 'parser'}]


DEFAULT_SECTION_HEADERS = [
    "Subjective", "Objective", "Assessment", "Plan",
    "History of Present Illness", "Past Medical History",
    "Medications", "Allergies", "Review of Systems",
    "Physical Examination", "Diagnosis", "Treatment Plan"
]

def load_section_headers() -> list:
    """Load section headers from config.yaml, fallback to defaults on error."""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        headers = config.get('section_headers', [])
        if headers:
            return headers
    except (FileNotFoundError, yaml.YAMLError):
        pass
    return DEFAULT_SECTION_HEADERS

def parse_document_into_sections(text: str) -> Dict[str, str]:
    """
    Parses a clinical note into sections based on headers from config.yaml or defaults.
    Uses regex to find headers followed by colons (case-insensitive).
    """
    section_headers = load_section_headers()
    if not section_headers:
        return {"full_text": text}

    pattern = r"^\s*(" + "|".join(re.escape(header) for header in section_headers) + r")\s*:"
    matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))

    if not matches:
        return {"unclassified": text}

    sections = {}
    if matches[0].start() > 0:
        pre_content = text[:matches[0].start()].strip()
        if pre_content:
            sections["Header"] = pre_content

    for i, match in enumerate(matches):
        section_header = match.group(1).strip()
        start_index = match.end()
        end_index = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_content = text[start_index:end_index].strip()
        canonical_header = next((h for h in section_headers if h.lower() == section_header.lower()), section_header)
        sections[canonical_header] = section_content

    return sections