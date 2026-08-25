"""
Embedding service.

Wraps a Sentence Transformers model (default: all-MiniLM-L6-v2). The model
is loaded once per process (module-level singleton) and reused for every
request - reloading it per-call would be extremely slow and wasteful.

Embeddings are L2-normalized so that FAISS IndexFlatIP (inner product)
behaves as cosine similarity.
"""
import threading

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("rag.embedding_service")

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                settings = get_settings()
                logger.info("Loading embedding model '%s' (first use)...", settings.embedding_model)
                _model = SentenceTransformer(settings.embedding_model)
                logger.info("Embedding model loaded")
    return _model


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12
    return vectors / norms


def embed_documents(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Embed a batch of chunk texts. Returns a normalized float32 (N, D) array."""
    if not texts:
        return np.zeros((0, embedding_dimension()), dtype="float32")
    model = _get_model()
    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
    vectors = _normalize(vectors.astype("float32"))
    return vectors


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string. Returns a normalized float32 (D,) array."""
    model = _get_model()
    vector = model.encode([text], convert_to_numpy=True)[0].astype("float32")
    vector = _normalize(vector.reshape(1, -1))[0]
    return vector


def embedding_dimension() -> int:
    model = _get_model()
    return model.get_sentence_embedding_dimension()
