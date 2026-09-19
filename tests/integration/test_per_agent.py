import os
import pytest
from datetime import datetime, timezone, timedelta
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from gateway.models.db import Base, Transaction
from gateway.models.schemas import PayoutRequest, ProvenanceData
from gateway.risk.orchestrator import orchestrate_payout, reset_model_singleton, _AGENT_MODELS

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///test_governor.db")
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def reset_cache():
    reset_model_singleton()
    yield
    reset_model_singleton()

def seed_agent_history(db: Session, agent_id: str, count: int, now: datetime, base_amount: int, payee_id: str):
    rng = random.Random(agent_id) # deterministic per agent
    for d in range(count, 0, -1):
        amt = base_amount + rng.randint(-200, 200)
        days_ago = (d // 2) + 1  
        business_hour = rng.randint(9, 17) 
        minute = rng.randint(0, 59)
        t_stamp = (now - timedelta(days=days_ago)).replace(
            hour=business_hour, 
            minute=minute, 
            second=0, 
            microsecond=0
        )
        txn = Transaction(
            txn_id=f"{agent_id}_hist_{d}",
            agent_id=agent_id,
            payee_id=payee_id,
            category="cloud",
            amount=amt,
            status="SUCCEEDED",
            timestamp=t_stamp
        )
        db.add(txn)
    db.commit()

def test_A_normal_procurement_agent(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None, hour=10, minute=0)
    
    # 48 realistic transactions for procurement-agent
    seed_agent_history(db_session, "procurement-agent", 48, now, 10000, "ven_test_normal")
    
    # Noise from other agents (dense background)
    seed_agent_history(db_session, "bg-agent-1", 100, now, 5000, "ven_saas")
    seed_agent_history(db_session, "bg-agent-2", 100, now, 5000, "ven_saas")
    
    req = PayoutRequest(
        agent_id="procurement-agent",
        request_id="req_A",
        idempotency_key="idemp_A",
        amount=10000,
        payee_id="ven_test_normal",
        category="cloud",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="procurement-agent",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk, _ = orchestrate_payout(
        db_session, req, "test_A", True, "AUTHORIZED", {}
    )
    
    # Should not be REVIEW just because other agents exist
    # The anomaly score for the normal txn evaluated strictly against procurement-agent's 48 txns
    # should be low because it's completely consistent with the 48 txns.
    assert risk["decision"] == "ALLOW"
    assert "BEHAVIOR_LOW_RISK" in risk["reason_codes"]
    print(f"\nScenario A Score: {risk['anomaly_score']:.3f}")


def test_B_anomalous_procurement_agent(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None, hour=10, minute=0)
    seed_agent_history(db_session, "procurement-agent", 48, now, 10000, "ven_test_normal")
    
    req = PayoutRequest(
        agent_id="procurement-agent",
        request_id="req_B",
        idempotency_key="idemp_B",
        amount=50000, # Highly anomalous amount
        payee_id="ven_anomalous", # Novel payee
        category="marketing", # Novel category
        timestamp=now.replace(hour=3), # Anomalous time
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="procurement-agent",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk, _ = orchestrate_payout(
        db_session, req, "test_B", True, "AUTHORIZED", {}
    )
    
    assert risk["decision"] == "REVIEW"
    assert "BEHAVIOR_REVIEW_REQUIRED" in risk["reason_codes"]


def test_C_policy_violation(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    seed_agent_history(db_session, "procurement-agent", 48, now, 10000, "ven_test_normal")
    
    req = PayoutRequest(
        agent_id="procurement-agent",
        request_id="req_C",
        idempotency_key="idemp_C",
        amount=10000,
        payee_id="ven_test_normal",
        category="cloud",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="procurement-agent",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk, _ = orchestrate_payout(
        db_session, req, "test_C", False, "POLICY_VIOLATION", {}
    )
    
    assert risk["decision"] == "DENY"
    assert "POLICY_VIOLATION" in risk["reason_codes"]


def test_D_unknown_agent(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    req = PayoutRequest(
        agent_id="unknown-agent",
        request_id="req_D",
        idempotency_key="idemp_D",
        amount=10000,
        payee_id="ven_test_normal",
        category="cloud",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="unknown-agent",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk, _ = orchestrate_payout(
        db_session, req, "test_D", False, "UNKNOWN_AGENT", {}
    )
    
    assert risk["decision"] == "DENY"
    assert "UNKNOWN_AGENT" in risk["reason_codes"]


def test_E_malicious_intent(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    seed_agent_history(db_session, "procurement-agent", 48, now, 10000, "ven_test_normal")
    
    req = PayoutRequest(
        agent_id="procurement-agent",
        request_id="req_E",
        idempotency_key="idemp_E",
        amount=10000,
        payee_id="ven_test_normal",
        category="cloud",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="UNTRUSTED_WEB_HOOK",
            source_id="external_123",
            source_trust="UNTRUSTED", # Provenance violation
            payment_intent_origin="EXTERNAL_UNVERIFIED"
        )
    )
    
    risk, _ = orchestrate_payout(
        db_session, req, "test_E", True, "AUTHORIZED", {}
    )
    
    assert risk["decision"] == "DENY"
    assert "PROVENANCE_UNTRUSTED_SOURCE" in risk["reason_codes"]


def test_F_sparse_history_agent(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Only 19 transactions (below MIN_HISTORY = 20)
    seed_agent_history(db_session, "new-agent", 19, now, 10000, "ven_test_normal")
    
    req = PayoutRequest(
        agent_id="new-agent",
        request_id="req_F",
        idempotency_key="idemp_F",
        amount=10000,
        payee_id="ven_test_normal",
        category="cloud",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="new-agent",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk, _ = orchestrate_payout(
        db_session, req, "test_F", True, "AUTHORIZED", {}
    )
    
    assert risk["decision"] == "REVIEW"
    assert "INSUFFICIENT_BEHAVIORAL_HISTORY" in risk["reason_codes"]
    assert risk["anomaly_score"] is None


def test_G_failed_eval(db_session: Session):
    # Test model/evaluation failure -> REVIEW
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    seed_agent_history(db_session, "procurement-agent", 48, now, 10000, "ven_test_normal")
    
    # We can force a failure by providing bad data or just mocking it.
    # Instead, we test that if `get_or_train_agent_model` throws, it degrades safely.
    from unittest.mock import patch
    with patch("gateway.risk.orchestrator.get_or_train_agent_model", side_effect=Exception("Model exploded")):
        req = PayoutRequest(
            agent_id="procurement-agent",
            request_id="req_G",
            idempotency_key="idemp_G",
            amount=10000,
            payee_id="ven_test_normal",
            category="cloud",
            timestamp=now,
            provenance=ProvenanceData(
                source_type="AGENT",
                source_id="procurement-agent",
                source_trust="TRUSTED",
                payment_intent_origin="INTERNAL_SYSTEM"
            )
        )
        risk, _ = orchestrate_payout(
            db_session, req, "test_G", True, "AUTHORIZED", {}
        )
        
        assert risk["decision"] == "REVIEW"
        assert "BEHAVIOR_EVALUATION_FAILED" in risk["reason_codes"]


def test_H_cross_agent_isolation(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Agent A has 48 txns
    seed_agent_history(db_session, "agent-A", 48, now, 10000, "ven_test_normal")
    
    # Agent B has 48 highly different txns
    seed_agent_history(db_session, "agent-B", 48, now, 500000, "ven_luxury")
    
    # Evaluate Agent A with A's normal txn
    req_A = PayoutRequest(
        agent_id="agent-A",
        request_id="req_H1",
        idempotency_key="idemp_H1",
        amount=10000,
        payee_id="ven_test_normal",
        category="cloud",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="agent-A",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk_A, _ = orchestrate_payout(
        db_session, req_A, "test_H_A", True, "AUTHORIZED", {}
    )
    
    assert risk_A["decision"] == "ALLOW"
    
    # If Agent A issues B's normal txn, it should be highly anomalous for A
    req_A_abnormal = PayoutRequest(
        agent_id="agent-A",
        request_id="req_H2",
        idempotency_key="idemp_H2",
        amount=500000,
        payee_id="ven_luxury",
        category="luxury",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="agent-A",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk_A_abnormal, _ = orchestrate_payout(
        db_session, req_A_abnormal, "test_H_A_abnormal", True, "AUTHORIZED", {}
    )
    
    assert risk_A_abnormal["decision"] == "REVIEW"


def test_I_temporal_isolation(db_session: Session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Give agent 19 valid historical transactions (below threshold)
    seed_agent_history(db_session, "temporal-agent", 19, now, 10000, "ven_test_normal")
    
    # Insert one transaction exactly AT the payout timestamp
    txn_at_now = Transaction(
        txn_id="temporal_hist_at_now",
        agent_id="temporal-agent",
        payee_id="ven_test_normal",
        category="cloud",
        amount=10000,
        status="SUCCEEDED",
        timestamp=now
    )
    db_session.add(txn_at_now)
    
    # Insert one transaction AFTER the payout timestamp
    txn_after = Transaction(
        txn_id="temporal_hist_after",
        agent_id="temporal-agent",
        payee_id="ven_test_normal",
        category="cloud",
        amount=10000,
        status="SUCCEEDED",
        timestamp=now + timedelta(hours=1)
    )
    db_session.add(txn_after)
    db_session.commit()
    
    # Evaluate payout AT 'now'
    req = PayoutRequest(
        agent_id="temporal-agent",
        request_id="req_I",
        idempotency_key="idemp_I",
        amount=10000,
        payee_id="ven_test_normal",
        category="cloud",
        timestamp=now,
        provenance=ProvenanceData(
            source_type="AGENT",
            source_id="temporal-agent",
            source_trust="TRUSTED",
            payment_intent_origin="INTERNAL_SYSTEM"
        )
    )
    
    risk, _ = orchestrate_payout(
        db_session, req, "test_I", True, "AUTHORIZED", {}
    )
    
    # Even though there are 21 successful txns in DB, only 19 are STRICTLY BEFORE 'now'.
    # Therefore, the model should see <20 txns and trigger INSUFFICIENT_BEHAVIORAL_HISTORY.
    assert risk["decision"] == "REVIEW"
    assert "INSUFFICIENT_BEHAVIORAL_HISTORY" in risk["reason_codes"]
    assert risk["anomaly_score"] is None
