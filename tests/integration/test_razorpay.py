import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import hmac
import hashlib
import json
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import os
from gateway.models.db import Base, Transaction, IdempotencyRecord, Mandate, MandateUsage, Agent, WebhookEvent
from gateway.models.schemas import PayoutRequest
from gateway.config import get_config
from execution.service import ExecutionService
from gateway.client import RazorpayXClient

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Setup test data
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    agent = Agent(agent_id="agt_integ", name="Integ Agent", status="ACTIVE")
    mandate = Mandate(
        mandate_id="man_integ",
        agent_id="agt_integ",
        version=1,
        effective_from=now - timedelta(days=1),
        expires_at=now + timedelta(days=10),
        daily_cap=10000,
        weekly_cap=10000,
        txn_cap=10000,
        allowed_categories=["cloud"],
        status="ACTIVE"
    )
    usage = MandateUsage(mandate_id="man_integ", daily_usage=1000, weekly_usage=1000)
    
    txn = Transaction(
        txn_id="idemp_integ_1",
        agent_id="agt_integ",
        payee_id="ven_1",
        category="cloud",
        amount=1000,
        status="UNKNOWN"
    )
    
    idemp = IdempotencyRecord(
        idempotency_key="idemp_integ_1",
        agent_id="agt_integ",
        request_hash="hash1",
        status="UNKNOWN"
    )
    
    session.add_all([agent, mandate, usage, txn, idemp])
    session.commit()
    
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_execute_spend_429_retry():
    client = RazorpayXClient()
    
    # Mock requests.post to return 429 twice, then 200
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.json.return_value = {"error": "Rate limited"}
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"id": "pout_test123", "status": "processed"}
    
    with patch('requests.post', side_effect=[mock_response_429, mock_response_429, mock_response_200]) as mock_post:
        with patch('time.sleep', return_value=None): # Skip actual sleep
            status, payload = client.execute_payout(1000, "INR", "ven_1", "idemp_429", "cloud")
            assert status == "SUCCEEDED"
            assert payload["id"] == "pout_test123"
            assert mock_post.call_count == 3

def test_webhook_signature_validation(db_session):
    from gateway.api.webhooks import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    
    client = TestClient(app)
    
    # Override dependency
    from gateway.api.webhooks import get_db
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    
    config = get_config()
    secret = config.webhook_secret
    
    payload = {
        "event": "payout.processed",
        "payload": {
            "payout": {
                "entity": {
                    "id": "pout_integ_123",
                    "reference_id": "idemp_integ_1"
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode()
    
    # Invalid signature
    headers = {
        "x-razorpay-signature": "invalid_sig",
        "x-razorpay-event-id": "ev_123"
    }
    response = client.post("/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"
    
    # Valid signature
    valid_sig = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    headers["x-razorpay-signature"] = valid_sig
    
    response = client.post("/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert response.status_code == 200
    
    # Verify DB state updated
    txn = db_session.query(Transaction).filter_by(txn_id="idemp_integ_1").first()
    assert txn.status == "SUCCEEDED"
    
    # Duplicate webhook event test
    response = client.post("/v1/webhooks/razorpay", content=raw_body, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "already processed"
