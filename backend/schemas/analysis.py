"""
Pydantic models (schemas) used by the FastAPI application.

These define the shape of requests coming into the API and the
shape of responses going out. Keeping them in one place makes it
easy to see the full "contract" of the API at a glance, and makes
it easy to extend in later stages (Stage 2+).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Body of POST /api/analyze"""
    text: str = Field(
        ...,
        description="Raw legal document text pasted/typed by the user.",
        min_length=1,
    )


# ---------------------------------------------------------------------------
# Response sub-models
# ---------------------------------------------------------------------------

class DocumentStats(BaseModel):
    characters: int
    words: int
    sentences: int
    chunks_processed: int = 0


class ModelInfo(BaseModel):
    name: str
    task: str = "Legal-domain language representation (embeddings)"
    device: str = "cpu"


class KeyInformation(BaseModel):
    parties: List[str] = []
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    other_dates: List[str] = []
    payment_amounts: List[str] = []
    penalties: List[str] = []
    percentages: List[str] = []
    contract_duration: Optional[str] = None
    renewal: Optional[str] = None
    termination_notice: Optional[str] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    dispute_resolution: Optional[str] = None


class ClauseResult(BaseModel):
    clause_name: str
    detected: bool
    detected_text: Optional[str] = None
    source_sentence: Optional[str] = None
    detection_indicator: str  # "Detected" | "Not Detected" | "Potential Indicator"
    position: Optional[int] = None  # sentence index in the document
    # Stage 5: closest sentence by Legal-BERT similarity (supplementary, NOT a detection)
    semantic_sentence: Optional[str] = None
    semantic_position: Optional[int] = None
    semantic_similarity: Optional[float] = None


class RiskIndicator(BaseModel):
    category: str
    level: str  # LOW | MEDIUM | HIGH
    reason: str
    evidence: str
    source_text: str


class DocumentSummary(BaseModel):
    overview: str
    parties: str
    main_purpose: str
    services: str
    payment: str
    contract_duration: str
    termination: str
    renewal: str
    important_obligations: str
    governing_law: str
    risk_overview: str


class ClauseExplanation(BaseModel):
    clause_name: str
    legal_text: str
    simple_english: str


class SearchIndexInfo(BaseModel):
    """Describes the Stage 3 semantic index built for the analysed document."""
    available: bool
    passages: int = 0
    embedding_dim: int = 0
    backend: str = "none"  # "faiss" or "numpy-fallback"


class KeySentence(BaseModel):
    rank: int
    sentence_index: int
    text: str
    centrality: float  # cosine similarity to the document's mean Legal-BERT embedding


class RiskComponent(BaseModel):
    name: str
    points: int
    detail: str


class RiskScore(BaseModel):
    score: int
    level: str
    formula: str
    components: List[RiskComponent] = []
    missing_clause_checks: List[str] = []


class AnalyzeResponse(BaseModel):
    document_id: Optional[str] = None
    search_index: SearchIndexInfo = SearchIndexInfo(available=False)
    document_stats: DocumentStats
    model: ModelInfo
    key_information: KeyInformation
    clauses: List[ClauseResult]
    risk_indicators: List[RiskIndicator]
    summary: DocumentSummary
    explanations: List[ClauseExplanation]
    key_sentences: List[KeySentence] = []
    risk_score: Optional[RiskScore] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    stage: int = 6
    ocr_available: bool = False
    vector_backend: str = "none"
    llm_configured: bool = False
    llm_provider: str = "none"


# ---------------------------------------------------------------------------
# Stage 2: file upload / text extraction
# ---------------------------------------------------------------------------

class ExtractResponse(BaseModel):
    filename: str
    source_type: str          # "pdf" | "image"
    pages: int
    method: str               # "text-layer" | "ocr" | "text-layer+ocr"
    ocr_used: bool
    characters: int
    text: str
    warnings: List[str] = []


# ---------------------------------------------------------------------------
# Stage 3: semantic search
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=10)


class SearchHit(BaseModel):
    rank: int
    passage_index: int
    text: str
    sentence_start: int
    sentence_end: int
    similarity: float


class SearchResponse(BaseModel):
    document_id: str
    query: str
    top_k: int
    backend: str
    similarity_note: str
    results: List[SearchHit]


# ---------------------------------------------------------------------------
# Stage 4: question answering (RAG) / Stage 5: AI summary
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(4, ge=1, le=8)


class AskResponse(BaseModel):
    question: str
    mode: str                      # "llm" | "retrieval-only"
    provider: Optional[str] = None
    answer: str
    closest_sentence: Optional[str] = None
    sources: List[SearchHit]
    note: str


class AiSummaryRequest(BaseModel):
    document_id: str = Field(..., min_length=1)


class AiSummaryResponse(BaseModel):
    mode: str                      # "llm" | "extractive"
    provider: Optional[str] = None
    text: str
    note: Optional[str] = None
