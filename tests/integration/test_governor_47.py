"""
Phase 4.7 integration tests — 16 mocked scenarios.

All tests use an in-memory SQLite DB (via override_get_db) and mock
RazorpayXClient so that no real Razorpay calls are made during pytest.

Decision precedence verified:
  1. Policy BLOCK -> never reaches ExecutionService
  2. Model failure -> FLAG, never ALLOW
  3. Behavioral FLAG -> never reaches ExecutionService
  4. Provenance FLAG -> never reaches ExecutionService
  5. ALLOW -> ExecutionService called exactly once
"""
import json
import hashlib
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import gateway.risk.orchestrator as orch_module

from gateway.models.db import (
    Base, Agent, Mandate, MandateUsage, Transaction,
    IdempotencyRecord, AuditEvent, ProvenanceRecord,
)
from gateway.api.routes import router, get_db

# ─── Shared test DB ──────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///:memory:"
_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True)
def reset_model_singleton():
    """Reset the cached model singleton between tests."""
    original = orch_module._MODEL_SINGLETON
    orch_module._MODEL_SINGLETON = None
    yield
    orch_module._MODEL_SINGLETON = original


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    session = TestingSession()

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    def make_agent(agent_id, name="Test Agent"):
        session.add(Agent(agent_id=agent_id, name=name, status="ACTIVE"))

    def make_mandate(mandate_id, agent_id, txn_cap=500_000, status="ACTIVE"):
        session.add(Mandate(
            mandate_id=mandate_id, agent_id=agent_id, version=1,
            effective_from=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
            daily_cap=1_000_000, weekly_cap=5_000_000, txn_cap=txn_cap,
            allowed_categories=["cloud", "vendor", "software"],
            status=status,
        ))
        session.add(MandateUsage(mandate_id=mandate_id, daily_usage=0, weekly_usage=0))

    make_agent("agt_normal")
    make_mandate("man_normal", "agt_normal")

    make_agent("agt_policy")
    make_mandate("man_policy", "agt_policy", txn_cap=50)  # cap = 0.50 INR

    make_agent("agt_behavior")
    make_mandate("man_behavior", "agt_behavior")

    make_agent("agt_provenance")
    make_mandate("man_provenance", "agt_provenance")

    make_agent("agt_revocation")
    make_mandate("man_revocation", "agt_revocation")

    make_agent("agt_model_fail")
    make_mandate("man_model_fail", "agt_model_fail")

    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def client(db_session):
    app = FastAPI()
    app.include_router(router)

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    return TestClient(app, raise_server_exceptions=True)


def payout_body(agent_id, idempotency_key, amount=10_000, provenance=None):
    body = {
        "agent_id": agent_id,
        "request_id": f"req_{idempotency_key}",
        "idempotency_key": idempotency_key,
        "payee_id": "ven_test",
        "category": "cloud",
        "amount": amount,
    }
    if provenance is not None:
        body["provenance"] = provenance
    return body


# ─── 1. Normal ALLOW ─────────────────────────────────────────────────────────

def test_normal_allow(client, db_session):
    """ALLOW path: policy passes, low behavior score, trusted provenance -> RazorpayX called once."""
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_test_001"})

            resp = client.post("/v1/payouts", json=payout_body(
                "agt_normal", "idemp_normal_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "task_1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))

    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "ALLOW"
    assert body["status"] == "SUCCEEDED"


# ─── 2. Policy BLOCK ─────────────────────────────────────────────────────────

def test_policy_block_does_not_call_razorpay(client, db_session):
    """Amount exceeds txn_cap -> BLOCK. RazorpayX must not be called."""
    with patch("execution.service.RazorpayXClient") as MockClient:
        resp = client.post("/v1/payouts", json=payout_body(
            "agt_policy", "idemp_policy_001", amount=10_000,  # cap is 50
            provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
        ))
        MockClient.return_value.execute_payout.assert_not_called()

    body = resp.json()
    assert body["decision"] == "BLOCK"
    assert "AMOUNT_EXCEEDS_TXN_CAP" in body["reason_codes"]


# ─── 3. Behavioral FLAG ───────────────────────────────────────────────────────

def test_behavioral_flag_does_not_call_razorpay(client, db_session):
    """High anomaly score -> FLAG. RazorpayX must not be called."""
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.85, "prediction": "ANOMALY", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            resp = client.post("/v1/payouts", json=payout_body(
                "agt_behavior", "idemp_behavior_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))
            MockClient.return_value.execute_payout.assert_not_called()

    body = resp.json()
    assert body["decision"] == "FLAG"
    assert "BEHAVIOR_REVIEW_REQUIRED" in body["reason_codes"]


# ─── 4. Provenance FLAG ───────────────────────────────────────────────────────

def test_provenance_flag_does_not_call_razorpay(client, db_session):
    """UNTRUSTED external content provenance -> FLAG even when behavior is low risk."""
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            resp = client.post("/v1/payouts", json=payout_body(
                "agt_provenance", "idemp_prov_001",
                provenance={"source_type": "EXTERNAL_CONTENT", "source_id": "ext_1", "source_trust": "UNTRUSTED", "payment_intent_origin": "EXTERNAL_CONTENT"}
            ))
            MockClient.return_value.execute_payout.assert_not_called()

    body = resp.json()
    assert body["decision"] == "FLAG"
    assert "PROVENANCE_UNTRUSTED_SOURCE" in body["reason_codes"]


# ─── 5. Missing provenance -> UNKNOWN -> FLAG ─────────────────────────────────

def test_missing_provenance_defaults_to_unknown_flag(client, db_session):
    """No provenance field in request -> defaults to UNKNOWN -> FLAG. Never TRUSTED."""
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            resp = client.post("/v1/payouts", json=payout_body(
                "agt_provenance", "idemp_prov_missing_001"
                # no provenance field
            ))
            MockClient.return_value.execute_payout.assert_not_called()

    body = resp.json()
    assert body["decision"] == "FLAG"
    assert "PROVENANCE_UNKNOWN_SOURCE" in body["reason_codes"]


# ─── 6. Idempotent Replay ─────────────────────────────────────────────────────

def test_idempotent_replay(client, db_session):
    """Same idempotency key twice -> second is IDEMPOTENT_REPLAY, Razorpay called once."""
    req_body = payout_body(
        "agt_normal", "idemp_replay_001",
        provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
    )

    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_replay_001"})

            resp1 = client.post("/v1/payouts", json=req_body)
            resp2 = client.post("/v1/payouts", json=req_body)

            assert mock_client_instance.execute_payout.call_count == 1

    assert resp1.json()["decision"] == "ALLOW"
    assert resp2.json()["decision"] == "IDEMPOTENT_REPLAY"


# ─── 7. Idempotency Conflict ──────────────────────────────────────────────────

def test_idempotency_conflict(client, db_session):
    """Same idempotency key with different amount -> HTTP 409."""
    provenance = {"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}

    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_conflict_01"})

            client.post("/v1/payouts", json=payout_body("agt_normal", "idemp_conflict_001", amount=1000, provenance=provenance))
            resp2 = client.post("/v1/payouts", json=payout_body("agt_normal", "idemp_conflict_001", amount=9999, provenance=provenance))

    assert resp2.status_code == 409
    assert "IDEMPOTENCY_KEY_CONFLICT" in resp2.json()["detail"]["reason"]


# ─── 8. Mandate Revocation ────────────────────────────────────────────────────

def test_mandate_revocation(client, db_session):
    """Revoke mandate between requests -> second request BLOCK."""
    provenance = {"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}

    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_revoc_01"})
            r1 = client.post("/v1/payouts", json=payout_body("agt_revocation", "idemp_revoc_001", provenance=provenance))

    assert r1.json()["decision"] == "ALLOW"

    # Revoke mandate in DB
    mandate = db_session.query(Mandate).filter_by(agent_id="agt_revocation").first()
    mandate.status = "REVOKED"
    db_session.commit()

    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            r2 = client.post("/v1/payouts", json=payout_body("agt_revocation", "idemp_revoc_002", provenance=provenance))
            MockClient.return_value.execute_payout.assert_not_called()

    assert r2.json()["decision"] == "BLOCK"


# ─── 9. Model Failure -> FLAG (never ALLOW) ───────────────────────────────────

def test_model_failure_flags(client, db_session):
    """Behavioral model raising an exception -> FLAG with BEHAVIOR_EVALUATION_FAILED."""
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_model.side_effect = RuntimeError("model error")

        with patch("execution.service.RazorpayXClient") as MockClient:
            resp = client.post("/v1/payouts", json=payout_body(
                "agt_model_fail", "idemp_fail_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))
            MockClient.return_value.execute_payout.assert_not_called()

    body = resp.json()
    assert body["decision"] == "FLAG"
    assert "BEHAVIOR_EVALUATION_FAILED" in body["reason_codes"]


# ─── 10. ALLOW calls Razorpay exactly once ────────────────────────────────────

def test_allow_calls_razorpay_exactly_once(client, db_session):
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            mock_client_instance = MockClient.return_value
            mock_client_instance.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_once_001"})

            client.post("/v1/payouts", json=payout_body(
                "agt_normal", "idemp_once_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))

            assert mock_client_instance.execute_payout.call_count == 1


# ─── 11. Audit events are generated ──────────────────────────────────────────

def test_audit_events_generated(client, db_session):
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            MockClient.return_value.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_audit_01"})
            client.post("/v1/payouts", json=payout_body(
                "agt_normal", "idemp_audit_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))

    events = db_session.query(AuditEvent).filter_by(entity_id="idemp_audit_001").order_by(AuditEvent.sequence_id).all()
    event_types = [e.event_type for e in events]

    assert "governor.policy_evaluated" in event_types
    assert "governor.behavior_evaluated" in event_types
    assert "governor.provenance_evaluated" in event_types
    assert "governor.decision_made" in event_types
    assert "razorpay.payout_created" in event_types


# ─── 12. Audit chain verification ────────────────────────────────────────────

def test_audit_chain_is_valid(client, db_session):
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            MockClient.return_value.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_chain_01"})
            client.post("/v1/payouts", json=payout_body(
                "agt_normal", "idemp_chain_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))

    from scripts.verify_audit_chain import verify
    import os; os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    # Verify the chain directly using the session-level state
    events = db_session.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
    GENESIS = "0" * 64
    expected_prev = GENESIS
    for event in events:
        assert event.previous_event_hash == expected_prev, f"Chain broken at seq {event.sequence_id}"
        canon = json.dumps(json.loads(event.payload), sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256()
        h.update(expected_prev.encode())
        h.update(canon.encode())
        assert event.event_hash == h.hexdigest(), f"Hash mismatch at seq {event.sequence_id}"
        expected_prev = event.event_hash


# ─── 13. Audit tampering detection ───────────────────────────────────────────

def test_audit_tampering_detected(client, db_session):
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            MockClient.return_value.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_tamper_01"})
            client.post("/v1/payouts", json=payout_body(
                "agt_normal", "idemp_tamper_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))

    # Tamper with first event payload
    first_event = db_session.query(AuditEvent).order_by(AuditEvent.sequence_id).first()
    first_event.payload = json.dumps({"tampered": True})
    db_session.commit()

    # Verify chain inline (same logic as verify_audit_chain.py)
    events = db_session.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
    GENESIS = "0" * 64
    expected_prev = GENESIS
    chain_valid = True
    for event in events:
        canon = json.dumps(json.loads(event.payload), sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256()
        h.update(expected_prev.encode())
        h.update(canon.encode())
        if event.event_hash != h.hexdigest():
            chain_valid = False
            break
        expected_prev = event.event_hash

    assert not chain_valid, "Tampered chain should be detected as INVALID"


# ─── 14. Concurrent audit append (chain serialization) ───────────────────────

def test_concurrent_audit_append_sqlite(db_session):
    """
    Verifies audit append correctness on the sequential path (single session).

    PostgreSQL's SELECT ... FOR UPDATE is the production serialization mechanism
    for concurrent appends. SQLite does not support FOR UPDATE, so multi-threaded
    concurrent appends via SQLite may produce hash-chain races (expected).

    This test verifies that:
    - All 5 sequential events are appended to the chain
    - Each event's event_hash is correctly computed from its own stored
      previous_event_hash and payload (i.e., no hash computation bug)

    The PostgreSQL concurrency guarantee is covered by the Phase 2 concurrency
    test suite (tests/unit/test_concurrency.py).
    """
    from gateway.core.audit import append_audit_event

    GENESIS = "0" * 64

    # Sequential appends via a single session (guaranteed ordering)
    for i in range(5):
        append_audit_event(db_session, f"test.event.{i}", "txn_seq_concurrent", {"n": i})
    db_session.commit()

    events = db_session.query(AuditEvent).filter_by(entity_id="txn_seq_concurrent").order_by(AuditEvent.sequence_id).all()

    assert len(events) == 5, f"Expected 5 events, got {len(events)}"

    # Verify each event's hash is correctly self-consistent
    for event in events:
        canon = json.dumps(json.loads(event.payload), sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256()
        h.update(event.previous_event_hash.encode())
        h.update(canon.encode())
        assert event.event_hash == h.hexdigest(), (
            f"Hash mismatch at seq {event.sequence_id}: stored={event.event_hash}, expected={h.hexdigest()}"
        )

    # Verify chain linkage for sequential appends
    expected_prev = GENESIS
    for event in events:
        assert event.previous_event_hash == expected_prev, (
            f"Chain break at seq {event.sequence_id}"
        )
        expected_prev = event.event_hash



# ─── 15. Aggregate reason codes (behavior + provenance) ──────────────────────

def test_behavioral_and_provenance_reasons_aggregated(client, db_session):
    """High anomaly + untrusted provenance -> FLAG with BOTH reason codes."""
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.85, "prediction": "ANOMALY", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            resp = client.post("/v1/payouts", json=payout_body(
                "agt_behavior", "idemp_agg_001",
                provenance={"source_type": "EXTERNAL_CONTENT", "source_id": "ext_1", "source_trust": "UNTRUSTED", "payment_intent_origin": "EXTERNAL_CONTENT"}
            ))
            MockClient.return_value.execute_payout.assert_not_called()

    body = resp.json()
    assert body["decision"] == "FLAG"
    assert "BEHAVIOR_REVIEW_REQUIRED" in body["reason_codes"]
    assert "PROVENANCE_UNTRUSTED_SOURCE" in body["reason_codes"]


# ─── 16. GET /v1/transactions, /v1/agents, /v1/audit, /v1/risk ───────────────

def test_get_endpoints(client, db_session):
    """Read endpoints return correct state from DB."""
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_model:
        mock_m = MagicMock()
        mock_m.is_fitted = True
        mock_m.predict_one.return_value = {"anomaly_score": 0.10, "prediction": "NORMAL", "model_version": "behavioral_iforest_v1"}
        mock_model.return_value = mock_m

        with patch("execution.service.RazorpayXClient") as MockClient:
            MockClient.return_value.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_get_01"})
            client.post("/v1/payouts", json=payout_body(
                "agt_normal", "idemp_get_001",
                provenance={"source_type": "TRUSTED_TASK", "source_id": "t1", "source_trust": "TRUSTED", "payment_intent_origin": "AGENT_TOOL"}
            ))

    assert client.get("/v1/transactions/idemp_get_001").status_code == 200
    assert client.get("/v1/agents/agt_normal").status_code == 200
    assert client.get("/v1/audit/idemp_get_001").status_code == 200
    assert client.get("/v1/risk/idemp_get_001").status_code == 200
    assert client.get("/v1/transactions/nonexistent").status_code == 404
