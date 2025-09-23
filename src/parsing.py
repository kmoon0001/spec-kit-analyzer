import os
from typing import List, Tuple

import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import pandas as pd

# This helper function is borrowed from main_window.py to replace the
# missing RecursiveCharacterTextSplitter.
def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """A simple text chunker."""
    if not isinstance(text, str) or not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        # Try to split at a newline for cleaner breaks
        newline_pos = text.rfind("\n", start, end)
        if newline_pos != -1 and newline_pos > start + (max_chars // 4):
            end = newline_pos
        chunks.append(text[start:end])
        start = end
    return chunks

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
