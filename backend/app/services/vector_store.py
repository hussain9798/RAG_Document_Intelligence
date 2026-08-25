"""
VectorStoreService - wraps a single global FAISS IndexFlatIP index.

MongoDB Atlas remains the source of truth for document/chunk/user/page
metadata (see app/models). FAISS is responsible only for storing vectors
and performing similarity search. The link between the two is the
integer `faiss_index` position, which is stored on each chunk document in
MongoDB.

The index (and a small local id-mapping file used for deletions) is
persisted to disk under storage/vector_indexes so the app can restart
without losing it.

Because FAISS's IndexFlatIP does not support true random-access deletion,
"deleting a document" is implemented via a tombstone set: vector positions
belonging to deleted chunks are recorded as deleted and excluded from
search results and from reuse. This keeps the FAISS-position -> chunk
mapping simple and never inconsistent. Periodic compaction (rebuilding the
index without tombstoned vectors) can be run offline if the index grows
too sparse; this is noted in the README as a possible future improvement.
"""
import json
import os
import threading

import faiss
import numpy as np

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("rag.vector_store")

_index: faiss.Index | None = None
_deleted_positions: set[int] = set()
_lock = threading.Lock()


def _paths() -> tuple[str, str]:
    settings = get_settings()
    os.makedirs(settings.vector_db_dir, exist_ok=True)
    index_path = os.path.join(settings.vector_db_dir, "global.index")
    meta_path = os.path.join(settings.vector_db_dir, "metadata.json")
    return index_path, meta_path


def _load() -> None:
    global _index, _deleted_positions
    index_path, meta_path = _paths()
    settings = get_settings()

    if os.path.exists(index_path):
        _index = faiss.read_index(index_path)
        logger.info("Loaded FAISS index with %d vectors from %s", _index.ntotal, index_path)
    else:
        from app.services.embedding_service import embedding_dimension

        dim = embedding_dimension()
        _index = faiss.IndexFlatIP(dim)
        logger.info("Created new FAISS IndexFlatIP (dim=%d)", dim)

    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            data = json.load(f)
            _deleted_positions = set(data.get("deleted_positions", []))
    else:
        _deleted_positions = set()


def _ensure_loaded() -> None:
    if _index is None:
        with _lock:
            if _index is None:
                _load()


def save_index() -> None:
    """Persist the current index + tombstone metadata to disk."""
    _ensure_loaded()
    index_path, meta_path = _paths()
    with _lock:
        faiss.write_index(_index, index_path)
        with open(meta_path, "w") as f:
            json.dump({"deleted_positions": sorted(_deleted_positions)}, f)
    logger.info("FAISS index saved (%d total vectors, %d tombstoned)", _index.ntotal, len(_deleted_positions))


def add_embeddings(vectors: np.ndarray) -> list[int]:
    """
    Add a batch of (already normalized) vectors to the index.
    Returns the list of FAISS positions assigned to them, in order.
    """
    _ensure_loaded()
    with _lock:
        start_pos = _index.ntotal
        _index.add(vectors)
        end_pos = _index.ntotal
    positions = list(range(start_pos, end_pos))
    return positions


def search(query_vector: np.ndarray, top_k: int) -> list[tuple[int, float]]:
    """
    Search for the top_k most similar vectors to query_vector.
    Returns a list of (faiss_position, score) tuples, excluding tombstoned
    positions, sorted by descending score.
    """
    _ensure_loaded()
    if _index.ntotal == 0:
        return []

    # Over-fetch to account for tombstoned results getting filtered out
    fetch_k = min(_index.ntotal, top_k + len(_deleted_positions) + 10)
    query = query_vector.reshape(1, -1).astype("float32")

    with _lock:
        scores, positions = _index.search(query, fetch_k)

    results = []
    for pos, score in zip(positions[0], scores[0]):
        if pos == -1 or pos in _deleted_positions:
            continue
        results.append((int(pos), float(score)))
        if len(results) >= top_k:
            break
    return results


def delete_positions(positions: list[int]) -> None:
    """Tombstone the given FAISS positions so they're excluded from future searches."""
    _ensure_loaded()
    with _lock:
        _deleted_positions.update(positions)
    save_index()
    logger.info("Tombstoned %d FAISS vector positions", len(positions))


def load_index() -> None:
    """Force a (re)load from disk. Mainly useful for tests / startup warmup."""
    global _index
    with _lock:
        _index = None
    _load()
