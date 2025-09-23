import os
from typing import List, Tuple

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

def parse_text_into_sections(text: str) -> dict:
    """
    Parses a clinical note into sections based on headers defined in config.yaml.
    """
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        section_headers = config.get('section_headers', [])
    except (FileNotFoundError, yaml.YAMLError):
        # Fallback to a default list if config is missing or invalid
        section_headers = ['Subjective', 'Objective', 'Assessment', 'Plan']

    if not section_headers:
        return {"full_text": text}

    # Create a regex pattern from the headers
    # This pattern looks for a header followed by a colon, optional whitespace, and then captures the text
    pattern = r'(' + '|'.join(section_headers) + r'):'

    # Split the text by the headers
    parts = re.split(pattern, text, flags=re.IGNORECASE)

    sections = {}
    current_header = "Header" # Default for text before the first header

    # The first part is the text before any headers
    if parts[0].strip():
        sections[current_header] = parts[0].strip()

    # Process the rest of the parts
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i+1].strip() if (i+1) < len(parts) else ""

        # Find the canonical header name (maintaining original case)
        canonical_header = next((h for h in section_headers if h.lower() == header.lower()), header)
        sections[canonical_header] = content

    return sections
