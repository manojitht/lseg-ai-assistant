"""
Retriever — embeds a query and searches the FAISS index.

Returns (documents, scores) so the caller (assistant.py) can apply
confidence thresholds and build citations without coupling to FAISS internals.
"""
from __future__ import annotations

from src import config
from src.embeddings import bedrock_embeddings
from src.ingestion.document_loader import Document
from src.vector_store.faiss_store import FaissStore


class Retriever:
    def __init__(self, store: FaissStore) -> None:
        self._store = store

    def retrieve(self, query: str, top_k: int = config.TOP_K) -> tuple[list[Document], list[float]]:
        """
        Embed the query, run k-NN search, return (docs, similarity_scores).
        Scores are cosine similarities in [0, 1]; higher = more relevant.
        """
        query_vec = bedrock_embeddings.embed(query)
        results   = self._store.search(query_vec, top_k=top_k)
        if not results:
            return [], []
        docs, scores = zip(*results)
        return list(docs), list(scores)
