"""
Legal-BERT model wrapper.

This module is responsible ONLY for loading the Legal-BERT model
(`nlpaueb/legal-bert-base-uncased`) and turning text into embeddings
(numerical vectors). It knows nothing about clauses, risk, or search --
those live in services/.

The pretrained checkpoint has no classification head, so it does not
output labels such as "Payment" or "High Risk". It produces general
legal-domain representations, which Stage 3 uses for semantic search.

The model is loaded ONCE, when the backend process starts (see main.py's
startup event), and reused for every request.
"""

import logging
from typing import List

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger("legal_bert")

MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
MAX_TOKENS = 512  # BERT-base positional embedding limit
EMBEDDING_DIM = 768


class LegalBertModel:
    """
    Thin, testable wrapper around the Hugging Face Legal-BERT model.

        legal_bert_model.load()                     # once, at startup
        vecs = legal_bert_model.embed_batch([...])  # (n, 768) float32
    """

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        self._loaded = False

    def load(self) -> None:
        """Download (if needed) and load the tokenizer + model once."""
        if self._loaded:
            return
        logger.info("Loading Legal-BERT tokenizer/model: %s", self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()  # inference mode: disables dropout
        self._loaded = True
        logger.info("Legal-BERT loaded successfully on device=%s", self.device)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def tokenize_length(self, text: str) -> int:
        """Number of Legal-BERT tokens `text` would use (incl. special tokens)."""
        if not self._loaded:
            raise RuntimeError("LegalBertModel.load() must be called first")
        return len(self.tokenizer.encode(text, add_special_tokens=True))

    @torch.no_grad()
    def embed_batch(self, texts: List[str], batch_size: int = 8) -> np.ndarray:
        """
        Encode texts into L2-normalised 768-d vectors (float32).

        Each text is passed through Legal-BERT and the last hidden layer is
        mean-pooled over the real (non-padding) tokens. Vectors are then
        normalised to unit length, so the dot product of two vectors equals
        their cosine similarity.
        """
        if not self._loaded:
            raise RuntimeError("LegalBertModel.load() must be called first")
        if not texts:
            return np.zeros((0, EMBEDDING_DIM), dtype="float32")

        outputs: List[np.ndarray] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=MAX_TOKENS,
                padding=True,
            ).to(self.device)

            hidden = self.model(**inputs).last_hidden_state          # (b, seq, 768)
            mask = inputs["attention_mask"].unsqueeze(-1)            # (b, seq, 1)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            outputs.append(pooled.cpu().numpy().astype("float32"))

        return np.vstack(outputs)

    def embed_chunk(self, text: str) -> List[float]:
        """Single-text convenience wrapper (kept from Stage 1)."""
        return self.embed_batch([text])[0].tolist()


# Module-level singleton used by the rest of the backend.
legal_bert_model = LegalBertModel()
