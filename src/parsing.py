import os
import logging
import pdfplumber
from typing import List, Dict

logger = logging.getLogger(__name__)

def parse_document_content(file_path: str) -> List[Dict[str, str]]:
    """
    Parses the content of a document (PDF, TXT, DOCX) into text chunks.

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
        else:
            current_text.append(stripped_line)

    if current_text or not sections:
        sections[current_section] = " ".join(current_text).strip()

    return sections

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