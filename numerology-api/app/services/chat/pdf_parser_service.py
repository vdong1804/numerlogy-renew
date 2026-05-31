"""Extract text from PDF bytes using pypdf, page-by-page with light cleanup.

We don't try to be clever about layout — pypdf's text extraction is "good
enough" for the numerology report format. Encrypted / image-only PDFs raise
`PdfParseError` so the router can return 422 with a clear message.
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from typing import Iterable

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"[ \t ]+")
_NEWLINES_RE = re.compile(r"\n{3,}")
# Soft hyphen at end of line: "exam-\nple" -> "example"
_HYPHEN_BREAK_RE = re.compile(r"-\s*\n\s*")
# Pure page-number lines (1-4 digits with nothing else)
_PAGE_NUMBER_LINE = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)


class PdfParseError(RuntimeError):
    """Raised when a PDF cannot be opened or contains no extractable text."""


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str


class PdfParserService:
    """Extract + clean text from a PDF byte buffer."""

    def extract_pages(self, pdf_bytes: bytes) -> list[PageText]:
        if not pdf_bytes:
            raise PdfParseError("empty file")
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except PdfReadError as exc:
            raise PdfParseError(f"invalid or encrypted PDF: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise PdfParseError(f"could not open PDF: {exc}") from exc

        if getattr(reader, "is_encrypted", False):
            raise PdfParseError("encrypted PDFs are not supported")

        pages: list[PageText] = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                raw = page.extract_text() or ""
            except Exception:  # noqa: BLE001
                logger.exception("pdf parser: page %d extract failed", i)
                raw = ""
            cleaned = self.clean_text(raw)
            if cleaned:
                pages.append(PageText(page_number=i, text=cleaned))
        if not pages:
            raise PdfParseError("no extractable text (image-only or empty PDF)")
        return pages

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Repair hyphenated line-breaks before collapsing whitespace.
        out = _HYPHEN_BREAK_RE.sub("", text)
        # Drop pure page-number lines.
        out = _PAGE_NUMBER_LINE.sub("", out)
        # Collapse runs of spaces/tabs.
        out = _WHITESPACE_RE.sub(" ", out)
        # Collapse 3+ newlines to 2 (preserves paragraph breaks).
        out = _NEWLINES_RE.sub("\n\n", out)
        return out.strip()

    @staticmethod
    def join_pages(pages: Iterable[PageText]) -> str:
        """Single concatenated string with `\\n\\n` between pages."""
        return "\n\n".join(p.text for p in pages)
