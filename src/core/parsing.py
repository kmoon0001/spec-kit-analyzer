import logging
import os
import re
from typing import Dict, List

import pdfplumber
import yaml
from docx import Document


logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def parse_document_content(file_path: str) -> List[Dict[str, str]]:
    """Parse supported documents into sentence chunks."""
    extension = os.path.splitext(file_path)[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return [
            {
                "sentence": f"Error: Unsupported file type '{extension}'. Only PDF, TXT, and DOCX are supported.",
                "source": "parser",
            }
        ]

    file_exists = os.path.exists(file_path)
    if extension in {".txt", ".docx"} and not file_exists:
        return [
            {
                "sentence": f"Error: File not found at {file_path}",
                "source": "parser",
            }
        ]

    try:
        if extension == ".pdf":
            return _parse_pdf(file_path)
        if extension == ".txt":
            return _parse_txt(file_path)
        if extension == ".docx":
            return _parse_docx(file_path)
    except FileNotFoundError:
        return [
            {
                "sentence": f"Error: File not found at {file_path}",
                "source": "parser",
            }
        ]
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to parse %s", file_path)
        return [
            {
                "sentence": f"Error parsing document '{os.path.basename(file_path)}': {exc}",
                "source": "parser",
            }
        ]

    return []


def _parse_pdf(file_path: str) -> List[Dict[str, str]]:
    chunks: List[Dict[str, str]] = []
    with pdfplumber.open(file_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(
                    {
                        "sentence": text,
                        "source": f"{os.path.basename(file_path)} (Page {index})",
                    }
                )
    return chunks


def _parse_txt(file_path: str) -> List[Dict[str, str]]:
    with open(file_path, "r", encoding="utf-8") as handle:
        text = handle.read().strip()
    return [{"sentence": text, "source": os.path.basename(file_path)}] if text else []


def _parse_docx(file_path: str) -> List[Dict[str, str]]:
    document = Document(file_path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    return [{"sentence": text, "source": os.path.basename(file_path)}] if text else []


DEFAULT_SECTION_HEADERS = [
    "Subjective",
    "Objective",
    "Assessment",
    "Plan",
    "History of Present Illness",
    "Past Medical History",
    "Medications",
    "Allergies",
    "Review of Systems",
    "Physical Examination",
    "Diagnosis",
    "Treatment Plan",
]


def load_section_headers() -> List[str]:
    try:
        with open("config.yaml", "r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return DEFAULT_SECTION_HEADERS

    headers = config.get("section_headers") or []
    return headers or DEFAULT_SECTION_HEADERS


def parse_document_into_sections(text: str) -> Dict[str, str]:
    headers = load_section_headers()
    if not headers:
        return {"full_text": text}

    pattern = r"^\s*(" + "|".join(re.escape(header) for header in headers) + r")\s*:"
    matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))

    if not matches:
        return {"unclassified": text}

    sections: Dict[str, str] = {}
    if matches[0].start() > 0:
        intro = text[: matches[0].start()].strip()
        if intro:
            sections["Header"] = intro

    for index, match in enumerate(matches):
        header = match.group(1)
        next_start = (
            matches[index + 1].start() if index + 1 < len(matches) else len(text)
        )
        content = text[match.end() : next_start].strip()
        normalized_header = next(
            (item for item in headers if item.lower() == header.lower()), header
        )
        sections[normalized_header] = content

    return sections
