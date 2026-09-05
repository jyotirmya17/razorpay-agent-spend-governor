"""
Phase 4.7 FastAPI routes.

POST /v1/payouts    — single orchestration entry point
GET  /v1/transactions/{id}
GET  /v1/agents/{id}
GET  /v1/audit/{transaction_id}
GET  /v1/risk/{transaction_id}

All state comes from the PostgreSQL database. No fake state.
FLAG and BLOCK are structurally prevented from reaching RazorpayX.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from gateway.models.db import (
    SessionLocal, Agent, Transaction, AuditEvent, ProvenanceRecord, init_db
)
from gateway.models.schemas import PayoutRequest
from policy.engine import check_policy
from gateway.risk.orchestrator import orchestrate_payout

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/v1/payouts")
def create_payout(
    request: PayoutRequest,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
):
    """
    Single orchestration entry point for agent payout requests.

    Flow:
      1. Policy check (mandate, caps, payee, category)
      2. Idempotency (handled inside check_policy)
      3. Behavioral risk evaluation (point-in-time profile + IsolationForest)
      4. Provenance evaluation (missing provenance -> UNKNOWN, never TRUSTED)
      5. Risk decision (aggregated reason codes)
      6. BLOCK/FLAG -> stop (never calls RazorpayX)
      7. ALLOW -> ExecutionService -> RazorpayX Test Mode
      8. Audit committed before execution
    """
    idempotency_key = x_idempotency_key or request.idempotency_key

    # --- Step 1 & 2: Policy + Idempotency ---
    policy_allowed, policy_reason, mandate_details = check_policy(db, request, idempotency_key)
    db.commit()

    # Handle idempotent replay before going to risk engine
    if policy_reason == "IDEMPOTENT_REPLAY":
        txn = db.query(Transaction).filter_by(txn_id=idempotency_key).first()
        return {
            "decision": "IDEMPOTENT_REPLAY",
            "reason_codes": ["IDEMPOTENT_REPLAY"],
            "transaction_id": idempotency_key,
            "status": txn.status if txn else None,
            "razorpay_payout_id": txn.razorpay_payout_id if txn else None,
        }

    if policy_reason in ("IDEMPOTENCY_KEY_CONFLICT", "UNKNOWN_IN_PROGRESS"):
        raise HTTPException(status_code=409, detail={"reason": policy_reason})

    # --- Steps 3-8: Risk orchestration ---
    risk_result, execution_result = orchestrate_payout(
        db=db,
        request=request,
        idempotency_key=idempotency_key,
        policy_allowed=policy_allowed,
        policy_reason=policy_reason,
        mandate_details=mandate_details,
    )

    response = {
        "decision": risk_result["decision"],
        "reason_codes": risk_result["reason_codes"],
        "anomaly_score": risk_result["anomaly_score"],
        "model_version": risk_result["model_version"],
        "transaction_id": idempotency_key,
        "agent_id": request.agent_id,
    }

    if execution_result:
        response["status"] = execution_result["status"]
        response["razorpay_payout_id"] = execution_result["razorpay_payout_id"]
    else:
        response["status"] = risk_result["decision"]

    return response


@router.get("/v1/transactions/{txn_id}")
def get_transaction(txn_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter_by(txn_id=txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "txn_id": txn.txn_id,
        "agent_id": txn.agent_id,
        "payee_id": txn.payee_id,
        "category": txn.category,
        "amount": txn.amount,
        "status": txn.status,
        "timestamp": txn.timestamp.isoformat(),
        "razorpay_payout_id": txn.razorpay_payout_id,
    }


@router.get("/v1/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter_by(agent_id=agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "status": agent.status,
    }


@router.get("/v1/audit/{transaction_id}")
def get_audit_trail(transaction_id: str, db: Session = Depends(get_db)):
    """Returns the full audit event timeline for a transaction, ordered by sequence_id."""
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_id == transaction_id)
        .order_by(AuditEvent.sequence_id)
        .all()
    )
    return {
        "transaction_id": transaction_id,
        "events": [
            {
                "sequence_id": e.sequence_id,
                "event_id": e.event_id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "entity_id": e.entity_id,
                "event_hash": e.event_hash,
                "previous_event_hash": e.previous_event_hash,
            }
            for e in events
        ],
    }


@router.get("/v1/risk/{transaction_id}")
def get_risk_summary(transaction_id: str, db: Session = Depends(get_db)):
    """Returns the risk summary: transaction state, provenance, and decision audit."""
    txn = db.query(Transaction).filter_by(txn_id=transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    prov = db.query(ProvenanceRecord).filter_by(txn_id=transaction_id).first()

    decision_event = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_id == transaction_id,
            AuditEvent.event_type == "governor.decision_made",
        )
        .order_by(AuditEvent.sequence_id.desc())
        .first()
    )

    import json
    decision_payload = json.loads(decision_event.payload) if decision_event else {}

    return {
        "transaction_id": transaction_id,
        "agent_id": txn.agent_id,
        "amount": txn.amount,
        "status": txn.status,
        "razorpay_payout_id": txn.razorpay_payout_id,
        "decision": decision_payload.get("decision"),
        "reason_codes": decision_payload.get("reason_codes", []),
        "anomaly_score": decision_payload.get("anomaly_score"),
        "provenance": {
            "source_type": prov.source_type if prov else None,
            "source_id": prov.source_id if prov else None,
            "source_trust": prov.source_trust if prov else None,
            "payment_intent_origin": prov.payment_intent_origin if prov else None,
        } if prov else None,
    }
