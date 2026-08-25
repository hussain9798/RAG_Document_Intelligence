"""
Mongo 'chunks' collection shape.

Each chunk record stores its own embedding vector directly (used by
MongoDB Atlas Vector Search on the "embedding" field). This removes the
need for a separate local FAISS index / faiss_index position mapping.
"""
from datetime import datetime, timezone


def new_chunk_document(
    user_id, document_id, chunk_index: int, page_number: int, text: str, embedding: list[float]
) -> dict:
    return {
        "user_id": user_id,
        "document_id": document_id,
        "chunk_index": chunk_index,
        "page_number": page_number,
        "text": text,
        "embedding": embedding,
        "created_at": datetime.now(timezone.utc),
    }