"""
FastAPI application entry point for the AI-Powered Legal Document Analyzer
(Stages 1-6: text/PDF/image input, Legal-BERT, FAISS search, Q&A, advanced
summary + risk scoring; voice is handled in the browser).

Endpoints:
    GET  /                  -> basic API info
    GET  /health            -> health check + model / OCR / index status
    POST /api/extract-text  -> Stage 2: upload PDF/image, get extracted text
    POST /api/analyze       -> analyse submitted text (also builds the index)
    POST /api/search        -> Stage 3: semantic search in an analysed document

Run with:   uvicorn main:app --reload
Swagger:    http://127.0.0.1:8000/docs
"""

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from models.legal_bert import legal_bert_model
from schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExtractResponse,
    HealthResponse,
    SearchHit,
    AskRequest,
    AskResponse,
    AiSummaryRequest,
    AiSummaryResponse,
    SearchRequest,
    SearchResponse,
)
from services import ocr, vector_store, llm, qa, advanced_summary
from services.analyzer import AnalysisError, analyze_document
from services.document_loader import MAX_FILE_BYTES, ExtractionError, extract_from_bytes
from services.semantic_search import SIMILARITY_NOTE, SearchError, search_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

app = FastAPI(
    title="AI-Powered Legal Document Analyzer",
    description="Stage 3: text/PDF/image input, Legal-BERT embeddings, FAISS semantic search.",
    version="6.0.0",
)

# ---------------------------------------------------------------------------
# CORS -- allow the local Vite dev server (and devices on the same local
# network, e.g. a Raspberry Pi opening the dashboard) to talk to this API.
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"http://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+):5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_model_on_startup() -> None:
    """
    Load Legal-BERT exactly once, when the server process starts.
    The first run may take a while because Hugging Face needs to download
    the model weights -- see README.md.
    """
    try:
        logger.info("Startup: loading Legal-BERT model...")
        legal_bert_model.load()
        logger.info("Startup: Legal-BERT model loaded and ready.")
    except Exception as exc:
        logger.error("Failed to load Legal-BERT model at startup: %s", exc)


@app.get("/")
def root():
    return {
        "name": "AI-Powered Legal Document Analyzer API",
        "stage": 6,
        "docs": "/docs",
        "health": "/health",
        "endpoints": ["/api/extract-text", "/api/analyze", "/api/search", "/api/ask", "/api/ai-summary"],
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok" if legal_bert_model.is_loaded else "degraded",
        model_loaded=legal_bert_model.is_loaded,
        model_name=legal_bert_model.model_name,
        ocr_available=ocr.is_available(),
        vector_backend=vector_store.BACKEND_NAME,
        llm_configured=llm.is_configured(),
        llm_provider=llm.describe(),
    )


@app.post("/api/extract-text", response_model=ExtractResponse)
def extract_text(file: UploadFile = File(...)):
    """Stage 2: read text from an uploaded PDF or image (OCR when needed)."""
    data = file.file.read(MAX_FILE_BYTES + 1)
    try:
        result = extract_from_bytes(file.filename or "", data)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error while extracting text")
        raise HTTPException(status_code=500, detail="The file could not be processed. Please try another file.")

    return ExtractResponse(
        filename=file.filename or "",
        source_type=result.source_type,
        pages=result.pages,
        method=result.method,
        ocr_used=result.ocr_used,
        characters=len(result.text),
        text=result.text,
        warnings=result.warnings,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    if not legal_bert_model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail=(
                "The Legal-BERT model is not loaded yet. If the server just "
                "started, it may still be downloading the model -- please "
                "wait a moment and try again."
            ),
        )
    try:
        return analyze_document(request.text)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:  # pragma: no cover
        logger.exception("Unexpected error during analysis")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while analyzing the document. Please try again.",
        )


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """Stage 3: semantic search over the passages of an analysed document."""
    try:
        hits = search_document(request.document_id, request.query, request.top_k)
    except SearchError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:  # pragma: no cover
        logger.exception("Unexpected error during search")
        raise HTTPException(status_code=500, detail="The search failed. Please try again.")

    return SearchResponse(
        document_id=request.document_id,
        query=request.query.strip(),
        top_k=request.top_k,
        backend=vector_store.BACKEND_NAME,
        similarity_note=SIMILARITY_NOTE,
        results=[SearchHit(**h) for h in hits],
    )


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Stage 4: answer a question about an analysed document (RAG; LLM optional)."""
    try:
        return AskResponse(**qa.answer_question(request.document_id, request.question, request.top_k))
    except qa.QAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:  # pragma: no cover
        logger.exception("Unexpected error during question answering")
        raise HTTPException(status_code=500, detail="The question could not be answered. Please try again.")


@app.post("/api/ai-summary", response_model=AiSummaryResponse)
def ai_summary(request: AiSummaryRequest):
    """Stage 5: plain-English summary (LLM if configured, else extractive key sentences)."""
    entry = vector_store.get(request.document_id)
    if entry is None:
        raise HTTPException(status_code=400, detail="This document is no longer indexed. Please analyze the document again.")
    return AiSummaryResponse(**advanced_summary.ai_summary(entry.key_sentences or [], entry.facts))
