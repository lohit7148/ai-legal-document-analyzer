"""
Vector store (Stage 3): keeps one semantic index per analysed document.

FAISS (IndexFlatIP) is used when installed. Because Legal-BERT embeddings are
L2-normalised, the inner product equals cosine similarity. If FAISS cannot be
imported (e.g. install problems), a NumPy matrix product gives identical
results, so the app still works -- the `backend` field reports which was used.

Indexes live in memory only (a small LRU cache); nothing is written to disk.
"""

import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from services.preprocessing import Chunk

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:  # pragma: no cover
    faiss = None
    FAISS_AVAILABLE = False

MAX_DOCUMENTS = 8
BACKEND_NAME = "faiss" if FAISS_AVAILABLE else "numpy-fallback"


@dataclass
class DocumentIndex:
    passages: List[Chunk]
    embeddings: np.ndarray
    index: Optional[object] = None
    key_sentences: Optional[List[str]] = None   # Stage 5: for the AI summary
    facts: str = ""

    def __post_init__(self):
        self.embeddings = np.ascontiguousarray(self.embeddings, dtype="float32")
        if FAISS_AVAILABLE and len(self.embeddings):
            self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
            self.index.add(self.embeddings)

    def search(self, query_vec: np.ndarray, top_k: int) -> List[Dict]:
        n = len(self.passages)
        if n == 0:
            return []
        k = min(top_k, n)
        q = np.ascontiguousarray(query_vec.reshape(1, -1), dtype="float32")
        if self.index is not None:
            scores, ids = self.index.search(q, k)
            pairs = list(zip(ids[0].tolist(), scores[0].tolist()))
        else:
            sims = (self.embeddings @ q[0])
            order = np.argsort(-sims)[:k]
            pairs = [(int(i), float(sims[i])) for i in order]

        hits = []
        for rank, (idx, score) in enumerate(pairs, start=1):
            if idx < 0:
                continue
            p = self.passages[idx]
            hits.append({"rank": rank, "passage_index": p.index, "text": p.text,
                         "sentence_start": p.sentence_start, "sentence_end": p.sentence_end,
                         "similarity": round(float(score), 4)})
        return hits


_registry: "OrderedDict[str, DocumentIndex]" = OrderedDict()
_lock = threading.Lock()


def register(passages: List[Chunk], embeddings: np.ndarray, key_sentences=None, facts: str = "") -> str:
    """Store a new index and return its document_id."""
    doc_id = uuid.uuid4().hex[:12]
    entry = DocumentIndex(passages=passages, embeddings=embeddings, key_sentences=key_sentences, facts=facts)
    with _lock:
        _registry[doc_id] = entry
        while len(_registry) > MAX_DOCUMENTS:
            _registry.popitem(last=False)
    return doc_id


def get(doc_id: str) -> Optional[DocumentIndex]:
    with _lock:
        entry = _registry.get(doc_id)
        if entry is not None:
            _registry.move_to_end(doc_id)
        return entry
