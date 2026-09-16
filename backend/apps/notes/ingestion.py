"""Text extraction for the PDF/URL note-import pipeline.

Kept deliberately dumb: pull raw text out of a source, nothing else. Chunking
and embedding are already handled downstream by apps.knowledge_base once a
Note is published -- this module's only job is producing clean plain text to
put in Note.content.
"""

from urllib.parse import urlparse

import trafilatura
from pypdf import PdfReader
from pypdf.errors import PdfReadError


class ExtractionError(Exception):
    """Raised when no usable text could be pulled from a source."""


def is_url(source: str) -> bool:
    return urlparse(source).scheme in ("http", "https")


def extract_pdf_text(file_obj) -> str:
    """file_obj: any file-like object opened in binary mode (upload or local file)."""
    try:
        reader = PdfReader(file_obj)
    except PdfReadError as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc

    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(page.strip() for page in pages if page.strip())
    if not text:
        raise ExtractionError(
            "No extractable text found in that PDF -- it may be a scanned/image-only "
            "document, which isn't supported (no OCR)."
        )
    return text


def extract_url_text(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ExtractionError(f"Could not fetch {url!r} -- check the URL is reachable.")

    text = trafilatura.extract(downloaded)
    if not text or not text.strip():
        raise ExtractionError(f"Could not extract readable article text from {url!r}.")
    return text.strip()
