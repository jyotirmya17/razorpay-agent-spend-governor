import os
import sys
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.config import get_config
from gateway.models.db import SessionLocal, Base, engine, Agent, Mandate, MandateUsage, Transaction, init_db

def seed_prod(dry_run=True):
    """
    Safely seeds production database with required demo fixtures.
    Does NOT delete, truncate, or reset any existing data.
    """
    safety_env = os.environ.get("SEED_PRODUCTION_DEMO", "false").lower()
    if safety_env != "true" and not dry_run:
        print("ERROR: Refusing to mutate database. SEED_PRODUCTION_DEMO=true is required.")
        return

    # In dry-run we just inspect. In active mode we mutate if needed.
    print(f"--- STARTING SEED (DRY_RUN={dry_run}) ---")
    
    init_db()
    db = SessionLocal()
    
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        demo_agents = [
            ("procurement-agent", "Procurement Agent"),
            ("finance-agent",     "Finance Agent"),
            ("marketing-agent",   "Marketing Agent"),
            ("support-agent",     "Support Agent"),
        ]

        # 1. AGENTS
        print("\n[AGENTS]")
        for agent_id, name in demo_agents:
            existing = db.query(Agent).filter_by(agent_id=agent_id).first()
            if existing:
                if existing.name != name or existing.status != "ACTIVE":
                    print(f"  CONFLICT: Agent {agent_id} exists but with mismatch (name={existing.name}, status={existing.status})")
                    if not dry_run: raise Exception(f"Conflict on Agent {agent_id}")
                else:
                    print(f"  MATCH: Agent {agent_id} already exists and matches.")
            else:
                print(f"  MISSING: Agent {agent_id} -> Will create.")
                if not dry_run:
                    db.add(Agent(agent_id=agent_id, name=name, status="ACTIVE"))

        if not dry_run:
            db.flush()

        # 2. MANDATES
        print("\n[MANDATES]")
        mandates = [
            ("man_procurement", "procurement-agent", 500000, 2000000, 500000, ["cloud", "software", "vendor"]),
            ("man_finance",     "finance-agent",     500000, 2000000, 100000, ["cloud", "finance"]),  
            ("man_marketing",   "marketing-agent",   500000, 2000000, 500000, ["cloud", "software", "ads"]),
            ("man_support",     "support-agent",     500000, 2000000, 500000, ["cloud", "refunds"]),
        ]

        for mandate_id, agent_id, daily_cap, weekly_cap, txn_cap, cats in mandates:
            existing_man = db.query(Mandate).filter_by(mandate_id=mandate_id).first()
            if existing_man:
                match = (
                    existing_man.agent_id == agent_id and
                    existing_man.daily_cap == daily_cap and
                    existing_man.weekly_cap == weekly_cap and
                    existing_man.txn_cap == txn_cap and
                    set(existing_man.allowed_categories) == set(cats) and
                    existing_man.status == "ACTIVE"
                )
                if match:
                    print(f"  MATCH: Mandate {mandate_id} already exists and matches.")
                else:
                    print(f"  CONFLICT: Mandate {mandate_id} exists but values differ. Stop.")
                    if not dry_run: raise Exception(f"Conflict on Mandate {mandate_id}")
            else:
                print(f"  MISSING: Mandate {mandate_id} -> Will create.")
                if not dry_run:
                    db.add(Mandate(
                        mandate_id=mandate_id,
                        agent_id=agent_id,
                        version=1,
                        effective_from=now - timedelta(days=30),
                        expires_at=now + timedelta(days=365),
                        daily_cap=daily_cap,
                        weekly_cap=weekly_cap,
                        txn_cap=txn_cap,
                        allowed_categories=cats,
                        status="ACTIVE",
                    ))

        if not dry_run:
            db.flush()

        # 3. MANDATE USAGE
        print("\n[MANDATE USAGE]")
        for mandate_id, _, _, _, _, _ in mandates:
            existing_mu = db.query(MandateUsage).filter_by(mandate_id=mandate_id).first()
            if existing_mu:
                print(f"  FOUND: MandateUsage for {mandate_id} exists (daily={existing_mu.daily_usage}, weekly={existing_mu.weekly_usage}). Will NOT reset.")
            else:
                print(f"  MISSING: MandateUsage for {mandate_id} -> Will create (0, 0).")
                if not dry_run:
                    db.add(MandateUsage(mandate_id=mandate_id, daily_usage=0, weekly_usage=0))

        if not dry_run:
            db.flush()

        # 4. TRANSACTIONS BASELINE
        print("\\n[TRANSACTIONS BASELINE]")
        demo_payee_id = get_config().demo_fund_account_id
        rng = random.Random(42)
        txns_to_create = 0
        txns_to_update = 0
        
        for d in range(48, 0, -1):
            txn_id = f"demo_normal_hist_{d}"
            existing_txn = db.query(Transaction).filter_by(txn_id=txn_id).first()
            
            amt = 10000 + rng.randint(-200, 200)
            
            # Realistic timestamp logic:
            # Spread 48 transactions randomly over the last ~25 days during normal business hours
            days_ago = (d // 2) + 1  
            business_hour = rng.randint(9, 17) 
            minute = rng.randint(0, 59)
            t_stamp = (now - timedelta(days=days_ago)).replace(
                hour=business_hour, 
                minute=minute, 
                second=0, 
                microsecond=0
            )
            
            payee = demo_payee_id if d % 2 == 0 else "ven_test_normal"
            
            if existing_txn:
                # Update existing demo transactions to fix the baseline
                txns_to_update += 1
                if not dry_run:
                    existing_txn.timestamp = t_stamp
                    existing_txn.amount = amt
                    existing_txn.payee_id = payee
                    existing_txn.agent_id = "procurement-agent"
            else:
                txns_to_create += 1
                if not dry_run:
                    db.add(Transaction(
                        txn_id=txn_id,
                        agent_id="procurement-agent",
                        payee_id=payee,
                        category="cloud",
                        amount=amt,
                        timestamp=t_stamp,
                        status="SUCCEEDED",
                        razorpay_payout_id=f"pout_hist_{d}",
                    ))
        
        if txns_to_update > 0:
            print(f"  FOUND: {txns_to_update}/48 baseline transactions -> Will UPDATE to realistic baseline.")
        if txns_to_create > 0:
            print(f"  MISSING: {txns_to_create}/48 baseline transactions -> Will CREATE realistic baseline.")
        if txns_to_update == 0 and txns_to_create == 0:
            print(f"  MATCH: All 48 baseline transactions for procurement-agent already exist.")

        # FINAL COMMIT
        if not dry_run:
            db.commit()
            print("\nSUCCESS: Production demo fixtures successfully seeded.")
        else:
            db.rollback()
            print("\nSUCCESS: Dry run completed with no modifications.")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: Transaction rolled back due to error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    is_dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        is_dry_run = False
    
    seed_prod(dry_run=is_dry_run)
