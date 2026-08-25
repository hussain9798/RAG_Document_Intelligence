"""
Mongo 'chunks' collection shape.

Each chunk record is the single link in the chain:
    User -> Document -> Page -> Chunk -> FAISS Vector
`faiss_index` is the integer position of this chunk's vector inside the
FAISS index, and must stay in sync with services/vector_store.py.
"""
from datetime import datetime, timezone


def new_chunk_document(
    user_id, document_id, chunk_index: int, page_number: int, text: str, faiss_index: int
) -> dict:
    return {
        "user_id": user_id,
        "document_id": document_id,
        "chunk_index": chunk_index,
        "page_number": page_number,
        "text": text,
        "faiss_index": faiss_index,
        "created_at": datetime.now(timezone.utc),
    }
