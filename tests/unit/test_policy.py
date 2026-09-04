import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gateway.models.db import Base, Agent, Mandate, Transaction
from gateway.models.schemas import PayoutRequest
from policy.engine import check_policy

import os
# Use PostgreSQL as primary for tests
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/governor_test")

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

def setup_test_data(db):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    agent_active = Agent(agent_id="agt_1", name="Test Agent", status="ACTIVE")
    agent_revoked = Agent(agent_id="agt_revoked", name="Revoked Agent", status="REVOKED")
    
    mandate_active = Mandate(
        mandate_id="man_1",
        agent_id="agt_1",
        version=1,
        effective_from=now - timedelta(days=1),
        expires_at=now + timedelta(days=10),
        daily_cap=100000,
        weekly_cap=500000,
        txn_cap=50000,
        allowed_categories=["cloud", "software"],
        allowed_payees=["ven_1", "ven_2"],
        status="ACTIVE"
    )
    
    mandate_expired = Mandate(
        mandate_id="man_2",
        agent_id="agt_1",
        version=2,
        effective_from=now - timedelta(days=10),
        expires_at=now - timedelta(days=1),
        daily_cap=100000,
        weekly_cap=500000,
        txn_cap=50000,
        allowed_categories=["cloud"],
        allowed_payees=None,
        status="EXPIRED"
    )
    
    db.add(agent_active)
    db.add(agent_revoked)
    db.commit()
    
    db.add(mandate_active)
    db.add(mandate_expired)
    db.commit()

def test_agent_unknown(db_session):
    req = PayoutRequest(
        agent_id="agt_missing",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_1",
        category="cloud",
        amount=100
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    assert reason == "AGENT_UNKNOWN"

def test_agent_revoked(db_session):
    setup_test_data(db_session)
    req = PayoutRequest(
        agent_id="agt_revoked",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_1",
        category="cloud",
        amount=100
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    assert reason == "AGENT_REVOKED"

def test_mandate_expired(db_session):
    # Temporarily set the active mandate to revoked to test the expired one
    setup_test_data(db_session)
    m = db_session.query(Mandate).filter(Mandate.mandate_id == "man_1").first()
    m.status = "REVOKED"
    db_session.commit()
    
    req = PayoutRequest(
        agent_id="agt_1",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_1",
        category="cloud",
        amount=100
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    # Note: engine.py currently fetches the latest ACTIVE mandate. If none is active, it returns MANDATE_NOT_FOUND_OR_REVOKED.
    assert reason == "MANDATE_NOT_FOUND_OR_REVOKED"

def test_valid_request(db_session):
    setup_test_data(db_session)
    req = PayoutRequest(
        agent_id="agt_1",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_1",
        category="cloud",
        amount=1000
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert allowed
    assert reason == "AUTHORIZED"
    assert details["mandate_id"] == "man_1"

def test_amount_exceeds_txn_cap(db_session):
    setup_test_data(db_session)
    req = PayoutRequest(
        agent_id="agt_1",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_1",
        category="cloud",
        amount=50001
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    assert reason == "AMOUNT_EXCEEDS_TXN_CAP"

def test_category_not_allowed(db_session):
    setup_test_data(db_session)
    req = PayoutRequest(
        agent_id="agt_1",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_1",
        category="marketing",
        amount=1000
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    assert reason == "CATEGORY_NOT_ALLOWED"

def test_payee_not_allowed(db_session):
    setup_test_data(db_session)
    req = PayoutRequest(
        agent_id="agt_1",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_3",
        category="cloud",
        amount=1000
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    assert reason == "PAYEE_NOT_ALLOWED"

def test_daily_cap_exceeded(db_session):
    setup_test_data(db_session)
    # Add usage that consumes the daily cap
    from gateway.models.db import MandateUsage
    mu = MandateUsage(
        mandate_id="man_1",
        daily_usage=99000,
        weekly_usage=99000
    )
    db_session.add(mu)
    db_session.commit()
    
    req = PayoutRequest(
        agent_id="agt_1",
        request_id="req_1",
        idempotency_key="id_1",
        payee_id="ven_1",
        category="cloud",
        amount=2000  # 99000 + 2000 = 101000 > 100000
    )
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    assert not allowed
    assert reason == "DAILY_CAP_EXCEEDED"
