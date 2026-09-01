import pytest
import json
from datetime import datetime, timezone

from gateway.models.db import IdempotencyRecord
from gateway.models.schemas import PayoutRequest
from policy.engine import check_policy
from policy.idempotency import hash_request
from tests.unit.test_policy import TestingSessionLocal, setup_test_data, engine
from gateway.models.db import Base

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    setup_test_data(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_identical_payload_replay(db_session):
    # INVARIANT 1 & 2: Same idempotency key + same payload -> return cached response
    req = PayoutRequest(
        agent_id="agt_1",
        idempotency_key="idemp_123",
        payee_id="ven_1",
        category="cloud",
        amount=500
    )
    
    # Simulate a previously completed request
    req_hash = hash_request(req)
    cached_payload = json.dumps({"status": "success", "txn_id": "txn_999"})
    record = IdempotencyRecord(
        idempotency_key="idemp_123",
        agent_id="agt_1",
        request_hash=req_hash,
        status="COMPLETED",
        response_payload=cached_payload
    )
    db_session.add(record)
    db_session.commit()
    
    # Run check_policy with identical payload
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    
    assert allowed is True
    assert reason == "IDEMPOTENT_REPLAY"
    assert details == {"status": "success", "txn_id": "txn_999"}

def test_different_payload_conflict(db_session):
    # INVARIANT 3: Same idempotency key + different payload -> conflict
    original_req = PayoutRequest(
        agent_id="agt_1",
        idempotency_key="idemp_123",
        payee_id="ven_1",
        category="cloud",
        amount=500
    )
    
    # Simulate a previously completed request
    req_hash = hash_request(original_req)
    record = IdempotencyRecord(
        idempotency_key="idemp_123",
        agent_id="agt_1",
        request_hash=req_hash,
        status="COMPLETED",
        response_payload=json.dumps({"status": "success"})
    )
    db_session.add(record)
    db_session.commit()
    
    # Now send a different payload (e.g. amount changed to 1000)
    different_req = PayoutRequest(
        agent_id="agt_1",
        idempotency_key="idemp_123", # same key
        payee_id="ven_1",
        category="cloud",
        amount=1000 # different amount
    )
    
    allowed, reason, details = check_policy(db_session, different_req, different_req.idempotency_key)
    
    assert allowed is False
    assert reason == "IDEMPOTENCY_KEY_CONFLICT"

def test_pending_request_wait_or_conflict(db_session):
    # INVARIANT 1: A valid idempotency key maps to exactly one logical payout operation.
    req = PayoutRequest(
        agent_id="agt_1",
        idempotency_key="idemp_123",
        payee_id="ven_1",
        category="cloud",
        amount=500
    )
    
    req_hash = hash_request(req)
    record = IdempotencyRecord(
        idempotency_key="idemp_123",
        agent_id="agt_1",
        request_hash=req_hash,
        status="PENDING"
    )
    db_session.add(record)
    db_session.commit()
    
    allowed, reason, details = check_policy(db_session, req, req.idempotency_key)
    
    assert allowed is False
    assert reason == "IDEMPOTENCY_KEY_CONFLICT"
