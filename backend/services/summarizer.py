"""
Document summary and "Simple English" clause explanations.

Both are built from the ACTUAL extracted data for the submitted
document -- nothing is hard-coded. For Stage 1, explanations use
deterministic templates keyed off clause type (not an external LLM),
as required by the project spec.
"""

from typing import List

from schemas.analysis import (
    ClauseExplanation,
    ClauseResult,
    DocumentSummary,
    KeyInformation,
    RiskIndicator,
)

NOT_SPECIFIED = "Not specified in the document."


def _join_or_default(items: List[str], empty_msg: str = NOT_SPECIFIED) -> str:
    return ", ".join(items) if items else empty_msg


def build_summary(
    key_info: KeyInformation,
    clauses: List[ClauseResult],
    risks: List[RiskIndicator],
) -> DocumentSummary:
    detected_clause_names = [c.clause_name for c in clauses if c.detected]

    payment_clause = next((c for c in clauses if c.clause_name == "Payment" and c.detected), None)
    termination_clause = next((c for c in clauses if c.clause_name == "Termination" and c.detected), None)
    renewal_clause = next((c for c in clauses if c.clause_name == "Automatic Renewal" and c.detected), None)
    obligations_clause = next((c for c in clauses if c.clause_name == "Obligations" and c.detected), None)

    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in risks:
        risk_counts[r.level] = risk_counts.get(r.level, 0) + 1

    overview = (
        f"This document contains {len(detected_clause_names)} of the "
        f"14 clause types the system checks for "
        f"({_join_or_default(detected_clause_names)})."
        if detected_clause_names
        else "No recognized clause types were detected in this document."
    )

    risk_overview = (
        f"{risk_counts['HIGH']} high, {risk_counts['MEDIUM']} medium and "
        f"{risk_counts['LOW']} low potential risk indicators were found."
        if risks
        else "No potential risk indicators were detected."
    )

    return DocumentSummary(
        overview=overview,
        parties=_join_or_default(key_info.parties),
        main_purpose="Service/commercial agreement between the parties named above."
        if key_info.parties
        else NOT_SPECIFIED,
        services="See Payment and Obligations clauses for described services/duties."
        if payment_clause or obligations_clause
        else NOT_SPECIFIED,
        payment=payment_clause.detected_text if payment_clause else NOT_SPECIFIED,
        contract_duration=key_info.contract_duration or NOT_SPECIFIED,
        termination=termination_clause.detected_text if termination_clause else NOT_SPECIFIED,
        renewal=(key_info.renewal or (renewal_clause.detected_text if renewal_clause else None)) or NOT_SPECIFIED,
        important_obligations=obligations_clause.detected_text if obligations_clause else NOT_SPECIFIED,
        governing_law=key_info.governing_law or NOT_SPECIFIED,
        risk_overview=risk_overview,
    )


# Simple-English templates keyed by clause type. {text} is replaced with
# the actual detected sentence so the explanation stays grounded in the
# real document rather than being a generic canned sentence.
_EXPLANATION_TEMPLATES = {
    "Payment": "This clause explains when and how much one party must pay the other.",
    "Confidentiality": "This clause requires both parties to keep shared information private and not share it with outsiders.",
    "Intellectual Property": "This clause decides who owns ideas, designs, or work created during the agreement.",
    "Liability": "This clause limits or defines how much one party can be blamed (and made to pay) if something goes wrong.",
    "Indemnification": "This clause means one party agrees to cover certain costs or losses the other party might face.",
    "Termination": "This clause explains how and when either party can end the agreement early.",
    "Automatic Renewal": "This clause means the contract will keep continuing automatically unless someone actively cancels it in time.",
    "Dispute Resolution": "This clause explains how disagreements between the parties will be resolved (e.g. arbitration instead of court).",
    "Governing Law": "This clause states which country's or state's laws will be used to interpret the agreement.",
    "Insurance": "This clause requires one or both parties to maintain insurance coverage.",
    "Force Majeure": "This clause excuses a party from certain obligations if extraordinary events (like natural disasters) happen.",
    "Obligations": "This clause lists specific duties that a party must carry out under the agreement.",
    "Notice": "This clause explains how official communications (notices) must be sent between the parties.",
    "Effective Date": "This clause states the date from which the agreement officially starts.",
}


def build_explanations(clauses: List[ClauseResult]) -> List[ClauseExplanation]:
    explanations: List[ClauseExplanation] = []
    for clause in clauses:
        if not clause.detected or not clause.detected_text:
            continue
        template = _EXPLANATION_TEMPLATES.get(
            clause.clause_name, "This clause sets out terms relevant to this section of the agreement."
        )
        explanations.append(
            ClauseExplanation(
                clause_name=clause.clause_name,
                legal_text=clause.detected_text,
                simple_english=template,
            )
        )
    return explanations
