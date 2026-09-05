"""
verify_audit_chain.py — Tamper-evident audit chain verifier.

Usage:
  python scripts/verify_audit_chain.py

Expected outputs:
  AUDIT CHAIN VALID         — all event hashes match and chain is unbroken
  AUDIT CHAIN INVALID       — at least one hash mismatch detected

Ordering: strictly by sequence_id (monotonic autoincrement), not timestamp.
This matches the append_audit_event() implementation exactly.
"""
import os
import sys
import hashlib
import json

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.models.db import SessionLocal, AuditEvent, init_db

GENESIS_HASH = "0" * 64


def canonical_payload(payload_str: str) -> str:
    """Re-serialise the stored payload string to ensure canonical form."""
    parsed = json.loads(payload_str)
    return json.dumps(parsed, sort_keys=True, separators=(",", ":"))


def verify():
    init_db()
    db = SessionLocal()
    try:
        events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()

        if not events:
            print("AUDIT CHAIN VALID (empty chain)")
            return True

        expected_previous = GENESIS_HASH
        valid = True

        for event in events:
            # 1. Verify previous_event_hash linkage
            if event.previous_event_hash != expected_previous:
                print(f"AUDIT CHAIN INVALID")
                print(f"  sequence_id={event.sequence_id} event_id={event.event_id}")
                print(f"  Expected previous_hash: {expected_previous}")
                print(f"  Stored  previous_hash:  {event.previous_event_hash}")
                valid = False

            # 2. Recalculate event_hash from stored previous + payload
            canon = canonical_payload(event.payload)
            hasher = hashlib.sha256()
            hasher.update(event.previous_event_hash.encode("utf-8"))
            hasher.update(canon.encode("utf-8"))
            expected_hash = hasher.hexdigest()

            if event.event_hash != expected_hash:
                print(f"AUDIT CHAIN INVALID")
                print(f"  sequence_id={event.sequence_id} event_id={event.event_id}")
                print(f"  Expected event_hash: {expected_hash}")
                print(f"  Stored  event_hash:  {event.event_hash}")
                valid = False

            expected_previous = event.event_hash

        if valid:
            print(f"AUDIT CHAIN VALID ({len(events)} events verified)")
        return valid

    finally:
        db.close()


if __name__ == "__main__":
    ok = verify()
    sys.exit(0 if ok else 1)
