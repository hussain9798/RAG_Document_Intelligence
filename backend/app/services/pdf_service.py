"""
PDF processing service.

Uses PyMuPDF (fitz) to extract text page-by-page, preserving page numbers.
Handles invalid/corrupted/encrypted/empty/scanned PDFs with clear,
actionable errors instead of silently producing an empty document.
"""
import fitz  # PyMuPDF

from app.utils.logger import get_logger

logger = get_logger("rag.pdf_service")


class PDFProcessingError(Exception):
    """Raised for any PDF that cannot be safely/meaningfully processed."""


def extract_pages(file_path: str) -> tuple[list[dict], int]:
    """
    Returns (pages, total_page_count) where pages is a list of
    {"page_number": int, "text": str} for every page that contains
    extractable text.

    Raises PDFProcessingError for corrupted files, password-protected files
    that can't be opened, or files with no extractable text at all (which
    usually means the PDF is scanned/image-only and needs OCR).
    """
    try:
        doc = fitz.open(file_path)
    except Exception as exc:  # PyMuPDF raises generic exceptions for bad files
        logger.warning("Failed to open PDF %s: %s", file_path, exc)
        raise PDFProcessingError("The file could not be opened. It may be corrupted or not a valid PDF.") from exc

    if doc.is_encrypted:
        # Try an empty-password unlock (some "protected" PDFs use blank owner passwords)
        if not doc.authenticate(""):
            doc.close()
            raise PDFProcessingError(
                "This PDF is password-protected. Please remove the password and re-upload."
            )

    if doc.page_count == 0:
        doc.close()
        raise PDFProcessingError("This PDF has no pages.")

    total_pages = doc.page_count
    pages = []
    for page_number, page in enumerate(doc, start=1):
        try:
            text = page.get_text().strip()
        except Exception as exc:
            logger.warning("Failed extracting page %s of %s: %s", page_number, file_path, exc)
            text = ""
        if text:
            pages.append({"page_number": page_number, "text": text})

    doc.close()

    if not pages:
        raise PDFProcessingError(
            "No extractable text was found in this PDF. It looks like a scanned or "
            "image-only document - OCR is required before it can be indexed."
        )

    logger.info("Extracted text from %d/%d pages of %s", len(pages), total_pages, file_path)
    return pages, total_pages
