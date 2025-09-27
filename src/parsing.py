import os
import re
from typing import List, Dict

import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import pandas as pd
import yaml

from src.core.smart_chunker import sentence_window_chunker

import logging

logger = logging.getLogger(__name__)

def parse_document_content(file_path: str) -> List[dict]:
    """
    Parses the content of a document and splits it into chunks.
    """
    logger.info(f"Parsing document: {file_path}")
    if not os.path.exists(file_path):
        return [{'sentence': f"Error: File not found at {file_path}", 'window': '', 'metadata': {'source': 'File System'}}]
    ext = os.path.splitext(file_path)[1].lower()
    logger.info(f"File extension: {ext}")

    try:
        chunks: list[dict] = []

        if ext == ".pdf":
            if not pdfplumber:
                return [{'sentence': "Error: pdfplumber not available.", 'window': '', 'metadata': {'source': 'PDF Parser'}}]
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    metadata = {'source_document': file_path, 'page': i}
                    page_chunks = sentence_window_chunker(page_text, metadata=metadata)
                    chunks.extend(page_chunks)
        elif ext == ".docx":
            try:
                docx_doc = Document(file_path)
            except Exception:
                return [{'sentence': "Error: python-docx not available.", 'window': '', 'metadata': {'source': 'DOCX Parser'}}]
            full_text = "\n".join([para.text for para in docx_doc.paragraphs])
            metadata = {'source_document': file_path}
            doc_chunks = sentence_window_chunker(full_text, metadata=metadata)
            chunks.extend(doc_chunks)
        elif ext in [".xlsx", ".xls", ".csv"]:
            try:
                if ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                    if isinstance(df, dict):
                        df = next(iter(df.values()))
                else:
                    df = pd.read_csv(file_path)
                content = df.to_string(index=False)
                metadata = {'source_document': file_path}
                data_chunks = sentence_window_chunker(content, metadata=metadata)
                chunks.extend(data_chunks)
            except Exception as e:
                return [{'sentence': f"Error: Failed to read tabular file: {e}", 'window': '', 'metadata': {'source': 'Data Parser'}}]
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            if not Image or not pytesseract:
                return [{'sentence': "Error: OCR dependencies not available.", 'window': '', 'metadata': {'source': 'OCR Parser'}}]
            try:
                img = Image.open(file_path)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                txt = pytesseract.image_to_string(img)
                metadata = {'source_document': file_path}
                ocr_chunks = sentence_window_chunker(txt or "", metadata=metadata)
                chunks.extend(ocr_chunks)
            except Image.UnidentifiedImageError as e:
                return [{'sentence': f"Error: Unidentified image: {e}", 'window': '', 'metadata': {'source': 'OCR Parser'}}]
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                txt = f.read()
            metadata = {'source_document': file_path}
            txt_chunks = sentence_window_chunker(txt, metadata=metadata)
            chunks.extend(txt_chunks)
        else:
            return [{'sentence': f"Error: Unsupported file type: {ext}", 'window': '', 'metadata': {'source': 'File Handler'}}]

        return chunks if chunks else [{'sentence': "Info: No text could be extracted from the document.", 'window': '', 'metadata': {'source': 'System'}}]

    except Exception as e:
        return [{'sentence': f"Error: An unexpected error occurred: {e}", 'window': '', 'metadata': {'source': 'System'}}]

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

parse_document_into_sections = parse_text_into_sections