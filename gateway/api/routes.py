import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from gateway.models.db import (
    SessionLocal, Agent, Mandate, MandateUsage, Transaction, AuditEvent, ProvenanceRecord, init_db
)
from gateway.models.schemas import PayoutRequest, ProvenanceData
from policy.engine import check_policy
from gateway.risk.orchestrator import orchestrate_payout, get_or_train_model
from gateway.core.audit import GENESIS_HASH
from gateway.config import get_config


logger = logging.getLogger(__name__)
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Existing Orchestration Endpoint ──────────────────────────────────────────

@router.post("/v1/payouts")
def create_payout(
    request: PayoutRequest,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
):
    idempotency_key = x_idempotency_key if isinstance(x_idempotency_key, str) and x_idempotency_key else request.idempotency_key


    policy_allowed, policy_reason, mandate_details = check_policy(db, request, idempotency_key)
    db.commit()

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


# ─── Phase 5 Read & Management Endpoints ─────────────────────────────────────

@router.get("/v1/health")
def get_health(db: Session = Depends(get_db)):
    """Genuine system status for DB, API, Risk Engine, RazorpayX Test Mode, and Audit Chain."""
    db_status = "healthy"
    dialect_name = db.bind.dialect.name
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    # RazorpayX status check
    razorpay_status = "ready"
    try:
        cfg = get_config()
        if cfg.mode != "test":
            razorpay_status = "degraded"
    except Exception:
        razorpay_status = "not_configured"

    # Risk model status check
    risk_status = "ready"
    model_ver = "behavioral_iforest_v1"
    try:
        get_or_train_model(db)
    except Exception:
        risk_status = "degraded"


    # Audit chain check
    audit_status = "verified"
    valid_chain = True
    audit_events_count = db.query(AuditEvent).count()
    events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
    prev_hash = GENESIS_HASH
    import hashlib
    for e in events:
        if e.previous_event_hash != prev_hash:
            valid_chain = False
            audit_status = "tampered"
            break
        hasher = hashlib.sha256()
        hasher.update(prev_hash.encode("utf-8"))
        hasher.update(e.payload.encode("utf-8"))
        if hasher.hexdigest() != e.event_hash:
            valid_chain = False
            audit_status = "tampered"
            break
        prev_hash = e.event_hash

    overall = "healthy" if (db_status == "healthy" and valid_chain and razorpay_status != "unavailable") else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": {"status": "healthy"},
            "postgres": {"status": db_status, "dialect": dialect_name},
            "risk_engine": {"status": risk_status, "model_version": model_ver},
            "razorpayx": {"status": razorpay_status, "mode": "TEST"},
            "audit_chain": {
                "status": audit_status,
                "valid": valid_chain,
                "events_count": audit_events_count,
            },
        },
    }


@router.get("/v1/overview/stats")
def get_overview_stats(db: Session = Depends(get_db)):
    """Aggregate statistics for Overview page."""
    total_agents = db.query(Agent).count()
    active_mandates = db.query(Mandate).filter(Mandate.status == "ACTIVE").count()

    total_transactions = db.query(Transaction).count()

    governed_paise = db.query(func.sum(Transaction.amount)).scalar() or 0

    # Decision counts from AuditEvent governor.decision_made
    decision_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.event_type == "governor.decision_made")
        .all()
    )

    counts = {"ALLOW": 0, "FLAG": 0, "BLOCK": 0, "IDEMPOTENT_REPLAY": 0}
    for ev in decision_events:
        try:
            p = json.loads(ev.payload)
            dec = p.get("decision")
            if dec in counts:
                counts[dec] += 1
        except Exception:
            pass

    return {
        "total_agents": total_agents,
        "active_mandates": active_mandates,
        "total_transactions": total_transactions,
        "governed_amount_paise": governed_paise,
        "governed_amount_inr": round(governed_paise / 100.0, 2),
        "decisions": counts,
    }


@router.get("/v1/transactions")
def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    decision: Optional[str] = None,
    agent_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Paginated, searchable & filterable transaction history."""
    query = db.query(Transaction)

    if agent_id:
        query = query.filter(Transaction.agent_id == agent_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Transaction.txn_id.like(search_pattern))
            | (Transaction.agent_id.like(search_pattern))
            | (Transaction.payee_id.like(search_pattern))
            | (Transaction.category.like(search_pattern))
        )

    total_count = query.count()
    query = query.order_by(Transaction.timestamp.desc())
    txns = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for t in txns:
        # Find decision audit
        dec_ev = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.entity_id == t.txn_id,
                AuditEvent.event_type == "governor.decision_made",
            )
            .order_by(AuditEvent.sequence_id.desc())
            .first()
        )
        dec_payload = json.loads(dec_ev.payload) if dec_ev else {}
        dec_val = dec_payload.get("decision", t.status)

        if decision and dec_val != decision:
            continue

        prov = db.query(ProvenanceRecord).filter_by(txn_id=t.txn_id).first()

        items.append(
            {
                "txn_id": t.txn_id,
                "agent_id": t.agent_id,
                "payee_id": t.payee_id,
                "category": t.category,
                "amount": t.amount,
                "amount_inr": round(t.amount / 100.0, 2),
                "timestamp": t.timestamp.isoformat(),
                "status": t.status,
                "decision": dec_val,
                "reason_codes": dec_payload.get("reason_codes", []),
                "anomaly_score": dec_payload.get("anomaly_score"),
                "razorpay_payout_id": t.razorpay_payout_id,
                "provenance_trust": prov.source_trust if prov else "UNKNOWN",
            }
        )

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
    }


@router.get("/v1/transactions/{txn_id}/full")
def get_transaction_full(txn_id: str, db: Session = Depends(get_db)):
    """Comprehensive investigation view: Policy, Behavior, Provenance, Decision, Execution, Audit."""
    txn = db.query(Transaction).filter_by(txn_id=txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Mandate info
    agent = db.query(Agent).filter_by(agent_id=txn.agent_id).first()
    mandate = (
        db.query(Mandate)
        .filter_by(agent_id=txn.agent_id)
        .order_by(Mandate.version.desc())
        .first()
    )

    # Provenance
    prov = db.query(ProvenanceRecord).filter_by(txn_id=txn_id).first()

    # Audit timeline for this transaction
    audit_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_id == txn_id)
        .order_by(AuditEvent.sequence_id)
        .all()
    )

    dec_payload = {}
    beh_payload = {}
    pol_payload = {}

    for ev in audit_events:
        try:
            p = json.loads(ev.payload)
            if ev.event_type == "governor.decision_made":
                dec_payload = p
            elif ev.event_type == "governor.behavior_evaluated":
                beh_payload = p
            elif ev.event_type == "governor.policy_evaluated":
                pol_payload = p
        except Exception:
            pass

    return {
        "request": {
            "txn_id": txn.txn_id,
            "agent_id": txn.agent_id,
            "agent_name": agent.name if agent else txn.agent_id,
            "payee_id": txn.payee_id,
            "category": txn.category,
            "amount": txn.amount,
            "amount_inr": round(txn.amount / 100.0, 2),
            "timestamp": txn.timestamp.isoformat(),
        },
        "policy": {
            "mandate_id": mandate.mandate_id if mandate else None,
            "mandate_status": mandate.status if mandate else None,
            "txn_cap": mandate.txn_cap if mandate else None,
            "daily_cap": mandate.daily_cap if mandate else None,
            "weekly_cap": mandate.weekly_cap if mandate else None,
            "allowed_categories": mandate.allowed_categories if mandate else [],
            "allowed_payees": mandate.allowed_payees if mandate else None,
            "policy_allowed": pol_payload.get("allowed", True),
            "policy_reason": pol_payload.get("reason"),
        },
        "behavior": {
            "anomaly_score": dec_payload.get("anomaly_score") or beh_payload.get("anomaly_score"),
            "model_version": dec_payload.get("model_version", "behavioral_iforest_v1"),
            "canonical_features": beh_payload.get("features", {}),
            "behavior_reasons": [r for r in dec_payload.get("reason_codes", []) if "BEHAVIOR" in r or "ANOMALY" in r],
        },
        "provenance": {
            "source_type": prov.source_type if prov else "UNKNOWN",
            "source_id": prov.source_id if prov else "N/A",
            "source_trust": prov.source_trust if prov else "UNKNOWN",
            "payment_intent_origin": prov.payment_intent_origin if prov else "UNKNOWN",
            "provenance_reasons": [r for r in dec_payload.get("reason_codes", []) if "PROVENANCE" in r],
        },
        "decision": {
            "decision": dec_payload.get("decision", txn.status),
            "reason_codes": dec_payload.get("reason_codes", []),
            "anomaly_score": dec_payload.get("anomaly_score"),
            "timestamp": dec_payload.get("timestamp", txn.timestamp.isoformat()),
        },
        "execution": {
            "status": txn.status,
            "razorpay_payout_id": txn.razorpay_payout_id,
        },
        "audit": [
            {
                "sequence_id": e.sequence_id,
                "event_id": e.event_id,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "event_hash": e.event_hash,
                "previous_event_hash": e.previous_event_hash,
            }
            for e in audit_events
        ],
    }


@router.get("/v1/agents")
def get_agents_list(db: Session = Depends(get_db)):
    """Returns all agents with their active mandate limits & usage."""
    agents = db.query(Agent).all()
    res = []
    for a in agents:
        mandate = (
            db.query(Mandate)
            .filter_by(agent_id=a.agent_id)
            .order_by(Mandate.version.desc())
            .first()
        )
        usage = (
            db.query(MandateUsage).filter_by(mandate_id=mandate.mandate_id).first()
            if mandate
            else None
        )

        txn_count = db.query(Transaction).filter_by(agent_id=a.agent_id).count()

        daily_cap = mandate.daily_cap if mandate else 0
        daily_used = usage.daily_usage if usage else 0
        utilization = round((daily_used / daily_cap) * 100.0, 1) if daily_cap > 0 else 0.0

        res.append(
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "status": a.status,
                "mandate_id": mandate.mandate_id if mandate else None,
                "mandate_status": mandate.status if mandate else "NONE",
                "daily_cap": daily_cap,
                "daily_cap_inr": round(daily_cap / 100.0, 2),
                "daily_usage": daily_used,
                "daily_usage_inr": round(daily_used / 100.0, 2),
                "weekly_cap": mandate.weekly_cap if mandate else 0,
                "weekly_cap_inr": round((mandate.weekly_cap if mandate else 0) / 100.0, 2),
                "weekly_usage": usage.weekly_usage if usage else 0,
                "weekly_usage_inr": round((usage.weekly_usage if usage else 0) / 100.0, 2),
                "utilization_pct": utilization,
                "transaction_count": txn_count,
            }
        )

    return res


@router.get("/v1/agents/{agent_id}/detail")
def get_agent_detail(agent_id: str, db: Session = Depends(get_db)):
    """Comprehensive agent detail: identity, mandate, limits, behavioral history."""
    agent = db.query(Agent).filter_by(agent_id=agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    mandate = (
        db.query(Mandate)
        .filter_by(agent_id=agent_id)
        .order_by(Mandate.version.desc())
        .first()
    )
    usage = (
        db.query(MandateUsage).filter_by(mandate_id=mandate.mandate_id).first()
        if mandate
        else None
    )

    recent_txns = (
        db.query(Transaction)
        .filter_by(agent_id=agent_id)
        .order_by(Transaction.timestamp.desc())
        .limit(10)
        .all()
    )

    txns_data = []
    for t in recent_txns:
        dec_ev = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.entity_id == t.txn_id,
                AuditEvent.event_type == "governor.decision_made",
            )
            .first()
        )
        dec_p = json.loads(dec_ev.payload) if dec_ev else {}
        txns_data.append(
            {
                "txn_id": t.txn_id,
                "amount": t.amount,
                "amount_inr": round(t.amount / 100.0, 2),
                "payee_id": t.payee_id,
                "category": t.category,
                "decision": dec_p.get("decision", t.status),
                "timestamp": t.timestamp.isoformat(),
            }
        )

    daily_cap = mandate.daily_cap if mandate else 0
    daily_used = usage.daily_usage if usage else 0
    utilization = round((daily_used / daily_cap) * 100.0, 1) if daily_cap > 0 else 0.0

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "status": agent.status,
        "mandate": {
            "mandate_id": mandate.mandate_id if mandate else None,
            "version": mandate.version if mandate else None,
            "status": mandate.status if mandate else None,
            "daily_cap": daily_cap,
            "daily_cap_inr": round(daily_cap / 100.0, 2),
            "daily_usage": daily_used,
            "daily_usage_inr": round(daily_used / 100.0, 2),
            "weekly_cap": mandate.weekly_cap if mandate else 0,
            "weekly_cap_inr": round((mandate.weekly_cap if mandate else 0) / 100.0, 2),
            "weekly_usage": usage.weekly_usage if usage else 0,
            "weekly_usage_inr": round((usage.weekly_usage if usage else 0) / 100.0, 2),
            "txn_cap": mandate.txn_cap if mandate else 0,
            "txn_cap_inr": round((mandate.txn_cap if mandate else 0) / 100.0, 2),
            "allowed_categories": mandate.allowed_categories if mandate else [],
            "allowed_payees": mandate.allowed_payees if mandate else None,
            "effective_from": mandate.effective_from.isoformat() if mandate else None,
            "expires_at": mandate.expires_at.isoformat() if mandate else None,
            "utilization_pct": utilization,
        },
        "recent_transactions": txns_data,
    }


@router.get("/v1/mandates")
def get_mandates_list(db: Session = Depends(get_db)):
    """Returns all mandates in PostgreSQL database."""
    mandates = db.query(Mandate).order_by(Mandate.effective_from.desc()).all()
    res = []
    for m in mandates:
        agent = db.query(Agent).filter_by(agent_id=m.agent_id).first()
        usage = db.query(MandateUsage).filter_by(mandate_id=m.mandate_id).first()
        daily_used = usage.daily_usage if usage else 0
        utilization = round((daily_used / m.daily_cap) * 100.0, 1) if m.daily_cap > 0 else 0.0

        res.append(
            {
                "mandate_id": m.mandate_id,
                "agent_id": m.agent_id,
                "agent_name": agent.name if agent else m.agent_id,
                "version": m.version,
                "status": m.status,
                "daily_cap": m.daily_cap,
                "daily_cap_inr": round(m.daily_cap / 100.0, 2),
                "daily_usage": daily_used,
                "daily_usage_inr": round(daily_used / 100.0, 2),
                "weekly_cap": m.weekly_cap,
                "weekly_cap_inr": round(m.weekly_cap / 100.0, 2),
                "txn_cap": m.txn_cap,
                "txn_cap_inr": round(m.txn_cap / 100.0, 2),
                "allowed_categories": m.allowed_categories,
                "allowed_payees": m.allowed_payees,
                "effective_from": m.effective_from.isoformat(),
                "expires_at": m.expires_at.isoformat(),
                "utilization_pct": utilization,
            }
        )
    return res


@router.post("/v1/mandates/{mandate_id}/revoke")
def revoke_mandate(mandate_id: str, db: Session = Depends(get_db)):
    """Revokes a mandate in PostgreSQL database and records audit event."""
    mandate = db.query(Mandate).filter_by(mandate_id=mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")

    mandate.status = "REVOKED"
    db.commit()

    # Log audit event
    from gateway.core.audit import append_audit_event

    append_audit_event(
        db=db,
        event_type="governor.mandate_revoked",
        entity_id=mandate_id,
        payload={
            "mandate_id": mandate_id,
            "agent_id": mandate.agent_id,
            "status": "REVOKED",
            "revoked_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.commit()

    return {
        "mandate_id": mandate_id,
        "agent_id": mandate.agent_id,
        "status": "REVOKED",
        "message": "Mandate revoked successfully in PostgreSQL",
    }


@router.get("/v1/risk/overview")
def get_risk_overview(db: Session = Depends(get_db)):
    """Operational risk distribution and signal metrics."""
    decision_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.event_type == "governor.decision_made")
        .all()
    )

    scores = []
    reasons_freq = {}
    prov_flags_count = 0
    decision_counts = {"ALLOW": 0, "FLAG": 0, "BLOCK": 0}

    for ev in decision_events:
        try:
            p = json.loads(ev.payload)
            dec = p.get("decision")
            if dec in decision_counts:
                decision_counts[dec] += 1

            score = p.get("anomaly_score")
            if score is not None:
                scores.append(float(score))

            for r in p.get("reason_codes", []):
                reasons_freq[r] = reasons_freq.get(r, 0) + 1
                if "PROVENANCE" in r:
                    prov_flags_count += 1
        except Exception:
            pass

    # Score distribution buckets
    b_low = sum(1 for s in scores if s < 0.3)
    b_med = sum(1 for s in scores if 0.3 <= s < 0.5)
    b_high = sum(1 for s in scores if 0.5 <= s < 0.7)
    b_elevated = sum(1 for s in scores if s >= 0.7)

    return {
        "total_evaluations": len(decision_events),
        "decisions": decision_counts,
        "provenance_flags_count": prov_flags_count,
        "score_buckets": {
            "low_risk_lt_03": b_low,
            "moderate_03_05": b_med,
            "elevated_05_07": b_high,
            "high_risk_gte_07": b_elevated,
        },
        "reason_code_frequencies": sorted(
            [{"reason": k, "count": v} for k, v in reasons_freq.items()],
            key=lambda x: x["count"],
            reverse=True,
        ),
    }


@router.get("/v1/audit/events")
def get_audit_events_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Paginated tamper-evident audit event stream ordered by sequence_id desc."""
    total_count = db.query(AuditEvent).count()
    events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.sequence_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        {
            "sequence_id": e.sequence_id,
            "event_id": e.event_id,
            "entity_id": e.entity_id,
            "event_type": e.event_type,
            "timestamp": e.timestamp.isoformat(),
            "previous_event_hash": e.previous_event_hash,
            "event_hash": e.event_hash,
        }
        for e in events
    ]

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
    }


@router.post("/v1/audit/verify")
def verify_audit_chain(db: Session = Depends(get_db)):
    """Verifies SHA-256 link integrity across all AuditEvents in PostgreSQL."""
    events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
    if not events:
        return {
            "valid": True,
            "events_checked": 0,
            "message": "Audit chain is empty",
        }

    import hashlib

    prev_hash = GENESIS_HASH
    first_seq = events[0].sequence_id
    last_seq = events[-1].sequence_id

    for i, e in enumerate(events):
        if e.previous_event_hash != prev_hash:
            return {
                "valid": False,
                "events_checked": i,
                "failed_sequence_id": e.sequence_id,
                "failed_event_id": e.event_id,
                "reason": "PREVIOUS_HASH_MISMATCH",
                "first_sequence_id": first_seq,
                "last_sequence_id": last_seq,
            }

        hasher = hashlib.sha256()
        hasher.update(prev_hash.encode("utf-8"))
        hasher.update(e.payload.encode("utf-8"))
        computed = hasher.hexdigest()

        if computed != e.event_hash:
            return {
                "valid": False,
                "events_checked": i,
                "failed_sequence_id": e.sequence_id,
                "failed_event_id": e.event_id,
                "reason": "EVENT_HASH_MISMATCH",
                "first_sequence_id": first_seq,
                "last_sequence_id": last_seq,
            }

        prev_hash = e.event_hash

    return {
        "valid": True,
        "events_checked": len(events),
        "first_sequence_id": first_seq,
        "last_sequence_id": last_seq,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/v1/demo/scenario/{scenario_id}")
def run_demo_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """
    Evaluator Demo Runner: executes specified scenario against real Governor /v1/payouts pipeline.
    Scenarios:
      1: normal_allow          (ALLOW)
      2: policy_block          (BLOCK — amount exceeds txn_cap)
      3: behavioral_flag       (FLAG — cold-start high anomaly)
      4: untrusted_provenance  (FLAG — external untrusted content)
      5: idempotent_replay     (IDEMPOTENT_REPLAY — repeated key)
      6: revoked_mandate       (BLOCK — mandate revoked)
    """
    # Step 1: ensure demo fixtures are seeded
    from scripts.seed_demo import seed
    try:
        seed()
    except Exception as e:
        logger.warning(f"Demo seed notice: {e}")

    import uuid
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_suffix = f"{now_str}_{uuid.uuid4().hex[:6]}"

    scenarios_meta = {
        "1": {
            "name": "Normal Authorized Payout",
            "description": "Valid agent request within policy mandate.",
            "expected_decision": "ALLOW",
            "agent_id": "demo_normal_agent",
            "idempotency_key": f"demo_key_1_{unique_suffix}",
            "amount": 10000, # 100 INR
            "payee_id": "ven_test_normal",
            "category": "cloud",
            "provenance": ProvenanceData(
                source_type="TRUSTED_TASK",
                source_id="task_monthly_infra",
                source_trust="TRUSTED",
                payment_intent_origin="AGENT_TOOL",
            ),
        },
        "2": {
            "name": "Policy Violation",
            "description": "Txn amount (100 INR) exceeds policy cap (1 INR).",
            "expected_decision": "BLOCK",
            "agent_id": "demo_policy_agent",
            "idempotency_key": f"demo_key_2_{unique_suffix}",
            "amount": 10000, # 100 INR (cap is 100 paise = 1 INR)
            "payee_id": "ven_test_policy",
            "category": "cloud",
            "provenance": ProvenanceData(
                source_type="TRUSTED_TASK",
                source_id="task_policy_check",
                source_trust="TRUSTED",
                payment_intent_origin="AGENT_TOOL",
            ),
        },
        "3": {
            "name": "Behavioral Anomaly",
            "description": "Cold-start agent attempting large uncharacteristic payment.",
            "expected_decision": "FLAG",
            "agent_id": "demo_behavior_agent",
            "idempotency_key": f"demo_key_3_{unique_suffix}",
            "amount": 450000, # 4,500 INR
            "payee_id": "brand_new_vendor",
            "category": "software",
            "provenance": ProvenanceData(
                source_type="TRUSTED_TASK",
                source_id="task_behavior_check",
                source_trust="TRUSTED",
                payment_intent_origin="AGENT_TOOL",
            ),
        },
        "4": {
            "name": "Untrusted Provenance",
            "description": "Payment intent originated from untrusted external content.",
            "expected_decision": "FLAG",
            "agent_id": "demo_provenance_agent",
            "idempotency_key": f"demo_key_4_{unique_suffix}",
            "amount": 100000, # 1,000 INR
            "payee_id": "ven_test_prov",
            "category": "cloud",
            "provenance": ProvenanceData(
                source_type="EXTERNAL_CONTENT",
                source_id="scraped_email_123",
                source_trust="UNTRUSTED",
                payment_intent_origin="EXTERNAL_CONTENT",
            ),
        },
        "5": {
            "name": "Idempotent Replay",
            "description": "Repeated request with identical idempotency key returns replay.",
            "expected_decision": "IDEMPOTENT_REPLAY",
            "agent_id": "demo_normal_agent",
            "idempotency_key": f"demo_key_replay_{unique_suffix}",
            "amount": 10000,
            "payee_id": "ven_test_normal",
            "category": "cloud",
            "provenance": ProvenanceData(
                source_type="TRUSTED_TASK",
                source_id="task_monthly_infra",
                source_trust="TRUSTED",
                payment_intent_origin="AGENT_TOOL",
            ),
        },
        "6": {
            "name": "Revoked Mandate",
            "description": "Attempt payment after agent mandate has been revoked.",
            "expected_decision": "BLOCK",
            "agent_id": "demo_revocation_agent",
            "idempotency_key": f"demo_key_6_{unique_suffix}",
            "amount": 10000,
            "payee_id": "ven_test_revoc",
            "category": "cloud",
            "provenance": ProvenanceData(
                source_type="TRUSTED_TASK",
                source_id="task_revoc_check",
                source_trust="TRUSTED",
                payment_intent_origin="AGENT_TOOL",
            ),
        },
    }

    if scenario_id not in scenarios_meta:
        raise HTTPException(status_code=404, detail="Scenario ID must be between 1 and 6")

    meta = scenarios_meta[scenario_id]

    req_id = f"req_demo_{scenario_id}_{unique_suffix}"

    # Special handling for Scenario 5: run once first if not present
    if scenario_id == "5":
        req = PayoutRequest(
            agent_id=meta["agent_id"],
            request_id=req_id,
            idempotency_key=meta["idempotency_key"],
            payee_id=meta["payee_id"],
            category=meta["category"],
            amount=meta["amount"],
            provenance=meta["provenance"],
        )
        create_payout(request=req, db=db)

    # Special handling for Scenario 6: revoke mandate first
    if scenario_id == "6":
        mandate = db.query(Mandate).filter_by(agent_id="demo_revocation_agent").first()
        if mandate:
            mandate.status = "REVOKED"
            db.commit()

    req = PayoutRequest(
        agent_id=meta["agent_id"],
        request_id=req_id,
        idempotency_key=meta["idempotency_key"],
        payee_id=meta["payee_id"],
        category=meta["category"],
        amount=meta["amount"],
        provenance=meta["provenance"],
    )

    result = create_payout(request=req, db=db)

    actual_dec = result.get("decision")
    execution_status = result.get("status")
    payout_id = result.get("razorpay_payout_id")

    audit_count = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_id == meta["idempotency_key"])
        .count()
    )

    return {
        "scenario_id": scenario_id,
        "scenario_name": meta["name"],
        "description": meta["description"],
        "expected_decision": meta["expected_decision"],
        "actual_decision": actual_dec,
        "matched_expected": actual_dec == meta["expected_decision"],
        "reason_codes": result.get("reason_codes", []),
        "anomaly_score": result.get("anomaly_score"),
        "execution_status": execution_status,
        "razorpay_payout_id": payout_id,
        "transaction_id": meta["idempotency_key"],
        "audit_events_count": audit_count,
        "raw_response": result,
    }


# ─── Legacy/Compatibility Getters ────────────────────────────────────────────

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

