import pytest
import json
from fastapi.testclient import TestClient
from gateway.main import app
from gateway.models.db import SessionLocal, AuditEvent

client = TestClient(app)

def test_audit_tampering_detection():
    # First, run a demo scenario to ensure we have some audit events
    client.post("/v1/demo/scenario/1")
    
    db = SessionLocal()
    
    # Get the last event
    last_event = db.query(AuditEvent).order_by(AuditEvent.sequence_id.desc()).first()
    assert last_event is not None, "No audit events found to tamper with"
    
    # Verify the chain is initially valid
    resp = client.post("/v1/audit/verify")
    assert resp.status_code == 200
    assert resp.json()["valid"] is True, "Audit chain was not initially valid"
    
    # Tamper with the event directly in the database
    # Modify the payload string slightly (e.g., replace an amount or just append a space)
    original_payload = last_event.payload
    tampered_payload = original_payload.replace("10000", "99999")
    if tampered_payload == original_payload:
        tampered_payload += " " # fallback tamper
        
    last_event.payload = tampered_payload
    db.commit()
    
    # Verify the chain again, it should fail
    resp = client.post("/v1/audit/verify")
    assert resp.status_code == 200
    assert resp.json()["valid"] is False, "Audit chain validation failed to detect tampering"
    assert resp.json()["reason"] == "EVENT_HASH_MISMATCH", "Unexpected tampering reason"
    
    # Restore the original payload so other tests don't fail
    last_event.payload = original_payload
    db.commit()
    db.close()
