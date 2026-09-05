"""
seed_demo.py — Deterministic demo fixture seeder for Phase 4.7.

Agents seeded (demo-only; do NOT use in production):
  demo_normal_agent      — active mandate, normal transaction history
  demo_policy_agent      — active mandate with a very low txn_cap (triggers BLOCK)
  demo_behavior_agent    — active mandate, no transaction history (cold-start -> high anomaly)
  demo_provenance_agent  — active mandate, no provenance supplied in request
  demo_revocation_agent  — mandate will be revoked to demonstrate BLOCK on revocation

All amounts and IDs are synthetic.
No real Razorpay payout IDs are fabricated here.
"""
import os
import sys
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.models.db import SessionLocal, Base, engine, Agent, Mandate, MandateUsage, Transaction, ProvenanceRecord, init_db


def seed(db=None):
    should_close = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close = True

    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Clean up transient scenario executions so velocity feature remains baseline-clean
        db.query(ProvenanceRecord).filter(ProvenanceRecord.txn_id.like("demo_key_%")).delete(synchronize_session=False)
        db.query(Transaction).filter(Transaction.txn_id.like("demo_key_%")).delete(synchronize_session=False)
        db.commit()

        demo_agents = [
            ("demo_normal_agent",      "Demo Normal Agent"),
            ("demo_policy_agent",      "Demo Policy Agent"),
            ("demo_behavior_agent",    "Demo Behavior Agent"),
            ("demo_provenance_agent",  "Demo Provenance Agent"),
            ("demo_revocation_agent",  "Demo Revocation Agent"),
        ]

        for agent_id, name in demo_agents:
            if not db.query(Agent).filter_by(agent_id=agent_id).first():
                db.add(Agent(agent_id=agent_id, name=name, status="ACTIVE"))
        db.flush()

        mandates = [
            # (mandate_id, agent_id, daily_cap, weekly_cap, txn_cap, categories)
            ("man_demo_normal",      "demo_normal_agent",      500_000, 2_000_000, 500_000, ["cloud", "software", "vendor"]),
            ("man_demo_policy",      "demo_policy_agent",      500_000, 2_000_000,     100, ["cloud"]),  # txn_cap=1 INR -> BLOCK
            ("man_demo_behavior",    "demo_behavior_agent",    500_000, 2_000_000, 500_000, ["cloud", "software"]),
            ("man_demo_provenance",  "demo_provenance_agent",  500_000, 2_000_000, 500_000, ["cloud"]),
            ("man_demo_revocation",  "demo_revocation_agent",  500_000, 2_000_000, 500_000, ["cloud"]),
        ]

        for mandate_id, agent_id, daily_cap, weekly_cap, txn_cap, cats in mandates:
            if not db.query(Mandate).filter_by(mandate_id=mandate_id).first():
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
                db.flush()
                db.add(MandateUsage(mandate_id=mandate_id, daily_usage=0, weekly_usage=0))
                db.flush()

        # Seed background baseline agents to establish population feature variance
        # bg_agent_1: High-frequency SaaS agent (software/cloud, varying hours)
        if not db.query(Agent).filter_by(agent_id="bg_agent_1").first():
            db.add(Agent(agent_id="bg_agent_1", name="Background SaaS Agent", status="ACTIVE"))
            db.flush()
            db.add(Mandate(
                mandate_id="man_bg_agent_1", agent_id="bg_agent_1", version=1,
                effective_from=now - timedelta(days=30), expires_at=now + timedelta(days=365),
                daily_cap=500_000, weekly_cap=2_000_000, txn_cap=500_000,
                allowed_categories=["software", "cloud", "vendor"], status="ACTIVE"
            ))
            db.flush()
            db.add(MandateUsage(mandate_id="man_bg_agent_1", daily_usage=0, weekly_usage=0))
            db.flush()
            rng1 = random.Random(101)
            for i in range(60):
                t_time = now - timedelta(days=i // 3 + 1, hours=(i * 7) % 24)
                amt = 5000 + rng1.randint(-2000, 2000)
                cat = "software" if i % 2 == 0 else "cloud"
                payee = f"ven_saas_{i % 3}"
                db.add(Transaction(
                    txn_id=f"bg_agent_1_hist_{i}", agent_id="bg_agent_1",
                    payee_id=payee, category=cat, amount=amt, timestamp=t_time,
                    status="SUCCEEDED", razorpay_payout_id=f"pout_bg1_{i}"
                ))

        # bg_agent_2: Office supplies agent (vendor category, daytime hours)
        if not db.query(Agent).filter_by(agent_id="bg_agent_2").first():
            db.add(Agent(agent_id="bg_agent_2", name="Background Vendor Agent", status="ACTIVE"))
            db.flush()
            db.add(Mandate(
                mandate_id="man_bg_agent_2", agent_id="bg_agent_2", version=1,
                effective_from=now - timedelta(days=30), expires_at=now + timedelta(days=365),
                daily_cap=500_000, weekly_cap=2_000_000, txn_cap=500_000,
                allowed_categories=["vendor", "software"], status="ACTIVE"
            ))
            db.flush()
            db.add(MandateUsage(mandate_id="man_bg_agent_2", daily_usage=0, weekly_usage=0))
            db.flush()
            rng2 = random.Random(202)
            for i in range(40):
                t_time = now - timedelta(days=i // 2 + 1, hours=(9 + (i * 2) % 8))
                amt = 15000 + rng2.randint(-4000, 4000)
                payee = f"ven_supplies_{i % 2}"
                db.add(Transaction(
                    txn_id=f"bg_agent_2_hist_{i}", agent_id="bg_agent_2",
                    payee_id=payee, category="vendor", amount=amt, timestamp=t_time,
                    status="SUCCEEDED", razorpay_payout_id=f"pout_bg2_{i}"
                ))

        # bg_agent_3: Heavy infra agent (cloud category, large amounts)
        if not db.query(Agent).filter_by(agent_id="bg_agent_3").first():
            db.add(Agent(agent_id="bg_agent_3", name="Background Infra Agent", status="ACTIVE"))
            db.flush()
            db.add(Mandate(
                mandate_id="man_bg_agent_3", agent_id="bg_agent_3", version=1,
                effective_from=now - timedelta(days=30), expires_at=now + timedelta(days=365),
                daily_cap=500_000, weekly_cap=2_000_000, txn_cap=500_000,
                allowed_categories=["cloud"], status="ACTIVE"
            ))
            db.flush()
            db.add(MandateUsage(mandate_id="man_bg_agent_3", daily_usage=0, weekly_usage=0))
            db.flush()
            rng3 = random.Random(303)
            for i in range(50):
                t_time = now - timedelta(days=i + 1, hours=(i * 5) % 24)
                amt = 30000 + rng3.randint(-10000, 10000)
                db.add(Transaction(
                    txn_id=f"bg_agent_3_hist_{i}", agent_id="bg_agent_3",
                    payee_id="ven_infra_main", category="cloud", amount=amt, timestamp=t_time,
                    status="SUCCEEDED", razorpay_payout_id=f"pout_bg3_{i}"
                ))

        # Seed historical SUCCEEDED transactions for demo_normal_agent to establish normal baseline profile
        if db.query(Transaction).filter_by(agent_id="demo_normal_agent").count() == 0:
            rng = random.Random(42)
            for d in range(48, 0, -1):
                amt = 10000 + rng.randint(-200, 200)
                t_stamp = now - timedelta(hours=23 * d)
                db.add(Transaction(
                    txn_id=f"demo_normal_hist_{d}",
                    agent_id="demo_normal_agent",
                    payee_id="ven_test_normal",
                    category="cloud",
                    amount=amt,
                    timestamp=t_stamp,
                    status="SUCCEEDED",
                    razorpay_payout_id=f"pout_hist_{d}",
                ))

        db.commit()

        from gateway.risk.orchestrator import reset_model_singleton
        reset_model_singleton()

        print("Demo fixtures seeded successfully.")
        print("Agents:", [a[0] for a in demo_agents])

    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed()
