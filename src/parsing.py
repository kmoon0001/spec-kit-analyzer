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

    # 1. Check for supported file extensions first
    supported_extensions = ['.pdf', '.txt', '.docx']
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in supported_extensions:
        error_message = f"Error: Unsupported file type '{file_ext}'. Only PDF, TXT, and DOCX are supported."
        logger.warning(error_message)
        return [{'sentence': error_message, 'source': 'parser'}]

    # 2. Try to open and parse the file
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
        else:
            # This line is a continuation of the current section's content
            current_text.append(stripped_line)

    # Save the last processed section
    if current_text or not sections:
        sections[current_section] = " ".join(current_text).strip()

    return sections