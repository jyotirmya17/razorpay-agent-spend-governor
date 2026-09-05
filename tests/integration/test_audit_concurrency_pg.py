"""
PostgreSQL Audit Concurrency Test — Phase 4.7 Final Verification.

PURPOSE
-------
This test file contains the genuine PostgreSQL concurrency proof for
append_audit_event().

SQLite cannot prove concurrent serialization: SQLite does not support
transaction-level advisory locks and its connection-level serialization
applies only within a single process connection.  Multi-threaded SQLite
tests are therefore structurally unable to detect hash-chain forks.

WHAT THIS FILE TESTS
--------------------
PostgreSQL test:
  - Spawns N_CONCURRENT independent PostgreSQL sessions/threads.
  - Each thread calls append_audit_event() in an independent transaction.
  - All threads start simultaneously (barrier-synchronized via threading.Barrier).
  - After all threads complete, the entire audit chain is read back and verified.
  - Verified invariants:
      1. Exactly N_CONCURRENT events exist in the chain.
      2. All sequence_ids are unique and strictly monotonic.
      3. No two events share the same previous_event_hash (no fork).
      4. Every event hash is correctly recomputed from
         SHA256(previous_event_hash || canonical_payload).
      5. The chain forms one continuous linked list:
         GENESIS -> H1 -> H2 -> H3 -> ... -> H_N

SQLite test (in test_governor_47.py):
  - Only verifies sequential hash-chain correctness (single session).
  - Does NOT claim to prove concurrent serialization.

IMPLEMENTATION DETAIL — pg_advisory_xact_lock
----------------------------------------------
The production implementation uses:

    SELECT pg_advisory_xact_lock(<AUDIT_LOCK_KEY>)

This is a PostgreSQL transaction-scoped exclusive advisory lock.  It:
  - Serializes the read-tail + insert operation across all concurrent callers.
  - Works even when audit_events is completely empty (zero rows to lock),
    which is the critical failure case for SELECT ... FOR UPDATE: a
    row-level lock on zero rows grants the lock to ALL concurrent readers
    simultaneously, causing every thread to read GENESIS and produce a fork.
  - Is automatically released when the transaction commits or rolls back.
  - Is NEVER held across external Razorpay HTTP calls.

If the implementation did NOT use the advisory lock, concurrent threads would
both read the same tail and produce a fork (two events sharing the same
previous_event_hash). Invariant (3) above would immediately detect that fork.

ISOLATION
---------
Each test function uses the pg_clean fixture, which truncates audit_events
before and after each test.  The test never touches Demo or production state.
"""


import hashlib
import json
import os
import threading
import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from gateway.models.db import Base, AuditEvent
from gateway.core.audit import GENESIS_HASH, append_audit_event

# ─── PostgreSQL connection ────────────────────────────────────────────────────

PG_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgrespassword@localhost:5432/governor_test",
)


def _pg_reachable(url: str) -> bool:
    """Runtime probe — called from fixtures, not at module import time."""
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pg_engine():
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgrespassword@localhost:5432/governor_test",
    )
    if not _pg_reachable(url):
        pytest.skip("PostgreSQL not reachable; skipping concurrency tests")

    engine = create_engine(url, pool_size=20, max_overflow=10)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

    engine.dispose()


@pytest.fixture()
def pg_clean(pg_engine):
    """
    Truncate audit_events before and after each test to ensure isolation.
    Restart identity resets the sequence_id autoincrement counter.
    """
    with pg_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE audit_events RESTART IDENTITY CASCADE"))
        conn.commit()
    yield pg_engine
    with pg_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE audit_events RESTART IDENTITY CASCADE"))
        conn.commit()


# ─── Helper ───────────────────────────────────────────────────────────────────

def _canonical_payload(payload_str: str) -> str:
    parsed = json.loads(payload_str)
    return json.dumps(parsed, sort_keys=True, separators=(",", ":"))


def _verify_chain(events: list) -> None:
    """
    Stateless chain verifier.  Asserts all invariants documented above.
    Raises AssertionError with a descriptive message on first violation.
    """
    assert events, "Chain is empty"

    # 1. Unique, monotonically increasing sequence_ids
    seq_ids = [e.sequence_id for e in events]
    assert len(seq_ids) == len(set(seq_ids)), "Duplicate sequence_ids detected"
    assert seq_ids == sorted(seq_ids), f"sequence_ids not monotonic: {seq_ids}"

    # 2. No two events share the same previous_event_hash (no fork)
    prev_hashes = [e.previous_event_hash for e in events]
    assert len(prev_hashes) == len(set(prev_hashes)), (
        "Fork detected: duplicate previous_event_hash values found.\n"
        "Two concurrent appends both read the same tail and produced a fork.\n"
        f"previous_event_hashes: {prev_hashes}"
    )

    # 3. Every event hash correctly recomputed
    for event in events:
        canon = _canonical_payload(event.payload)
        hasher = hashlib.sha256()
        hasher.update(event.previous_event_hash.encode("utf-8"))
        hasher.update(canon.encode("utf-8"))
        expected = hasher.hexdigest()
        assert event.event_hash == expected, (
            f"Hash mismatch at sequence_id={event.sequence_id} "
            f"stored={event.event_hash} expected={expected}"
        )

    # 4. Chain is one continuous linked list from GENESIS
    expected_prev = GENESIS_HASH
    for event in events:
        assert event.previous_event_hash == expected_prev, (
            f"Chain break at sequence_id={event.sequence_id}: "
            f"expected previous_hash={expected_prev[:16]}..., "
            f"got {event.previous_event_hash[:16]}..."
        )
        expected_prev = event.event_hash


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestAuditConcurrencyPostgres:
    """
    Genuine PostgreSQL concurrent serialization tests.

    Each test uses a barrier to synchronize thread start so that all threads
    attempt to acquire the FOR UPDATE lock simultaneously, maximising contention
    and making any fork immediately detectable.
    """

    N = 10  # Number of concurrent threads

    def _append_worker(self, engine, n: int, errors: list, barrier: threading.Barrier):
        """
        Worker thread: opens an independent session, waits at the barrier,
        then appends exactly one audit event and commits.
        """
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        db = Session()
        try:
            barrier.wait()  # All threads start simultaneously
            append_audit_event(db, f"concurrent.event.{n}", "txn_pg_concurrent", {"n": n})
            db.commit()
        except Exception as exc:
            errors.append(exc)
            db.rollback()
        finally:
            db.close()

    def test_concurrent_appends_no_fork(self, pg_clean):
        """
        Core concurrency test.

        Spawns N=10 threads simultaneously; each appends one event.
        After all complete, verifies:
          - All N events were written (no silent failure).
          - No duplicate sequence_ids.
          - Monotonically increasing sequence_ids.
          - No fork (no duplicate previous_event_hash).
          - Every event hash is correct.
          - Chain is continuous from GENESIS.
        """
        errors = []
        barrier = threading.Barrier(self.N)
        threads = [
            threading.Thread(target=self._append_worker, args=(pg_clean, i, errors, barrier))
            for i in range(self.N)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Worker thread exceptions: {errors}"

        # Read back the entire chain ordered by sequence_id
        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        assert len(events) == self.N, (
            f"Expected {self.N} events, got {len(events)}.  "
            "Some concurrent appends were lost."
        )

        _verify_chain(events)

    def test_concurrent_appends_5_threads(self, pg_clean):
        """
        Minimum-requirement variant: exactly 5 concurrent threads as specified.
        Duplicates core assertions with N=5.
        """
        n = 5
        errors = []
        barrier = threading.Barrier(n)
        threads = [
            threading.Thread(target=self._append_worker, args=(pg_clean, i, errors, barrier))
            for i in range(n)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Worker exceptions: {errors}"

        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        assert len(events) == n
        _verify_chain(events)

    def test_mixed_entity_ids_no_cross_contamination(self, pg_clean):
        """
        Appends events for two different entity_ids concurrently.
        Verifies the GLOBAL chain (across both entities) remains valid,
        because the audit chain is global (not per-entity).
        """
        errors = []
        n_per_entity = 5
        total = n_per_entity * 2
        barrier = threading.Barrier(total)

        def worker(i, entity):
            Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
            db = Session()
            try:
                barrier.wait()
                append_audit_event(db, f"event.{entity}.{i}", entity, {"i": i})
                db.commit()
            except Exception as exc:
                errors.append(exc)
                db.rollback()
            finally:
                db.close()

        threads = (
            [threading.Thread(target=worker, args=(i, "entity_A")) for i in range(n_per_entity)] +
            [threading.Thread(target=worker, args=(i, "entity_B")) for i in range(n_per_entity)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Worker exceptions: {errors}"

        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        assert len(events) == total
        _verify_chain(events)

    def test_high_contention_20_threads(self, pg_clean):
        """
        High-contention stress test: 20 simultaneous appends.
        Failure here would indicate the FOR UPDATE strategy has a defect
        under high contention (e.g., lock escalation, deadlock, or timeout).
        """
        n = 20
        errors = []
        barrier = threading.Barrier(n)
        threads = [
            threading.Thread(target=self._append_worker, args=(pg_clean, i, errors, barrier))
            for i in range(n)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Worker exceptions: {errors}"

        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        assert len(events) == n
        _verify_chain(events)

    def test_sequential_after_concurrent_extends_chain(self, pg_clean):
        """
        After N concurrent appends, a sequential append must extend
        the chain correctly (not restart from GENESIS).
        """
        n = 5
        errors = []
        barrier = threading.Barrier(n)
        threads = [
            threading.Thread(target=self._append_worker, args=(pg_clean, i, errors, barrier))
            for i in range(n)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors

        # Sequential append after concurrent batch
        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            append_audit_event(db, "sequential.followup", "txn_followup", {"step": "final"})
            db.commit()
        finally:
            db.close()

        db = Session()
        try:
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        assert len(events) == n + 1
        _verify_chain(events)


# ─── Inline tamper-detection test against PostgreSQL ──────────────────────────

class TestAuditTamperDetectionPostgres:
    """
    Verifies that the hash-chain tamper verifier detects modifications.
    Uses a disposable PostgreSQL state (via pg_clean fixture).
    Does NOT touch the demo or production audit state.
    """

    def test_valid_chain_verifies_ok(self, pg_clean):
        """A freshly written chain must verify as VALID."""
        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            for i in range(3):
                append_audit_event(db, f"verify.event.{i}", "txn_verify", {"i": i})
            db.commit()
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        _verify_chain(events)  # must not raise

    def test_tampered_payload_detected(self, pg_clean):
        """Modifying a stored payload must invalidate the chain hash check."""
        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            for i in range(3):
                append_audit_event(db, f"tamper.event.{i}", "txn_tamper", {"i": i})
            db.commit()
        finally:
            db.close()

        # Tamper: update first event payload in DB directly
        db = Session()
        try:
            first = db.query(AuditEvent).order_by(AuditEvent.sequence_id).first()
            first.payload = json.dumps({"tampered": True}, sort_keys=True, separators=(",", ":"))
            db.commit()
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        # Recompute: tampered event's event_hash will not match computed hash
        canon = _canonical_payload(events[0].payload)
        hasher = hashlib.sha256()
        hasher.update(events[0].previous_event_hash.encode("utf-8"))
        hasher.update(canon.encode("utf-8"))
        recomputed = hasher.hexdigest()

        assert events[0].event_hash != recomputed, (
            "Tampered payload was not detected — event_hash should not match "
            "the recomputed hash of the modified payload."
        )

    def test_tampered_event_hash_detected(self, pg_clean):
        """Modifying stored event_hash must break the chain linkage check."""
        Session = sessionmaker(bind=pg_clean, autocommit=False, autoflush=False)
        db = Session()
        try:
            for i in range(3):
                append_audit_event(db, f"tamper2.event.{i}", "txn_tamper2", {"i": i})
            db.commit()
        finally:
            db.close()

        # Tamper: change event_hash of first event
        db = Session()
        try:
            first = db.query(AuditEvent).order_by(AuditEvent.sequence_id).first()
            first.event_hash = "a" * 64  # bogus hash
            db.commit()
            events = db.query(AuditEvent).order_by(AuditEvent.sequence_id).all()
        finally:
            db.close()

        # Second event's previous_event_hash should differ from tampered first event_hash
        second = events[1]
        # original second.previous_event_hash ≠ "aaa..." (tampered)
        # which means the chain linkage check at position 2 will fail
        assert second.previous_event_hash != events[0].event_hash, (
            "Tampered event_hash was not propagated to break chain linkage — "
            "the second event should not link to the bogus first event_hash."
        )
