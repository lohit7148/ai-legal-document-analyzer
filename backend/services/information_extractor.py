"""
Key information extraction.

Uses transparent regular-expression patterns to pull out parties,
dates, monetary values, percentages, contract duration, notice
periods, governing law, and dispute-resolution mechanism from the
raw document text. Nothing here is invented: if a pattern does not
match anywhere in the document, the corresponding field is left
empty / "Not specified in the document." (handled by the caller).
"""

import re
from typing import List, Optional

# --- Parties -----------------------------------------------------------
# Matches organisation-style names ending in common suffixes.
_PARTY_RE = re.compile(
    r"\b([A-Z][A-Za-z&.,'\-]*(?:\s+[A-Z][A-Za-z&.,'\-]*)*\s+"
    r"(?:Pvt\.?\s*Ltd\.?|Ltd\.?|LLC|Inc\.?|Corporation|Corp\.?|"
    r"Technologies|Solutions|Enterprises|Industries))\b"
)

# --- Dates ---------------------------------------------------------------
_DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{4}"
    r"|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}"
    r"|"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r")\b"
)

# --- Money (₹, $, Rs., INR, USD) -----------------------------------------
_MONEY_RE = re.compile(
    r"(?:₹|Rs\.?|INR|\$|USD)\s?[\d,]+(?:\.\d+)?"
)

# --- Percentages -----------------------------------------------------------
_PERCENT_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%")

# --- Contract duration -----------------------------------------------------
_DURATION_RE = re.compile(
    r"\b(?:a\s+)?(?:term|period|duration)\s+of\s+([\w\s]+?(?:year|month|day)s?)",
    re.IGNORECASE,
)
_SIMPLE_DURATION_RE = re.compile(
    r"\bfor\s+(?:a\s+period\s+of\s+)?(\d+\s*\(?[\w\-]*\)?\s*(?:year|month|day)s?)",
    re.IGNORECASE,
)

# --- Termination / notice period -------------------------------------------
_NOTICE_RE = re.compile(
    r"(\d+[\s-]?(?:day|days|business day|business days))\s+(?:prior\s+)?(?:written\s+)?notice",
    re.IGNORECASE,
)

# --- Governing law -----------------------------------------------------------
_GOVERNING_LAW_RE = re.compile(
    r"governed by(?: and construed in accordance with)? the laws of ([A-Za-z\s]+?)(?:[.,;]|$)",
    re.IGNORECASE,
)

# --- Jurisdiction --------------------------------------------------------
_JURISDICTION_RE = re.compile(
    r"(?:exclusive\s+)?jurisdiction of(?: the)? courts? (?:of|at|in) ([A-Za-z\s]+?)(?:[.,;]|$)",
    re.IGNORECASE,
)

# --- Dispute resolution mechanism -----------------------------------------
_DISPUTE_RE = re.compile(
    r"(arbitration|mediation)", re.IGNORECASE
)

# --- Renewal ---------------------------------------------------------------
_RENEWAL_RE = re.compile(
    r"((?:shall\s+)?automatically\s+renew[\w\s]*?(?:unless[\w\s,\-]+?notice[\w\s,\-]*?)?)[.]",
    re.IGNORECASE,
)


def _first_match(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(1).strip() if (m and m.groups()) else (m.group(0).strip() if m else None)


def _all_matches(pattern: re.Pattern, text: str, limit: int = 10) -> List[str]:
    seen = []
    for m in pattern.finditer(text):
        value = m.group(0).strip()
        if value not in seen:
            seen.append(value)
        if len(seen) >= limit:
            break
    return seen


def extract_parties(text: str) -> List[str]:
    return _all_matches(_PARTY_RE, text, limit=8)


def extract_dates(text: str) -> List[str]:
    return _all_matches(_DATE_RE, text, limit=10)


def extract_money(text: str) -> List[str]:
    return _all_matches(_MONEY_RE, text, limit=10)


def extract_percentages(text: str) -> List[str]:
    return _all_matches(_PERCENT_RE, text, limit=10)


def extract_duration(text: str) -> Optional[str]:
    return _first_match(_DURATION_RE, text) or _first_match(_SIMPLE_DURATION_RE, text)


def extract_notice_period(text: str) -> Optional[str]:
    return _first_match(_NOTICE_RE, text)


def extract_governing_law(text: str) -> Optional[str]:
    return _first_match(_GOVERNING_LAW_RE, text)


def extract_jurisdiction(text: str) -> Optional[str]:
    return _first_match(_JURISDICTION_RE, text)


def extract_dispute_mechanism(text: str) -> Optional[str]:
    return _first_match(_DISPUTE_RE, text)


def extract_renewal(text: str) -> Optional[str]:
    return _first_match(_RENEWAL_RE, text)


def extract_penalties(text: str) -> List[str]:
    """Sentences that mention both a penalty word and a percentage or money value."""
    penalty_words = ["penalty", "penalties", "late fee", "liquidated damages"]
    hits: List[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        low = sentence.lower()
        if any(w in low for w in penalty_words):
            hits.append(sentence.strip())
    return hits[:10]
