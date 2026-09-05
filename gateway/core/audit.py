"""
Tamper-evident audit service.

Chain ordering: strictly by sequence_id (autoincrement PK).
previous_event_hash is the event_hash of the row with the highest sequence_id
at the time of insert.

Serialization strategy
----------------------
PostgreSQL: pg_advisory_xact_lock(AUDIT_LOCK_KEY) is called at the start of
every append.  This is a transaction-scoped exclusive advisory lock that
PostgreSQL automatically releases on commit or rollback.  Unlike
SELECT ... FOR UPDATE, advisory locks serialize access even when the table is
completely empty (which is the critical case that SELECT ... FOR UPDATE fails
to handle — it locks zero rows and therefore allows concurrent forks).

SQLite: advisory locks are not available.  We fall back to
SELECT ... FOR UPDATE (a no-op in SQLite) because SQLite uses
connection-level serialization and the test suite uses a single shared
connection, making concurrent-thread forks impossible in practice.

The audit-chain lock is NEVER held across external Razorpay calls.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from gateway.models.db import AuditEvent


GENESIS_HASH = "0" * 64  # canonical genesis sentinel

# Stable 64-bit key for the advisory lock.  Must be the same across all
# processes / connections.  Any non-zero constant works; we use a fixed
# value derived from the application name.
_AUDIT_LOCK_KEY = 5_897_322_347  # "audit_chain" → stable literal


def _canonical_payload(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _is_postgresql(db: Session) -> bool:
    """Returns True if the underlying dialect is PostgreSQL."""
    return db.bind.dialect.name == "postgresql"


def append_audit_event(db: Session, event_type: str, entity_id: str, payload: dict) -> AuditEvent:
    """
    Appends one event to the tamper-evident audit chain.

    Serialization:
      PostgreSQL — acquires pg_advisory_xact_lock(_AUDIT_LOCK_KEY) before
                   reading the tail.  This prevents concurrent forks even on
                   an empty table (the case SELECT...FOR UPDATE cannot handle).
      SQLite     — falls back to SELECT...FOR UPDATE (single-connection
                   serialization is sufficient for test use).

    The lock is transaction-scoped and is automatically released on commit
    or rollback.  It is never held across external calls.
    """
    if _is_postgresql(db):
        # Acquire exclusive transaction-scoped advisory lock.
        # Blocks if another transaction holds the same key.
        db.execute(text(f"SELECT pg_advisory_xact_lock({_AUDIT_LOCK_KEY})"))
        last_event = (
            db.query(AuditEvent)
            .order_by(AuditEvent.sequence_id.desc())
            .first()
        )
    else:
        # SQLite path: FOR UPDATE is a no-op but documents intent.
        last_event = (
            db.query(AuditEvent)
            .order_by(AuditEvent.sequence_id.desc())
            .with_for_update()
            .first()
        )

    previous_hash = last_event.event_hash if last_event else GENESIS_HASH
    canon = _canonical_payload(payload)

    hasher = hashlib.sha256()
    hasher.update(previous_hash.encode("utf-8"))
    hasher.update(canon.encode("utf-8"))
    new_hash = hasher.hexdigest()

    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        event_type=event_type,
        entity_id=entity_id,
        payload=canon,
        previous_event_hash=previous_hash,
        event_hash=new_hash,
    )
    db.add(event)
    db.flush()  # assigns sequence_id inside the current transaction
    return event
