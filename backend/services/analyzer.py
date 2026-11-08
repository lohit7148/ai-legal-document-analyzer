"""
Top-level orchestrator: ties preprocessing, Legal-BERT embedding + FAISS
indexing, clause detection, key-information extraction, risk detection, and
summarization together into one AnalyzeResponse.

This is the ONLY module that should be called directly from main.py's
API route -- everything else is a focused, single-purpose service.
"""

import logging

from models.legal_bert import legal_bert_model
from models.legal_bert import EMBEDDING_DIM
from schemas.analysis import (
    AnalyzeResponse,
    ClauseResult,
    DocumentStats,
    KeyInformation,
    ModelInfo,
    RiskIndicator,
    SearchIndexInfo,
    KeySentence,
    RiskScore,
)
from services import (
    clause_detector,
    information_extractor as info,
    preprocessing,
    risk_analyzer,
    summarizer,
    vector_store,
    advanced_summary,
    semantic_clauses,
    risk_scoring,
)

logger = logging.getLogger("analyzer")

MIN_CHARS = 20
MAX_CHARS = 200_000  # generous ceiling to avoid pathological inputs
INDEX_PASSAGE_TOKENS = 160  # passage size used for the Stage 3 semantic index


class AnalysisError(Exception):
    """Raised for user-input problems (empty/too short/too long text)."""


def analyze_document(raw_text: str) -> AnalyzeResponse:
    if raw_text is None or not raw_text.strip():
        raise AnalysisError("The document text is empty. Please paste or type a legal document.")

    if len(raw_text.strip()) < MIN_CHARS:
        raise AnalysisError(
            f"The document text is too short to analyze meaningfully "
            f"(minimum {MIN_CHARS} characters)."
        )

    if len(raw_text) > MAX_CHARS:
        raise AnalysisError(
            f"The document text is too long (maximum {MAX_CHARS:,} characters). "
            f"Please split it into smaller sections."
        )

    text = preprocessing.clean_text(raw_text)
    sentences = preprocessing.split_sentences(text)
    # --- Legal-BERT embeddings + FAISS index (Stage 3) ----------------------
    # The document is split into small passages, each passage is encoded by
    # Legal-BERT, and the vectors are stored in an in-memory FAISS index so the
    # user can later run semantic searches against this document.
    document_id = None
    index_info = SearchIndexInfo(available=False)
    passages_indexed = 0
    passages = embeddings = None
    key_sentences = []
    semantic = {}
    if legal_bert_model.is_loaded:
        try:
            passages = preprocessing.build_chunks(sentences, token_budget=INDEX_PASSAGE_TOKENS)
            embeddings = legal_bert_model.embed_batch([p.text for p in passages])
            passages_indexed = len(passages)
        except Exception as exc:  # pragma: no cover
            logger.warning("Semantic indexing failed: %s", exc)
            passages = embeddings = None
        # Stage 5: sentence-level Legal-BERT embeddings -> key sentences + closest-clause candidates
        try:
            idx = advanced_summary.candidate_indices(sentences)
            if idx:
                sent_emb = legal_bert_model.embed_batch([sentences[i] for i in idx])
                key_sentences = advanced_summary.select_key_sentences(sentences, idx, sent_emb)
                semantic = semantic_clauses.closest_sentences(sentences, idx, sent_emb)
        except Exception as exc:  # pragma: no cover
            logger.warning("Sentence-level analysis failed: %s", exc)

    # --- Clause / key-information / risk analysis (transparent, explainable)
    clause_hits = clause_detector.detect_clauses(sentences)
    clauses = [
        ClauseResult(
            clause_name=h.clause_name,
            detected=h.detected,
            detected_text=h.detected_text,
            source_sentence=h.source_sentence,
            detection_indicator=h.detection_indicator,
            position=h.position,
            semantic_sentence=(semantic.get(h.clause_name) or {}).get("sentence"),
            semantic_position=(semantic.get(h.clause_name) or {}).get("position"),
            semantic_similarity=(semantic.get(h.clause_name) or {}).get("similarity"),
        )
        for h in clause_hits
    ]

    risk_hits = risk_analyzer.detect_risk_indicators(text)
    risk_indicators = [
        RiskIndicator(
            category=r.category,
            level=r.level,
            reason=r.reason,
            evidence=r.evidence,
            source_text=r.source_text,
        )
        for r in risk_hits
    ]

    # Stage 5: numeric checks + transparent overall score
    for extra in risk_scoring.numeric_indicators(text):
        risk_indicators.append(RiskIndicator(**extra))
    _order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    risk_indicators.sort(key=lambda r: _order.get(r.level, 3))
    missing = risk_scoring.missing_clause_checks({c.clause_name: c.detected for c in clauses})
    risk_score = RiskScore(**risk_scoring.score_risks([r.level for r in risk_indicators], missing))

    key_information = KeyInformation(
        parties=info.extract_parties(text),
        effective_date=(info.extract_dates(text)[0] if info.extract_dates(text) else None),
        expiration_date=None,
        other_dates=info.extract_dates(text)[1:] if len(info.extract_dates(text)) > 1 else [],
        payment_amounts=info.extract_money(text),
        penalties=info.extract_penalties(text),
        percentages=info.extract_percentages(text),
        contract_duration=info.extract_duration(text),
        renewal=info.extract_renewal(text),
        termination_notice=info.extract_notice_period(text),
        governing_law=info.extract_governing_law(text),
        jurisdiction=info.extract_jurisdiction(text),
        dispute_resolution=info.extract_dispute_mechanism(text),
    )

    if passages is not None and embeddings is not None:
        facts = "; ".join(filter(None, [
            "parties: " + ", ".join(key_information.parties) if key_information.parties else "",
            "payment: " + ", ".join(key_information.payment_amounts) if key_information.payment_amounts else "",
            "duration: " + key_information.contract_duration if key_information.contract_duration else "",
            "governing law: " + key_information.governing_law if key_information.governing_law else "",
        ])) or "no structured facts found"
        document_id = vector_store.register(passages, embeddings, key_sentences=[k["text"] for k in key_sentences], facts=facts)
        index_info = SearchIndexInfo(available=True, passages=passages_indexed, embedding_dim=EMBEDDING_DIM, backend=vector_store.BACKEND_NAME)

    summary = summarizer.build_summary(key_information, clauses, risk_indicators)
    explanations = summarizer.build_explanations(clauses)

    stats = DocumentStats(
        characters=preprocessing.count_characters(raw_text),
        words=preprocessing.count_words(raw_text),
        sentences=len(sentences),
        chunks_processed=passages_indexed,
    )

    model_info = ModelInfo(
        name=legal_bert_model.model_name,
        task="Legal-domain language representation (embeddings)",
        device=legal_bert_model.device,
    )

    return AnalyzeResponse(
        document_id=document_id,
        search_index=index_info,
        document_stats=stats,
        model=model_info,
        key_information=key_information,
        clauses=clauses,
        risk_indicators=risk_indicators,
        summary=summary,
        explanations=explanations,
        key_sentences=[KeySentence(**k) for k in key_sentences],
        risk_score=risk_score,
    )
