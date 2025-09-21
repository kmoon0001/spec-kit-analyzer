"""
Unified Text Extractor Module

Supports extracting text from:
- PDF documents (including text-based PDFs)
- Word documents (.docx)
- Excel spreadsheets (.xlsx)
- Scanned images (PNG, JPG, TIFF) using Tesseract OCR

Dependencies:
- pdfplumber
- python-docx
- pandas
- pillow
- pytesseract

Install dependencies (if not done already):
pip install pdfplumber python-docx pandas pillow pytesseract

Ensure Tesseract OCR engine is installed on your system and pytesseract can find it.
"""

import os
from typing import Optional
import pdfplumber
import docx
import pandas as pd
from PIL import Image
import pytesseract

class UnifiedTextExtractor:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_from_pdf(self, file_path: str) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def extract_from_word(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def extract_from_excel(self, file_path: str) -> str:
        df = pd.read_excel(file_path)
        return df.to_string()

    def extract_from_image(self, file_path: str) -> str:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text

    def extract_text(self, file_path: str) -> str:
        """
        Main method to detect file type and extract text accordingly.
        """

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return self.extract_from_pdf(file_path)
        elif ext in [".docx"]:
            return self.extract_from_word(file_path)
        elif ext in [".xlsx", ".xls"]:
            return self.extract_from_excel(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return self.extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

# Basic usage example
if __name__ == "__main__":
    extractor = UnifiedTextExtractor()

    # Replace with your file path to test
    sample_file_path = "test_document.pdf"

    try:
        text_output = extractor.extract_text(sample_file_path)
        print("Extracted Text:")
        print(text_output)
    except Exception as e:
        print(f"Error extracting text: {e}")
