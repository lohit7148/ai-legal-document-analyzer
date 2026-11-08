"""
Semantic search (Stage 3): find the passages of the analysed document that
are closest in meaning to a free-text query, using Legal-BERT embeddings and
the FAISS index built during analysis.
"""

from typing import Dict, List

from models.legal_bert import legal_bert_model
from services import vector_store

SIMILARITY_NOTE = (
    "Similarity is the cosine similarity (-1 to 1) between the Legal-BERT embedding of your "
    "query and of each passage. It is a ranking aid, not a probability. Legal-BERT is not "
    "fine-tuned for sentence similarity, so always read the passage itself."
)


class SearchError(Exception):
    """User-facing search problem (unknown document, empty query...)."""


def search_document(document_id: str, query: str, top_k: int) -> List[Dict]:
    query = (query or "").strip()
    if not query:
        raise SearchError("Please enter a search query.")
    entry = vector_store.get(document_id)
    if entry is None:
        raise SearchError("This document is no longer indexed. Please analyze the document again.")
    if not legal_bert_model.is_loaded:
        raise SearchError("The Legal-BERT model is not loaded yet.")

    query_vec = legal_bert_model.embed_batch([query])[0]
    return entry.search(query_vec, top_k)
