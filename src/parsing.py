import os
import re
from typing import List, Tuple, Dict

import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import pandas as pd

from src.utils import chunk_text

def parse_document_content(file_path: str) -> List[Tuple[str, str]]:
    """
    Parses the content of a document and splits it into chunks.
    """
    if not os.path.exists(file_path):
        return [(f"Error: File not found at {file_path}", "File System")]
    ext = os.path.splitext(file_path)[1].lower()

    try:
        chunks_with_source: list[tuple[str, str]] = []

        # --- Step 1: Extract text from the document based on its type ---
        if ext == ".pdf":
            if not pdfplumber:
                return [("Error: pdfplumber not available.", "PDF Parser")]
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    page_chunks = chunk_text(page_text)
                    for chunk in page_chunks:
                        chunks_with_source.append((chunk, f"Page {i}"))
        elif ext == ".docx":
            try:
                from docx import Document
            except Exception:
                return [("Error: python-docx not available.", "DOCX Parser")]
            docx_doc = Document(file_path)
            full_text = "\n".join([para.text for para in docx_doc.paragraphs])
            doc_chunks = chunk_text(full_text)
            for chunk in doc_chunks:
                chunks_with_source.append((chunk, "DOCX Document"))
        elif ext in [".xlsx", ".xls", ".csv"]:
            try:
                if ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                    if isinstance(df, dict):
                        df = next(iter(df.values()))
                else:
                    df = pd.read_csv(file_path)
                content = df.to_string(index=False)
                data_chunks = chunk_text(content)
                for chunk in data_chunks:
                    chunks_with_source.append((chunk, "Table"))
            except Exception as e:
                return [(f"Error: Failed to read tabular file: {e}", "Data Parser")]
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            if not Image or not pytesseract:
                return [("Error: OCR dependencies not available.", "OCR Parser")]
            try:
                img = Image.open(file_path)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                txt = pytesseract.image_to_string(img)
                ocr_chunks = chunk_text(txt or "")
                for chunk in ocr_chunks:
                    chunks_with_source.append((chunk, "Image (OCR)"))
            except Image.UnidentifiedImageError as e:
                return [(f"Error: Unidentified image: {e}", "OCR Parser")]
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                txt = f.read()
            txt_chunks = chunk_text(txt)
            for chunk in txt_chunks:
                chunks_with_source.append((chunk, "Text File"))
        else:
            return [(f"Error: Unsupported file type: {ext}", "File Handler")]

        return chunks_with_source if chunks_with_source else [("Info: No text could be extracted from the document.", "System")]

    except FileNotFoundError:
        return [(f"Error: File not found at {file_path}", "File System")]
    except Exception as e:
        return [(f"Error: An unexpected error occurred: {e}", "System")]

import yaml
import re
from typing import Dict

# Default headers if config is missing or invalid
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

def parse_text_into_sections(text: str) -> Dict[str, str]:
    """
    Parses a clinical note into sections based on headers from config.yaml or defaults.
    Uses regex to find headers followed by colons (case-insensitive).
    """
    section_headers = load_section_headers()
    if not section_headers:
        return {"full_text": text}

    # Assemble regex pattern for section headers
    pattern = r"^\s*(" + "|".join(re.escape(header) for header in section_headers) + r")\s*:"
    matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))

    if not matches:
        return {"unclassified": text}

    sections = {}
    # Find text before first header for completeness
    if matches[0].start() > 0:
        pre_content = text[:matches[0].start()].strip()
        if pre_content:
            sections["Header"] = pre_content

    # Iterate through matches to extract content
    for i, match in enumerate(matches):
        section_header = match.group(1).strip()
        start_index = match.end()
        end_index = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_content = text[start_index:end_index].strip()
        canonical_header = next((h for h in section_headers if h.lower() == section_header.lower()), section_header)
        sections[canonical_header] = section_content

    return sections

# For compatibility: expose both parse_text_into_sections and parse_document_into_sections
parse_document_into_sections = parse_text_into_sections
