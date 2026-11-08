"""
Text preprocessing and chunking for legal documents.

Legal documents contain information that must NOT be destroyed by
aggressive NLP cleaning: monetary values, dates, section numbers,
percentages, and punctuation like "§", "%", "/", "-". This module
only normalizes whitespace and splits text into sentences/chunks --
it never strips digits, currency symbols, or punctuation.
"""

import re
from dataclasses import dataclass
from typing import List

from models.legal_bert import legal_bert_model, MAX_TOKENS

# Reserve room for [CLS]/[SEP] and keep a safety margin below the
# hard 512-token Legal-BERT limit.
CHUNK_TOKEN_BUDGET = 400


@dataclass
class Chunk:
    index: int
    text: str
    sentence_start: int  # index of first sentence in this chunk
    sentence_end: int    # index of last sentence in this chunk (inclusive)


def clean_text(raw_text: str) -> str:
    """
    Normalize whitespace only. Legal punctuation, numbers, currency
    symbols, and dates are preserved untouched.
    """
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of spaces/tabs, but keep paragraph breaks.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# A conservative sentence splitter tuned for legal text: it avoids
# splitting on abbreviations like "Pvt.", "Ltd.", "No.", "Sec.", "Mr.",
# "U.S.", and on decimal numbers like "2.5%".
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "pvt", "ltd", "inc", "co", "no", "sec",
    "art", "cl", "para", "u.s", "vs", "etc", "e.g", "i.e",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\"])")


def split_sentences(text: str) -> List[str]:
    """Split cleaned text into sentences while preserving legal detail."""
    # First split on paragraph breaks so section boundaries are kept.
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    sentences: List[str] = []

    for paragraph in paragraphs:
        candidates = _SENTENCE_SPLIT_RE.split(paragraph)
        buffer = ""
        for cand in candidates:
            cand = cand.strip()
            if not cand:
                continue
            buffer = f"{buffer} {cand}".strip() if buffer else cand
            last_word = re.findall(r"[A-Za-z\.]+$", buffer)
            trailing_token = last_word[0].lower().rstrip(".") if last_word else ""
            if trailing_token in _ABBREVIATIONS:
                # Likely a false sentence break (e.g. "XYZ Pvt." ) -- keep
                # accumulating into the same sentence.
                continue
            sentences.append(buffer)
            buffer = ""
        if buffer:
            sentences.append(buffer)

    return sentences if sentences else ([text] if text else [])


def build_chunks(sentences: List[str], token_budget: int = CHUNK_TOKEN_BUDGET) -> List[Chunk]:
    """
    Group sentences into token-budget-limited chunks so that long
    documents can be processed by Legal-BERT without silently
    truncating everything after the first 512 tokens.

    `token_budget` lets different stages pick a chunk size: Stage 1 used
    400 tokens; Stage 3 uses smaller passages for finer semantic search.
    """
    chunks: List[Chunk] = []
    current_sentences: List[str] = []
    current_start = 0

    def flush(end_index: int):
        if not current_sentences:
            return
        chunk_text = " ".join(current_sentences)
        chunks.append(
            Chunk(
                index=len(chunks),
                text=chunk_text,
                sentence_start=current_start,
                sentence_end=end_index,
            )
        )

    for i, sentence in enumerate(sentences):
        candidate = " ".join(current_sentences + [sentence])
        token_len = _safe_token_len(candidate)

        if current_sentences and token_len > token_budget:
            flush(i - 1)
            current_sentences = [sentence]
            current_start = i
        else:
            if not current_sentences:
                current_start = i
            current_sentences.append(sentence)

    flush(len(sentences) - 1)
    return chunks


def _safe_token_len(text: str) -> int:
    """Token length via Legal-BERT tokenizer if loaded, else a heuristic."""
    if legal_bert_model.is_loaded:
        try:
            return legal_bert_model.tokenize_length(text)
        except Exception:
            pass
    # Rough heuristic fallback (~0.75 words per token for English legal text)
    return int(len(text.split()) / 0.75)


_HEADING_RE = re.compile(r"^\d+\.\s*[A-Z][A-Z\s\-/&]*$")


def is_heading(sentence: str) -> bool:
    """
    True for short, all-caps section headings such as "8. TERMINATION"
    or "AUTOMATIC RENEWAL". These are excluded from clause/risk keyword
    matching so a heading alone doesn't get mistaken for substantive
    clause text -- the real clause body sentence is used instead.
    """
    stripped = sentence.strip()
    if not stripped:
        return True
    if _HEADING_RE.match(stripped):
        return True
    words = stripped.rstrip(".").split()
    if len(words) <= 6 and stripped == stripped.upper() and any(c.isalpha() for c in stripped):
        return True
    return False


def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def count_characters(text: str) -> int:
    return len(text)
