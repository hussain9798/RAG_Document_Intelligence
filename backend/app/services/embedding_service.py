"""
Embedding service.

Uses Google's Gemini embedding API (models/gemini-embedding-001) instead of a
locally-loaded model. This keeps the app's memory footprint small enough to
run comfortably on Render's free tier - no torch / sentence-transformers
loaded into memory.
"""
import time

import google.generativeai as genai
import numpy as np

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("rag.embedding_service")

_configured = False

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM = 768


def _ensure_configured() -> None:
    global _configured
    if not _configured:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set (or is empty) in the environment. "
                "Set it in Render's Environment tab."
            )
        import os

        os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True


def _embed_batch(texts: list[str], task_type: str) -> list[list[float]]:
    """
    Calls the Gemini embedding API in small batches, with one retry on
    transient failures (the free tier can rate-limit under bursty traffic).
    """
    _ensure_configured()
    vectors: list[list[float]] = []
    batch_size = 20

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=batch,
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIM,
            )
        except Exception:
            logger.warning("Gemini embedding call failed, retrying once...")
            time.sleep(2)
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=batch,
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIM,
            )

        embeddings = result["embedding"]
        if batch and isinstance(embeddings[0], float):
            embeddings = [embeddings]
        vectors.extend(embeddings)

    return vectors


def embed_documents(texts: list[str], batch_size: int = 20) -> np.ndarray:
    """Embed a batch of chunk texts for storage. Returns a float32 (N, D) array."""
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")
    vectors = _embed_batch(texts, task_type="retrieval_document")
    return np.array(vectors, dtype="float32")


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string for search. Returns a float32 (D,) array."""
    vectors = _embed_batch([text], task_type="retrieval_query")
    return np.array(vectors[0], dtype="float32")


def embedding_dimension() -> int:
    return EMBEDDING_DIM