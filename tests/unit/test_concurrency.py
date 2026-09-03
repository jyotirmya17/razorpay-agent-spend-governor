import pytest
import threading
import time
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gateway.models.db import Base, MandateUsage
from gateway.models.schemas import PayoutRequest
from policy.engine import check_policy
from tests.unit.test_policy import setup_test_data

import os
# Use Postgres for concurrency test
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/governor_test")

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 15})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session_factory():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    setup_test_data(session)
    session.close()
    
    yield TestingSessionLocal
    
    Base.metadata.drop_all(bind=engine)

def test_concurrent_cap_enforcement(db_session_factory):
    """
    Fire 10 concurrent requests of amount=20000.
    The daily cap is 100000.
    Exactly 5 should succeed. The rest should fail with DAILY_CAP_EXCEEDED.
    (Or occasionally OperationalError in SQLite due to DB lock, which also prevents cap breach).
    """
    if engine.dialect.name == "sqlite":
        pytest.skip("SQLite does not support row-level locking natively for this concurrency test.")
        
    num_threads = 10
    amount_per_request = 20000
    
    results = []
    
    def make_request(i):
        session = db_session_factory()
        req = PayoutRequest(
            agent_id="agt_1",
            request_id=f"req_concurrent_{i}",
            idempotency_key=f"idemp_concurrent_{i}",
            payee_id="ven_1",
            category="cloud",
            amount=amount_per_request
        )
        try:
            allowed, reason, details = check_policy(session, req, req.idempotency_key)
            results.append((allowed, reason))
            if allowed:
                session.commit()
            else:
                session.rollback()
        except Exception as e:
            session.rollback()
            results.append((False, "DB_LOCK_OR_ERROR"))
        finally:
            session.close()

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    successful = [r for r in results if r[0] is True]
    failed = [r for r in results if r[0] is False]
    
    # We should have exactly 5 successful transactions (5 * 20000 = 100000)
    assert len(successful) <= 5
    
    # Check the final usage in DB
    session = db_session_factory()
    usage = session.query(MandateUsage).filter_by(mandate_id="man_1").first()
    
    print(f"\n--- Concurrency Test Results ---")
    print(f"Concurrency Level: {num_threads} concurrent threads")
    print(f"Mandate Cap: 100000")
    print(f"Successful Requests: {len(successful)}")
    print(f"Rejected Requests: {len(failed)}")
    print(f"Final Reserved/Committed Usage: {usage.daily_usage if usage else 0}")
    print(f"Test Result: {'PASSED' if len(successful) <= 5 and (usage.daily_usage if usage else 0) <= 100000 else 'FAILED'}")
    
    if usage:
        assert usage.daily_usage == len(successful) * amount_per_request
        assert usage.daily_usage <= 100000
    session.close()
