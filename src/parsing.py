import os
import re
from typing import List, Tuple, Dict

import cv2
import numpy as np
import pdfplumber
import yaml
from docx import Document
import pytesseract
from PIL import Image
import pandas as pd

from src.utils import chunk_text

import logging

logger = logging.getLogger(__name__)

def _load_ocr_config():
    """Loads OCR configuration from config.yaml."""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config.get('ocr', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}

OCR_CONFIG = _load_ocr_config()

def _preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    """
    Preprocesses an image for OCR by converting it to grayscale,
    applying a binary threshold, and optionally deskewing.
    """
    if not isinstance(img, Image.Image):
        raise TypeError("The 'img' argument must be a PIL Image object.")

    if not OCR_CONFIG.get('preprocessing', True):
        return img

    try:
        open_cv_image = np.array(img.convert('RGB'))
        gray = cvcv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

        if OCR_CONFIG.get('deskew', True):
            coords = np.column_stack(np.where(gray > 0))
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return Image.fromarray(binary)
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        return img.convert("L")

def _parse_pdf(file_path: str) -> List[Tuple[str, str]]:
    """
    Handles PDF parsing, including scanned documents, based on config settings.
    """
    chunks_with_source = []
    if not pdfplumber:
        return [("Error: pdfplumber not available.", "PDF Parser")]

    resolution = OCR_CONFIG.get('resolution', 300)

    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if len(page_text.strip()) < 10:
                    try:
                        page_image = page.to_image(resolution=resolution).original
                        processed_image = _preprocess_image_for_ocr(page_image)
                        page_text = pytesseract.image_to_string(processed_image)
                        source = f"Page {i} (Scanned)"
                    except Exception as ocr_e:
                        logger.error(f"OCR failed on page {i}: {ocr_e}")
                        source = f"Page {i} (OCR Failed)"
                        page_text = ""
                else:
                    source = f"Page {i}"

                if page_text:
                    page_chunks = chunk_text(page_text)
                    for chunk in page_chunks:
                        chunks_with_source.append((chunk, source))
    except Exception as e:
        logger.error(f"PDF parsing error for {file_path}: {e}")
        return [("Error: Failed to parse PDF.", "PDF Parser")]
    return chunks_with_source

def _parse_docx(file_path: str) -> List[Tuple[str, str]]:
    """Handles DOCX parsing."""
    chunks_with_source = []
    try:
        doc = Document(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        doc_chunks = chunk_text(full_text)
        for chunk in doc_chunks:
            chunks_with_source.append((chunk, "DOCX Document"))
    except Exception as e:
        logger.error(f"DOCX parsing error: {e}")
        return [("Error: Failed to parse DOCX.", "DOCX Parser")]
    return chunks_with_source

def _parse_tabular(file_path: str, ext: str) -> List[Tuple[str, str]]:
    """Handles tabular data files (Excel, CSV)."""
    chunks_with_source = []
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
        logger.error(f"Tabular file parsing error: {e}")
        return [(f"Error: Failed to read tabular file: {e}", "Data Parser")]
    return chunks_with_source

def _parse_image(file_path: str) -> List[Tuple[str, str]]:
    """Handles image files with OCR."""
    chunks_with_source = []
    try:
        img = Image.open(file_path)
        processed_img = _preprocess_image_for_ocr(img)
        txt = pytesseract.image_to_string(processed_img)
        ocr_chunks = chunk_text(txt or "")
        for chunk in ocr_chunks:
            chunks_with_source.append((chunk, "Image (OCR)"))
    except Image.UnidentifiedImageError as e:
        logger.error(f"Unidentified image error: {e}")
        return [(f"Error: Unidentified image: {e}", "OCR Parser")]
    except Exception as e:
        logger.error(f"Image parsing error: {e}")
        return [("Error: Failed to process image.", "OCR Parser")]
    return chunks_with_source

def _parse_text(file_path: str) -> List[Tuple[str, str]]:
    """Handles plain text files."""
    chunks_with_source = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            txt = f.read()
        txt_chunks = chunk_text(txt)
        for chunk in txt_chunks:
            chunks_with_source.append((chunk, "Text File"))
    except Exception as e:
        logger.error(f"Text file parsing error: {e}")
        return [("Error: Failed to read text file.", "Text Parser")]
    return chunks_with_source

def parse_document_content(file_path: str) -> List[Tuple[str, str]]:
    """
    Parses the content of a document and splits it into chunks.
    """
    if not os.path.exists(file_path):
        return [(f"Error: File not found at {file_path}", "File System")]

    ext = os.path.splitext(file_path)[1].lower()
    logger.info(f"Parsing document: {file_path} with extension: {ext}")

    try:
        if ext == ".pdf":
            chunks_with_source = _parse_pdf(file_path)
        elif ext == ".docx":
            chunks_with_source = _parse_docx(file_path)
        elif ext in [".xlsx", ".xls", ".csv"]:
            chunks_with_source = _parse_tabular(file_path, ext)
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            chunks_with_source = _parse_image(file_path)
        elif ext == ".txt":
            chunks_with_source = _parse_text(file_path)
        else:
            return [(f"Error: Unsupported file type: {ext}", "File Handler")]

        return chunks_with_source if chunks_with_source else [("Info: No text could be extracted.", "System")]
    except Exception as e:
        logger.error(f"An unexpected error occurred in parse_document_content: {e}")
        return [(f"Error: An unexpected error occurred: {e}", "System")]

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
