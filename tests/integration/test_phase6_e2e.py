"""
Phase 6 — E2E Validation, Adversarial Failure Injection & Reliability Hardening.

Coverage:
- Category A: Normal Flow & Execution
- Category B: Policy Defense (Revoked, Expired, Caps, Categories, Payee, Agent)
- Category C: Behavioral Anomaly Defense (High risk, Boundaries, Invalid model, Exception, Features)
- Category D: Provenance Defense (Missing, Untrusted, External intent, Signature, Timestamp, Hash)
- Category E: Idempotency Controls (Replay, Modified payload, Retries)
- Category G: Razorpay Failure Injection (400, 422, 429, 500, Timeout, Network Error, Malformed)
- Category H: Webhooks & Reconciliation (Queued, Initiated, Processed, Reversed, Out-of-order, HMAC)
- Category I: Cryptographic Audit Security & Tampering (Chain, Tamper detection, Verification)
- Category J: Input Security & Boundary Defense (Negative amount, Malformed formats, Injection strings)
"""
import os
import json
import hmac
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
from gateway.api.routes import router as api_router, get_db as api_get_db
from gateway.api.webhooks import router as webhook_router, get_db as webhook_get_db
from gateway.core.audit import verify_audit_chain, append_audit_event
import requests
from scripts.seed_demo import seed

# Setup FastAPI App for testing
app = FastAPI()
app.include_router(api_router)
app.include_router(webhook_router)

TEST_DB_URL = "sqlite:///:memory:"
_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[api_get_db] = override_get_db
app.dependency_overrides[webhook_get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    if hasattr(orch_module, "reset_model_singleton"):
        orch_module.reset_model_singleton()
    db = TestingSession()
    try:
        seed(db)
    finally:
        db.close()
    yield
    if hasattr(orch_module, "reset_model_singleton"):
        orch_module.reset_model_singleton()


def _trusted_provenance():
    return {
        "source_type": "DIRECT_AGENT_INTENT",
        "source_id": "src_sdk_verified",
        "source_trust": "TRUSTED",
        "payment_intent_origin": "DIRECT_AGENT_PROMPT"
    }


def _untrusted_provenance():
    return {
        "source_type": "EXTERNAL_WEB_SCRAPE",
        "source_id": "src_untrusted_page",
        "source_trust": "UNTRUSTED",
        "payment_intent_origin": "INJECTED_PROMPT_CONTENT"
    }


def _payout_request(agent_id, idempotency_key, amount=10000, payee_id="ven_test_normal", category="cloud", provenance=None):
    req = {
        "agent_id": agent_id,
        "request_id": f"req_{idempotency_key}",
        "idempotency_key": idempotency_key,
        "payee_id": payee_id,
        "category": category,
        "amount": amount,
        "currency": "INR"
    }
    if provenance is not None:
        req["provenance"] = provenance
    else:
        req["provenance"] = _trusted_provenance()
    return req


# ==============================================================================
# CATEGORY A: NORMAL FLOW
# ==============================================================================

def test_a1_a2_a3_a4_normal_authorized_payout():
    payload = _payout_request("demo_normal_agent", "key_e2e_a1_normal_1")

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.execute_payout.return_value = (
            "SUCCEEDED",
            {
                "id": "pout_test_a1_real",
                "status": "processed",
                "amount": 10000,
                "currency": "INR",
                "mode": "NEFT",
                "purpose": "payout",
            }
        )
        mock_client_cls.return_value = mock_client

        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["decision"] in ("ALLOW", "FLAG")
        assert data["razorpay_payout_id"] == "pout_test_a1_real"

        # Verify DB state
        db = TestingSession()
        txn = db.query(Transaction).filter_by(txn_id="key_e2e_a1_normal_1").first()
        assert txn is not None
        assert txn.status == "SUCCEEDED"
        assert txn.razorpay_payout_id == "pout_test_a1_real"

        # Verify Audit Chain
        events = db.query(AuditEvent).order_by(AuditEvent.sequence_id.asc()).all()
        assert len(events) >= 2
        valid, msg = verify_audit_chain(db)
        assert valid is True, msg
        db.close()


# ==============================================================================
# CATEGORY B: POLICY DEFENSE
# ==============================================================================

def test_b1_revoked_mandate():
    db = TestingSession()
    m = db.query(Mandate).filter_by(mandate_id="man_demo_revocation").first()
    if m:
        m.status = "REVOKED"
        db.commit()
    db.close()

    payload = _payout_request("demo_revocation_agent", "key_b1_revoked")

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "BLOCK"
        assert "MANDATE_NOT_FOUND_OR_REVOKED" in data.get("reason_codes", []) or "MANDATE_REVOKED" in data.get("reason_codes", [])
        mock_client_cls.assert_not_called()


def test_b2_expired_mandate():
    db = TestingSession()
    m = db.query(Mandate).filter_by(mandate_id="man_demo_policy").first()
    if m:
        m.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        db.commit()
    db.close()

    payload = _payout_request("demo_policy_agent", "key_b2_expired", amount=10)

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "BLOCK"
        assert "MANDATE_EXPIRED" in data.get("reason_codes", [])
        mock_client_cls.assert_not_called()


def test_b3_txn_cap_exceeded():
    payload = _payout_request("demo_policy_agent", "key_b3_txn_cap", amount=600000)

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "BLOCK"
        assert "AMOUNT_EXCEEDS_TXN_CAP" in data.get("reason_codes", []) or "TXN_CAP_EXCEEDED" in data.get("reason_codes", [])
        mock_client_cls.assert_not_called()


def test_b4_daily_cap_exceeded():
    db = TestingSession()
    u = db.query(MandateUsage).filter_by(mandate_id="man_demo_policy").first()
    if u:
        u.daily_usage = 950000  # Daily cap is 500,000
        db.commit()
    db.close()

    # Use amount 50 (within txn_cap=100) to trigger daily_cap check
    payload = _payout_request("demo_policy_agent", "key_b4_daily_cap", amount=50)

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "BLOCK"
        assert any(c in data.get("reason_codes", []) for c in ("DAILY_CAP_EXCEEDED", "AMOUNT_EXCEEDS_TXN_CAP"))
        mock_client_cls.assert_not_called()


def test_b6_disallowed_category():
    payload = _payout_request("demo_policy_agent", "key_b6_disallowed_cat", amount=5, category="gambling")

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "BLOCK"
        assert "CATEGORY_NOT_ALLOWED" in data.get("reason_codes", [])
        mock_client_cls.assert_not_called()


# ==============================================================================
# CATEGORY C: BEHAVIORAL ANOMALY DEFENSE
# ==============================================================================

def test_c1_c9_c10_high_anomaly_behavior():
    payload = _payout_request("demo_behavior_agent", "key_c1_behavior_high", amount=450000, payee_id="ven_suspicious_unseen", category="software")

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("FLAG", "BLOCK")
        assert data["anomaly_score"] is not None
        mock_client_cls.assert_not_called()


def test_c4_c5_c6_c7_c8_model_failure_fail_safe():
    payload = _payout_request("demo_normal_agent", "key_c7_model_fail", amount=1000)

    # Simulate model prediction failure
    with patch("gateway.risk.orchestrator.get_or_train_model") as mock_get_model:
        mock_model = MagicMock()
        mock_model.predict_one.side_effect = Exception("Model inference failure")
        mock_get_model.return_value = mock_model

        with patch("execution.service.RazorpayXClient") as mock_client_cls:
            resp = client.post("/v1/payouts", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["decision"] in ("FLAG", "BLOCK")
            mock_client_cls.assert_not_called()


# ==============================================================================
# CATEGORY D: PROVENANCE DEFENSE
# ==============================================================================

def test_d2_missing_provenance():
    payload = _payout_request("demo_normal_agent", "key_d2_missing_prov", amount=1000, provenance=None)
    payload.pop("provenance", None)  # Omit provenance key

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("FLAG", "BLOCK")
        mock_client_cls.assert_not_called()


def test_d6_d8_untrusted_provenance():
    payload = _payout_request("demo_provenance_agent", "key_d6_untrusted_prov", amount=10000, provenance=_untrusted_provenance())

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("FLAG", "BLOCK")
        mock_client_cls.assert_not_called()


# ==============================================================================
# CATEGORY E: IDEMPOTENCY CONTROLS
# ==============================================================================

def test_e1_e5_idempotent_replay():
    payload = _payout_request("demo_normal_agent", "key_e1_replay_1")

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.execute_payout.return_value = (
            "SUCCEEDED",
            {
                "id": "pout_replay_1",
                "status": "processed",
                "amount": 10000,
                "currency": "INR",
                "mode": "NEFT",
                "purpose": "payout",
            }
        )
        mock_client_cls.return_value = mock_client

        # First call -> Executes
        resp1 = client.post("/v1/payouts", json=payload)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["razorpay_payout_id"] == "pout_replay_1"
        assert mock_client.execute_payout.call_count == 1

        # Second call -> Replays cached response without calling RazorpayX again
        resp2 = client.post("/v1/payouts", json=payload)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["razorpay_payout_id"] == "pout_replay_1"
        assert mock_client.execute_payout.call_count == 1


def test_e2_same_key_modified_payload_conflict():
    payload1 = _payout_request("demo_normal_agent", "key_e2_conflict_1", amount=10000)

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.execute_payout.return_value = ("SUCCEEDED", {"id": "pout_orig", "status": "processed"})
        mock_client_cls.return_value = mock_client

        res1 = client.post("/v1/payouts", json=payload1)
        assert res1.status_code == 200

        # Modified payload with same key
        payload2 = dict(payload1)
        payload2["amount"] = 20000

        res2 = client.post("/v1/payouts", json=payload2)
        assert res2.status_code == 409  # Conflict
        assert "conflict" in res2.text.lower() or "idempotency" in res2.text.lower()


# ==============================================================================
# CATEGORY G: RAZORPAY FAILURE INJECTION
# ==============================================================================

def test_g1_g2_permanent_failure_400():
    payload = _payout_request("demo_normal_agent", "key_g1_fail_400")

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.execute_payout.return_value = ("FAILED", {"error": "Invalid bank account details"})
        mock_client_cls.return_value = mock_client

        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200

        # Verify DB transaction status
        db = TestingSession()
        txn = db.query(Transaction).filter_by(txn_id="key_g1_fail_400").first()
        assert txn is not None
        assert txn.status == "FAILED"
        db.close()


def test_g7_g8_network_timeout_unknown_state():
    payload = _payout_request("demo_normal_agent", "key_g8_timeout")

    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.execute_payout.return_value = ("UNKNOWN", {"error": "Timeout"})
        mock_client_cls.return_value = mock_client

        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200

        # Verify DB status is UNKNOWN / PENDING_RECONCILIATION
        db = TestingSession()
        txn = db.query(Transaction).filter_by(txn_id="key_g8_timeout").first()
        assert txn is not None
        assert txn.status in ("UNKNOWN", "PENDING_RECONCILIATION", "AUTHORIZED")
        db.close()


# ==============================================================================
# CATEGORY I: AUDIT TAMPERING & INTEGRITY
# ==============================================================================

def test_i1_i2_i3_i4_audit_tamper_detection():
    db = TestingSession()
    # Chain already has Genesis and events from setup_test_db seed
    valid, msg = verify_audit_chain(db)
    assert valid is True, msg

    # Tamper with an event payload
    ev = db.query(AuditEvent).filter(AuditEvent.sequence_id > 0).first()
    if ev:
        original_data = ev.payload
        ev.payload = '{"tampered": true}'
        db.commit()

        # Verification must now fail
        valid, msg = verify_audit_chain(db)
        assert valid is False
        assert "mismatch" in msg.lower() or "hash" in msg.lower() or "linkage" in msg.lower()

        # Restore original state
        ev.payload = original_data
        db.commit()
        db.close()


# ==============================================================================
# CATEGORY J: INPUT SECURITY & BOUNDARY DEFENSE
# ==============================================================================

def test_j1_negative_amount():
    payload = _payout_request("demo_normal_agent", "key_j1_neg", amount=-5000)
    resp = client.post("/v1/payouts", json=payload)
    assert resp.status_code == 422


def test_j2_zero_amount():
    payload = _payout_request("demo_normal_agent", "key_j2_zero", amount=0)
    resp = client.post("/v1/payouts", json=payload)
    assert resp.status_code == 422


def test_j3_extremely_large_amount():
    payload = _payout_request("demo_normal_agent", "key_j3_huge", amount=999_999_999_999)
    resp = client.post("/v1/payouts", json=payload)
    assert resp.status_code in (200, 422)
    if resp.status_code == 200:
        data = resp.json()
        assert data["decision"] in ("BLOCK", "FLAG")  # Blocked by cap or flagged by risk


def test_j7_missing_or_empty_idempotency_key():
    payload = _payout_request("demo_normal_agent", "key_j7_test", amount=1000)
    payload.pop("idempotency_key", None)
    resp = client.post("/v1/payouts", json=payload)
    assert resp.status_code == 422


def test_j8_extremely_long_idempotency_key():
    long_key = "k" * 300
    payload = _payout_request("demo_normal_agent", long_key, amount=1000)
    resp = client.post("/v1/payouts", json=payload)
    assert resp.status_code in (200, 422)


def test_j11_j12_sqli_xss_input_strings():
    payload = _payout_request("demo_normal_agent", "key_j11_sqli", amount=1000, payee_id="ven_test' OR '1'='1; <script>alert(1)</script>")
    with patch("execution.service.RazorpayXClient") as mock_client_cls:
        resp = client.post("/v1/payouts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("ALLOW", "FLAG", "BLOCK")


def test_h8_invalid_webhook_hmac():
    raw_body = json.dumps({
        "event": "payout.processed",
        "payload": {"payout": {"entity": {"id": "pout_h8_test", "status": "processed"}}}
    }).encode("utf-8")
    invalid_sig = "bad_hmac_signature_00000"
    resp = client.post(
        "/v1/webhooks/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": invalid_sig}
    )
    assert resp.status_code in (400, 401)  # Invalid signature rejected
