import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(fake_model):
    import main
    return TestClient(main.app)  # not used as a context manager -> startup (model download) is skipped


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["stage"] == 6 and "vector_backend" in body


def test_analyze_sample_builds_index(client, sample_text):
    r = client.post("/api/analyze", json={"text": sample_text})
    assert r.status_code == 200
    body = r.json()
    assert body["document_id"]
    assert body["search_index"]["available"] and body["search_index"]["passages"] >= 2
    assert sum(c["detected"] for c in body["clauses"]) == 14
    assert "₹250000" in body["key_information"]["payment_amounts"]


def test_analyze_is_not_hardcoded(client, sample_text):
    r = client.post("/api/analyze", json={"text": sample_text.replace("₹250000", "₹500000")})
    assert "₹500000" in r.json()["key_information"]["payment_amounts"]


def test_analyze_empty_and_short(client):
    assert client.post("/api/analyze", json={"text": "   "}).status_code == 400
    assert client.post("/api/analyze", json={"text": "too short"}).status_code == 400


def test_semantic_search_finds_relevant_passage(client, sample_text):
    doc_id = client.post("/api/analyze", json={"text": sample_text}).json()["document_id"]
    r = client.post("/api/search", json={"document_id": doc_id, "query": "late payment penalty per month", "top_k": 3})
    assert r.status_code == 200
    results = r.json()["results"]
    assert 1 <= len(results) <= 3
    assert results[0]["rank"] == 1
    assert "penalty" in results[0]["text"].lower()
    sims = [h["similarity"] for h in results]
    assert sims == sorted(sims, reverse=True)


def test_search_errors(client):
    assert client.post("/api/search", json={"document_id": "nope", "query": "x"}).status_code == 400
    assert client.post("/api/search", json={"document_id": "nope", "query": ""}).status_code == 422


def _make_pdf(text: str) -> bytes:
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(50, 50, 550, 750), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def test_extract_text_layer_pdf(client):
    pdf = _make_pdf("This Agreement shall be governed by the laws of India. The Client shall pay a fee of Rs. 5000 per month to the Provider.")
    r = client.post("/api/extract-text", files={"file": ("a.pdf", pdf, "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    assert body["method"] == "text-layer" and not body["ocr_used"]
    assert "laws of India" in body["text"]


def test_extract_rejects_bad_files(client):
    assert client.post("/api/extract-text", files={"file": ("a.txt", b"hello", "text/plain")}).status_code == 400
    assert client.post("/api/extract-text", files={"file": ("a.pdf", b"not a pdf", "application/pdf")}).status_code == 400
    assert client.post("/api/extract-text", files={"file": ("a.pdf", b"", "application/pdf")}).status_code == 400


def test_ocr_on_image_and_scanned_pdf(client):
    pytest.importorskip("rapidocr_onnxruntime")
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1000, 260), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    d.text((30, 40), "The Client shall pay fees monthly.", fill="black", font=font)
    d.text((30, 130), "This Agreement is governed by Indian law.", fill="black", font=font)
    buf = io.BytesIO(); img.save(buf, format="PNG")

    r = client.post("/api/extract-text", files={"file": ("scan.png", buf.getvalue(), "image/png")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ocr_used"] and body["method"] == "ocr"
    assert "shall pay" in body["text"].lower()

    # scanned PDF = a PDF page that only contains an image
    import pymupdf
    doc = pymupdf.open(); page = doc.new_page()
    page.insert_image(pymupdf.Rect(40, 40, 555, 200), stream=buf.getvalue())
    pdf = doc.tobytes(); doc.close()
    r2 = client.post("/api/extract-text", files={"file": ("scan.pdf", pdf, "application/pdf")})
    assert r2.status_code == 200, r2.text
    assert r2.json()["ocr_used"] and "governed" in r2.json()["text"].lower()


# ---------------------------------------------------------------------------
# Stage 4: question answering
# ---------------------------------------------------------------------------

def _doc_id(client, sample_text):
    return client.post("/api/analyze", json={"text": sample_text}).json()["document_id"]


def test_ask_retrieval_only_without_llm(client, sample_text, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    r = client.post("/api/ask", json={"document_id": _doc_id(client, sample_text), "question": "late payment penalty per month"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "retrieval-only" and body["provider"] is None
    assert body["sources"] and "penalty" in body["answer"].lower()
    assert "No LLM" in body["note"]


def test_ask_uses_llm_and_grounds_prompt(client, sample_text, monkeypatch):
    from services import llm
    seen = {}

    def fake_generate(system, user):
        seen["system"], seen["user"] = system, user
        return "The penalty is 2% per month [1]."

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setattr(llm, "generate", fake_generate)
    r = client.post("/api/ask", json={"document_id": _doc_id(client, sample_text), "question": "late payment penalty"})
    body = r.json()
    assert body["mode"] == "llm" and body["answer"].startswith("The penalty")
    assert "ONLY the numbered passages" in seen["system"]
    assert "Passages:\n[1]" in seen["user"] and "Question: late payment penalty" in seen["user"]


def test_ask_falls_back_when_llm_fails(client, sample_text, monkeypatch):
    from services import llm

    def boom(system, user):
        raise llm.LLMError("The LLM service could not be reached.")

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setattr(llm, "generate", boom)
    body = client.post("/api/ask", json={"document_id": _doc_id(client, sample_text), "question": "termination notice"}).json()
    assert body["mode"] == "retrieval-only" and "could not be reached" in body["note"]


def test_ask_errors(client):
    assert client.post("/api/ask", json={"document_id": "nope", "question": "x"}).status_code == 400
    assert client.post("/api/ask", json={"document_id": "nope", "question": ""}).status_code == 422


# ---------------------------------------------------------------------------
# Stage 5: key sentences, semantic candidates, risk score, AI summary
# ---------------------------------------------------------------------------

def test_key_sentences_are_real_sentences(client, sample_text):
    body = client.post("/api/analyze", json={"text": sample_text}).json()
    ks = body["key_sentences"]
    assert 1 <= len(ks) <= 5
    assert [k["sentence_index"] for k in ks] == sorted(k["sentence_index"] for k in ks)
    flat = " ".join(sample_text.split())
    assert all(" ".join(k["text"].split()) in flat for k in ks)


def test_semantic_candidates_do_not_change_detection(client, sample_text):
    body = client.post("/api/analyze", json={"text": sample_text}).json()
    assert all(c["semantic_sentence"] for c in body["clauses"])
    assert sum(c["detected"] for c in body["clauses"]) == 14
    no_term = "\n".join(l for l in sample_text.splitlines() if "terminate" not in l.lower() and "TERMINATION" not in l)
    body2 = client.post("/api/analyze", json={"text": no_term}).json()
    term = next(c for c in body2["clauses"] if c["clause_name"] == "Termination")
    assert term["detected"] is False and term["detection_indicator"] == "Not Detected"
    assert term["semantic_similarity"] is not None  # candidate shown, but still Not Detected


def test_risk_score_is_transparent(client, sample_text):
    rs = client.post("/api/analyze", json={"text": sample_text}).json()["risk_score"]
    assert 0 <= rs["score"] <= 100 and rs["level"] in {"LOW", "MEDIUM", "HIGH"}
    assert "score = min(100" in rs["formula"]
    assert rs["score"] == min(100, sum(c["points"] for c in rs["components"]))


def test_missing_clause_and_numeric_checks(client):
    text = ("This Agreement is between ABC Technologies Pvt. Ltd. and XYZ Solutions Pvt. Ltd. "
            "A late payment penalty of 5% per month shall apply to unpaid invoices. "
            "Either party may terminate this Agreement with 7 days written notice.")
    body = client.post("/api/analyze", json={"text": text}).json()
    rs = body["risk_score"]
    assert "Liability" in rs["missing_clause_checks"] and "Governing Law" in rs["missing_clause_checks"]
    reasons = " ".join(r["reason"] for r in body["risk_indicators"])
    assert "3% or more" in reasons and "only 7 days" in reasons


def test_ai_summary_extractive_without_llm(client, sample_text, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    r = client.post("/api/ai-summary", json={"document_id": _doc_id(client, sample_text)})
    assert r.status_code == 200 and r.json()["mode"] == "extractive" and r.json()["text"]
    assert client.post("/api/ai-summary", json={"document_id": "nope"}).status_code == 400


def test_health_reports_llm_status(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    body = client.get("/health").json()
    assert body["llm_configured"] is False and body["llm_provider"] == "none"
