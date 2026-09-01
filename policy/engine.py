from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from gateway.models.db import Agent, Mandate, Transaction
from gateway.models.schemas import PayoutRequest

class PolicyViolation(Exception):
    def __init__(self, reason_code: str):
        self.reason_code = reason_code
        super().__init__(self.reason_code)

def check_policy(db: Session, request: PayoutRequest) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates the deterministic policy rules.
    Returns: (is_allowed, reason_code_if_blocked, mandate_details_dict)
    Throws PolicyViolation if blocked, or just returns it. 
    Let's return (False, REASON) on block.
    """
    
    # 1. Agent exists and is active
    agent = db.query(Agent).filter(Agent.agent_id == request.agent_id).first()
    if not agent:
        return False, "AGENT_UNKNOWN", {}
    if agent.status != "ACTIVE":
        return False, "AGENT_REVOKED", {}
        
    # 2. Mandate exists and is active
    mandate = db.query(Mandate).filter(
        Mandate.agent_id == request.agent_id,
        Mandate.status == "ACTIVE"
    ).order_by(Mandate.version.desc()).first()
    
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
            
    # 7 & 8. Daily and Weekly Caps
    # For SQLite compat (and general portability without raw SQL date grouping), 
    # we can calculate rolling 24h and rolling 7 days.
    # In a true financial system, we'd align to calendar day boundaries, 
    # but rolling windows are safer for simple demo constraints.
    # Let's align to calendar day for "daily" if possible, or just 24h rolling.
    # We will use rolling 24h for "daily" and rolling 7 days for "weekly" to be simple and portable across DBs for now.
    
    time_24h_ago = now - timedelta(days=1)
    time_7d_ago = now - timedelta(days=7)
    
    # Calculate daily spend
    daily_spend = db.query(func.sum(Transaction.amount)).filter(
        Transaction.agent_id == request.agent_id,
        Transaction.timestamp >= time_24h_ago,
        Transaction.status == "COMPLETED"
    ).scalar() or 0
    
    if daily_spend + request.amount > mandate.daily_cap:
        return False, "DAILY_CAP_EXCEEDED", {}
        
    # Calculate weekly spend
    weekly_spend = db.query(func.sum(Transaction.amount)).filter(
        Transaction.agent_id == request.agent_id,
        Transaction.timestamp >= time_7d_ago,
        Transaction.status == "COMPLETED"
    ).scalar() or 0
    
    if weekly_spend + request.amount > mandate.weekly_cap:
        return False, "WEEKLY_CAP_EXCEEDED", {}
        
    mandate_details = {
        "mandate_id": mandate.mandate_id,
        "version": mandate.version,
    }
        
    return True, "PASS", mandate_details
