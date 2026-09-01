from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from gateway.models.db import Agent, Mandate, Transaction, MandateUsage
from gateway.models.schemas import PayoutRequest
from policy.idempotency import check_idempotency, create_idempotency_record

def check_policy(db: Session, request: PayoutRequest, idempotency_key: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates the deterministic policy rules.
    Returns: (is_allowed, reason_code_if_blocked, mandate_details_dict)
    Throws PolicyViolation if blocked, or just returns it. 
    Let's return (False, REASON) on block.
    """
    
    # 0. Idempotency Check
    is_conflict, is_cached, cached_response = check_idempotency(db, request.agent_id, idempotency_key, request)
    if is_conflict:
        return False, "IDEMPOTENCY_KEY_CONFLICT", {}
    if is_cached:
        return True, "IDEMPOTENT_REPLAY", cached_response

    # 1. Agent exists and is active
    agent = db.query(Agent).filter(Agent.agent_id == request.agent_id).first()
    if not agent:
        return False, "AGENT_UNKNOWN", {}
    if agent.status != "ACTIVE":
        return False, "AGENT_REVOKED", {}
        
    # 2. Mandate exists and is active
    # We use with_for_update() to serialize access to the mandate for the duration of this transaction
    mandate = db.query(Mandate).filter(
        Mandate.agent_id == request.agent_id,
        Mandate.status == "ACTIVE"
    ).order_by(Mandate.version.desc()).with_for_update().first()
    
    if not mandate:
        # Might be revoked or suspended
        return False, "MANDATE_NOT_FOUND_OR_REVOKED", {}
        
    # 3. Mandate has not expired
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if now < mandate.effective_from:
        return False, "MANDATE_NOT_YET_EFFECTIVE", {}
    if now > mandate.expires_at:
        return False, "MANDATE_EXPIRED", {}
        
    # 4. Amount <= per-transaction cap
    if request.amount > mandate.txn_cap:
        return False, "AMOUNT_EXCEEDS_TXN_CAP", {}
        
    # 5. Category is allowed
    if request.category not in mandate.allowed_categories:
        return False, "CATEGORY_NOT_ALLOWED", {}
        
    # 6. Payee is allowed (if scoping is active)
    if mandate.allowed_payees is not None:
        if request.payee_id not in mandate.allowed_payees:
            return False, "PAYEE_NOT_ALLOWED", {}
            
    # 7 & 8. Daily and Weekly Caps using MandateUsage
    usage = db.query(MandateUsage).filter(
        MandateUsage.mandate_id == mandate.mandate_id
    ).with_for_update().first()
    
    if not usage:
        usage = MandateUsage(mandate_id=mandate.mandate_id, daily_usage=0, weekly_usage=0)
        db.add(usage)
        db.flush() # Ensure it's locked and visible
        
    # Check if we need to reset usage (simplified rolling/calendar boundary check)
    # For a robust system we'd reset at midnight. For now, if > 24h passed, reset daily.
    if (now - usage.last_reset_date).days >= 1:
        usage.daily_usage = 0
        if (now - usage.last_reset_date).days >= 7:
            usage.weekly_usage = 0
        usage.last_reset_date = now
    
    if usage.daily_usage + request.amount > mandate.daily_cap:
        return False, "DAILY_CAP_EXCEEDED", {}
        
    if usage.weekly_usage + request.amount > mandate.weekly_cap:
        return False, "WEEKLY_CAP_EXCEEDED", {}
        
    # 9. Authorization successful, commit the usage (reservation)
    usage.daily_usage += request.amount
    usage.weekly_usage += request.amount
    
    # 10. Record idempotency pending
    create_idempotency_record(db, request.agent_id, idempotency_key, request)
        
    mandate_details = {
        "mandate_id": mandate.mandate_id,
        "version": mandate.version,
    }
        
    return True, "PASS", mandate_details
