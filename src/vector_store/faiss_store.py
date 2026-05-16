"""
FAISS vector store — build, persist, load, and search.

Uses IndexFlatIP (inner product) over unit-normalised vectors, which is
equivalent to cosine similarity. Scores are in [0, 1] after normalisation.

Production replacement: Amazon OpenSearch Serverless with k-NN plugin.
The retriever interface (search → list[tuple[Document, float]]) is identical;
only this module needs to be swapped. See infra/opensearch_setup.py.
"""
from __future__ import annotations

import os
import pickle
from pathlib import Path

import faiss
import numpy as np

from src.ingestion.document_loader import Document


class FaissStore:
    def __init__(self, dim: int) -> None:
        self.dim   = dim
        self.index = faiss.IndexFlatIP(dim)   # inner product = cosine on unit vecs
        self.docs:  list[Document] = []


    def add(self, docs: list[Document], embeddings: list[list[float]]) -> None:
        """Add documents + their embeddings to the index."""
        vecs = np.array(embeddings, dtype=np.float32)
        # Normalise to unit length so inner product == cosine similarity
        faiss.normalize_L2(vecs)
        self.index.add(vecs)
        self.docs.extend(docs)


    def search(self, query_vec: list[float], top_k: int) -> list[tuple[Document, float]]:
        """Return (document, cosine_similarity) pairs sorted descending by score."""
        vec = np.array([query_vec], dtype=np.float32)
        faiss.normalize_L2(vec)
        scores, indices = self.index.search(vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.docs[idx], float(score)))
        return results


    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, f"{path}.index")
        with open(f"{path}.docs", "wb") as f:
            pickle.dump(self.docs, f)

    @classmethod
    def load(cls, path: str) -> "FaissStore":
        index = faiss.read_index(f"{path}.index")
        with open(f"{path}.docs", "rb") as f:
            docs = pickle.load(f)
        store      = cls(dim=index.d)
        store.index = index
        store.docs  = docs
        return store

    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(f"{path}.index") and os.path.exists(f"{path}.docs")

    def __len__(self) -> int:
        return self.index.ntotal
