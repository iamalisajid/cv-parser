"""Extract text from PDF files using pdfplumber."""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text(pdf_path: Path) -> str:
    """Return all text from *pdf_path*, concatenated across pages.

    Returns an empty string if the file is unreadable or has no text layer
    (e.g. scanned image-only PDF).
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            full_text = "\n\n".join(pages)
            if not full_text.strip():
                logger.warning("No text extracted from %s (scanned / image-only?)", pdf_path)
            return full_text
    except Exception:
        logger.exception("Failed to parse PDF: %s", pdf_path)
        return ""
