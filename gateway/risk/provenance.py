"""
Provenance evaluation for Phase 4.7.

Trust levels:
  TRUSTED  -> no penalty
  UNTRUSTED -> FLAG + PROVENANCE_UNTRUSTED_SOURCE
  UNKNOWN   -> FLAG + PROVENANCE_UNKNOWN_SOURCE (only when provenance is required
               but origin cannot be established)

Missing provenance in the request defaults to UNKNOWN (never implicitly TRUSTED).

Provenance reasons are independent of behavioral reasons; they are aggregated.
"""
from typing import Optional, List
from gateway.models.schemas import ProvenanceData


TRUSTED = "TRUSTED"
UNTRUSTED = "UNTRUSTED"
UNKNOWN = "UNKNOWN"


def evaluate_provenance(provenance: Optional[ProvenanceData]) -> List[str]:
    """
    Returns a (possibly empty) list of provenance reason codes.

    Empty list means no provenance penalty (TRUSTED source).
    Non-empty list always means FLAG is warranted.
    """
    if provenance is None:
        # Missing provenance defaults to UNKNOWN, never implicitly TRUSTED.
        return ["PROVENANCE_UNKNOWN_SOURCE"]

    trust = provenance.source_trust.upper()

    reasons: List[str] = []

    if provenance.payment_intent_origin == "EXTERNAL_CONTENT":
        reasons.append("PROVENANCE_PAYMENT_INTENT_FROM_EXTERNAL_CONTENT")

    if trust == UNTRUSTED:
        reasons.append("PROVENANCE_UNTRUSTED_SOURCE")
    elif trust == UNKNOWN:
        reasons.append("PROVENANCE_UNKNOWN_SOURCE")
    # TRUSTED => no reason added

    return reasons
