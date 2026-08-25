"""
Chunking service.

Splits per-page text into overlapping, word-bounded chunks, trying to break
on sentence boundaries where possible. Chunk size/overlap are configurable
via backend settings (CHUNK_SIZE_WORDS / CHUNK_OVERLAP_WORDS).
"""
import re

from app.config import get_settings

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    sentences = _SENTENCE_END.split(text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_page_text(page_number: int, text: str) -> list[dict]:
    """
    Returns a list of {"page_number": int, "text": str} chunks for a single
    page, respecting the configured word count and overlap while preferring
    to break between sentences rather than mid-sentence.
    """
    settings = get_settings()
    chunk_size = settings.chunk_size_words
    overlap = settings.chunk_overlap_words

    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: list[dict] = []
    current_words: list[str] = []

    def flush():
        if current_words:
            chunks.append({"page_number": page_number, "text": " ".join(current_words).strip()})

    for sentence in sentences:
        sentence_words = sentence.split()

        if len(current_words) + len(sentence_words) > chunk_size and current_words:
            flush()
            # Start the next chunk with the overlap tail of the previous one
            overlap_words = current_words[-overlap:] if overlap > 0 else []
            current_words = overlap_words.copy()

        # If a single sentence is itself longer than chunk_size, hard-split it
        if len(sentence_words) > chunk_size:
            for i in range(0, len(sentence_words), chunk_size - overlap if chunk_size > overlap else chunk_size):
                piece = sentence_words[i : i + chunk_size]
                current_words.extend(piece)
                if len(current_words) >= chunk_size:
                    flush()
                    overlap_words = current_words[-overlap:] if overlap > 0 else []
                    current_words = overlap_words.copy()
        else:
            current_words.extend(sentence_words)

    flush()
    return chunks


def chunk_document(pages: list[dict]) -> list[dict]:
    """
    pages: list of {"page_number": int, "text": str} (already cleaned).
    Returns a flat, ordered list of {"page_number": int, "chunk_index": int, "text": str}.
    """
    all_chunks: list[dict] = []
    chunk_index = 0
    for page in pages:
        page_chunks = chunk_page_text(page["page_number"], page["text"])
        for c in page_chunks:
            all_chunks.append(
                {"page_number": c["page_number"], "chunk_index": chunk_index, "text": c["text"]}
            )
            chunk_index += 1
    return all_chunks
