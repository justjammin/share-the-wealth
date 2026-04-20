"""
Local RAG retriever using sentence-transformers for chunk similarity search.
No-ops gracefully when sentence-transformers is not installed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class _NullRetriever:
    def ensure_indexed(self, context: str) -> None:
        pass

    def retrieve(self, query: str) -> list[str]:
        return []


_instance: "_NullRetriever | _EmbeddingRetriever | None" = None


class _EmbeddingRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 512, top_k: int = 6):
        from sentence_transformers import SentenceTransformer
        import numpy as np
        self._model = SentenceTransformer(model_name)
        self._chunk_size = chunk_size
        self._top_k = top_k
        self._chunks: list[str] = []
        self._embeddings = None
        self._indexed_hash: int | None = None

    def ensure_indexed(self, context: str) -> None:
        import numpy as np
        h = hash(context)
        if h == self._indexed_hash:
            return
        words = context.split()
        self._chunks = [
            " ".join(words[i : i + self._chunk_size])
            for i in range(0, len(words), self._chunk_size)
        ]
        if self._chunks:
            self._embeddings = self._model.encode(self._chunks, convert_to_numpy=True)
        self._indexed_hash = h

    def retrieve(self, query: str) -> list[str]:
        import numpy as np
        if not self._chunks or self._embeddings is None:
            return []
        q_emb = self._model.encode([query], convert_to_numpy=True)
        scores = (self._embeddings @ q_emb.T).flatten()
        top_idx = scores.argsort()[::-1][: self._top_k]
        return [self._chunks[i] for i in top_idx]


def get_rag_retriever() -> "_EmbeddingRetriever | _NullRetriever":
    global _instance
    if _instance is None:
        try:
            from share_the_wealth.config import Settings
            from share_the_wealth.ai import local_embeddings
            if local_embeddings.is_available():
                _instance = _EmbeddingRetriever(top_k=Settings.RAG_TOP_K)
            else:
                _instance = _NullRetriever()
        except Exception:
            _instance = _NullRetriever()
    return _instance
