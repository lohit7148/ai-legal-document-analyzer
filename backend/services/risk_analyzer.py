"""
Potential Risk Indicator detection.

This module is explicitly NOT a "Legal Risk Determination" engine --
it is an academic, transparent keyword/pattern module that flags
contractual patterns which commonly warrant a closer look. Every
indicator returned includes the category, a plain-English reason,
the matching rule's evidence keyword, and the exact source sentence
it came from, so a user can verify the finding themselves.

LOW / MEDIUM / HIGH levels are assigned by simple, documented rules
(e.g. presence of an unlimited-liability phrase => HIGH). These are
NOT machine-learned confidence scores.
"""

import re
from dataclasses import dataclass
from typing import List

from services import preprocessing


@dataclass
class RiskHit:
    category: str
    level: str
    reason: str
    evidence: str
    source_text: str


# Each rule: (category, level, reason, [trigger phrases])
RISK_RULES = [
    (
        "Payment",
        "MEDIUM",
        "The agreement includes a late-payment penalty, which can add unexpected cost if payments slip.",
        ["late payment penalty", "penalty of", "late fee"],
    ),
    (
        "Payment",
        "HIGH",
        "The agreement references liquidated damages, which can impose a large predefined financial cost.",
        ["liquidated damages"],
    ),
    (
        "Liability",
        "HIGH",
        "The agreement uses broad or unlimited liability language, which can expose a party to significant financial risk.",
        ["unlimited liability", "no limitation of liability", "in no event shall liability be limited"],
    ),
    (
        "Liability",
        "MEDIUM",
        "The agreement limits liability, which may reduce the ability to recover losses in a dispute.",
        ["limitation of liability", "liability shall not exceed", "liability is limited to"],
    ),
    (
        "Indemnification",
        "MEDIUM",
        "The agreement requires one party to indemnify (financially protect) the other, which is a meaningful obligation to review.",
        ["indemnify", "indemnification", "hold harmless"],
    ),
    (
        "Automatic Renewal",
        "MEDIUM",
        "The agreement automatically renews unless notice is given, which can unintentionally extend the contract term.",
        ["automatically renew", "auto-renew", "automatic renewal"],
    ),
    (
        "Termination",
        "MEDIUM",
        "The agreement sets specific/strict conditions or notice periods for termination.",
        ["terminate for cause", "termination notice", "right to terminate immediately"],
    ),
    (
        "Confidentiality",
        "LOW",
        "The agreement imposes confidentiality restrictions that continue to apply and should be tracked.",
        ["confidential information", "non-disclosure", "shall not disclose"],
    ),
    (
        "Intellectual Property",
        "MEDIUM",
        "The agreement addresses ownership or restriction of intellectual property, which can affect future use of work product.",
        ["intellectual property", "ownership of work product", "proprietary rights"],
    ),
    (
        "Obligations",
        "LOW",
        "The agreement creates an ongoing obligation that should be tracked for compliance.",
        ["shall be responsible for", "shall ensure that", "obligations under this agreement"],
    ),
    (
        "Dispute Resolution",
        "LOW",
        "The agreement requires arbitration/mediation rather than standard court proceedings for disputes.",
        ["arbitration", "mediation", "binding arbitration"],
    ),
    (
        "Force Majeure",
        "LOW",
        "The agreement includes a force majeure clause affecting obligations during extraordinary events.",
        ["force majeure", "act of god"],
    ),
]

_LEVEL_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def detect_risk_indicators(text: str) -> List[RiskHit]:
    """
    Scan sentence-by-sentence for rule triggers. If the same
    (category, level) combination matches multiple sentences, only
    the first is kept to avoid a noisy, repetitive list in the demo UI.
    """
    sentences = preprocessing.split_sentences(text)
    seen_keys = set()
    hits: List[RiskHit] = []

    for sentence in sentences:
        if preprocessing.is_heading(sentence):
            continue
        low = sentence.lower()
        for category, level, reason, triggers in RISK_RULES:
            for trigger in triggers:
                if trigger in low:
                    key = (category, level)
                    if key in seen_keys:
                        break
                    seen_keys.add(key)
                    hits.append(
                        RiskHit(
                            category=category,
                            level=level,
                            reason=reason,
                            evidence=trigger,
                            source_text=sentence.strip(),
                        )
                    )
                    break

    # Sort HIGH -> MEDIUM -> LOW so the most important items surface first.
    hits.sort(key=lambda h: -_LEVEL_ORDER.get(h.level, 0))
    return hits
