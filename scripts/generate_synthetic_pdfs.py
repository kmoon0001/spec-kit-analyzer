#!/usr/bin/env python3
"""Generate synthetic PDFs for stress-testing ingestion and analysis."""

from __future__ import annotations

import argparse
import random
import string
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def _random_text(paragraph_words: int) -> str:
    words = []
    for _ in range(paragraph_words):
        word_len = random.randint(3, 10)
        words.append("".join(random.choices(string.ascii_lowercase, k=word_len)))
    return " ".join(words)


def generate_pdf(
    output_path: Path,
    pages: int,
    paragraphs_per_page: int,
    words_per_paragraph: int,
    seed: int | None,
) -> None:
    if seed is not None:
        random.seed(seed)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    width, height = LETTER
    top_margin = height - 0.75 * inch
    left_margin = 0.75 * inch
    line_height = 0.18 * inch

    for page_index in range(1, pages + 1):
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(left_margin, top_margin, "Synthetic Therapy Note")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(
            left_margin,
            top_margin - line_height,
            f"Generated: {datetime.now().isoformat()} | Page {page_index}/{pages}",
        )

        y_cursor = top_margin - 2 * line_height
        for paragraph_index in range(paragraphs_per_page):
            if y_cursor < inch:
                pdf.showPage()
                y_cursor = top_margin
                pdf.setFont("Helvetica", 9)
            text = _random_text(words_per_paragraph)
            pdf.drawString(
                left_margin,
                y_cursor,
                f"{paragraph_index + 1}. {text}",
            )
            y_cursor -= line_height

        pdf.showPage()

    pdf.save()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic PDFs for ingestion tests."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("synthetic-pdfs"),
        help="Output directory for generated PDFs.",
    )
    parser.add_argument(
        "--files",
        type=int,
        default=3,
        help="Number of PDF files to generate.",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=50,
        help="Number of pages per PDF file.",
    )
    parser.add_argument(
        "--paragraphs",
        type=int,
        default=40,
        help="Paragraphs per page.",
    )
    parser.add_argument(
        "--words",
        type=int,
        default=30,
        help="Words per paragraph.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for index in range(1, args.files + 1):
        output_file = args.output / f"synthetic_{timestamp}_{index:02d}.pdf"
        generate_pdf(
            output_path=output_file,
            pages=args.pages,
            paragraphs_per_page=args.paragraphs,
            words_per_paragraph=args.words,
            seed=args.seed,
        )
        print(f"Generated {output_file}")


if __name__ == "__main__":
    main()
