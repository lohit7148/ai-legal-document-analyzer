"""
Improved risk analysis (Stage 5): transparent scoring + extra checks.

Still NOT a legal risk determination. Everything here is a documented,
countable rule, shown to the user with the formula:

  score = min(100, 25 x HIGH + 12 x MEDIUM + 4 x LOW indicators
                   + 8 x (important clause types not found))
  level : 0-24 LOW, 25-54 MEDIUM, 55-100 HIGH

Extra checks added on top of the keyword indicators:
  * numeric checks on the extracted numbers (late-payment rate, short
    termination notice, very long non-renewal window);
  * "potentially missing" important clauses (a keyword search found nothing,
    which does not prove the clause is absent).
"""

import re
from typing import Dict, List, Tuple

from services.preprocessing import split_sentences, is_heading

FORMULA = ("score = min(100, 25 x HIGH + 12 x MEDIUM + 4 x LOW indicators + 8 x important clause types not found); "
           "0-24 LOW, 25-54 MEDIUM, 55-100 HIGH")
POINTS = {"HIGH": 25, "MEDIUM": 12, "LOW": 4}
MISSING_POINTS = 8
IMPORTANT_CLAUSES = ["Liability", "Termination", "Governing Law", "Dispute Resolution", "Confidentiality"]

_PENALTY_RE = re.compile(r"(\d+(?:\.\d+)?)\s?%\s*(?:per|a|every)\s*(month|week|day|year)", re.I)
_NOTICE_RE = re.compile(r"(\d+)[\s-]*(?:business\s+)?days?'?\s*(?:prior\s+)?(?:written\s+)?notice", re.I)


def numeric_indicators(text: str) -> List[Dict]:
    """Extra indicators from numbers in the text (each carries its source sentence)."""
    found: List[Dict] = []
    for s in split_sentences(text):
        if is_heading(s):
            continue
        low = s.lower()
        m = _PENALTY_RE.search(s)
        if m and any(w in low for w in ("penalty", "late", "interest")):
            rate, unit = float(m.group(1)), m.group(2).lower()
            monthly = rate * {"day": 30, "week": 4.3, "month": 1, "year": 1 / 12}[unit]
            if monthly >= 3:
                found.append({"category": "Payment", "level": "HIGH",
                              "reason": f"The late-payment rate works out to about {monthly:.1f}% per month, which is 3% or more.",
                              "evidence": m.group(0), "source_text": s.strip()})
        n = _NOTICE_RE.search(s)
        if n and "terminat" in low and int(n.group(1)) < 15:
            found.append({"category": "Termination", "level": "MEDIUM",
                          "reason": f"The termination notice period is only {n.group(1)} days, which leaves little time to react.",
                          "evidence": n.group(0), "source_text": s.strip()})
        if n and "renew" in low and int(n.group(1)) >= 90:
            found.append({"category": "Automatic Renewal", "level": "MEDIUM",
                          "reason": f"Non-renewal notice must be given {n.group(1)} days ahead, so the deadline is easy to miss.",
                          "evidence": n.group(0), "source_text": s.strip()})
    return found


def missing_clause_checks(detected: Dict[str, bool]) -> List[str]:
    return [c for c in IMPORTANT_CLAUSES if not detected.get(c, False)]


def score_risks(levels: List[str], missing: List[str]) -> Dict:
    components: List[Dict] = []
    for lvl in ("HIGH", "MEDIUM", "LOW"):
        count = sum(1 for x in levels if x == lvl)
        if count:
            components.append({"name": f"{count} {lvl} indicator(s)", "points": count * POINTS[lvl],
                               "detail": f"{count} x {POINTS[lvl]} points"})
    if missing:
        components.append({"name": f"{len(missing)} important clause type(s) not found", "points": len(missing) * MISSING_POINTS,
                           "detail": ", ".join(missing)})
    score = min(100, sum(c["points"] for c in components))
    level = "LOW" if score < 25 else "MEDIUM" if score < 55 else "HIGH"
    return {"score": score, "level": level, "formula": FORMULA, "components": components, "missing_clause_checks": missing}
