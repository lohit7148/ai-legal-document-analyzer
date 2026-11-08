"""
Test setup. Real Legal-BERT is large, so tests replace only its *embedding*
step with a small deterministic stand-in (hashed bag-of-words vectors). All
other code -- preprocessing, chunking, FAISS, OCR, PDF reading, API routes --
runs for real. Tests therefore do not need internet access.
"""
import hashlib
import os
import re
import sys
import types

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DIM = 128


def fake_embed(texts):
    out = np.zeros((len(texts), DIM), dtype="float32")
    for i, text in enumerate(texts):
        for tok in re.findall(r"[a-z]+", text.lower()):
            out[i, int(hashlib.md5(tok.encode()).hexdigest(), 16) % DIM] += 1.0
        norm = np.linalg.norm(out[i]) or 1.0
        out[i] /= norm
    return out


try:  # real torch/transformers installed -> use the real wrapper object
    import torch  # noqa: F401
    import transformers  # noqa: F401
except Exception:  # sandbox without torch -> provide a minimal stand-in module
    stub = types.ModuleType("models.legal_bert")

    class _Stub:
        model_name = "nlpaueb/legal-bert-base-uncased"
        device = "cpu"
        _loaded = False
        is_loaded = False

    stub.legal_bert_model = _Stub()
    stub.MAX_TOKENS = 512
    stub.EMBEDDING_DIM = 768
    pkg = types.ModuleType("models")
    pkg.legal_bert = stub
    sys.modules["models"] = pkg
    sys.modules["models.legal_bert"] = stub


@pytest.fixture()
def fake_model(monkeypatch):
    from models.legal_bert import legal_bert_model as m
    monkeypatch.setattr(m, "_loaded", True, raising=False)
    try:  # stand-in object (no torch installed) has a plain attribute
        monkeypatch.setattr(m, "is_loaded", True)
    except AttributeError:  # real wrapper: is_loaded is a property reading _loaded
        pass
    monkeypatch.setattr(m, "embed_batch", lambda texts, batch_size=8: fake_embed(texts), raising=False)
    monkeypatch.setattr(m, "tokenize_length", lambda text: int(len(text.split()) / 0.75), raising=False)
    return m


@pytest.fixture()
def sample_text():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_documents", "sample_service_agreement.txt")
    with open(path, encoding="utf-8") as f:
        return f.read()
