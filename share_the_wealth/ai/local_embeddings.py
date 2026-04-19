"""
Local embedding model (sentence-transformers) — $0 API cost for RAG retrieval.

Default model: all-MiniLM-L6-v2 (~80MB first download, fast on CPU).
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from share_the_wealth.config import Settings


def is_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(Settings.ST_EMBEDDING_MODEL)


def encode_normalized(texts: list[str]) -> np.ndarray:
    """Return L2-normalized embeddings; cosine similarity = dot product."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = get_model()
    emb = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return np.asarray(emb, dtype=np.float32)
