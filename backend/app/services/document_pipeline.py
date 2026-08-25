"""
Document processing pipeline orchestrator.

Runs: extract -> clean -> chunk -> embed -> store-in-FAISS -> store-metadata-in-Mongo
-> update document status. Runs as a FastAPI background task after upload so
the HTTP response returns immediately with status="uploaded"/"processing".
"""
from bson import ObjectId

from app.database.mongodb import get_database
from app.models.chunk import new_chunk_document
from app.models.document import STATUS_FAILED, STATUS_PROCESSED, STATUS_PROCESSING
from app.services.chunking_service import chunk_document
from app.services.cleaning_service import clean_text
from app.services.embedding_service import embed_documents
from app.services.pdf_service import PDFProcessingError, extract_pages
from app.services.vector_store import add_embeddings, save_index
from app.utils.logger import get_logger

logger = get_logger("rag.document_pipeline")


async def process_document(document_id: str, user_id: str, file_path: str) -> None:
    db = get_database()
    doc_object_id = ObjectId(document_id)

    async def set_status(status: str, **extra):
        from datetime import datetime, timezone

        await db.documents.update_one(
            {"_id": doc_object_id}, {"$set": {"status": status, "updated_at": datetime.now(timezone.utc), **extra}}
        )

    await set_status(STATUS_PROCESSING)
    logger.info("Document processing started: %s", document_id)

    try:
        pages, total_pages = extract_pages(file_path)

        cleaned_pages = [{"page_number": p["page_number"], "text": clean_text(p["text"])} for p in pages]
        cleaned_pages = [p for p in cleaned_pages if p["text"]]

        chunks = chunk_document(cleaned_pages)
        if not chunks:
            raise PDFProcessingError("No meaningful text chunks could be created from this document.")

        texts = [c["text"] for c in chunks]
        vectors = embed_documents(texts)
        logger.info("Embedding generation completed for document %s (%d chunks)", document_id, len(chunks))

        faiss_positions = add_embeddings(vectors)
        save_index()
        logger.info("FAISS indexing completed for document %s", document_id)

        chunk_docs = [
            new_chunk_document(
                user_id=user_id,
                document_id=document_id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                text=c["text"],
                faiss_index=pos,
            )
            for c, pos in zip(chunks, faiss_positions)
        ]
        if chunk_docs:
            await db.chunks.insert_many(chunk_docs)

        await set_status(STATUS_PROCESSED, page_count=total_pages, error_message=None)
        logger.info("Document processing completed: %s (%d pages, %d chunks)", document_id, total_pages, len(chunks))

    except PDFProcessingError as exc:
        logger.warning("Document processing failed (PDF error) for %s: %s", document_id, exc)
        await set_status(STATUS_FAILED, error_message=str(exc))
    except Exception as exc:
        logger.error("Document processing failed (unexpected) for %s: %s", document_id, exc)
        await set_status(STATUS_FAILED, error_message="An unexpected error occurred while processing this document.")
