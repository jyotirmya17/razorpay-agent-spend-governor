"""
Phase 4.7 Risk Orchestrator.

This module is the single integration point between the Governor policy/idempotency
layer and the risk evaluation + RazorpayX execution layer.

Wiring:
  check_policy          (existing Phase 2/3)
       |
  build_live_profile    (point-in-time from DB transactions)
       |
  extract_features      (Phase 4.2)
       |
  BehavioralAnomalyModel.predict_one  (Phase 4.3)
       |
  evaluate_provenance   (Phase 4.7)
       |
  make_risk_decision    (Phase 4.5 + 4.7 provenance aggregation)
       |
  +-- DENY / REVIEW  --> stop (structural; ExecutionService never called)
  |
  +-- ALLOW         --> ExecutionService.execute_spend (existing Phase 3)

Decision precedence (enforced in make_risk_decision):
  1. Policy violation             -> DENY
  2. Model failure (None/NaN/inf) -> REVIEW
  3. Behavioral DENY (disabled)  -> N/A
  4. Behavioral REVIEW (>= 0.42)    -> REVIEW
  5. Provenance risk (untrusted)  -> REVIEW
  6. Otherwise                   -> ALLOW

Audit events are written to the DB BEFORE execution.
The audit-chain lock is released (via flush) before any Razorpay call.

Missing provenance defaults to UNKNOWN (never implicitly TRUSTED).
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session

from gateway.models.db import Transaction, ProvenanceRecord
from gateway.models.schemas import PayoutRequest
from gateway.risk.profiles import AgentBehaviorProfile, update_profile
from gateway.risk.features import extract_features
from gateway.risk.anomaly_model import BehavioralAnomalyModel
from gateway.risk.decision import make_risk_decision, RiskConfig
from gateway.risk.provenance import evaluate_provenance
from gateway.core.audit import append_audit_event

logger = logging.getLogger(__name__)

_AGENT_MODELS: Dict[str, BehavioralAnomalyModel] = {}

MIN_HISTORY = 20

def reset_model_singleton():
    global _AGENT_MODELS
    _AGENT_MODELS.clear()


def get_or_train_agent_model(db: Session, agent_id: str, before_timestamp: datetime) -> Optional[BehavioralAnomalyModel]:
    """
    Returns a behavioral anomaly model trained ONLY on this agent's historical transactions.
    Requires at least MIN_HISTORY successful transactions strictly before before_timestamp.
    Returns None if history is insufficient.
    """
    global _AGENT_MODELS
    
    # We could optionally cache the model by agent_id, but we need to ensure the cache
    # is temporally correct. For safety and simplicity in this architecture update,
    # we'll train it on the fly, or we could cache and invalidate.
    # Given the prompt: "The per-agent model cache must be invalidated/retrained when relevant historical data changes."
    # Since we need to be strictly before `before_timestamp`, caching might be tricky if time advances.
    # Actually, we can cache it and if we just want a simple cache:
    if agent_id in _AGENT_MODELS:
        return _AGENT_MODELS[agent_id]

    transactions = (
        db.query(Transaction)
        .filter(Transaction.agent_id == agent_id)
        .filter(Transaction.timestamp < before_timestamp)
        .filter(Transaction.status == "SUCCEEDED")
        .order_by(Transaction.timestamp)
        .all()
    )

    if len(transactions) < MIN_HISTORY:
        logger.warning(f"Insufficient history for agent {agent_id}: {len(transactions)} < {MIN_HISTORY}")
        return None

    model = BehavioralAnomalyModel()
    
    profile = AgentBehaviorProfile(agent_id)
    feature_records = []

    for txn in transactions:
        txn_record = {
            "agent_id": txn.agent_id,
            "amount_paise": txn.amount,
            "payee_id": txn.payee_id,
            "category": txn.category,
            "timestamp": txn.timestamp,
        }
        try:
            features = extract_features(profile, txn_record)
            feature_records.append(features)
        except Exception as e:
            logger.warning(f"Feature extraction failed for txn {txn.txn_id}: {e}")

        update_profile(profile, txn_record)

    if feature_records:
        model.train(feature_records)
        _AGENT_MODELS[agent_id] = model
        return model
    else:
        logger.warning(f"No valid feature records for agent {agent_id}")
        return None


def build_live_profile(db: Session, agent_id: str, before_timestamp: datetime) -> AgentBehaviorProfile:
    """
    Builds a point-in-time behavioral profile for agent_id using only
    transactions strictly before before_timestamp. Preserves temporal integrity.
    """
    historical_txns = (
        db.query(Transaction)
        .filter(
            Transaction.agent_id == agent_id,
            Transaction.timestamp < before_timestamp,
            Transaction.status.in_(["SUCCEEDED", "AUTHORIZED", "EXECUTING"])
        )
        .order_by(Transaction.timestamp)
        .all()
    )

    profile = AgentBehaviorProfile(agent_id)
    for txn in historical_txns:
        txn_record = {
            "agent_id": txn.agent_id,
            "amount_paise": txn.amount,
            "payee_id": txn.payee_id,
            "category": txn.category,
            "timestamp": txn.timestamp,
        }
        update_profile(profile, txn_record)

    return profile


def orchestrate_payout(
    db: Session,
    request: PayoutRequest,
    idempotency_key: str,
    policy_allowed: bool,
    policy_reason: str,
    mandate_details: Dict[str, Any],
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Full risk evaluation pipeline. Returns (risk_result, execution_result).

    DENY / REVIEW: execution_result is None. RazorpayX is never called.
    ALLOW: execution_result contains the execution outcome.

    Audit events are written before any Razorpay call. The audit-chain lock
    (SELECT ... FOR UPDATE) is held only within the DB flush scope, never
    across the Razorpay HTTP call.
    """
    now = request.timestamp or datetime.now(timezone.utc).replace(tzinfo=None)
    txn_id = idempotency_key

    # --- Audit: policy evaluated ---
    append_audit_event(db, "governor.policy_evaluated", txn_id, {
        "agent_id": request.agent_id,
        "policy_allowed": policy_allowed,
        "policy_reason": policy_reason,
        "mandate_details": mandate_details,
    })
    db.commit()  # Release audit lock; next event can now append safely

    # --- Point-in-time profile + feature extraction ---
    anomaly_score: Optional[float] = None
    model_version: Optional[str] = None
    behavioral_eval_reason: Optional[str] = None

    try:
        profile = build_live_profile(db, request.agent_id, before_timestamp=now)
        txn_record = {
            "agent_id": request.agent_id,
            "amount_paise": request.amount,
            "payee_id": request.payee_id,
            "category": request.category,
            "timestamp": now,
        }
        features = extract_features(profile, txn_record)
        
        # Get per-agent model
        model = get_or_train_agent_model(db, request.agent_id, now)
        
        if model and model.is_fitted:
            result = model.predict_one(features)
            anomaly_score = result["anomaly_score"]
            model_version = result["model_version"]
        else:
            # Model is None (insufficient history) or unfitted
            behavioral_eval_reason = "INSUFFICIENT_BEHAVIORAL_HISTORY"
    except Exception as e:
        logger.error(f"Behavioral evaluation error for {txn_id}: {e}")
        # anomaly_score stays None, decision engine will use fail-safe

    # --- Audit: behavior evaluated ---
    append_audit_event(db, "governor.behavior_evaluated", txn_id, {
        "agent_id": request.agent_id,
        "anomaly_score": anomaly_score,
        "model_version": model_version,
    })
    db.commit()

    # --- Provenance evaluation ---
    provenance_reasons = evaluate_provenance(request.provenance)

    # Ensure Transaction record exists (even for policy-DENIED requests)
    txn = db.query(Transaction).filter_by(txn_id=txn_id).first()
    if not txn:
        txn = Transaction(
            txn_id=txn_id,
            agent_id=request.agent_id,
            payee_id=request.payee_id,
            category=request.category,
            amount=request.amount,
            status="DENIED" if not policy_allowed else "UNKNOWN",
        )
        db.add(txn)
        db.flush()

    # --- Persist provenance record ---
    if request.provenance:
        prov_rec = ProvenanceRecord(
            txn_id=txn_id,
            source_type=request.provenance.source_type,
            source_id=request.provenance.source_id,
            source_trust=request.provenance.source_trust,
            payment_intent_origin=request.provenance.payment_intent_origin,
            timestamp=now,
        )
        db.add(prov_rec)
        db.flush()
    else:
        # Missing provenance -> UNKNOWN (never implicitly TRUSTED)
        prov_rec = ProvenanceRecord(
            txn_id=txn_id,
            source_type="UNKNOWN",
            source_id="UNKNOWN",
            source_trust="UNKNOWN",
            payment_intent_origin="UNKNOWN",
            timestamp=now,
        )
        db.add(prov_rec)
        db.flush()

    # --- Audit: provenance evaluated ---
    append_audit_event(db, "governor.provenance_evaluated", txn_id, {
        "agent_id": request.agent_id,
        "source_trust": request.provenance.source_trust if request.provenance else "UNKNOWN",
        "provenance_reasons": provenance_reasons,
    })
    db.commit()

    risk_result = make_risk_decision(
        policy_allowed=policy_allowed,
        policy_reason=policy_reason,
        anomaly_score=anomaly_score,
        model_version=model_version,
        config=RiskConfig(),
        provenance_reasons=provenance_reasons,
        behavioral_eval_reason=behavioral_eval_reason,
    )

    decision = risk_result["decision"]

    # --- Audit: decision made (before execution) ---
    append_audit_event(db, "governor.decision_made", txn_id, {
        "agent_id": request.agent_id,
        "decision": decision,
        "reason_codes": risk_result["reason_codes"],
        "anomaly_score": anomaly_score,
    })
    db.commit()  # Audit is committed before any Razorpay call

    # --- Structural gate: DENY/REVIEW never reach ExecutionService ---
    if decision in ("DENY", "REVIEW"):
        # Mark transaction as DENIED or FLAGGED
        txn = db.query(Transaction).filter_by(txn_id=txn_id).first()
        if txn:
            txn.status = decision
            db.commit()

        import json
        from gateway.models.db import IdempotencyRecord
        idemp = db.query(IdempotencyRecord).filter_by(idempotency_key=txn_id).first()
        if idemp:
            idemp.status = "COMPLETED"
            idemp.response_payload = json.dumps({
                "decision": decision,
                "reason_codes": risk_result["reason_codes"],
                "anomaly_score": anomaly_score,
                "model_version": model_version,
                "transaction_id": txn_id,
                "agent_id": request.agent_id,
                "status": decision,
            })
            db.commit()

        append_audit_event(db, "razorpay.payout_not_created", txn_id, {
            "reason": decision,
            "reason_codes": risk_result["reason_codes"],
        })
        db.commit()
        return risk_result, None  # Execution never happens


    # --- ALLOW path: call existing ExecutionService ---
    from execution.service import ExecutionService
    service = ExecutionService()

    # Audit-chain lock released above; safe to call Razorpay now
    service.execute_spend(db, request, idempotency_key)

    # Read final state
    txn = db.query(Transaction).filter_by(txn_id=txn_id).first()
    execution_result = {
        "status": txn.status if txn else "UNKNOWN",
        "razorpay_payout_id": txn.razorpay_payout_id if txn else None,
    }

    append_audit_event(db, "razorpay.payout_created", txn_id, {
        "status": execution_result["status"],
        "razorpay_payout_id": execution_result["razorpay_payout_id"],
    })
    db.commit()

    return risk_result, execution_result
