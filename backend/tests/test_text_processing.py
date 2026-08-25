"""
Unit tests for text cleaning and chunking - pure functions, no DB/network
required. Run with: pytest backend/tests/test_text_processing.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.cleaning_service import clean_text
from app.services.chunking_service import chunk_document, chunk_page_text


def test_clean_text_collapses_wrapped_lines():
    raw = "This is a sen-\ntence that wraps\nacross lines."
    cleaned = clean_text(raw)
    assert "\n" not in cleaned or "sentence" in cleaned
    assert "sentence" in cleaned


def test_clean_text_removes_page_number_lines():
    raw = "Some real content here.\n\n12\n\nMore real content."
    cleaned = clean_text(raw)
    assert "\n12\n" not in cleaned


def test_clean_text_preserves_content():
    raw = "Supervised learning uses labelled data."
    cleaned = clean_text(raw)
    assert "Supervised learning uses labelled data." in cleaned


def test_chunk_page_text_respects_word_count():
    text = " ".join(f"word{i}." for i in range(2000))
    chunks = chunk_page_text(page_number=1, text=text)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c["text"].split()) <= 900  # generous upper bound including overlap


def test_chunk_document_preserves_page_numbers():
    pages = [
        {"page_number": 1, "text": "First page content. " * 50},
        {"page_number": 2, "text": "Second page content. " * 50},
    ]
    chunks = chunk_document(pages)
    page_numbers = {c["page_number"] for c in chunks}
    assert page_numbers == {1, 2}
    # chunk_index must be sequential across the whole document
    indices = [c["chunk_index"] for c in chunks]
    assert indices == sorted(indices)


def test_chunk_document_empty_pages_returns_empty():
    assert chunk_document([]) == []
