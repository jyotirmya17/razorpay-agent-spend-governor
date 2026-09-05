"""
Phase 5 REST API Integration Tests.

Tests all new Phase 5 backend endpoints:
- GET /v1/health
- GET /v1/overview/stats
- GET /v1/transactions
- GET /v1/transactions/{id}/full
- GET /v1/agents
- GET /v1/agents/{id}/detail
- GET /v1/mandates
- POST /v1/mandates/{id}/revoke
- GET /v1/risk/overview
- GET /v1/audit/events
- POST /v1/audit/verify
- POST /v1/demo/scenario/{scenario_id}
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gateway.main import app
from gateway.api.routes import get_db
from gateway.models.db import Base, Agent, Mandate, MandateUsage, Transaction, AuditEvent
from scripts.seed_demo import seed

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/governor_test")
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from gateway.risk.orchestrator import reset_model_singleton
    reset_model_singleton()
    db_seed = TestingSessionLocal()
    try:
        seed(db_seed)
    finally:
        db_seed.close()
    reset_model_singleton()
    yield
    reset_model_singleton()


def test_health_endpoint():
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "components" in data
    assert data["components"]["api"]["status"] == "healthy"
    assert data["components"]["postgres"]["status"] in ("healthy", "ready")
    assert data["components"]["audit_chain"]["valid"] is True


def test_overview_stats_endpoint():
    resp = client.get("/v1/overview/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_agents"] >= 5
    assert data["active_mandates"] >= 4
    assert "decisions" in data
    assert "ALLOW" in data["decisions"]


def test_transactions_listing_and_filtering():
    client.post("/v1/demo/scenario/1")
    client.post("/v1/demo/scenario/2")

    resp = client.get("/v1/transactions?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 2
    assert len(data["items"]) <= 10

    resp_search = client.get("/v1/transactions?search=demo_normal_agent")
    assert resp_search.status_code == 200
    assert len(resp_search.json()["items"]) >= 1


def test_transaction_full_investigation():
    r = client.post("/v1/demo/scenario/1")
    txn_id = r.json()["transaction_id"]

    resp = client.get(f"/v1/transactions/{txn_id}/full")
    assert resp.status_code == 200
    data = resp.json()
    assert "request" in data
    assert "policy" in data
    assert "behavior" in data
    assert "provenance" in data
    assert "decision" in data
    assert "execution" in data
    assert "audit" in data
    assert data["request"]["txn_id"] == txn_id
    assert data["decision"]["decision"] == "ALLOW"


def test_agents_listing_and_detail():
    resp = client.get("/v1/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) >= 5
    agent_ids = [a["agent_id"] for a in agents]
    assert "demo_normal_agent" in agent_ids

    resp_detail = client.get("/v1/agents/demo_normal_agent/detail")
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["agent_id"] == "demo_normal_agent"
    assert "mandate" in detail
    assert detail["mandate"]["daily_cap"] == 500000


def test_mandates_listing_and_revocation():
    resp = client.get("/v1/mandates")
    assert resp.status_code == 200
    mandates = resp.json()
    assert len(mandates) >= 5

    man_id = "man_demo_revocation"
    resp_revoke = client.post(f"/v1/mandates/{man_id}/revoke")
    assert resp_revoke.status_code == 200
    assert resp_revoke.json()["status"] == "REVOKED"

    resp_check = client.get("/v1/mandates")
    revoked_mandate = next(m for m in resp_check.json() if m["mandate_id"] == man_id)
    assert revoked_mandate["status"] == "REVOKED"


def test_risk_overview_endpoint():
    client.post("/v1/demo/scenario/3")
    client.post("/v1/demo/scenario/4")

    resp = client.get("/v1/risk/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_evaluations" in data
    assert "score_buckets" in data
    assert "reason_code_frequencies" in data


def test_audit_events_and_verification():
    client.post("/v1/demo/scenario/1")
    resp_events = client.get("/v1/audit/events?page=1&page_size=20")
    assert resp_events.status_code == 200
    assert "items" in resp_events.json()
    assert len(resp_events.json()["items"]) > 0

    resp_verify = client.post("/v1/audit/verify")
    assert resp_verify.status_code == 200
    v = resp_verify.json()
    assert v["valid"] is True
    assert v["events_checked"] > 0


def test_all_six_demo_scenarios():
    scenarios = [
        ("1", "ALLOW"),
        ("2", "BLOCK"),
        ("3", "FLAG"),
        ("4", "FLAG"),
        ("5", "IDEMPOTENT_REPLAY"),
        ("6", "BLOCK"),
    ]

    for scenario_id, expected_dec in scenarios:
        resp = client.post(f"/v1/demo/scenario/{scenario_id}")
        assert resp.status_code == 200
        res = resp.json()
        assert res["scenario_id"] == scenario_id
        assert res["actual_decision"] == expected_dec
        assert res["matched_expected"] is True

        if expected_dec in ("BLOCK", "FLAG"):
            assert res["razorpay_payout_id"] is None


def test_scenario_1_uses_real_execution_service():
    from unittest.mock import patch
    with patch("execution.service.RazorpayXClient") as MockClient:
        MockClient.return_value.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_rzp_test_real_001"})
        resp = client.post("/v1/demo/scenario/1")
        assert resp.status_code == 200
        res = resp.json()
        assert res["actual_decision"] == "ALLOW"
        assert res["execution_status"] == "SUCCEEDED"
        assert res["razorpay_payout_id"] == "pout_rzp_test_real_001"
        assert not res["razorpay_payout_id"].startswith("pout_mock_")
        MockClient.return_value.execute_payout.assert_called_once()


def test_demo_scenarios_razorpayx_gating():
    from unittest.mock import patch
    with patch("execution.service.RazorpayXClient") as MockClient:
        # Scenarios 2, 3, 4, 6 must NEVER reach execution service
        for s_id in ["2", "3", "4", "6"]:
            client.post(f"/v1/demo/scenario/{s_id}")
        MockClient.return_value.execute_payout.assert_not_called()


def test_demo_scenarios_audit_integrity():
    # Verify audit chain remains cryptographically valid after running demo scenarios
    client.post("/v1/demo/scenario/1")
    client.post("/v1/demo/scenario/3")
    resp = client.post("/v1/audit/verify")
    assert resp.status_code == 200
    assert resp.json()["valid"] is True

