"""
Legal clause detection.

IMPORTANT (see project requirements): the pretrained
`nlpaueb/legal-bert-base-uncased` checkpoint does NOT come with a
classification head for clause types such as "Payment" or
"Termination" -- it only produces general-purpose legal-domain
embeddings. Training a real classifier is out of scope for Stage 1.

So clause detection here is implemented as TRANSPARENT, EXPLAINABLE
keyword/pattern matching over the sentence-split document. Each
clause type has a set of trigger phrases. A sentence is flagged as
"Detected" for a clause type when it contains at least one trigger
phrase for that type. This keeps the system honest: every detection
can be traced back to the exact text and rule that caused it.

Legal-BERT embeddings (see models/legal_bert.py) are computed
alongside this and exposed for future stages (e.g. semantic
similarity search / RAG), but are not required to make Stage 1's
clause detection work.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from services.preprocessing import is_heading

# clause_name -> list of trigger phrases / regex-safe keywords
CLAUSE_KEYWORDS: Dict[str, List[str]] = {
    "Payment": [
        "shall pay", "payment of", "service fee", "invoice", "due within",
        "payment terms", "amount payable", "consideration", "fees payable",
        "per month", "monthly payment",
    ],
    "Confidentiality": [
        "confidential information", "confidentiality", "non-disclosure",
        "shall not disclose", "keep confidential", "proprietary information",
    ],
    "Intellectual Property": [
        "intellectual property", "copyright", "trademark", "patent",
        "ownership of work product", "proprietary rights", "trade secret",
    ],
    "Liability": [
        "liability", "liable for", "limitation of liability",
        "in no event shall", "consequential damages", "indirect damages",
    ],
    "Indemnification": [
        "indemnify", "indemnification", "hold harmless", "defend and indemnify",
    ],
    "Termination": [
        "terminate this agreement", "termination", "right to terminate",
        "terminate for convenience", "terminate for cause",
    ],
    "Automatic Renewal": [
        "automatically renew", "auto-renew", "automatic renewal",
        "shall renew for", "renewal term",
    ],
    "Dispute Resolution": [
        "dispute resolution", "arbitration", "mediation",
        "resolve any dispute", "binding arbitration",
    ],
    "Governing Law": [
        "governing law", "governed by the laws of", "construed in accordance with",
    ],
    "Insurance": [
        "insurance", "insurance coverage", "policy of insurance", "insured",
    ],
    "Force Majeure": [
        "force majeure", "act of god", "beyond its reasonable control",
        "circumstances beyond",
    ],
    "Obligations": [
        "shall be responsible for", "obligations under this agreement",
        "duties of", "shall ensure that", "responsibilities of",
    ],
    "Notice": [
        "written notice", "notice shall be", "notify the other party",
        "notice period",
    ],
    "Effective Date": [
        "effective date", "effective as of", "commencing on",
        "shall commence on",
    ],
}


@dataclass
class ClauseHit:
    clause_name: str
    detected: bool
    detected_text: Optional[str]
    source_sentence: Optional[str]
    detection_indicator: str
    position: Optional[int]


def _sentence_matches(sentence: str, keywords: List[str]) -> Optional[str]:
    lower = sentence.lower()
    for kw in keywords:
        if kw in lower:
            return kw
    return None


def detect_clauses(sentences: List[str]) -> List[ClauseHit]:
    """
    For every known clause type, scan all sentences and return the
    FIRST matching sentence as evidence (keeps the response compact
    and easy to read in a B.Tech capstone demo). If a clause type has
    no match anywhere in the document, it is returned with
    detected=False and detection_indicator="Not Detected".
    """
    results: List[ClauseHit] = []

    for clause_name, keywords in CLAUSE_KEYWORDS.items():
        found = False
        for idx, sentence in enumerate(sentences):
            if is_heading(sentence):
                continue
            matched_kw = _sentence_matches(sentence, keywords)
            if matched_kw:
                results.append(
                    ClauseHit(
                        clause_name=clause_name,
                        detected=True,
                        detected_text=sentence.strip(),
                        source_sentence=sentence.strip(),
                        detection_indicator="Detected",
                        position=idx,
                    )
                )
                found = True
                break
        if not found:
            results.append(
                ClauseHit(
                    clause_name=clause_name,
                    detected=False,
                    detected_text=None,
                    source_sentence=None,
                    detection_indicator="Not Detected",
                    position=None,
                )
            )

    return results
