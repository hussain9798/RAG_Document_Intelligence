"""
Retrieval service.

Given a question and an authenticated user_id, this is the only place that
turns a FAISS search into MongoDB-backed, user-scoped source chunks. It is
the enforcement point for user isolation: chunks belonging to other users
are filtered out even if (hypothetically) a stray vector search hit them.
"""
from bson import ObjectId

from app.config import get_settings
from app.database.mongodb import get_database
from app.services.embedding_service import embed_query
from app.services.vector_store import search as faiss_search
from app.utils.logger import get_logger

logger = get_logger("rag.retrieval_service")


async def retrieve_relevant_chunks(
    user_id: str, question: str, document_ids: list[str] | None = None
) -> list[dict]:
    """
    Returns a list of source dicts:
    {chunk_id, document_id, document_name, page_number, score, text}
    sorted by descending similarity score, filtered to the authenticated
    user's own documents and respecting the configured similarity threshold.
    """
    settings = get_settings()
    db = get_database()

    query_vector = embed_query(question)

    # Over-fetch from FAISS since we still need to apply the user/document
    # filter and the similarity threshold in MongoDB.
    raw_hits = faiss_search(query_vector, top_k=settings.top_k * 4)
    if not raw_hits:
        return []

    faiss_positions = [pos for pos, _ in raw_hits]
    score_by_position = {pos: score for pos, score in raw_hits}

    mongo_query: dict = {"user_id": user_id, "faiss_index": {"$in": faiss_positions}}
    if document_ids:
        mongo_query["document_id"] = {"$in": document_ids}

    cursor = db.chunks.find(mongo_query)
    chunk_docs = [c async for c in cursor]

    if not chunk_docs:
        return []

    doc_ids = list({c["document_id"] for c in chunk_docs})
    doc_object_ids = [ObjectId(d) for d in doc_ids]
    documents = await db.documents.find({"_id": {"$in": doc_object_ids}, "user_id": user_id}).to_list(length=None)
    doc_name_by_id = {str(d["_id"]): d["filename"] for d in documents}

    results = []
    for chunk in chunk_docs:
        # Defensive re-check: only include chunks whose parent document also
        # belongs to this user (guards against any stale/foreign metadata).
        if chunk["document_id"] not in doc_name_by_id:
            continue
        score = score_by_position.get(chunk["faiss_index"])
        if score is None or score < settings.similarity_threshold:
            continue
        results.append(
            {
                "chunk_id": str(chunk["_id"]),
                "document_id": chunk["document_id"],
                "document_name": doc_name_by_id[chunk["document_id"]],
                "page_number": chunk["page_number"],
                "score": round(score, 4),
                "text": chunk["text"],
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    top = results[: settings.top_k]
    logger.info("Retrieval for user %s returned %d chunks (threshold=%s)", user_id, len(top), settings.similarity_threshold)
    return top
