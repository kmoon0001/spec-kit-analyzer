import os
import re
from typing import List, Tuple

import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import pandas as pd
import spacy

from src.text_chunking import RecursiveCharacterTextSplitter

# --- SpaCy Model Loading ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    nlp = None

def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    if not nlp:
        return [text]
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

def parse_document_content(file_path: str) -> List[Tuple[str, str]]:
    """
    Parses the content of a document and splits it into chunks.
    Uses a recursive character text splitter for more effective chunking.
    """
    if not os.path.exists(file_path):
        return [(f"Error: File not found at {file_path}", "File System")]
    ext = os.path.splitext(file_path)[1].lower()

    # Initialize the text splitter with configurable settings
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    try:
        chunks_with_source: list[tuple[str, str]] = []
        full_text = ""

        # --- Step 1: Extract text from the document based on its type ---
        if ext == ".pdf":
            if not pdfplumber:
                return [("Error: pdfplumber not available.", "PDF Parser")]
            with pdfplumber.open(file_path) as pdf:
                # Process page by page to maintain source information
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    page_chunks = text_splitter.split_text(page_text)
                    for chunk in page_chunks:
                        if chunk:
                            chunks_with_source.append((chunk, f"Page {i}"))
        elif ext == ".docx":
            try:
                from docx import Document
            except Exception:
                return [("Error: python-docx not available.", "DOCX Parser")]
            docx_doc = Document(file_path)
            # Process paragraph by paragraph
            for i, para in enumerate(docx_doc.paragraphs, start=1):
                if not para.text.strip():
                    continue
                para_chunks = text_splitter.split_text(para.text)
                for chunk in para_chunks:
                    if chunk:
                        chunks_with_source.append((chunk, f"Paragraph {i}"))
        elif ext in [".xlsx", ".xls", ".csv"]:
            try:
                if ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                    if isinstance(df, dict):
                        df = next(iter(df.values()))
                else:
                    df = pd.read_csv(file_path)
                content = df.to_string(index=False)
                data_chunks = text_splitter.split_text(content)
                for chunk in data_chunks:
                    if chunk:
                        chunks_with_source.append((chunk, "Table"))
            except Exception as e:
                return [(f"Error: Failed to read tabular file: {e}",
                         "Data Parser")]
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            if not Image or not pytesseract:
                return [("Error: OCR dependencies not available.",
                         "OCR Parser")]
            try:
                img = Image.open(file_path)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                txt = pytesseract.image_to_string(img)
                ocr_chunks = text_splitter.split_text(txt or "")
                for chunk in ocr_chunks:
                    if chunk:
                        chunks_with_source.append((chunk, "Image (OCR)"))
            except Image.UnidentifiedImageError as e:
                return [(f"Error: Unidentified image: {e}", "OCR Parser")]
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                txt = f.read()
            txt_chunks = text_splitter.split_text(txt)
            for chunk in txt_chunks:
                if chunk:
                    chunks_with_source.append((chunk, "Text File"))
        else:
            return [(f"Error: Unsupported file type: {ext}", "File Handler")]

        return chunks_with_source if chunks_with_source else [
            ("Info: No text could be extracted from the document.", "System")]

    except FileNotFoundError:
        return [(f"Error: File not found at {file_path}", "File System")]
    except Exception as e:
        return [(f"Error: An unexpected error occurred: {e}", "System")]
