import pytest
from fastapi.testclient import TestClient
from gateway.main import app
from gateway.models.db import SessionLocal, Agent
from gateway.config import get_config

client = TestClient(app)

def test_soft_delete_agent():
    # Setup: Create an agent manually
    db = SessionLocal()
    agent = Agent(agent_id="test_soft_delete_agent", name="Test Agent", status="ACTIVE", is_active=True)
    db.merge(agent)
    db.commit()
    
    # 1. Deactivate the agent using the DELETE endpoint
    config = get_config()
    headers = {"X-Admin-Token": config.webhook_secret}
    
    resp = client.delete("/v1/agents/test_soft_delete_agent", headers=headers)
    assert resp.status_code == 200, f"Failed to deactivate: {resp.text}"
    
    # 2. Verify it's deactivated in the DB
    agent = db.query(Agent).filter_by(agent_id="test_soft_delete_agent").first()
    assert not agent.is_active, "Agent was not soft-deleted"
    
    # 3. Try to run a payout with the deactivated agent, it should fail policy
    payload = {
        "agent_id": "test_soft_delete_agent",
        "request_id": "req_test_inactive",
        "idempotency_key": "test_soft_delete_txn",
        "amount": 100,
        "payee_id": "ven_test",
        "category": "cloud",
        "reason": "test payout",
        "provenance": {
            "source_type": "TRUSTED_TASK",
            "source_id": "test_task",
            "source_trust": "TRUSTED",
            "payment_intent_origin": "AGENT_TOOL"
        }
    }
    
    resp = client.post("/v1/payouts", json=payload, headers={"X-Idempotency-Key": "test_soft_delete_txn"})
    # Since agent is inactive, it should return AGENT_INACTIVE status
    assert resp.status_code == 200
    assert resp.json()["decision"] == "BLOCK"
    assert "AGENT_INACTIVE" in resp.json().get("reason_codes", [])
    
    db.close()
