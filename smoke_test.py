import os
import uuid
import logging

# Ensure we use an isolated sqlite DB for the smoke test
os.environ["DATABASE_URL"] = "sqlite:///smoke_test.db"

from sqlalchemy.orm import sessionmaker
from gateway.models.db import engine, Base, Agent, Mandate, MandateUsage
from gateway.models.schemas import PayoutRequest
from policy.engine import check_policy
from execution.service import ExecutionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_smoke_test():
    # Verify environment variables
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    account_number = os.environ.get("RAZORPAY_ACCOUNT_NUMBER")
    fund_account_id = os.environ.get("FUND_ACCOUNT_ID")
    
    if not key_id or not key_secret or not account_number or not fund_account_id:
        logger.error("Configuration missing. Cannot run smoke test.")
        print(f"KEY_ID present: {bool(key_id)}")
        print(f"KEY_SECRET present: {bool(key_secret)}")
        print(f"ACCOUNT_NUMBER present: {bool(account_number)}")
        print(f"FUND_ACCOUNT_ID present: {bool(fund_account_id)}")
        return
        
    if not key_id.startswith("rzp_test_"):
        logger.error("RAZORPAY_KEY_ID must be a test key starting with 'rzp_test_'")
        return

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # 1. Setup Data
    agent_id = "agt_smoke_1"
    mandate_id = "man_smoke_1"
    
    # Check if agent exists
    if not db.query(Agent).filter_by(agent_id=agent_id).first():
        agent = Agent(agent_id=agent_id, name="Smoke Test Agent", status="ACTIVE")
        db.add(agent)
        
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        mandate = Mandate(
            mandate_id=mandate_id,
            agent_id=agent_id,
            version=1,
            effective_from=now - timedelta(days=1),
            expires_at=now + timedelta(days=10),
            daily_cap=500000,
            weekly_cap=500000,
            txn_cap=500000,
            allowed_categories=["cloud", "test"],
            status="ACTIVE"
        )
        db.add(mandate)
        
        usage = MandateUsage(mandate_id=mandate_id, daily_usage=0, weekly_usage=0)
        db.add(usage)
        db.commit()

    # 2. Prepare payout request
    idempotency_key = f"smoke_test_txn_{uuid.uuid4().hex[:8]}"
    
    request = PayoutRequest(
        request_id=f"req_{uuid.uuid4().hex[:8]}",
        idempotency_key=idempotency_key,
        agent_id=agent_id,
        payee_id=fund_account_id,
        category="test",
        amount=100 # Exactly 100 paise (1.00 INR)
    )
    
    # 3. Policy Check
    allowed, status, mandate_details = check_policy(db, request, idempotency_key)
    
    if not allowed:
        logger.error(f"Policy check failed: {status}")
        return
        
    logger.info(f"Policy approved. Txn ID: {idempotency_key}")
    
    # 4. Execute Payout
    service = ExecutionService()
    service.execute_spend(db, request, idempotency_key)
    
    # 5. Verify and Print Result
    from gateway.models.db import Transaction, IdempotencyRecord
    txn = db.query(Transaction).filter_by(txn_id=idempotency_key).first()
    idemp = db.query(IdempotencyRecord).filter_by(idempotency_key=idempotency_key).first()
    
    print("==================================================")
    print("FIRST PAYOUT RESULT:")
    print(f"Transaction ID (Internal): {txn.txn_id}")
    print(f"Razorpay Payout ID: {txn.razorpay_payout_id}")
    print(f"Status: {txn.status}")
    print(f"Idempotency Status: {idemp.status}")
    print(f"Idempotency Payload: {idemp.response_payload}")
    print("==================================================")
    
    # 6. Idempotency Test
    print("\n--- Testing Idempotency Replay ---")
    allowed2, status2, details2 = check_policy(db, request, idempotency_key)
    if not allowed2:
        print(f"Policy rejected duplicate natively: {status2}")
    else:
        # If it returns allowed=True, we would normally execute.
        # But wait, our check_policy should return False for duplicates.
        print("Idempotency replay allowed? It shouldn't be. Let's see what happens.")
        
    txn2 = db.query(Transaction).filter_by(txn_id=idempotency_key).first()
    print(f"Transaction status after replay attempt: {txn2.status}")
    print(f"Razorpay Payout ID after replay attempt: {txn2.razorpay_payout_id}")
    print("==================================================")

if __name__ == "__main__":
    run_smoke_test()
