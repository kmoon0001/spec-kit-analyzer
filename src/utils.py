# Standard library
import logging
import os
import re
import sys
import html
import difflib
from typing import List, Tuple
from collections import Counter

# Third-party
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, UnidentifiedImageError
from docx import Document
from docx.opc.exceptions import PackageNotFoundError

logger = logging.getLogger(__name__)

# --- PHI scrubber ---
_PHI_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:\d{2}|\d{4})\b"), "[DATE]"),
    (re.compile(r"\b\d{6,10}\b"), "[MRN]"),
    (re.compile(r"\b\d{1,5}\s+[A-Za-z0-9.\- ]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane)\b", re.I),
     "[ADDR]"),
]

def scrub_phi(text: str) -> str:
    if not isinstance(text, str):
        return text
    out = text
    for pat, repl in _PHI_PATTERNS:
        out = re.sub(pat, repl, out)
    return out

# --- Utilities ---
def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _open_path(p: str) -> None:
    try:
        if os.name == "nt":
            os.startfile(p)
        elif sys.platform == "darwin":
            os.system(f"open \"{p}\"")
        else:
            os.system(f"xdg-open \"{p}\"")
    except OSError as e:
        logger.warning(f"Failed to open path {p}: {e}")

# --- Parsing (PDF/DOCX/CSV/XLSX/Images with optional OCR) ---
def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text) if p.strip()]
    if not sents:
        sents = text.splitlines()
    return [s for s in sents if s]

def parse_document_content(file_path: str, ocr_lang: str = "eng") -> List[Tuple[str, str]]:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        sentences: list[tuple[str, str]] = []
        if ext == ".pdf":
            if not pdfplumber:
                return [("Error: pdfplumber not available.", "PDF Parser")]
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    txt = page.extract_text() or ""
                    for s in split_sentences(txt):
                        if s:
                            sentences.append((s, f"Page {i}"))
        elif ext == ".docx":
            try:
                docx_doc = Document(file_path)
                for i, para in enumerate(docx_doc.paragraphs, start=1):
                    if not para.text.strip():
                        continue
                    for s in split_sentences(para.text):
                        if s:
                            sentences.append((s, f"Paragraph {i}"))
            except PackageNotFoundError:
                return [("Error: Invalid DOCX file.", "DOCX Parser")]
        elif ext in [".xlsx", ".xls", ".csv"]:
            try:
                if ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                    if isinstance(df, dict):
                        df = next(iter(df.values()))
                else:
                    df = pd.read_csv(file_path)
                content = df.to_string(index=False)
                for s in split_sentences(content):
                    if s:
                        sentences.append((s, "Table"))
            except (pd.errors.ParserError, ValueError) as e:
                return [(f"Error: Failed to read tabular file: {e}", "Data Parser")]
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            if not Image or not pytesseract:
                return [("Error: OCR dependencies not available.", "OCR Parser")]
            try:
                img = Image.open(file_path)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                txt = pytesseract.image_to_string(img, lang=ocr_lang)
                for s in split_sentences(txt or ""):
                    if s:
                        sentences.append((s, "Image (OCR)"))
            except UnidentifiedImageError as e:
                return [(f"Error: Unidentified image: {e}", "OCR Parser")]
            except pytesseract.TesseractNotFoundError:
                return [("Error: Tesseract is not installed or not in your PATH.", "OCR Parser")]
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                txt = f.read()
            for s in split_sentences(txt):
                if s:
                    sentences.append((s, "Text File"))
        else:
            return [(f"Error: Unsupported file type: {ext}", "File Handler")]
        return sentences if sentences else [("Info: No text could be extracted from the document.", "System")]
    except FileNotFoundError:
        return [(f"Error: File not found at {file_path}", "File System")]
    except (IOError, OSError) as e:
        logger.exception("parse_document_content failed")
        return [(f"Error: An unexpected error occurred: {e}", "System")]

# --- Dedup helpers ---
def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(a=_normalize_text(a), b=_normalize_text(b)).ratio()

def collapse_similar_sentences_simple(items: list[Tuple[str, str]], threshold: float) -> list[Tuple[str, str]]:
    kept: list[Tuple[str, str]] = []
    for t, s in items:
        if not kept:
            kept.append((t, s))
            continue
        sim = max(_similarity(t, kt) for (kt, _) in kept)
        if sim < threshold:
            kept.append((t, s))
    return kept

def collapse_similar_sentences_tfidf(items: list[Tuple[str, str]], threshold: float) -> list[Tuple[str, str]]:
    texts = [t for t, _ in items]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vect = TfidfVectorizer(min_df=1, ngram_range=(1, 2), max_features=10000)
        X = vect.fit_transform([_normalize_text(t) for t in texts])
        sim = cosine_similarity(X)
    except ImportError:
        logger.warning("scikit-learn not available, falling back to simple similarity.")
        return collapse_similar_sentences_simple(items, threshold)
    kept_idx: list[int] = []
    for i in range(len(items)):
        if not kept_idx:
            kept_idx.append(i)
            continue
        if max(sim[i, j] for j in kept_idx) < threshold:
            kept_idx.append(i)
    return [items[i] for i in kept_idx]

def build_rich_summary(original: list[Tuple[str, str]], collapsed: list[Tuple[str, str]]) -> dict:
    from collections import Counter

    def tok(text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z']+", text.lower())
        stop = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was", "were", "be",
                "as", "at", "by", "from", "that"}
        return [t for t in tokens if t not in stop]

    total_raw = len(original)
    total_final = len(collapsed)
    by_source = Counter(s for _, s in collapsed)
    lengths = [len(t) for t, _ in collapsed]
    avg_len = (sum(lengths) / len(lengths)) if lengths else 0
    p95 = (sorted(lengths)[int(0.95 * (len(lengths) - 1))] if lengths else 0)
    all_text = " ".join(t for t, _ in collapsed)
    tokens = tok(all_text)
    top_tokens = Counter(tokens).most_common(15)
    return {
        "total_sentences_raw": total_raw,
        "total_sentences_final": total_final,
        "dedup_removed": max(0, total_raw - total_final),
        "avg_sentence_length_chars": round(avg_len, 1),
        "p95_sentence_length_chars": p95,
        "total_words": len(tokens),
        "by_source": dict(by_source),
        "top_tokens": top_tokens,
    }

def count_categories(issues: list[dict]) -> dict:
    from collections import Counter
    c = Counter((i.get("category") or "General") for i in issues)
    return dict(c)
