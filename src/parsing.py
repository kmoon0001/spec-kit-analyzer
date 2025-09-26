import os
import re
from typing import List, Tuple, Dict

import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import pandas as pd

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

<<<<<<< HEAD
    supported_extensions = ['.pdf', '.txt', '.docx']
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in supported_extensions:
        error_message = f"Error: Unsupported file type '{file_ext}'. Only PDF, TXT, and DOCX are supported."
        logger.warning(error_message)
        return [{'sentence': error_message, 'source': 'parser'}]

||||||| 3810719
    # 1. Check for supported file extensions first
    supported_extensions = ['.pdf', '.txt', '.docx']
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in supported_extensions:
        error_message = f"Error: Unsupported file type '{file_ext}'. Only PDF, TXT, and DOCX are supported."
        logger.warning(error_message)
        return [{'sentence': error_message, 'source': 'parser'}]

    # 2. Try to open and parse the file
=======
>>>>>>> origin/main
    try:
        chunks: list[dict] = []

        # --- Step 1: Extract text from the document based on its type ---
        if ext == ".pdf":
            if not pdfplumber:
                return [{'sentence': "Error: pdfplumber not available.", 'window': '', 'metadata': {'source': 'PDF Parser'}}]
            with pdfplumber.open(file_path) as pdf:
<<<<<<< HEAD
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    chunks.append({'sentence': text, 'source': f'{os.path.basename(file_path)} (Page {i+1})'})

        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks.append({'sentence': text, 'source': os.path.basename(file_path)})

        return chunks

    except FileNotFoundError:
        error_message = f"Error: File not found at {file_path}"
        logger.error(error_message)
        return [{'sentence': error_message, 'source': 'parser'}]
    except Exception as e:
        error_message = f"Error parsing document '{os.path.basename(file_path)}': {e}"
        logger.error(error_message, exc_info=True)
        return [{'sentence': error_message, 'source': 'parser'}]

def parse_document_into_sections(document_text: str) -> Dict[str, str]:
    """
    Parses a document's full text into standard sections (Subjective, Objective, etc.).
    """
    sections = {}
    current_section = "unclassified"
    current_text = []
    headers = ["subjective", "objective", "assessment", "plan"]
    found_first_header = False

    for line in document_text.strip().split('\n'):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        line_lower = stripped_line.lower()
        found_header = None
        for header in headers:
            if line_lower.startswith(header + ":"):
                found_header = header
                break

        if found_header:
            if current_text and (found_first_header or current_section != "unclassified"):
                 sections[current_section] = " ".join(current_text).strip()

            found_first_header = True
            current_section = found_header
            content_start_index = len(found_header) + 1
            initial_content = stripped_line[content_start_index:].strip()
            current_text = [initial_content] if initial_content else []
||||||| 3810719
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    chunks.append({'sentence': text, 'source': f'{os.path.basename(file_path)} (Page {i+1})'})

        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks.append({'sentence': text, 'source': os.path.basename(file_path)})

        # Note: python-docx is not in requirements, so this part is commented out but shows
        # how it would be extended. If it were active, it would need a test case.
        # elif file_ext == '.docx':
        #     import docx
        #     doc = docx.Document(file_path)
        #     full_text = "\n".join([para.text for para in doc.paragraphs])
        #     chunks.append({'sentence': full_text, 'source': os.path.basename(file_path)})

        return chunks

    except FileNotFoundError:
        error_message = f"Error: File not found at {file_path}"
        logger.error(error_message)
        return [{'sentence': error_message, 'source': 'parser'}]
    except Exception as e:
        error_message = f"Error parsing document '{os.path.basename(file_path)}': {e}"
        logger.error(error_message, exc_info=True)
        return [{'sentence': error_message, 'source': 'parser'}]


def parse_document_into_sections(document_text: str) -> Dict[str, str]:
    """
    Parses a document's full text into standard sections (Subjective, Objective, etc.).
    This version correctly handles cases where content is on the same line as the header.
    """
    sections = {}
    current_section = "unclassified"
    current_text = []
    headers = ["subjective", "objective", "assessment", "plan"]

    # This flag helps handle documents that don't start with a standard header
    found_first_header = False

    for line in document_text.strip().split('\n'):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        line_lower = stripped_line.lower()

        found_header = None
        # Check if the line starts with any of the known headers, followed by a colon
        for header in headers:
            if line_lower.startswith(header + ":"):
                found_header = header
                break

        if found_header:
            # If we were already processing a section, save its content before starting the new one.
            if current_text and (found_first_header or current_section != "unclassified"):
                 sections[current_section] = " ".join(current_text).strip()

            found_first_header = True
            current_section = found_header
            # The content is the part of the line after the header and colon
            content_start_index = len(found_header) + 1
            initial_content = stripped_line[content_start_index:].strip()
            current_text = [initial_content] if initial_content else []
=======
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
>>>>>>> origin/main
        else:
<<<<<<< HEAD
            current_text.append(stripped_line)
||||||| 3810719
            # This line is a continuation of the current section's content
            current_text.append(stripped_line)
=======
            return [{'sentence': f"Error: Unsupported file type: {ext}", 'window': '', 'metadata': {'source': 'File Handler'}}]
>>>>>>> origin/main

<<<<<<< HEAD
    if current_text or not sections:
        sections[current_section] = " ".join(current_text).strip()
||||||| 3810719
    # Save the last processed section
    if current_text or not sections:
        sections[current_section] = " ".join(current_text).strip()
=======
        return chunks if chunks else [{'sentence': "Info: No text could be extracted from the document.", 'window': '', 'metadata': {'source': 'System'}}]

<<<<<<< HEAD
    except Exception as e:
        return [{'sentence': f"Error: An unexpected error occurred: {e}", 'window': '', 'metadata': {'source': 'System'}}]

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
>>>>>>> origin/main

    return sections
<<<<<<< HEAD

def parse_guideline_file(file_path: str) -> List[Dict[str, str]]:
    """
    Parses a guideline text file into a list of dictionaries.
    """
    logger.info(f"Parsing guideline file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return [{'text': text, 'source': os.path.basename(file_path)}]
    except FileNotFoundError:
        error_message = f"Error: Guideline file not found at {file_path}"
        logger.error(error_message)
        return []
    except Exception as e:
        error_message = f"Error parsing guideline file '{os.path.basename(file_path)}': {e}"
        logger.error(error_message, exc_info=True)
        return []
||||||| 3810719
=======

# For compatibility: expose both parse_text_into_sections and parse_document_into_sections
parse_document_into_sections = parse_text_into_sections
||||||| c46cdd8
    return sections
=======
    return sections
>>>>>>> origin/main
>>>>>>> origin/main
