import pytest
import os
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/governor_test")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(DATABASE_URL)
    
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from gateway.models.db import Base, Agent, Mandate, MandateUsage, Transaction, IdempotencyRecord
from gateway.models.schemas import PayoutRequest
from policy.engine import check_policy
from execution.service import ExecutionService
from unittest.mock import patch
from policy.idempotency import check_idempotency

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Setup test data
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    agent = Agent(agent_id="agt_exec", name="Exec Agent", status="ACTIVE")
    mandate = Mandate(
        mandate_id="man_exec",
        agent_id="agt_exec",
        version=1,
        effective_from=now - timedelta(days=1),
        expires_at=now + timedelta(days=10),
        daily_cap=10000,
        weekly_cap=10000,
        txn_cap=10000,
        allowed_categories=["cloud"],
        status="ACTIVE"
    )
    usage = MandateUsage(mandate_id="man_exec", daily_usage=0, weekly_usage=0)
    
    session.add(agent)
    session.flush()
    session.add(mandate)
    session.flush()
    session.add(usage)
    session.commit()
    
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_successful_execution(db_session):
    req = PayoutRequest(
        agent_id="agt_exec",
        request_id="req_1",
        idempotency_key="idemp_1",
        payee_id="ven_1",
        category="cloud",
        amount=1000
    )
    
    # 1. Authorize
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert allowed
    assert reason == "AUTHORIZED"
    db_session.commit()
    
    # 2. Execute
    service = ExecutionService()
    with patch.object(service.client, 'execute_payout', return_value=("SUCCEEDED", {"id": "pout_123"})):
        service.execute_spend(db_session, req, req.idempotency_key)
    
    # 3. Verify SUCCESS state
    txn = db_session.query(Transaction).filter_by(txn_id=req.idempotency_key).first()
    assert txn.status == "SUCCEEDED"
    
    usage = db_session.query(MandateUsage).filter_by(mandate_id="man_exec").first()
    assert usage.daily_usage == 1000  # Usage is maintained

def test_explicit_failure_execution(db_session):
    req = PayoutRequest(
        agent_id="agt_exec",
        request_id="req_fail",
        idempotency_key="idemp_fail",
        payee_id="ven_1",
        category="cloud",
        amount=999 # Amount 999 is hardcoded to fail
    )
    
    # 1. Authorize
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert allowed
    db_session.commit()
    
    usage_before = db_session.query(MandateUsage).filter_by(mandate_id="man_exec").first().daily_usage
    assert usage_before == 999
    
    # 2. Execute (simulating explicit failure)
    service = ExecutionService()
    with patch.object(service.client, 'execute_payout', return_value=("FAILED", {"error": "bad request"})):
        service.execute_spend(db_session, req, req.idempotency_key)
    
    # 3. Verify FAILED state and usage rollback
    txn = db_session.query(Transaction).filter_by(txn_id=req.idempotency_key).first()
    assert txn.status == "FAILED"
    
    usage_after = db_session.query(MandateUsage).filter_by(mandate_id="man_exec").first().daily_usage
    assert usage_after == 0  # Rolled back

def test_timeout_and_reconciliation(db_session):
    req = PayoutRequest(
        agent_id="agt_exec",
        request_id="req_timeout",
        idempotency_key="idemp_timeout",
        payee_id="ven_1",
        category="cloud",
        amount=888 # Amount 888 is hardcoded to timeout
    )
    
    # 1. Authorize
    check_policy(db_session, req, req.idempotency_key)
    db_session.commit()
    
    # 2. Execute (simulating timeout)
    service = ExecutionService()
    with patch.object(service.client, 'execute_payout', return_value=("UNKNOWN", {"error": "timeout"})):
        service.execute_spend(db_session, req, req.idempotency_key)
    
    # 3. Verify UNKNOWN state
    txn = db_session.query(Transaction).filter_by(txn_id=req.idempotency_key).first()
    assert txn.status == "UNKNOWN"
    
    usage_after = db_session.query(MandateUsage).filter_by(mandate_id="man_exec").first().daily_usage
    assert usage_after == 888  # Usage NOT rolled back for UNKNOWN
    
    # 4. Reconcile as FAILED
    service.reconcile_spend(db_session, req.idempotency_key, "FAILED", req.agent_id, req.amount)
    
    # 5. Verify FAILED state and usage rollback
    txn_recon = db_session.query(Transaction).filter_by(txn_id=req.idempotency_key).first()
    assert txn_recon.status == "FAILED"
    
    usage_final = db_session.query(MandateUsage).filter_by(mandate_id="man_exec").first().daily_usage
    assert usage_final == 0

def test_bounded_idempotency_wait(db_session):
    # Simulate a crashed worker leaving a PENDING record
    req = PayoutRequest(
        agent_id="agt_exec",
        request_id="req_crash",
        idempotency_key="idemp_crash",
        payee_id="ven_1",
        category="cloud",
        amount=1000
    )
    
    from policy.idempotency import create_idempotency_record
    create_idempotency_record(db_session, req.agent_id, req.idempotency_key, req)
    db_session.commit()
    
    # Try again with the same request, since it's fresh (not stale), it will poll and return UNKNOWN_IN_PROGRESS
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    assert reason == "UNKNOWN_IN_PROGRESS"
