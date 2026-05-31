"""Unit tests for PdfParserService — focus on cleanup + error paths.

pypdf's actual text extraction is library behavior; we just verify that bad
input raises PdfParseError and that clean_text normalizes correctly.
"""

import pytest

from app.services.chat.pdf_parser_service import PdfParseError, PdfParserService


def test_empty_bytes_raises():
    svc = PdfParserService()
    with pytest.raises(PdfParseError):
        svc.extract_pages(b"")


def test_non_pdf_bytes_raises():
    svc = PdfParserService()
    with pytest.raises(PdfParseError):
        svc.extract_pages(b"hello world, definitely not a pdf")


def test_clean_text_collapses_runs_of_spaces():
    svc = PdfParserService()
    assert svc.clean_text("a    b\t\tc") == "a b c"


def test_clean_text_repairs_hyphenated_linebreak():
    svc = PdfParserService()
    assert svc.clean_text("exam-\nple") == "example"
    assert svc.clean_text("multi-\n  line break") == "multiline break"


def test_clean_text_strips_pure_page_number_lines():
    svc = PdfParserService()
    cleaned = svc.clean_text("real content\n42\nmore content")
    assert "42" not in cleaned
    assert "real content" in cleaned
    assert "more content" in cleaned


def test_clean_text_collapses_multiple_blank_lines():
    svc = PdfParserService()
    out = svc.clean_text("para1\n\n\n\n\npara2")
    # Three or more newlines collapse to exactly two
    assert "\n\n\n" not in out
    assert "para1\n\npara2" in out


def test_clean_text_returns_empty_for_empty():
    svc = PdfParserService()
    assert svc.clean_text("") == ""
    assert svc.clean_text("   \n\n  ") == ""
