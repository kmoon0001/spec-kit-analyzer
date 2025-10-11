import hashlib
import logging
import os
import re

import pdfplumber
import PIL
import yaml
from docx import Document
from PIL import Image

from .cache_service import cache_service

# OCR imports with fallback
try:
    import cv2
    import numpy as np
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None  # type: ignore[assignment]
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def _get_file_hash(file_path: str) -> str:
    """Calculates the SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_document_content(file_path: str) -> list[dict[str, str]]:
    """Parse supported documents into sentence chunks with OCR support and content-based caching."""
    if not os.path.exists(file_path):
        return [
            {
                "sentence": f"Error: File not found at {file_path}",
                "source": "parser",
            },
        ]

    extension = os.path.splitext(file_path)[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return [
            {
                "sentence": f"Error: Unsupported file type '{extension}'. Supported formats: {supported_list}",
                "source": "parser",
            },
        ]

    cache_key = "parsed_document_" + hashlib.sha256(file_path.encode("utf-8")).hexdigest()

    cached_result = cache_service.get_from_disk(cache_key)
    if cached_result is not None:
        logger.info("Cache hit for document: %s", os.path.basename(file_path))
        return cached_result

    logger.info("Cache miss for document: %s. Parsing from scratch.", os.path.basename(file_path))

    try:
        if extension == ".pdf":
            result = _parse_pdf_with_ocr(file_path)
        elif extension == ".txt":
            result = _parse_txt(file_path)
        elif extension == ".docx":
            result = _parse_docx(file_path)
        elif extension in IMAGE_EXTENSIONS:
            result = _parse_image_with_ocr(file_path)
        else:
            result = []

        cache_service.set_to_disk(cache_key, result)
        return result

    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.exception("Error parsing %s: {e}", file_path)
        return [
            {
                "sentence": f"Error parsing file: {e!s}",
                "source": "parser",
            },
        ]


def _preprocess_image_for_ocr(image):
    """Preprocess image for better OCR accuracy."""
    if not OCR_AVAILABLE:
        return image

    try:
        # Convert PIL Image to OpenCV format
        if isinstance(image, Image.Image):
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            image_cv = image

        # Convert to grayscale
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

        # Apply deskewing
        coords = np.column_stack(np.where(gray > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) > 0.5:  # Only deskew if angle is significant
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # Noise removal
        gray = cv2.medianBlur(gray, 3)

        # Thresholding to get better contrast
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        return gray

    except Exception as e:
        logger.warning("Image preprocessing failed: %s, using original image", e)
        return image


def _parse_image_with_ocr(file_path: str) -> list[dict[str, str]]:
    """Parse image files using OCR."""
    if not OCR_AVAILABLE:
        return [
            {
                "sentence": "Error: OCR functionality not available. Please install pytesseract and opencv-python.",
                "source": "parser",
            },
        ]

    try:
        # Load image
        image = Image.open(file_path)

        # Preprocess image for better OCR
        processed_image = _preprocess_image_for_ocr(image)

        # Perform OCR with medical-optimized settings
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}"-/\n '

        text = pytesseract.image_to_string(processed_image, config=custom_config)

        if not text.strip():
            return [
                {
                    "sentence": "Warning: No text could be extracted from the image. The image may be too low quality or contain no readable text.",
                    "source": "ocr",
                },
            ]

        # Split into sentences and clean up
        sentences = _split_into_sentences(text)

        return [
            {
                "sentence": sentence.strip(),
                "source": "ocr",
            }
            for sentence in sentences
            if sentence.strip()
        ]

    except (OSError, FileNotFoundError) as e:
        logger.exception("OCR processing failed for %s: {e}", file_path)
        return [
            {
                "sentence": f"Error: OCR processing failed - {e!s}",
                "source": "parser",
            },
        ]


def _parse_pdf_with_ocr(file_path: str) -> list[dict[str, str]]:
    """Parse PDF with OCR fallback for scanned documents."""
    try:
        # First try regular text extraction
        with pdfplumber.open(file_path) as pdf:
            text_content = []
            ocr_pages = []

            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()

                if page_text and page_text.strip():
                    # Page has extractable text
                    sentences = _split_into_sentences(page_text)
                    for sentence in sentences:
                        if sentence.strip():
                            text_content.append(
                                {
                                    "sentence": sentence.strip(),
                                    "source": f"pdf_page_{page_num + 1}",
                                }
                            )
                else:
                    # Page appears to be scanned, try OCR
                    if OCR_AVAILABLE:
                        try:
                            # Convert page to image
                            page_image = page.to_image(resolution=300)
                            pil_image = page_image.original

                            # Preprocess and OCR
                            processed_image = _preprocess_image_for_ocr(pil_image)
                            custom_config = r"--oem 3 --psm 6"
                            ocr_text = pytesseract.image_to_string(processed_image, config=custom_config)

                            if ocr_text.strip():
                                sentences = _split_into_sentences(ocr_text)
                                for sentence in sentences:
                                    if sentence.strip():
                                        text_content.append(
                                            {
                                                "sentence": sentence.strip(),
                                                "source": f"ocr_page_{page_num + 1}",
                                            }
                                        )
                                ocr_pages.append(page_num + 1)

                        except (PIL.UnidentifiedImageError, OSError, ValueError):
                            logger.warning("OCR failed for page %s: {e}", page_num + 1)
                            text_content.append(
                                {
                                    "sentence": f"Warning: Page {page_num + 1} could not be processed (may be scanned image without OCR capability)",
                                    "source": "parser",
                                }
                            )
                    else:
                        text_content.append(
                            {
                                "sentence": f"Warning: Page {page_num + 1} appears to be scanned but OCR is not available. Install pytesseract for scanned document support.",
                                "source": "parser",
                            }
                        )

            if ocr_pages:
                logger.info("OCR was used for pages: %s", ocr_pages)
                text_content.insert(
                    0,
                    {
                        "sentence": f"Note: OCR was used to extract text from scanned pages: {', '.join(map(str, ocr_pages))}",
                        "source": "ocr_info",
                    },
                )

            return (
                text_content
                if text_content
                else [
                    {
                        "sentence": "Error: No text could be extracted from the PDF.",
                        "source": "parser",
                    },
                ]
            )

    except (OSError, FileNotFoundError) as e:
        logger.exception("PDF parsing failed for %s: {e}", file_path)
        return [
            {
                "sentence": f"Error parsing PDF: {e!s}",
                "source": "parser",
            },
        ]


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences with medical document awareness."""
    # Clean up the text
    text = re.sub(r"\s+", " ", text)  # Normalize whitespace
    text = re.sub(r"([.!?])\s*([A-Z])", r"\1\n\2", text)  # Split on sentence boundaries

    # Handle medical abbreviations that shouldn't be split
    medical_abbrevs = ["Dr.", "Mr.", "Mrs.", "Ms.", "PT.", "OT.", "SLP.", "etc.", "vs.", "i.e.", "e.g."]
    for abbrev in medical_abbrevs:
        text = text.replace(abbrev + "\n", abbrev + " ")

    sentences = [s.strip() for s in text.split("\n") if s.strip()]

    # Merge very short sentences (likely fragments)
    merged_sentences = []
    current_sentence = ""

    for sentence in sentences:
        if len(sentence) < 20 and current_sentence:
            current_sentence += " " + sentence
        else:
            if current_sentence:
                merged_sentences.append(current_sentence)
            current_sentence = sentence

    if current_sentence:
        merged_sentences.append(current_sentence)

    return merged_sentences


def _parse_pdf(file_path: str) -> list[dict[str, str]]:
    """Legacy PDF parser - redirects to OCR-enabled version."""
    return _parse_pdf_with_ocr(file_path)


def _parse_txt(file_path: str) -> list[dict[str, str]]:
    with open(file_path, "r", encoding="utf-8") as handle:
        text = handle.read().strip()
    return [{"sentence": text, "source": os.path.basename(file_path)}] if text else []


def _parse_docx(file_path: str) -> list[dict[str, str]]:
    document = Document(file_path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    return [{"sentence": text, "source": os.path.basename(file_path)}] if text else []


DEFAULT_SECTION_HEADERS = [
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


def load_section_headers() -> list[str]:
    try:
        with open("config.yaml", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return DEFAULT_SECTION_HEADERS

    headers = config.get("section_headers") or []
    return headers or DEFAULT_SECTION_HEADERS


def parse_document_into_sections(text: str) -> dict[str, str]:
    headers = load_section_headers()
    if not headers:
        return {"full_text": text}

    pattern = r"^\s*(" + "|".join(re.escape(header) for header in headers) + r")\s*:"
    matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))

    if not matches:
        return {"unclassified": text}

    sections: dict[str, str] = {}
    if matches[0].start() > 0:
        intro = text[: matches[0].start()].strip()
        if intro:
            sections["Header"] = intro

    for index, match in enumerate(matches):
        header = match.group(1)
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[match.end() : next_start].strip()
        normalized_header = next((item for item in headers if item.lower() == header.lower()), header)
        sections[normalized_header] = content

    return sections
