import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from gateway.main import app
from gateway.models.db import SessionLocal, init_db, Agent, Mandate, Transaction

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()

def setup_realistic_baseline(db: Session):
    """Setup a realistic baseline for procurement-agent manually."""
    db.query(Transaction).filter(Transaction.agent_id == "procurement-agent").delete()
    db.query(Mandate).filter(Mandate.agent_id == "procurement-agent").delete()
    db.query(Agent).filter(Agent.agent_id == "procurement-agent").delete()
    db.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(Agent(agent_id="procurement-agent", name="Procurement Agent", status="ACTIVE"))
    db.add(Mandate(
        mandate_id="man_procurement",
        agent_id="procurement-agent",
        version=1,
        effective_from=now - timedelta(days=30),
        expires_at=now + timedelta(days=365),
        daily_cap=500_000,
        weekly_cap=2_000_000,
        txn_cap=500_000,
        allowed_categories=["cloud", "software", "vendor"],
        status="ACTIVE"
    ))

    from gateway.config import get_config
    import random
    
    demo_payee_id = get_config().demo_fund_account_id
    rng = random.Random(42)

    # Insert exactly 100 transactions with realistic variation
    for d in range(100, 0, -1):
        amt = 10000 + rng.randint(-200, 200)
        days_ago = (d // 2) + 1  
        business_hour = rng.randint(9, 17) 
        minute = rng.randint(0, 59)
        t_stamp = (now - timedelta(days=days_ago)).replace(
            hour=business_hour, 
            minute=minute, 
            second=0, 
            microsecond=0
        )
        payee = demo_payee_id if d % 2 == 0 else "ven_test_normal"

        db.add(Transaction(
            txn_id=f"demo_normal_hist_{d}",
            agent_id="procurement-agent",
            payee_id=payee,
            category="cloud",
            amount=amt,
            timestamp=t_stamp,
            status="SUCCEEDED",
            razorpay_payout_id=f"pout_{d}"
        ))
    db.commit()

def test_scenario_does_not_mutate_baseline(db_session: Session):
    """
    Proves that calling the demo scenario endpoint does NOT delete,
    recreate, or rewrite existing historical transactions.
    """
    setup_realistic_baseline(db_session)
    
    # Capture state before
    txns_before = db_session.query(Transaction).filter(
        Transaction.agent_id == "procurement-agent",
        Transaction.status == "SUCCEEDED"
    ).all()
    count_before = len(txns_before)
    
    assert count_before == 100
    
    # Store the exact timestamps and IDs to ensure they are unchanged
    state_before = {t.txn_id: t.timestamp for t in txns_before}
    
    # Execute scenario 1
    response = client.post("/v1/demo/scenario/1")
    assert response.status_code == 200
    
    # Capture state after
    txns_after = db_session.query(Transaction).filter(
        Transaction.agent_id == "procurement-agent",
        Transaction.status == "SUCCEEDED",
        Transaction.txn_id.like("demo_normal_hist_%")
    ).all()
    count_after = len(txns_after)
    
    assert count_after == 100
    
    state_after = {t.txn_id: t.timestamp for t in txns_after}
    
    # Verify no transactions were deleted, added (among the baseline), or modified
    assert set(state_before.keys()) == set(state_after.keys())
    for tid, ts in state_before.items():
        assert state_after[tid] == ts, f"Transaction {tid} timestamp was modified"


def test_scenario_1_anomaly_score(db_session: Session):
    """
    Proves that a realistic historical baseline remains intact after running Scenario 1,
    and the score evaluates correctly.
    """
    setup_realistic_baseline(db_session)
    
    # Needs to reset model singleton to test the newly generated data properly
    from gateway.risk.orchestrator import reset_model_singleton
    reset_model_singleton()
    
    response = client.post("/v1/demo/scenario/1")
    assert response.status_code == 200
    data = response.json()
    
    assert data["expected_decision"] == "ALLOW"
    assert data["actual_decision"] == "ALLOW"
    assert data["matched_expected"] is True
    
    score = data["anomaly_score"]
    assert score is not None
    # We ensure it evaluates as safe for the procurement-agent baseline
    assert score < 0.42, f"Score should be below behavioral-review threshold (0.42), got {score}"
