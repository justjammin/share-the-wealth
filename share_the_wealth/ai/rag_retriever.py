"""
Chunk DB-derived context, embed with sentence-transformers, retrieve top-k by cosine similarity.
"""

from __future__ import annotations

import numpy as np

from . import local_embeddings
from share_the_wealth.config import Settings


def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_chars:
            parts.append(remaining.strip())
            break
        chunk = remaining[:max_chars]
        break_at = max(chunk.rfind("\n"), chunk.rfind(" "))
        if break_at > max_chars // 2:
            chunk = remaining[:break_at]
        parts.append(chunk.strip())
        remaining = remaining[len(chunk) :].lstrip()
    return [p for p in parts if p]


class RAGRetriever:
    """In-process index; rebuild when context string changes (hash cache)."""

    def __init__(self) -> None:
        self._ctx_hash: int | None = None
        self._chunks: list[str] = []
        self._emb: np.ndarray | None = None

    def ensure_indexed(self, full_text: str) -> None:
        h = hash(full_text)
        if h == self._ctx_hash and self._chunks:
            return
        self._chunks = chunk_text(full_text)
        if not self._chunks:
            self._chunks = [full_text[:4000]] if full_text.strip() else ["(no portfolio data)"]
        self._ctx_hash = h
        if not Settings.USE_LOCAL_RAG or not local_embeddings.is_available():
            self._emb = None
            return
        try:
            self._emb = local_embeddings.encode_normalized(self._chunks)
        except Exception:
            self._emb = None

    def retrieve(self, query: str, top_k: int | None = None) -> list[str]:
        k = top_k if top_k is not None else Settings.RAG_TOP_K
        k = max(1, k)
        if not self._chunks:
            return []
        if self._emb is None or not query.strip():
            return self._chunks[:k]
        try:
            q = local_embeddings.encode_normalized([query.strip()])
            sims = (q @ self._emb.T).flatten()
            idx = np.argsort(-sims)[:k]
            return [self._chunks[i] for i in idx]
        except Exception:
            return self._chunks[:k]


_retriever: RAGRetriever | None = None


def get_rag_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever
