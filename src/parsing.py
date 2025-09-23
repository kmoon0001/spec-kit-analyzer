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


# A simple list of section headers that are commonly found in clinical notes.
SECTION_HEADERS = [
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

def parse_document_into_sections(document_text: str) -> Dict[str, str]:
    """
    Parses a document into sections based on a predefined list of headers.

    This is a simple implementation that uses regular expressions to find section
    headers. It assumes that a section starts with a header and ends at the
    next header.

    :param document_text: The text of the document to parse.
    :return: A dictionary where keys are section headers and values are the
             content of the sections.
    """
    sections = {}
    # Create a regex pattern to find any of the section headers at the start of a line.
    # The `re.IGNORECASE` flag makes the matching case-insensitive.
    pattern = r"^\s*(" + "|".join(re.escape(header) for header in SECTION_HEADERS) + r")\s*:"

    # Find all matches of the pattern in the document.
    matches = list(re.finditer(pattern, document_text, re.MULTILINE | re.IGNORECASE))

    if not matches:
        # If no headers are found, return the entire document as an "unclassified" section.
        return {"unclassified": document_text}

    # Iterate through the matches to extract the content of each section.
    for i, match in enumerate(matches):
        section_header = match.group(1).strip()
        start_index = match.end()

        # The end index of the section is the start index of the next section,
        # or the end of the document if it's the last section.
        end_index = matches[i + 1].start() if i + 1 < len(matches) else len(document_text)

        section_content = document_text[start_index:end_index].strip()
        sections[section_header] = section_content

    return sections
