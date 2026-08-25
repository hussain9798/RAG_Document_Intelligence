"""
Retrieval service.

Given a question and an authenticated user_id, this is the only place that
turns a MongoDB Atlas Vector Search query into user-scoped source chunks.
It is the enforcement point for user isolation: the vector search itself
is pre-filtered to the requesting user's own chunks.
"""
from bson import ObjectId

from app.config import get_settings
from app.database.mongodb import get_database
from app.services.embedding_service import embed_query
from app.utils.logger import get_logger

logger = get_logger("rag.retrieval_service")

VECTOR_INDEX_NAME = "chunk_vector_index"


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

    query_vector = embed_query(question).tolist()

    vector_filter: dict = {"user_id": {"$eq": user_id}}
    if document_ids:
        vector_filter = {"$and": [vector_filter, {"document_id": {"$in": document_ids}}]}

    fetch_limit = settings.top_k * 4
    num_candidates = max(fetch_limit * 10, 150)

    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": num_candidates,
                "limit": fetch_limit,
                "filter": vector_filter,
            }
        },
        {
            "$project": {
                "_id": 1,
                "document_id": 1,
                "page_number": 1,
                "text": 1,
                "atlas_score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    chunk_docs = [c async for c in db.chunks.aggregate(pipeline)]
    if not chunk_docs:
        return []

    doc_ids = list({c["document_id"] for c in chunk_docs})
    doc_object_ids = [ObjectId(d) for d in doc_ids]
    documents = await db.documents.find({"_id": {"$in": doc_object_ids}, "user_id": user_id}).to_list(length=None)
    doc_name_by_id = {str(d["_id"]): d["filename"] for d in documents}

    results = []
    for chunk in chunk_docs:
        if chunk["document_id"] not in doc_name_by_id:
            continue
        # Atlas cosine vectorSearchScore = (1 + cosine_similarity) / 2, in [0, 1].
        # Convert back to raw cosine so similarity_threshold keeps its old meaning.
        cosine_score = 2 * chunk["atlas_score"] - 1
        if cosine_score < settings.similarity_threshold:
            continue
        results.append(
            {
                "chunk_id": str(chunk["_id"]),
                "document_id": chunk["document_id"],
                "document_name": doc_name_by_id[chunk["document_id"]],
                "page_number": chunk["page_number"],
                "score": round(cosine_score, 4),
                "text": chunk["text"],
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    top = results[: settings.top_k]
    logger.info(
        "Retrieval for user %s returned %d chunks (threshold=%s)", user_id, len(top), settings.similarity_threshold
    )
    return top