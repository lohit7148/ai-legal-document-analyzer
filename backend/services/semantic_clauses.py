"""
Semantic clause candidates (Stage 5).

For every clause type there is a short plain-English description (a
"prototype"). Legal-BERT embeds the description and every sentence of the
document; the sentence with the highest cosine similarity is returned as the
closest candidate.

IMPORTANT: this is supplementary evidence, NOT a detection. The pretrained
Legal-BERT is not fine-tuned for this, similarity values are not
probabilities, and a candidate is returned even when the clause does not
exist. The "Detected / Not Detected" status still comes from the keyword
search in clause_detector.py.
"""

from typing import Dict, List

import numpy as np

from models.legal_bert import legal_bert_model

PROTOTYPES: Dict[str, str] = {
    "Payment": "The client shall pay the service fee and invoices are payable within a number of days.",
    "Confidentiality": "Each party shall keep confidential information secret and not disclose it to third parties.",
    "Intellectual Property": "Ownership of intellectual property, software and work product created under the agreement.",
    "Liability": "A party's liability is limited and neither party is liable for indirect or consequential damages.",
    "Indemnification": "One party shall indemnify and hold harmless the other party against third-party claims.",
    "Termination": "Either party may terminate the agreement by giving written notice or for material breach.",
    "Automatic Renewal": "The agreement automatically renews for a further term unless notice of non-renewal is given.",
    "Dispute Resolution": "Disputes shall be resolved by mediation or binding arbitration.",
    "Governing Law": "This agreement is governed by and construed in accordance with the laws of a country or state.",
    "Insurance": "The service provider shall maintain insurance coverage during the term of the agreement.",
    "Force Majeure": "A party is not liable for delays caused by events beyond its reasonable control such as natural disasters.",
    "Obligations": "Each party is responsible for complying with laws and performing its obligations under the agreement.",
    "Notice": "Notices must be given in writing and delivered by email or courier to the address of the other party.",
    "Effective Date": "This agreement is effective as of a stated date and continues for a stated term.",
}


def closest_sentences(sentences: List[str], indices: List[int], sentence_embeddings: np.ndarray) -> Dict[str, Dict]:
    if len(indices) == 0:
        return {}
    names = list(PROTOTYPES)
    proto_vecs = legal_bert_model.embed_batch([PROTOTYPES[n] for n in names])
    sims = proto_vecs @ sentence_embeddings.T          # (clauses, sentences)
    out = {}
    for row, name in enumerate(names):
        j = int(np.argmax(sims[row]))
        out[name] = {"sentence": sentences[indices[j]], "position": indices[j], "similarity": round(float(sims[row, j]), 4)}
    return out
